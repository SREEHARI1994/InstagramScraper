import os
import requests
import threading
import time
import random
from instagrapi import Client
from datetime import datetime
import sys


# Extract arguments from command-line
if len(sys.argv) < 6:
    print("You didn't provide all the necessary inputs")
    sys.exit(1)

target_username = sys.argv[1]
folder = sys.argv[2]
passed_start_date=sys.argv[3]
passed_end_date=sys.argv[4]
call=sys.argv[5]
print(passed_start_date)
print(passed_end_date)
SESSION_FILE = "session.json"

# Initialize Instagram Client
cl = Client()

try:
    cl.load_settings(SESSION_FILE)
    cl.get_timeline_feed()  # Test a lightweight request to validate session
    print("✅ Session loaded successfully!")
            
except Exception as e:
    print("⚠️ Failed to load session, log in again")

# Set Folder Paths
SAVE_FOLDER = folder
os.makedirs(SAVE_FOLDER, exist_ok=True)

# Function to download media
def download_file(url, filename):
    if not url:
        print(f"⚠️ Skipping: No URL for {filename}")
        return

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(filename, "wb") as file:
            for chunk in response.iter_content(chunk_size=16384):
                file.write(chunk)
        print(f"✅ Downloaded: {filename}")
    except Exception as e:
        print(f"❌ Error downloading {filename}: {e}")
# Function to check if media is within date range

def is_within_date_range(media, start_date, end_date):
    media_date = media.taken_at.strftime("%Y-%m-%d")
    return start_date <= media_date <= end_date


def fetch_all_comments_safe(media_id, max_comments=100):
    """Fetches up to max_comments safely, avoiding detection."""
    try:
        comments = cl.media_comments(media_id, amount=max_comments)  # Let Instagrapi paginate automatically
        time.sleep(random.uniform(3, 6))  # Add delay to avoid detection
        return comments
    except Exception as e:
        print(f"Error fetching comments: {e}")
        return []


def save_post_info(post, filename):
    try:
        # Fetch full media details to get views
        try:
            detailed_post = cl.media_info(post.id)  # ✅ Fetch full media details
            views_count = getattr(detailed_post, "view_count", "Unknown")
            if views_count==0:
                views_count="Not available"
        except Exception as e:
            print(f"⚠️ Failed to fetch detailed post info: {e}")
            views_count = "Unknown"

        # Extract metadata safely
        caption = post.caption_text if hasattr(post, "caption_text") else "No Caption"
        date_str = post.taken_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(post, "taken_at") else "Unknown Date"
        comments_count = post.comment_count if hasattr(post, "comment_count") else 0
        likes_count = post.like_count if hasattr(post, "like_count") else 0

        # Extract usertags
        tagged_users = ", ".join([ut.user.username for ut in post.usertags]) if hasattr(post, "usertags") else "None"

        # Extract location
        location = post.location.name if hasattr(post, "location") and post.location else "No Location"

        # Fetch all comments safely
        comments = []
        try:
            all_comments = fetch_all_comments_safe(post.id, max_comments=100)
            for comment in all_comments:
                comment_text = getattr(comment, "text", "No Comment")
                comment_user = getattr(comment.user, "username", "Unknown User")
                comment_time = getattr(comment, "created_at", None)

                if comment_time:
                    comment_time = comment_time.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    comment_time = "Unknown Time"

                comments.append(f"{comment_time} - @{comment_user}: {comment_text}")
        except Exception as e:
            comments.append(f"Error fetching comments: {e}")

        # Generate metadata content
        info_content = f"""📅 Date: {date_str}
📝 Caption: {caption}
👀 Views: {views_count}  
❤️ Likes: {likes_count}
💬 Comments: {comments_count}
🏷️ Tagged Users: {tagged_users}
📍 Location: {location}
🔗 Post URL: https://www.instagram.com/p/{post.code}/

🗨️ Comments:
""" + "\n".join(comments)

        # Save metadata to a text file
        with open(filename, "w", encoding="utf-8") as file:
            file.write(info_content)

        print(f"✅ Metadata saved: {filename}")

    except Exception as e:
        print(f"❌ Error saving metadata: {e}")


# Function to download reels between dates
def download_reels_between_dates(username, start_date, end_date=None):
    user_id = cl.user_id_from_username(username)
    if not end_date:
        end_date = start_date
    reels = cl.user_clips(user_id)

    def download_reel(index, reel):
        date_str = reel.taken_at.strftime("%Y-%m-%d")
        video_filename = os.path.join(SAVE_FOLDER, f"reel{index}_{date_str}.mp4")
        thumb_filename = os.path.join(SAVE_FOLDER, f"reel{index}_{date_str}_thumb.jpg")
        metadata_filename = video_filename.replace(".mp4", ".txt")

        download_file(reel.video_url, video_filename)
        if reel.thumbnail_url:
            download_file(reel.thumbnail_url, thumb_filename)
        time.sleep(2)
        save_post_info(reel, metadata_filename)

        time.sleep(random.uniform(2, 5))  # Random delay to prevent detection

    threads = []
    reels_within_date=[]
    for reel in reels:
        if is_within_date_range(reel, start_date, end_date):
            reels_within_date.append(reel)
    
    for index, reel in enumerate(reels_within_date, start=1):
        thread = threading.Thread(target=download_reel, args=(index, reel))
        threads.append(thread)
        thread.start()
        time.sleep(random.uniform(1, 3))  # Additional delay between thread starts
    
    #print(f"total no of reels to download={len(reels_within_date)}\n")
    for thread in threads:
        thread.join()
    print(f"✅ Reels from {start_date} to {end_date} downloaded!")

# Function to download posts between dates
def download_posts_between_dates(username, start_date, end_date=None):
    user_id = cl.user_id_from_username(username)
    if not end_date:
        end_date = start_date
    #posts = cl.user_medias(user_id)  # Limit to 10 posts to avoid restrictions
    try:
        posts = [m for m in cl.user_medias(user_id, amount=0) if m.media_type != 2]  # Exclude reels
    except KeyError as e:
        print(f"⚠️ Warning: KeyError encountered: {e}, but continuing...")
        posts = []

 
    def download_post(index, post):
        date_str = post.taken_at.strftime("%Y-%m-%d")

        # Download each resource in the post (multiple images/videos)
        for media_index, resource in enumerate(post.resources, start=1):
            ext = "mp4" if resource.video_url else "jpg"
            url = resource.video_url if ext == "mp4" else resource.thumbnail_url
            filename = os.path.join(SAVE_FOLDER, f"post{index}_{date_str}_{media_index}.{ext}")

            download_file(url, filename)

            # Download thumbnail for video posts
            if ext == "mp4" and resource.thumbnail_url:
                thumb_filename = os.path.join(SAVE_FOLDER, f"post{index}_{date_str}_{media_index}_thumb.jpg")
                download_file(resource.thumbnail_url, thumb_filename)

        # Save post metadata
        metadata_filename = os.path.join(SAVE_FOLDER, f"post{index}_{date_str}.txt")
        save_post_info(post, metadata_filename)

    threads = []
    valid_posts=[post for post in posts if is_within_date_range(post, start_date, end_date)]
    if not valid_posts:
        print("No posts found!")
        return
    for index, post in enumerate(valid_posts, start=1):
        thread = threading.Thread(target=download_post, args=(index, post))
        threads.append(thread)
        thread.start()
        time.sleep(random.uniform(1, 3))  # Delay between thread starts
    print(f"total no of posts to download={len(posts)}\n")
    for thread in threads:
        thread.join()

    print(f"✅ Posts from {start_date} to {end_date} downloaded!")

if call == "post":
    if passed_start_date and passed_end_date:
        download_posts_between_dates(target_username, passed_start_date, passed_end_date)
    else:   
        date = passed_start_date or passed_end_date
        download_posts_between_dates(date)
if call == "reel":
    if passed_start_date and passed_end_date:
        download_reels_between_dates(target_username, passed_start_date, passed_end_date)
    else:   
        date = passed_start_date or passed_end_date
        download_reels_between_dates(date)