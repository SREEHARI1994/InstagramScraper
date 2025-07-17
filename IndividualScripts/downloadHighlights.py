import os
import time
import random
import requests
from instagrapi import Client
from datetime import datetime

SESSION_FILE = "session.json"

def sanitize_filename(name):
    """Sanitize filenames to avoid illegal characters."""
    return "".join(c if c.isalnum() or c in " _-" else "_" for c in name).strip()

def login(username, password):
    """Login using session or create a new session."""
    cl = Client()
    if os.path.exists(SESSION_FILE):
        try:
            cl.load_settings(SESSION_FILE)
            #cl.login(username, password, relogin=True)
            print("Logged in using saved session.")
            return cl
        except Exception as e:
            print(f"Session load failed: {e}, logging in again...")

    cl.login(username, password)
    cl.dump_settings(SESSION_FILE)
    print("New session saved.")
    return cl

def download_media(url, save_path, cl):
    """Download media file using requests with authentication headers."""
    if not url:
        print(f"Skipping download, URL is None for {save_path}")
        return

    headers = {
        "User-Agent": "Instagram 123.0.0.26.121 Android",
        "Referer": "https://www.instagram.com/",
        "Cookie": f"sessionid={cl.sessionid}"
    }

    try:
        #commenting out the downloading and download status print to avoid bulky output
        #print(f"Downloading: {url}")  # Debugging print
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        #print(f"Download Status: {response.status_code}, URL: {url}")
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Saved: {save_path}")
    except requests.RequestException as e:
        print(f"Failed to download {url}: {e}")

def download_highlights(username, password, target_username, save_path):
    """Download all highlight sections from a target Instagram account."""
    cl = login(username, password)

    # Check if login is working
    try:
        user_id = cl.user_id_from_username(target_username)
        print(f"Fetched user_id: {user_id}")
    except Exception as e:
        print(f"Error fetching user_id: {e}")
        return

    # Fetch highlights using authenticated request
    try:
        highlights = cl.user_highlights(user_id)
        print(f"Fetched {len(highlights)} highlights.") 
        if not highlights:
            print("No highlights found.")
            return
    except Exception as e:
        print(f"Error fetching highlights: {e}")
        return

    # Define the base save path where highlights will be stored
    base_folder = os.path.join(save_path, f"{target_username}_highlights")
    os.makedirs(base_folder, exist_ok=True)

    for index, highlight in enumerate(highlights):
        highlight_name = highlight.title.strip() if highlight.title else f"highlights_{index+1}"
        highlight_name = sanitize_filename(highlight_name)
        highlight_folder = os.path.join(base_folder, highlight_name)
        os.makedirs(highlight_folder, exist_ok=True)

        print(f"\nProcessing highlight: {highlight.title} ({highlight.id})")

        # Extract only the numeric ID
        highlight_id_numeric = highlight.id.split(":")[-1]

        # Fetch stories inside the highlight
        try:
            highlight_items = cl.highlight_info(highlight_id_numeric).items  # Use numeric ID
            print(f"Highlight {highlight.id} contains {len(highlight_items)} stories")
        except Exception as e:
            print(f"Error fetching stories for highlight {highlight.id}: {e}")
            continue  # Skip this highlight if there's an error

        for i, item in enumerate(highlight_items):
            timestamp = item.taken_at.strftime("%Y-%m-%d_%H-%M-%S")
            media_url = item.video_url if item.video_url else item.thumbnail_url
            ext = ".mp4" if item.video_url else ".jpg"
            '''
            # Debugging print statements
            print(f"Story {i+1}: {item.pk}")
            print(f"   Video URL: {item.video_url}")
            print(f"   Image URL: {item.thumbnail_url}")
            print(f"   Media URL Selected: {media_url}")
            '''
            if media_url:
                story_filename = os.path.join(highlight_folder, f"story{i+1}_{timestamp}{ext}")
                download_media(media_url, story_filename, cl)
            else:
                print(f"Warning: No media URL found for highlight {highlight_name} story {i+1}")

        # Add a random delay of 2-3 seconds between highlight sections
        # try replacing with higher values in case of instagra blocking
        delay = random.uniform(4, 5)
        print(f"Sleeping for {delay:.2f} seconds to avoid detection...")
        time.sleep(delay)

if __name__ == "__main__":
    USERNAME = "your_username"
    PASSWORD = "your_password"
    TARGET_USERNAME = "username_of_account_toBeDowloaded"
    SAVE_PATH = r"path to folder for saving highlights"  # Change this to your desired directory

    download_highlights(USERNAME, PASSWORD, TARGET_USERNAME, SAVE_PATH)
