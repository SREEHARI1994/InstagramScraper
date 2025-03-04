import os
import requests
import threading
from instagrapi import Client
from datetime import datetime

# Instagram Credentials
USERNAME = "your_username"
PASSWORD = "your_password"
SESSION_FILE = "session.json"

# Initialize Instagrapi
cl = Client()
def login():
    if os.path.exists(SESSION_FILE):
        try:
            cl.load_settings(SESSION_FILE)
            cl.login(USERNAME, PASSWORD)
            print("✅ Session loaded successfully!")
            return
        except Exception as e:
            print("⚠️ Failed to load session, logging in again...")
    
    cl.login(USERNAME, PASSWORD)
    cl.dump_settings(SESSION_FILE)
    print("✅ Logged in and session saved!")

login()

# Target Instagram Account
TARGET_USER = "target_user_name"
SAVE_FOLDER = r"Path to the folder where you want the reels saved"

# Ensure Save Folder Exists
os.makedirs(SAVE_FOLDER, exist_ok=True)

# Get User ID
user_id = cl.user_id_from_username(TARGET_USER)

# Fetch All Reels (1 API Call)
reels = cl.user_clips(user_id, amount=0)

# Download Function (Parallel Execution)
def download_reel(index, reel):
    if not reel.video_url:
        print(f"❌ Skipping Reel {index}, No Video URL Found!")
        return

    # Extract Date & Format as YYYY-MM-DD
    date_str = reel.taken_at.strftime("%Y-%m-%d")

    # Generate Filename (Only Reel Index & Date)
    filename = os.path.join(SAVE_FOLDER, f"reel{index}_{date_str}.mp4")

    try:
        response = requests.get(reel.video_url, stream=True)
        response.raise_for_status()
        
        with open(filename, "wb") as file:
            for chunk in response.iter_content(chunk_size=16384):
                file.write(chunk)

        print(f"✅ Downloaded Reel {index} ({date_str}): {filename}")
    
    except Exception as e:
        print(f"❌ Error downloading Reel {index}: {e}")

# Create Threads for Parallel Downloads
threads = []
for index, reel in enumerate(reels, start=1):
    thread = threading.Thread(target=download_reel, args=(index, reel))
    threads.append(thread)
    thread.start()

# Wait for All Threads to Finish
for thread in threads:
    thread.join()

print("✅ All Reels Downloaded Successfully!")
