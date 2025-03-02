import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from instagrapi import Client
import os
import threading

# Instagram Login Credentials
USERNAME = "your_username"
PASSWORD = "your_password"

# Initialize Instagram Client
cl = Client()
cl.login(USERNAME, PASSWORD)

# Tkinter App
app = tk.Tk()
app.title("Instagram Downloader")
app.geometry("500x500")

save_location = tk.StringVar()
filename_prefix = tk.StringVar()
progress_var = tk.DoubleVar()

def choose_directory():
    folder_selected = filedialog.askdirectory()
    save_location.set(folder_selected)

def update_progress(value):
    progress_var.set(value)
    app.update_idletasks()

def show_alert(message):
    progress_bar.pack_forget()
    messagebox.showinfo("Download Complete", message)

def download_latest_post():
    threading.Thread(target=_download_latest_post).start()

def _download_latest_post():
    username = entry_username.get()
    user_id = cl.user_id_from_username(username)
    medias = cl.user_medias(user_id, amount=10)
    
    latest_media = next((media for media in medias if media.media_type == 1), None)
    
    if not latest_media:
        show_alert("No recent posts found!")
        return
    
    filename = os.path.join(save_location.get(), f"{filename_prefix.get()}1.jpg")
    cl.photo_download_by_url(latest_media.thumbnail_url, filename)
    show_alert("Latest post downloaded successfully!")

def download_latest_reel():
    threading.Thread(target=_download_latest_reel).start()

def _download_latest_reel():
    username = entry_username.get()
    user_id = cl.user_id_from_username(username)
    reels = cl.user_clips(user_id, amount=1)
    if not reels:
        show_alert("No reels found!")
        return
    
    filename = os.path.join(save_location.get(), f"{filename_prefix.get()}1.mp4")
    cl.clip_download(reels[0].id, filename)
    show_alert("Latest reel downloaded successfully!")

def download_all_posts():
    threading.Thread(target=_download_all_posts).start()

def _download_all_posts():
    username = entry_username.get()
    user_id = cl.user_id_from_username(username)
    medias = cl.user_medias(user_id, amount=10)
    
    for index, media in enumerate(medias, start=1):
        if media.media_type == 1:
            filename = os.path.join(save_location.get(), f"{filename_prefix.get()}{index}.jpg")
            cl.photo_download_by_url(media.thumbnail_url, filename)
        update_progress((index / len(medias)) * 100)
    progress_bar.pack_forget()
    show_alert("All posts downloaded successfully!")

def download_all_reels():
    threading.Thread(target=_download_all_reels).start()

def _download_all_reels():
    username = entry_username.get()
    user_id = cl.user_id_from_username(username)
    reels = cl.user_clips(user_id, amount=10)
    
    for index, reel in enumerate(reels, start=1):
        filename = os.path.join(save_location.get(), f"{filename_prefix.get()}{index}.mp4")
        cl.clip_download(reel.id, filename)
        update_progress((index / len(reels)) * 100)
    progress_bar.pack_forget()
    show_alert("All reels downloaded successfully!")

def download_stories():
    threading.Thread(target=_download_stories).start()

def _download_stories():
    username = entry_username.get()
    user_id = cl.user_id_from_username(username)
    stories = cl.user_stories(user_id)
    
    for index, story in enumerate(stories, start=1):
        ext = "mp4" if story.video_url else "jpg"
        filename = os.path.join(save_location.get(), f"{filename_prefix.get()}{index}.{ext}")
        cl.story_download(story.id, filename)
        update_progress((index / len(stories)) * 100)
    progress_bar.pack_forget()
    show_alert("Stories downloaded successfully!")

# UI Components with Spacing
tk.Label(app, text="Save Location:").pack(pady=5)
tk.Entry(app, textvariable=save_location, width=40).pack(pady=5)
tk.Button(app, text="Choose Folder", command=choose_directory).pack(pady=5)

tk.Label(app, text="Filename Prefix:").pack(pady=5)
tk.Entry(app, textvariable=filename_prefix, width=20).pack(pady=5)

tk.Label(app, text="Instagram Username:").pack(pady=5)
entry_username = tk.Entry(app, width=30)
entry_username.pack(pady=5)

progress_bar = ttk.Progressbar(app, orient="horizontal", length=300, mode="determinate", variable=progress_var)
progress_bar.pack(pady=10)

# Buttons with Spacing
tk.Button(app, text="Download Latest Post", command=download_latest_post).pack(pady=5)
tk.Button(app, text="Download Latest Reel", command=download_latest_reel).pack(pady=5)
tk.Button(app, text="Download All Posts", command=download_all_posts).pack(pady=5)
tk.Button(app, text="Download All Reels", command=download_all_reels).pack(pady=5)
tk.Button(app, text="Download Stories", command=download_stories).pack(pady=5)

app.mainloop()
