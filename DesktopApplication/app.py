import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkcalendar import DateEntry
from datetime import datetime
from pathlib import Path

# ------------------ Login Check ------------------
SESSION_FILE = "session.json"
SESSION_EXISTS = os.path.exists(SESSION_FILE)

# ------------------ GUI Setup ------------------
root = tk.Tk()
root.title("Easy Instagram Downloader")
root.geometry("750x650")
root.resizable(False, False)

# ------------------ Tkinter Variables ------------------
url_var = tk.StringVar()
username_var = tk.StringVar()
folder_var = tk.StringVar()
number_var = tk.StringVar()
start_date_var = tk.StringVar()
end_date_var = tk.StringVar()

login_username_var = tk.StringVar()
login_password_var = tk.StringVar()

# ------------------ Functions ------------------

def browse_folder():
    folder = filedialog.askdirectory()
    if folder:
        folder_var.set(folder)

def stream_output(process):
    for line in process.stdout:
        output_text.insert(tk.END, line)
        output_text.see(tk.END)

def run_script(script_name, args):
    try:
        cmd = ["python", script_name] + args
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",   # 👈 Force UTF-8 decoding
            errors="replace"    # 👈 Replace characters that can't be decoded
        )
        threading.Thread(target=stream_output, args=(process,), daemon=True).start()
    except Exception as e:
        messagebox.showerror("Error", str(e))

def posts_diverter(username,folder,start_date,end_date,num):
    print(start_date)
    if start_date or end_date:
        run_script("downloadByDateApp.py", [
                  username, folder,
                  start_date, end_date,"post"])
    else:
        run_script("downloadPostsApp.py", [
                  username, folder,num])

def reels_diverter(username,folder,start_date,end_date,num):
    print(start_date)
    if start_date or end_date:
        run_script("downloadByDateApp.py", [
                  username, folder,
                  start_date, end_date,"reels"])
    else:
        run_script("downloadReelsApp.py", [
                  username, folder,num]) 
            
def login():
    username = login_username_var.get().strip()
    password = login_password_var.get().strip()
    if not username or not password:
        messagebox.showwarning("Missing Info", "Please enter both username and password.")
        return

    login_status_label.config(text="Attempting to Login. Please wait...", fg="blue")
    root.update_idletasks()

    from instagrapi import Client
    cl = Client()
    try:
        cl.login(username, password)
        cl.dump_settings(SESSION_FILE)
        login_status_label.config(text="")
        messagebox.showinfo("Success", "Login successful and session saved.")
        login_frame.pack_forget()
        main_ui()
    except Exception as e:
        login_status_label.config(
            text="Login Failed. Retry by closing and opening or check login on browser for challenge error",
            fg="red"
        )

def main_ui():
    # ------------------ Main App UI ------------------
    ui_frame = tk.Frame(root)
    ui_frame.pack(pady=10, padx=10, fill='x')

    # URL input
    tk.Label(ui_frame, text="URL:").grid(row=0, column=0, sticky='e')
    tk.Entry(ui_frame, textvariable=url_var, width=50).grid(row=0, column=1, columnspan=3, pady=5, sticky='w')
    tk.Button(ui_frame, text="Download URL", width=15,
              command=lambda: run_script("downloadbyUrlApp.py", [url_var.get(), folder_var.get()])).grid(row=0, column=4, padx=5)

    # Target username
    tk.Label(ui_frame, text="Target Username:").grid(row=1, column=0, sticky='e')
    tk.Entry(ui_frame, textvariable=username_var, width=30).grid(row=1, column=1, pady=5, sticky='w')

    # Folder select
    tk.Label(ui_frame, text="Select Folder:").grid(row=2, column=0, sticky='e')
    tk.Entry(ui_frame, textvariable=folder_var, width=30).grid(row=2, column=1, pady=5, sticky='w')
    tk.Button(ui_frame, text="Browse", command=browse_folder).grid(row=2, column=2, padx=5)

    # Number input
    tk.Label(ui_frame, text="Select number of things:").grid(row=3, column=0, sticky='e')
    tk.Entry(ui_frame, textvariable=number_var, width=10).grid(row=3, column=1, pady=5, sticky='w')

    # Date range
    tk.Label(ui_frame, text="Select Date Range:").grid(row=4, column=0, sticky='e')
    
    start_date_selected = False
    end_date_selected = False

    def on_start_date_selected(event):
        global start_date_selected
        start_date_selected = True

    def on_end_date_selected(event):
        global end_date_selected
        end_date_selected = True

    start_entry = DateEntry(ui_frame, textvariable=start_date_var, width=12)
    start_entry.grid(row=4, column=1, sticky='w')
    start_entry.bind("<<DateEntrySelected>>", on_start_date_selected)

    end_entry = DateEntry(ui_frame, textvariable=end_date_var, width=12)
    end_entry.grid(row=4, column=2, padx=5)
    end_entry.bind("<<DateEntrySelected>>", on_end_date_selected)
    start = start_date_var.get() if start_date_selected else ""
    end = end_date_var.get() if end_date_selected else ""
    print(start)
    print(end)
    # Buttons
    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=10)
    
    try:
        num = int(number_var.get().strip())
    except ValueError:
        num = 0  # Treat blank or invalid input as "all"
    
    tk.Button(btn_frame, text="Download Posts", width=25,
              command=lambda:posts_diverter(
                  username_var.get(), folder_var.get(),
                  start, end,str(num))).pack(pady=2)
    
    tk.Button(btn_frame, text="Download Reels", width=25,
              command=lambda:reels_diverter(
                  username_var.get(), folder_var.get(),
                  start, end,str(num))).pack(pady=2)
    
    tk.Button(btn_frame, text="Download Stories", width=25,
              command=lambda: run_script("downloadStoriesApp.py", [
                  username_var.get(), folder_var.get()])).pack(pady=2)
    
    tk.Button(btn_frame, text="Download Highlights", width=25,
              command=lambda: run_script("downloadHighlights.py", [
                  username_var.get(), folder_var.get()])).pack(pady=2)

    # Terminal Output
    tk.Label(root, text="Terminal Output:").pack(pady=(10, 0))
    global output_text
    output_text = scrolledtext.ScrolledText(root, width=90, height=18)
    output_text.pack(padx=10, pady=5)

# ------------------ Login Frame ------------------
if not SESSION_EXISTS:
    login_frame = tk.Frame(root)
    login_frame.pack(pady=10)

    tk.Label(login_frame, text="Username:").grid(row=0, column=0, padx=10, pady=5, sticky='e')
    tk.Entry(login_frame, textvariable=login_username_var, width=30).grid(row=0, column=1, padx=10, pady=5)

    tk.Label(login_frame, text="Password:").grid(row=1, column=0, padx=10, pady=5, sticky='e')
    tk.Entry(login_frame, textvariable=login_password_var, show='*', width=30).grid(row=1, column=1, padx=10, pady=5)

    tk.Button(login_frame, text="Login", command=login).grid(row=2, columnspan=2, pady=10)

    login_status_label = tk.Label(login_frame, text="", fg="blue")
    login_status_label.grid(row=3, columnspan=2, pady=5)

else:
    main_ui()

# ------------------ Run App ------------------
root.mainloop()
