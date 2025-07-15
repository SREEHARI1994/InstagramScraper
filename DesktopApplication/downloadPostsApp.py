import os
import requests
import concurrent.futures
from instagrapi import Client
from datetime import datetime
import sys

# Extract arguments from command-line
if len(sys.argv) < 4:
    print("You didn't provide all the necessary inputs")
    sys.exit(1)

target_username = sys.argv[1]
folder = sys.argv[2]
number_of_things=int(sys.argv[3])
print(str(number_of_things))

# Instagram Login Credentials
SAVE_FOLDER=folder
SESSION_FILE = "session.json"


# Initialize Instagram Client
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

def download_all_posts(username):
    user_id = cl.user_id_from_username(username)
    try:
        #posts = [m for m in cl.user_medias(user_id,amount=number_of_things) if m.media_type != 2]  # Exclude reels
        all_media=cl.user_medias(user_id)
        all_posts=[m for m in all_media if m.media_type !=2]
        print(len(all_posts))
        if number_of_things==0:
            posts=all_posts
        else:
            posts=all_posts[:number_of_things]
    except KeyError as e:
        print(f"⚠️ Warning: KeyError encountered: {e}, but continuing...\n\n")
        #posts = []
    #print(posts)
    print("\nIgnore the KeyError above and wait for sometime,the program will coninue to run and work correctly\n")
    if not posts:
        print("No posts found!")
        return
    
    os.makedirs(SAVE_FOLDER, exist_ok=True)
    tasks = []
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for index, post in enumerate(posts, start=1):
            post_date = post.taken_at.strftime("%Y-%m-%d")

            # For single image posts
            if post.media_type == 1:
                image_url = post.thumbnail_url or post.image_versions2['candidates'][0]['url']
                filename = os.path.join(SAVE_FOLDER, f"post{index}_{post_date}.jpg")
                tasks.append(executor.submit(download_file, image_url, filename))

            # For carousel posts (multi-image)
            if post.media_type == 8:
                for media_index, resource in enumerate(post.resources, start=1):
                    ext = "mp4" if resource.video_url else "jpg"
                    url = resource.video_url if ext == "mp4" else resource.thumbnail_url
                    filename = os.path.join(SAVE_FOLDER, f"post{index}_{post_date}_{media_index}.{ext}")
                    tasks.append(executor.submit(download_file, url, filename))
    
    concurrent.futures.wait(tasks)
    print("✅ All posts downloaded successfully!")

# Example Usage
download_all_posts(target_username)
#sys.exit(1)