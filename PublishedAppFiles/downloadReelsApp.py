import os
import requests
import threading
from instagrapi import Client
from datetime import datetime
import time
#import signal
import sys


# Extract arguments from command-line
if len(sys.argv) < 4:
    print("You didn't provide all the necessary inputs")
    sys.exit(1)

target_username = sys.argv[1]
SAVE_FOLDER = sys.argv[2]
number_of_things=int(sys.argv[3])
amount=number_of_things
#print(str(number_of_things))

# Instagram Credentials
SESSION_FILE = "session.json"

# Initialize Instagrapi
cl = Client()

def login():
    if os.path.exists(SESSION_FILE):
        try:
            cl.load_settings(SESSION_FILE)
            #cl.login(USERNAME, PASSWORD)
            print("✅ Session loaded successfully!")
            return
        except Exception as e:
            print(f"⚠️ Failed to load session, login in again: {e}")

login()

# Ensure Save Folder Exists
os.makedirs(SAVE_FOLDER, exist_ok=True)

# Get User ID
user_id = cl.user_id_from_username(target_username)

# Fetch All Reels (1 API Call)
reels = cl.user_clips(user_id, amount) #replace amount=0 with the number to get only that many number of latest reels
total=len(reels)
print(f"Total number of reels to download is {total} Stand by \n")
downloaded=0
error =0
last_success_time = time.time()

# Download Function with Retry Logic
def download_reel(index, reel, max_retries=3):
    global downloaded, error, last_success_time
    if not reel.video_url:
        print(f"❌ Skipping Reel {index}, No Video URL Found!")
        return

    date_str = reel.taken_at.strftime("%Y-%m-%d")
    filename = os.path.join(SAVE_FOLDER, f"reel{index}_{date_str}.mp4")
    thumb_filename = os.path.join(SAVE_FOLDER, f"reel{index}_{date_str}_thumb.jpg")

    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(reel.video_url, stream=True)
            response.raise_for_status()

            with open(filename, "wb") as file:
                for chunk in response.iter_content(chunk_size=16384):
                    file.write(chunk)
        
            downloaded=downloaded+1
            last_success_time = time.time()
            print(f"✅ Downloaded Reel {index} ({date_str}): {filename}")
            
            # Download Thumbnail (if available)
            if reel.thumbnail_url:
                response = requests.get(reel.thumbnail_url, stream=True)
                response.raise_for_status()
                with open(thumb_filename, "wb") as file:
                    for chunk in response.iter_content(chunk_size=16384):
                        file.write(chunk)
                print(f"✅ Downloaded Thumbnail for Reel {index}: {thumb_filename}")
            
            return  # Exit loop if successful

        except requests.exceptions.RequestException as e:
            retries += 1
            print(f"⚠️ Error downloading Reel {index}: {e} (Attempt {retries} of {max_retries})")
            time.sleep(3)  # Add delay before retrying

    print(f"❌ Failed to download Reel {index} after {max_retries} attempts")
    error=error + 1
# Create Threads for Parallel Downloads
threads = []
for index, reel in enumerate(reels, start=1):
    thread = threading.Thread(target=download_reel, args=(index, reel))
    threads.append(thread)
    thread.start()
    

# -----------------------------
# Timeout Watchdog (4 min inactivity)
# -----------------------------
timeout_seconds = 240  # 4 minutes
check_interval = 5     # check every 5 seconds

while any(thread.is_alive() for thread in threads):
    if time.time() - last_success_time > timeout_seconds:
        print("⏰ No download progress for 4 minutes. Exiting safely...")
        os._exit(0)
    time.sleep(check_interval)

# -----------------------------
# Wait for All Threads to Finish (final join)
# -----------------------------
for thread in threads:
    thread.join()



# -----------------------------
# Summary
# -----------------------------
print(f"\n✅ Finished!")
print(f"Downloaded: {downloaded}")
print(f"Errors: {error}")
print(f"Total Reels Attempted: {total}")

if downloaded + error == total:
    print("✅ All Reels Downloaded Successfully!")
else:
    print("⚠️ Some downloads may have failed.")