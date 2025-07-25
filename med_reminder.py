#!/usr/bin/env python3
import time
import subprocess
import os
import sys
from datetime import datetime
import json
import tkinter as tk
from tkinter import messagebox, ttk

class MedReminder:
    def __init__(self, reminder_type="morning"):
        self.reminder_type = reminder_type
        
        if reminder_type == "morning":
            self.medicines = [
                "Elvanse 20mg",
                "Escitalopram 5mg", 
                "Dexamfetamine 5mg"
            ]
            self.reminder_title = "🌅 MORNING MEDICATION TIME!"
        elif reminder_type == "afternoon":
            self.medicines = [
                "Dexamfetamine 5mg (afternoon dose)"
            ]
            self.reminder_title = "🌆 AFTERNOON MEDICATION TIME!"
        
        self.log_file = os.path.expanduser("~/med_log.json")
        self.reminder_count = 0
        self.max_reminders = 10
        
    def get_today_key(self):
        return datetime.now().strftime("%Y-%m-%d")
    
    def load_log(self):
        try:
            with open(self.log_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_log(self, taken_meds):
        log = self.load_log()
        today_key = self.get_today_key()
        
        if today_key not in log:
            log[today_key] = {}
        
        log[today_key][self.reminder_type] = {
            'medicines': taken_meds,
            'time_taken': datetime.now().isoformat(),
            'reminder_count': self.reminder_count
        }
        
        with open(self.log_file, 'w') as f:
            json.dump(log, f, indent=2)
    
    def already_taken_today(self):
        log = self.load_log()
        today = self.get_today_key()
        return (today in log and 
                self.reminder_type in log[today] and 
                len(log[today][self.reminder_type].get('medicines', [])) == len(self.medicines))
    
    def show_desktop_notification(self, urgency="normal"):
        message = f"🏥 MEDICATION TIME!\n\n" + "\n".join([f"• {med}" for med in self.medicines])
        try:
            subprocess.run([
                'notify-send', 
                '-u', urgency,
                '-t', '30000' if urgency == 'critical' else '10000',
                '-i', 'dialog-warning',
                'Medication Reminder', 
                message
            ], check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Desktop notifications not available - showing console message")
            print(f"*** {message} ***")
    
    def play_alarm_sound(self):
        # Try different alarm sounds in order of preference
        sounds = [
            "/usr/share/sounds/freedesktop/stereo/complete.oga",
            "/usr/share/sounds/freedesktop/stereo/dialog-information.oga",
            "/usr/share/sounds/sound-icons/piano-3.wav",
            "/usr/share/sounds/sound-icons/chord-7.wav"
        ]
        
        for sound in sounds:
            if os.path.exists(sound):
                try:
                    # Play sound multiple times for urgency
                    for _ in range(3):
                        subprocess.run(['paplay', sound], check=False)
                        time.sleep(0.5)
                    return
                except FileNotFoundError:
                    # Try aplay as backup
                    try:
                        subprocess.run(['aplay', sound], check=False)
                        return
                    except FileNotFoundError:
                        continue
        
        # Fallback to system beep if no sounds work
        print("\a" * 5)  # Terminal bell
    
    def show_gui_reminder(self):
        completed = [False]  # Use list to allow modification in nested function
        
        def on_taken():
            selected = []
            for i, var in enumerate(med_vars):
                if var.get():
                    selected.append(self.medicines[i])
            
            if len(selected) == len(self.medicines):
                self.save_log(selected)
                messagebox.showinfo("Success", "Great! All medications logged. See you tomorrow!")
                completed[0] = True
                root.destroy()
            else:
                messagebox.showwarning("Incomplete", f"Please check all {len(self.medicines)} medications")
        
        def on_snooze():
            root.destroy()
            
        root = tk.Tk()
        root.title("Medication Reminder")
        root.geometry("400x300")
        root.attributes('-topmost', True)
        root.attributes('-fullscreen', False)
        
        # Make window more prominent
        if self.reminder_count > 3:
            root.configure(bg='red')
        elif self.reminder_count > 1:
            root.configure(bg='orange')
        else:
            root.configure(bg='lightblue')
            
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(main_frame, text=self.reminder_title, font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        time_label = ttk.Label(main_frame, text=f"Reminder #{self.reminder_count + 1}", font=("Arial", 10))
        time_label.pack(pady=5)
        
        med_vars = []
        for med in self.medicines:
            var = tk.BooleanVar()
            med_vars.append(var)
            cb = ttk.Checkbutton(main_frame, text=med, variable=var)
            cb.pack(pady=5, anchor='w')
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20, fill=tk.X)
        
        taken_btn = ttk.Button(button_frame, text="✅ Taken All", command=on_taken)
        taken_btn.pack(side=tk.LEFT, padx=5)
        
        snooze_btn = ttk.Button(button_frame, text="😴 Snooze 5min", command=on_snooze)
        snooze_btn.pack(side=tk.RIGHT, padx=5)
        
        # Auto-focus and bring to front
        root.focus_force()
        root.lift()
        
        try:
            root.mainloop()
            return completed[0]  # Return True if medications were taken
        except tk.TclError:
            return False
    
    def run_reminder_cycle(self):
        if self.already_taken_today():
            print("Medications already taken today!")
            return
        
        print(f"Starting medication reminder cycle...")
        
        while self.reminder_count < self.max_reminders:
            # Check if medications were taken while script was running
            if self.already_taken_today():
                print("Medications were taken - stopping reminders!")
                return
                
            print(f"Reminder #{self.reminder_count + 1}")
            
            # Show notifications with increasing urgency
            if self.reminder_count == 0:
                self.show_desktop_notification("normal")
            elif self.reminder_count < 3:
                self.show_desktop_notification("normal")
                self.play_alarm_sound()
            else:
                self.show_desktop_notification("critical")
                self.play_alarm_sound()
            
            # Show GUI - this blocks until user responds
            if self.show_gui_reminder():
                print("Medications taken successfully!")
                return
            
            self.reminder_count += 1
            
            # Wait between reminders (shorter intervals as urgency increases)
            if self.reminder_count < 3:
                wait_time = 300  # 5 minutes
            elif self.reminder_count < 6:
                wait_time = 180  # 3 minutes  
            else:
                wait_time = 60   # 1 minute
                
            print(f"Waiting {wait_time//60} minutes before next reminder...")
            time.sleep(wait_time)
        
        print("Maximum reminders reached. Please take your medication!")

if __name__ == "__main__":
    reminder_type = "morning"  # default
    if len(sys.argv) > 1:
        reminder_type = sys.argv[1]
    
    reminder = MedReminder(reminder_type)
    reminder.run_reminder_cycle()