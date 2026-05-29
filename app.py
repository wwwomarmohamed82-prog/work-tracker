from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
from pathlib import Path
import time
from datetime import datetime, timedelta
import threading
app = Flask(__name__)
app.secret_key = 'replace-this-with-a-secure-key'

@app.route('/')
def home():
    # Renders templates/index.html
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    if request.method == "POST":
       # getting input with name = sday in HTML form
       first_day = request.form.get("sday")
       # getting input with name = lday in HTML form 
       last_day = request.form.get("lday") 
       ftime = request.form.get("stime")
       ltime = request.form.get("etime")
       myvars = {"start_day": first_day, "end_day": last_day, "start_time": ftime, "end_time": ltime}
       df = pd.DataFrame([myvars])
       if Path("worklog.xlsx").exists():
        df_existing = pd.read_excel("worklog.xlsx")
        df = pd.concat([df_existing, df], ignore_index=True)
       df.to_excel("worklog.xlsx", index=False)
       thread = threading.Thread(target=run_reminder)
       thread.daemon = True
       thread.start()
       flash('Work log saved successfully!', 'success')
       return redirect(url_for('home'))

def run_reminder():
    
    try:
        from plyer import notification
        HAS_PLYER = True
    except Exception:
        HAS_PLYER = False

    # Read the last entry from the worklog
    filereader = pd.read_excel("worklog.xlsx")
    last_row = filereader.iloc[-1]
    endtime = last_row["end_time"]

    # Normalize endtime to a Python time object
    if isinstance(endtime, pd.Timestamp):
        end_time_obj = endtime.time()
    elif isinstance(endtime, datetime):
        end_time_obj = endtime.time()
    elif isinstance(endtime, str):
        try:
            end_time_obj = datetime.strptime(endtime, "%H:%M").time()
        except Exception:
            try:
                end_time_obj = datetime.strptime(endtime, "%I:%M %p").time()
            except Exception:
                end_time_obj = pd.to_datetime(endtime).time()
    else:
        # assume it's already a time object
        end_time_obj = endtime

    # Combine with today's date (so the reminder is scheduled for that day)
    endtime_parsed = datetime.combine(datetime.today(), end_time_obj)
    remindertime = endtime_parsed - timedelta(minutes=15)

    # Calculate seconds until reminder
    now = datetime.now().replace(year=endtime_parsed.year, month=endtime_parsed.month, day=endtime_parsed.day)
    diff = remindertime - now
    seconds = diff.total_seconds()

    if seconds > 0:
        time.sleep(seconds)
        if HAS_PLYER:
            notification.notify(
                title="Reminder",
                message="Your work log will end at " + endtime_parsed.strftime('%H:%M %p'),
                timeout=10
            )
        else:
            print("Notification: Your work log will end at " + endtime_parsed.strftime('%H:%M %p'))

    print("End time:", endtime_parsed)
    print("Reminder time:", remindertime)
    print("Now:", now)
    print("Seconds to wait:", seconds)

if __name__ == '__main__':
    app.run(debug=True)
