import os
from instagrapi import Client

# Instagram Credentials (Use your account)
USERNAME = "your_instagram_username"
PASSWORD = "your_password"

# Specify Save Location
SAVE_LOCATION = r"C:\Users\YourName\Downloads\LatestInstagramReel"  # Change this path

# Ensure the directory exists
os.makedirs(SAVE_LOCATION, exist_ok=True)

# Create an instance of Instagrapi Client and login
cl = Client()
try:
    cl.login(USERNAME, PASSWORD)
    print("Logged in successfully!")
except Exception as e:
    print(f"Login failed: {e}")
    exit()

# Function to download the latest reel from a public Instagram account
def download_latest_reel(username):
    """Download the latest reel from the given public Instagram account."""
    try:
        user_id = cl.user_id_from_username(username)  # Get user ID from username
        reels = cl.user_clips(user_id, amount=1)  # Fetch only the latest reel
        
        if not reels:
            print(f"No reels found for {username}.")
            return
        
        latest_reel = reels[0]  # Get the most recent reel
        reel_path = cl.clip_download(latest_reel.pk, folder=SAVE_LOCATION)  # Download the latest reel
        
        if reel_path:
            print(f"Latest reel downloaded: {reel_path}")
        else:
            print(f"Failed to download the latest reel.")

    except Exception as e:
        print(f"Error downloading latest reel: {e}")

# Specify the public Instagram username
PUBLIC_USERNAME = "instagram_user"  # Replace with the public account's username

# Download the latest reel from the specified public account
download_latest_reel(PUBLIC_USERNAME)
