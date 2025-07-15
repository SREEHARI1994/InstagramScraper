import os
import requests
import threading
from instagrapi import Client
from datetime import datetime
import sys

# Extract arguments from command-line
if len(sys.argv) < 3:
    print("Usage: script.py <username> <folder> [<number> <start_date> <end_date>]")
    sys.exit(1)

target_username = sys.argv[1]
folder = sys.argv[2]

SAVE_FOLDER = folder
SESSION_FILE = "session.json"


# Initialize Instagram Client
cl = Client()

try:
    cl.load_settings(SESSION_FILE)
    cl.get_timeline_feed()  # Test a lightweight request to validate session
    print("✅ Session loaded successfully!")
            
except Exception as e:
    print("⚠️ Failed to load session, log in again")


def download_file(url, filename):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"✅ Downloaded: {filename}")
    except Exception as e:
        print(f"❌ Error downloading {filename}: {e}")

def download_story(story, index):
    media_date = story.taken_at.strftime("%Y-%m-%d")
    media_time = story.taken_at.strftime("%H-%M-%S")
    os.makedirs(SAVE_FOLDER, exist_ok=True)
    
    if story.media_type == 2:  # Video Story
        filename = os.path.join(SAVE_FOLDER, f"story{index}_{media_date}_{media_time}.mp4")
        download_file(story.video_url, filename)
    else:  # Image Story
        filename = os.path.join(SAVE_FOLDER, f"story{index}_{media_date}_{media_time}.jpg")
        download_file(story.thumbnail_url, filename)

def download_all_stories(username):
    try:
        user_id = cl.user_id_from_username(username)
        stories = cl.user_stories(user_id)
        story_present=True
        if not stories:
            story_present=False
        threads = []
        
        for index, story in enumerate(stories, start=1):
            thread = threading.Thread(target=download_story, args=(story, index))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        if story_present:
            print("✅ All stories downloaded successfully!")
        else:
            print("The user has not added any stories for the day\n")
    except Exception as e:
        print(f"❌ Error fetching stories: {e}")

# Example Usage
download_all_stories(target_username)
