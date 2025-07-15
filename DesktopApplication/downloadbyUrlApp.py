import os
import sys
import requests
from instagrapi import Client
from urllib.parse import urlparse

# Extract arguments from command-line
if len(sys.argv) < 3:
    print("Usage: script.py <username> <folder> [<number> <start_date> <end_date>]")
    sys.exit(1)

instagram_url = sys.argv[1]
SAVE_FOLDER = sys.argv[2]

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


# Function to Save Post Details to TXT File
def save_post_info(post, filename):
    try:
        # Extracting metadata safely
        caption = post.caption_text if hasattr(post, "caption_text") else "No Caption"
        date_str = post.taken_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(post, "taken_at") else "Unknown Date"
        comments_count = post.comment_count if hasattr(post, "comment_count") else 0
        likes_count = post.like_count if hasattr(post, "like_count") else 0
        
        # Ensure usertags exist and extract usernames
        if hasattr(post, "usertags") and post.usertags:
            tagged_users = ", ".join([ut.user.username for ut in post.usertags if hasattr(ut.user, "username")])
        else:
            tagged_users = "None"
        
        # Ensure location exists
        location = post.location.name if hasattr(post, "location") and post.location else "No Location"

        # Fetch all comments (if available)
        comments = []
        try:
            media_id = post.id
            all_comments = cl.media_comments(media_id, amount=0)  # Fetch all comments
            for comment in all_comments:
                comment_text = comment.text if hasattr(comment, "text") else "No Comment"
                comment_user = comment.user.username if hasattr(comment.user, "username") else "Unknown User"
                comment_time = comment.created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(comment, "created_at") else "Unknown Time"
                comments.append(f"{comment_time} - @{comment_user}: {comment_text}")
        except Exception as e:
            comments.append(f"Error fetching comments: {e}")

        # Generate metadata content
        info_content = f"""📅 Date: {date_str}
📝 Caption: {caption}
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


def download_instagram_content(url):
    try:
        media_pk = cl.media_pk_from_url(url)
        media_info = cl.media_info(media_pk)
        post_date = media_info.taken_at.strftime("%Y-%m-%d")
        
        os.makedirs(SAVE_FOLDER, exist_ok=True)
        
        if media_info.media_type == 1:  # Photo
            filename = os.path.join(SAVE_FOLDER, f"post_{post_date}.jpg")
            download_file(media_info.thumbnail_url, filename)
            # Save Metadata
            metadata_filename = filename.replace(f".jpg", ".txt")
            save_post_info(media_info, metadata_filename)
        elif media_info.media_type == 2:  # Video or Reel
            filename = os.path.join(SAVE_FOLDER, f"reel_{post_date}.mp4")
            download_file(media_info.video_url, filename)
            # Download reel thumbnail
            thumb_filename = os.path.join(SAVE_FOLDER, f"reel_{post_date}_thumb.jpg")
            download_file(media_info.thumbnail_url, thumb_filename)
            metadata_filename = filename.replace(f".mp4", ".txt")
            save_post_info(media_info, metadata_filename)
        elif media_info.media_type == 8:  # Album (Multiple Photos/Videos)
            for index, resource in enumerate(media_info.resources, start=1):
                ext = "mp4" if resource.video_url else "jpg"
                url = resource.video_url if ext == "mp4" else resource.thumbnail_url
                filename = os.path.join(SAVE_FOLDER, f"post_{post_date}_{index}.{ext}")
                download_file(url, filename)
            metadata_filename = os.path.join(SAVE_FOLDER, f"post_{post_date}.txt")
            save_post_info(media_info, metadata_filename)
        else:
            print("⚠️ Unsupported media type!")
    except Exception as e:
        print(f"❌ Error fetching media: {e}")

download_instagram_content(instagram_url)
