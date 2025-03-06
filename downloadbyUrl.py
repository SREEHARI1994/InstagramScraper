import os
import requests
from instagrapi import Client
from urllib.parse import urlparse

# Instagram Login Credentials
USERNAME = "your_username"
PASSWORD = "your_password"
SAVE_FOLDER = r"Path to the folder where you want the reels saved"
SESSION_FILE = "session.json"

# Initialize Instagram Client
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

def download_instagram_content(url):
    try:
        media_pk = cl.media_pk_from_url(url)
        media_info = cl.media_info(media_pk)
        post_date = media_info.taken_at.strftime("%Y-%m-%d")
        
        os.makedirs(SAVE_FOLDER, exist_ok=True)
        
        if media_info.media_type == 1:  # Photo
            filename = os.path.join(SAVE_FOLDER, f"post_{post_date}.jpg")
            download_file(media_info.thumbnail_url, filename)
        elif media_info.media_type == 2:  # Video or Reel
            filename = os.path.join(SAVE_FOLDER, f"reel_{post_date}.mp4")
            download_file(media_info.video_url, filename)
            # Download reel thumbnail
            thumb_filename = os.path.join(SAVE_FOLDER, f"reel_{post_date}_thumb.jpg")
            download_file(media_info.thumbnail_url, thumb_filename)
        elif media_info.media_type == 8:  # Album (Multiple Photos/Videos)
            for index, resource in enumerate(media_info.resources, start=1):
                ext = "mp4" if resource.video_url else "jpg"
                url = resource.video_url if ext == "mp4" else resource.thumbnail_url
                filename = os.path.join(SAVE_FOLDER, f"post_{post_date}_{index}.{ext}")
                download_file(url, filename)
        else:
            print("⚠️ Unsupported media type!")
    except Exception as e:
        print(f"❌ Error fetching media: {e}")

# Example Usage
instagram_url = "link to the content you want downloaded"  # Replace with actual URL
download_instagram_content(instagram_url)
