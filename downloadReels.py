import os
import requests
import threading
from instagrapi import Client
from datetime import datetime
import time
import signal

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
reels = cl.user_clips(user_id, amount=0) #replace amount=0 with the number to get only that many number of latest reels
total=len(reels)
print(f"Total number of reels to download is {total} Stand by \n")
downloaded=0
error =0
# Download Function with Retry Logic
def download_reel(index, reel, max_retries=3):
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
            global downloaded
            downloaded=downloaded+1
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
    global error
    error=error + 1
# Create Threads for Parallel Downloads
threads = []
for index, reel in enumerate(reels, start=1):
    thread = threading.Thread(target=download_reel, args=(index, reel))
    threads.append(thread)
    thread.start()

# Wait for All Threads to Finish
for thread in threads:
    thread.join()
print("error + download="+str(error+downloaded))
if (downloaded + error)==total:
    print("✅ All Reels Downloaded Successfully!")
    os._exit(0)



def timeout_handler(signum, frame):
    raise TimeoutError("Function took too long!")

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(240)  # Set a 5-second timeout

try:
    download_reel()  # Replace with your function
except TimeoutError:
    print("Nothng seems to be happening for 4minutes.Therefore exiting\n")
    os._exit(0)

signal.alarm(0)  # Disable the alarm
print("✅ All Reels Downloaded Successfully!")
