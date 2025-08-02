"""
batch_text_generator.py
Batch processing implementation for OpenAI API calls.
Handles bulk title and story generation with up to 24-hour processing window.
"""

import os
import json
import time
from typing import List, Tuple, Dict, Optional
from openai import OpenAI
from datetime import datetime

from config_manager import get_config
from utils import read_file, create_output_folder, write_text_file


class BatchTextGenerator:
    def __init__(self):
        """Initialize the batch text generator with OpenAI client."""
        api_key = get_config("FINE_TUNED_FOR_STORIES")
        if not api_key:
            raise ValueError("OpenAI API key not configured")
        
        self.client = OpenAI(api_key=api_key)
        self.model_id = get_config("openai_model_id", "gpt-4o-mini")
        
    def prepare_batch_requests(self, num_runs: int, custom_titles: Optional[List[str]], 
                             system_prompt_title: str, system_prompt_story: str) -> str:
        """
        Prepare JSONL file with all title and story generation requests.
        Returns the path to the created JSONL file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        jsonl_filename = f"batch_input_{timestamp}.jsonl"
        
        with open(jsonl_filename, "w") as f:
            request_id = 1
            
            # First, generate title requests for those without custom titles
            for i in range(num_runs):
                if not custom_titles or i >= len(custom_titles):
                    # Need to generate title
                    title_request = {
                        "custom_id": f"title_{i}",
                        "method": "POST",
                        "url": "/v1/chat/completions",
                        "body": {
                            "model": self.model_id,
                            "messages": [
                                {"role": "system", "content": system_prompt_title},
                                {"role": "user", "content": "Generate a creative title for a story"}
                            ],
                            "temperature": 0.7
                        }
                    }
                    f.write(json.dumps(title_request) + "\n")
                    request_id += 1
            
            # Then, generate story requests
            # Note: Stories depend on titles, so this is a two-phase process
            
        return jsonl_filename
    
    def create_batch_job(self, jsonl_path: str) -> str:
        """Upload JSONL file and create batch job. Returns job ID."""
        print("📤 Uploading batch file to OpenAI...")
        
        # Upload the file
        with open(jsonl_path, "rb") as f:
            batch_file = self.client.files.create(
                file=f,
                purpose="batch"
            )
        
        print(f"✅ File uploaded: {batch_file.id}")
        
        # Create batch job
        print("🚀 Creating batch job...")
        job = self.client.batches.create(
            input_file_id=batch_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h"
        )
        
        print(f"✅ Batch job created: {job.id}")
        print("⏰ Maximum processing time: 24 hours")
        
        return job.id
    
    def poll_job_status(self, job_id: str, check_interval: int = 60) -> Dict:
        """
        Poll job status until completion. Returns job results.
        check_interval: seconds between status checks (default 60)
        """
        print("\n⏳ Waiting for batch processing to complete...")
        print("This may take up to 24 hours. You can close this program and check back later.")
        print("Job ID:", job_id)
        
        start_time = time.time()
        
        while True:
            job_status = self.client.batches.retrieve(job_id)
            elapsed_time = time.time() - start_time
            elapsed_hours = elapsed_time / 3600
            
            print(f"\r⏱️ Status: {job_status.status} | Elapsed: {elapsed_hours:.1f} hours", end="", flush=True)
            
            if job_status.status == "completed":
                print("\n✅ Batch job completed!")
                return job_status
            elif job_status.status in ("failed", "expired", "cancelled"):
                print(f"\n❌ Batch job {job_status.status}")
                raise RuntimeError(f"Batch job {job_status.status}: {job_status}")
            
            time.sleep(check_interval)
    
    def parse_batch_results(self, job_status) -> Dict[str, str]:
        """Download and parse batch results. Returns mapping of custom_id to content."""
        print("📥 Downloading results...")
        
        output_file_id = job_status.output_file_id
        if not output_file_id:
            raise ValueError("No output file ID in job status")
        
        # Download results
        file_response = self.client.files.content(output_file_id)
        output_content = file_response.read()
        
        # Parse results
        results = {}
        for line in output_content.decode("utf-8").splitlines():
            if line.strip():
                data = json.loads(line)
                custom_id = data["custom_id"]
                
                # Extract response content
                if "response" in data and data["response"]["status_code"] == 200:
                    content = data["response"]["body"]["choices"][0]["message"]["content"]
                    results[custom_id] = content
                else:
                    print(f"⚠️ Failed request: {custom_id}")
        
        print(f"✅ Retrieved {len(results)} results")
        return results
    
    def generate_stories_batch(self, num_runs: int, custom_titles: Optional[List[str]] = None) -> List[Tuple[str, str, str]]:
        """
        Generate all titles and stories using batch processing.
        This is a two-phase process: first generate titles, then stories.
        
        Returns: List of (title, story, output_folder) tuples
        """
        # Read system prompts
        title_prompt_path = get_config("title_prompt_path", "System_Title_Prompt.txt")
        story_prompt_path = get_config("story_prompt_path", "Story_System_Prompt.txt")
        
        if not os.path.exists(title_prompt_path) or not os.path.exists(story_prompt_path):
            raise FileNotFoundError("System prompt files not found")
        
        system_prompt_title = read_file(title_prompt_path)
        system_prompt_story = read_file(story_prompt_path)
        
        print("\n🎯 Starting two-phase batch processing...")
        print("Phase 1: Title generation")
        print("Phase 2: Story generation based on titles")
        
        # Phase 1: Generate titles
        titles = []
        titles_to_generate = []
        
        for i in range(num_runs):
            if custom_titles and i < len(custom_titles):
                titles.append(custom_titles[i])
            else:
                titles_to_generate.append(i)
        
        if titles_to_generate:
            print(f"\n📝 Phase 1: Generating {len(titles_to_generate)} titles via batch API...")
            
            # Create title batch
            title_jsonl = f"batch_titles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
            with open(title_jsonl, "w") as f:
                for idx in titles_to_generate:
                    request = {
                        "custom_id": f"title_{idx}",
                        "method": "POST",
                        "url": "/v1/chat/completions",
                        "body": {
                            "model": self.model_id,
                            "messages": [
                                {"role": "system", "content": system_prompt_title},
                                {"role": "user", "content": "Generate a creative title for a story"}
                            ],
                            "temperature": 0.7
                        }
                    }
                    f.write(json.dumps(request) + "\n")
            
            # Process title batch
            job_id = self.create_batch_job(title_jsonl)
            job_status = self.poll_job_status(job_id)
            title_results = self.parse_batch_results(job_status)
            
            # Insert generated titles in correct positions
            for idx in titles_to_generate:
                if f"title_{idx}" in title_results:
                    titles.insert(idx, title_results[f"title_{idx}"])
            
            # Cleanup
            os.remove(title_jsonl)
        
        # Phase 2: Generate stories based on titles
        print(f"\n📖 Phase 2: Generating {num_runs} stories via batch API...")
        
        story_jsonl = f"batch_stories_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        with open(story_jsonl, "w") as f:
            for i, title in enumerate(titles):
                request = {
                    "custom_id": f"story_{i}",
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": {
                        "model": self.model_id,
                        "messages": [
                            {"role": "system", "content": system_prompt_story},
                            {"role": "user", "content": title}
                        ],
                        "temperature": 0.8
                    }
                }
                f.write(json.dumps(request) + "\n")
        
        # Process story batch
        job_id = self.create_batch_job(story_jsonl)
        job_status = self.poll_job_status(job_id)
        story_results = self.parse_batch_results(job_status)
        
        # Create output folders and save results
        output_base = get_config("output_path", os.path.expanduser("~/DaVinci Vids"))
        os.makedirs(output_base, exist_ok=True)
        
        successful_stories = []
        for i, title in enumerate(titles):
            if f"story_{i}" in story_results:
                story = story_results[f"story_{i}"]
                
                # Create output folder
                output_folder = create_output_folder(output_base, title)
                
                # Save title and story
                write_text_file(output_folder, "title.txt", title)
                write_text_file(output_folder, "story.txt", story)
                
                successful_stories.append((title, story, output_folder))
                print(f"✅ Saved story {i+1}: {title}")
        
        # Cleanup
        os.remove(story_jsonl)
        
        return successful_stories
    
    def save_job_state(self, job_id: str, phase: str):
        """Save job state for recovery in case of interruption."""
        state_file = f".batch_job_state_{phase}.json"
        with open(state_file, "w") as f:
            json.dump({
                "job_id": job_id,
                "phase": phase,
                "timestamp": datetime.now().isoformat()
            }, f)
    
    def load_job_state(self, phase: str) -> Optional[Dict]:
        """Load saved job state if exists."""
        state_file = f".batch_job_state_{phase}.json"
        if os.path.exists(state_file):
            with open(state_file, "r") as f:
                return json.load(f)
        return None


def generate_all_stories_batch(num_runs: int, custom_titles: Optional[List[str]] = None) -> List[Tuple[str, str, str]]:
    """
    Wrapper function to generate all stories using batch processing.
    Compatible with existing pipeline interface.
    """
    print("\n⚠️ BATCH PROCESSING MODE")
    print("━" * 60)
    print("⏰ WARNING: Batch processing can take up to 24 HOURS!")
    print("   However, it's more cost-effective for large batches.")
    print("   You can close this program and results will be saved.")
    print("━" * 60)
    
    confirm = input("\nDo you understand and want to proceed? (yes/no): ").lower()
    if confirm != "yes":
        print("Batch processing cancelled.")
        return []
    
    try:
        generator = BatchTextGenerator()
        return generator.generate_stories_batch(num_runs, custom_titles)
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")
        return []