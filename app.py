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

@app.route('/checkin', methods=['GET', 'POST'])
def checkin():
    if request.method == 'POST':
        checkin_date = request.form.get('checkin_date')
        start_time = request.form.get('start_time')
        expected_end_time = request.form.get('expected_end_time')

        if not checkin_date or not start_time or not expected_end_time:
            flash('Please complete all check-in fields.', 'danger')
            return redirect(url_for('checkin'))

        record = {
            'checkin_date': checkin_date,
            'start_time': start_time,
            'expected_end_time': expected_end_time,
            'checkout_date': '',
            'checkout_time': ''
        }

        df = pd.DataFrame([record])
        if Path("worklog.xlsx").exists():
            df_existing = pd.read_excel("worklog.xlsx")
            df = pd.concat([df_existing, df], ignore_index=True)
        df.to_excel("worklog.xlsx", index=False)

        thread = threading.Thread(target=run_reminder)
        thread.daemon = True
        thread.start()

        flash('Check-in saved successfully!', 'success')
        return redirect(url_for('checkin'))

    return render_template('checkin.html')


@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        checkout_date = request.form.get('checkout_date')
        checkout_time = request.form.get('checkout_time')

        if not checkout_date or not checkout_time:
            flash('Please complete all check-out fields.', 'danger')
            return redirect(url_for('checkout'))

        record = {
            'checkin_date': '',
            'start_time': '',
            'expected_end_time': '',
            'checkout_date': checkout_date,
            'checkout_time': checkout_time
        }

        df = pd.DataFrame([record])
        if Path("worklog.xlsx").exists():
            df_existing = pd.read_excel("worklog.xlsx")
            df = pd.concat([df_existing, df], ignore_index=True)
        df.to_excel("worklog.xlsx", index=False)

        hours_worked = None
        overtime = None

        try:
            df_existing = pd.read_excel("worklog.xlsx", dtype=str)
            matching = df_existing[
                (df_existing['checkin_date'] == checkout_date) &
                df_existing['start_time'].notna() &
                (df_existing['start_time'] != '')
            ]

            if not matching.empty:
                last_checkin = matching.iloc[-1]
                start_time_obj = _parse_time(last_checkin['start_time'])
                checkout_time_obj = _parse_time(checkout_time)
                expected_end_obj = _parse_time(last_checkin.get('expected_end_time', ''))

                if start_time_obj and checkout_time_obj:
                    start_dt = datetime.combine(datetime.today(), start_time_obj)
                    checkout_dt = datetime.combine(datetime.today(), checkout_time_obj)
                    if checkout_dt < start_dt:
                        checkout_dt += timedelta(days=1)

                    duration = checkout_dt - start_dt
                    hours_worked = _format_duration(duration)

                    if expected_end_obj:
                        expected_dt = datetime.combine(datetime.today(), expected_end_obj)
                        if expected_dt < start_dt:
                            expected_dt += timedelta(days=1)

                        overtime_delta = checkout_dt - expected_dt
                        overtime = _format_duration(overtime_delta) if overtime_delta.total_seconds() > 0 else 'No'
        except Exception:
            pass

        flash('Check-out saved successfully!', 'success')
        return render_template('checkout.html', hours_worked=hours_worked, overtime=overtime)

    return render_template('checkout.html')


def _parse_time(value):
    if not value or value is None:
        return None

    value = str(value).strip()
    for fmt in ('%H:%M', '%I:%M %p'):
        try:
            return datetime.strptime(value, fmt).time()
        except ValueError:
            continue

    try:
        return pd.to_datetime(value).time()
    except Exception:
        return None


def _format_duration(delta):
    if not delta or delta.total_seconds() < 0:
        return None
    total_seconds = int(delta.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    if hours > 0 and minutes > 0:
        return f"{hours}h {minutes}m"
    if hours > 0:
        return f"{hours}h"
    return f"{minutes}m"


def run_reminder():
    
    try:
        from plyer import notification
        HAS_PLYER = True
    except Exception:
        HAS_PLYER = False

    # Read the last entry from the worklog
    filereader = pd.read_excel("worklog.xlsx")
    last_row = filereader.iloc[-1]
    endtime = None

    if 'expected_end_time' in last_row and last_row['expected_end_time']:
        endtime = last_row['expected_end_time']
    elif 'end_time' in last_row and last_row['end_time']:
        endtime = last_row['end_time']

    if endtime is None or str(endtime).strip() == '':
        print('No valid expected end time found for reminder.')
        return

    end_time_obj = _parse_time(endtime)
    if end_time_obj is None:
        print('Unable to parse reminder time:', endtime)
        return

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
