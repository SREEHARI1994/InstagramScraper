import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from tkcalendar import DateEntry
from datetime import datetime
from pathlib import Path
import sys
import runpy
import io
from contextlib import redirect_stdout, redirect_stderr


# ------------------ Device Rotation ------------------
from instagrapi import Client

DEVICE_LIST = [
    {"app_version": "123.0.0.21.114", "android_version": 24, "android_release": "7.0", "dpi": "640dpi", "resolution": "1440x2560", "manufacturer": "samsung", "device": "SM-G935F", "model": "hero2lte", "cpu": "samsungexynos8890"},
    {"app_version": "150.0.0.33.120", "android_version": 29, "android_release": "10.0", "dpi": "420dpi", "resolution": "1080x2340", "manufacturer": "google", "device": "Pixel 4a", "model": "sunfish", "cpu": "qcom"},
    {"app_version": "190.0.0.41.120", "android_version": 30, "android_release": "11.0", "dpi": "480dpi", "resolution": "1080x2400", "manufacturer": "OnePlus", "device": "OnePlus8", "model": "IN2011", "cpu": "qcom"},
    {"app_version": "210.0.0.27.120", "android_version": 33, "android_release": "13.0", "dpi": "560dpi", "resolution": "1440x3120", "manufacturer": "LGE", "device": "LM-G820", "model": "G8", "cpu": "qcom"},
    {"app_version": "250.0.0.50.120", "android_version": 34, "android_release": "14.0", "dpi": "560dpi", "resolution": "1440x3120", "manufacturer": "samsung", "device": "SM-S918B", "model": "Galaxy S23 Ultra", "cpu": "qcom"},
]

current_device_index = 0  # global index tracker

def get_next_device():
    """Rotate to next device and return a Client instance"""
    global current_device_index
    current_device_index = (current_device_index + 1) % len(DEVICE_LIST)
    device = DEVICE_LIST[current_device_index]
    cl = Client()
    cl.set_device(device)
    return cl


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
option_var = tk.BooleanVar(value=False)
def browse_folder():
    folder = filedialog.askdirectory()
    if folder:
        folder_var.set(folder)

def stream_output(process):
    for line in process.stdout:
        output_text.insert(tk.END, line)
        output_text.see(tk.END)
    #process.stdout.close()

#previous working one
def run_script(script_name, args):
    def target():
        try:
            if hasattr(sys, "_MEIPASS"):
                script_path = os.path.join(sys._MEIPASS, script_name)
            else:
                script_path = script_name

            class TextRedirector(io.TextIOBase):
                def write(self, msg):
                    if msg:
                        if not msg.endswith("\n"):   # force newline if missing
                            msg += "\n"
                        output_text.insert(tk.END, msg)
                        output_text.see(tk.END)
                        output_text.update_idletasks()

                def flush(self):
                    pass


            # Redirect inside this thread
            old_stdout, old_stderr = sys.stdout, sys.stderr
            sys.stdout = sys.stderr = TextRedirector()
            old_argv = sys.argv
            #sys.argv = [script_path] + args
            try:
                sys.argv = [script_path] + args
                runpy.run_path(script_path, run_name="__main__")
            finally:
                sys.stdout, sys.stderr = old_stdout, old_stderr
                sys.argv = old_argv  # restore after script finishes


        except Exception as e:
            messagebox.showerror("Error", str(e))

    threading.Thread(target=target, daemon=True).start()



def number_extractor(num):
    try:
        new_num = int(num.strip())
    except ValueError:
        new_num = 0  # Treat blank or invalid input as "all"
    return new_num

def date_extractor(passed_date):
    l=passed_date.split("/")
    if int(l[1])//10==0:
        l[1]="0"+l[1]
    if int(l[0])//10==0:
        l[0]="0"+l[0]
    return "20"+l[2]+"-"+l[0]+"-"+l[1]

def posts_diverter(username,folder,start_date,end_date,num):
    
    number_of_things=number_extractor(num)
    if not option_var.get():
        run_script("downloadPostsApp.py", [
                  username, folder,str(number_of_things)])
        
    else:
        start_date=date_extractor(start_date)
        end_date=date_extractor(end_date)
        run_script("downloadByDateApp.py", [
                  username, folder,
                  start_date, end_date,"post"])

def reels_diverter(username,folder,start_date,end_date,num):
    
    number_of_things=number_extractor(num)  
    if not option_var.get():
    # Assume user doesn't want date filtering
         run_script("downloadReelsApp.py", [
                  username, folder,str(number_of_things)]) 
    else:
        start_date=date_extractor(start_date)
        end_date=date_extractor(end_date)
        run_script("downloadByDateApp.py", [
                  username, folder,
                  start_date, end_date,"reel"])
    

def login():
    username = login_username_var.get().strip()
    password = login_password_var.get().strip()
    if not username or not password:
        messagebox.showwarning("Missing Info", "Please enter both username and password.")
        return

    login_status_label.config(text="Attempting to Login. Please wait...", fg="blue")
    root.update_idletasks()

    
    import threading

    cl = Client()
    cl.set_device(DEVICE_LIST[current_device_index])  # <-- start with current device
    code_event = threading.Event()
    code_value = {"code": None}

    def challenge_code_handler(username_, choice):
        # This function runs in the same thread as login()
        def ask_code():
            popup = tk.Toplevel(root)
            popup.title("Instagram Verification Required")
            popup.geometry("400x200")

            # Clean display of challenge type
            choice_str = str(choice)
            if "EMAIL" in choice_str.upper():
                choice_str = "email"
            elif "SMS" in choice_str.upper() or "PHONE" in choice_str.upper():
                choice_str = "phone"
            else:
                choice_str = "registered contact"

            tk.Label(
                popup,
                text=f"A verification code was sent to your {choice_str}. Please enter it below:",
                font=("Arial", 11),
                wraplength=350,
                justify="center"
            ).pack(pady=10)

            code_var = tk.StringVar()
            tk.Entry(popup, textvariable=code_var, font=("Arial", 12)).pack(pady=5)

            def submit_code():
                code = code_var.get().strip()
                if code:
                    code_value["code"] = code
                    code_event.set()  # signal that user entered code
                    popup.destroy()
                else:
                    messagebox.showwarning("Missing Code", "Please enter the code before submitting.")

            tk.Button(popup, text="Submit", command=submit_code).pack(pady=10)

        root.after(0, ask_code)
        code_event.wait()  # ⏸️ wait until user submits code
        return code_value["code"]

    cl.challenge_code_handler = challenge_code_handler

    def do_login():
        try:
            cl.login(username, password)
            cl.dump_settings(SESSION_FILE)
            login_status_label.config(text="")
            messagebox.showinfo("Success", "Login successful and session saved.")
            login_frame.pack_forget()
            main_ui()
        except Exception as e:
            login_status_label.config(
                text="Login Failed. Check credentials or login on browser to check for on challenge error.",
                fg="red"
            )
            print("Login Error:", e)
            show_change_device_ui()  # 👈 show our new helper UI section

    threading.Thread(target=do_login, daemon=True).start()

def show_change_device_ui():
    """Show the device rotation hint and button below failed login message."""
    if hasattr(root, "device_hint_shown") and root.device_hint_shown:
        return  # prevent duplicates
    root.device_hint_shown = True

    hint_label = tk.Label(
        login_frame,
        text=("If you feel after many failed login attempts that Instagram has blocked this app "
              "from scraping, then try changing device by clicking the button below."),
        wraplength=400,
        justify="center",
        fg="gray"
    )
    hint_label.grid(row=4, columnspan=2, pady=(10, 5))

    # Create button showing current device number
    def change_device_action():
        global current_device_index
        cl = get_next_device()
        current_device = DEVICE_LIST[current_device_index]
        messagebox.showinfo(
            "Device Changed",
            f"Device changed to:\n{current_device['model']} ({current_device['manufacturer']})"
        )
        update_button_text()  # refresh button label

    def update_button_text():
        change_btn.config(
            text=f"Change Device ({current_device_index + 1}/{len(DEVICE_LIST)})"
        )

    change_btn = tk.Button(login_frame, command=change_device_action)
    change_btn.grid(row=5, columnspan=2, pady=5)

    update_button_text()  # set initial text


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

    #option_var = tk.BooleanVar(value=False)
    global option_var
    tk.Radiobutton(root, variable=option_var, value="none").pack_forget()
    radio_frame = tk.Frame(root)
    radio_frame.pack(pady=10)
    # Create widgets outside the function so you can access them later
    date_label = tk.Label(ui_frame, text="Select Date Range:")
    start_entry = DateEntry(ui_frame, textvariable=start_date_var, width=12)
    end_entry = DateEntry(ui_frame, textvariable=end_date_var, width=12)   

    # Initially hide them (don’t grid yet)

    def on_option_selected():
        
        if option_var.get():

            date_label.grid(row=4, column=0, sticky='e')
            start_entry.grid(row=4, column=1, sticky='w')
            end_entry.grid(row=4, column=2, padx=5)
            
        else:
            date_label.grid_remove()
            start_entry.grid_remove()
            end_entry.grid_remove()
            # Clear the variables
            start_date_var.set("")
            end_date_var.set("")

            # Also clear the actual DateEntry widgets
            start_entry.delete(0, 'end')
            end_entry.delete(0, 'end')
           
    tk.Checkbutton(root, text="Filter By Date", variable=option_var, command=on_option_selected).pack()

    # Buttons
    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=10)
    
    tk.Button(btn_frame, text="Download Posts", width=25,
            command=lambda:posts_diverter(
                username_var.get(), folder_var.get(),start_date_var.get(),
                end_date_var.get(),
                number_var.get())).pack(pady=2)
    
    tk.Button(btn_frame, text="Download Reels", width=25,
            command=lambda:reels_diverter(
                username_var.get(), folder_var.get(),
                start_date_var.get(), end_date_var.get(),number_var.get())).pack(pady=2)
    
    tk.Button(btn_frame, text="Download Stories", width=25,
            command=lambda: run_script("downloadStoriesApp.py", [
                username_var.get(), folder_var.get()])).pack(pady=2)
    
    tk.Button(btn_frame, text="Download Highlights", width=25,
            command=lambda: run_script("downloadHighlightsApp.py", [
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
