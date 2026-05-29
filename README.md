# Work Tracker

A small Flask app for recording work log entries to `worklog.xlsx` and running a background reminder based on the latest end time.

## Features

- Submit a work log entry via a simple HTML form
- Save entries to `worklog.xlsx`
- Redirect back to the home page after save
- Show a flash message on successful submit
- Background reminder thread reads the last end time and triggers a notification or console message

## Files

- `app.py` — main Flask application
- `reminder.py` — reminder helper logic for reading the latest work log entry
- `templates/index.html` — dark themed form UI with flash message support
- `worklog.xlsx` — saved work log data file

## Requirements

- Python 3.10+ (tested with Python 3.11)
- Flask
- pandas
- plyer (optional for desktop notifications)

## Installation

1. Create and activate a virtual environment:

```bash
python -m venv .venv
.\.venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install flask pandas plyer
```

## Run the app

```bash
python app.py
```

Then open `http://127.0.0.1:5000/` in your browser.

## Notes

- The app writes form submissions to `worklog.xlsx` in the project directory.
- On successful submit, the app redirects back to the home page and displays a flash message.
- If `plyer` is not available, reminders will print to the console instead of showing a desktop notification.

## Customization

- Change the Flask secret key in `app.py` before deploying to production.
- Modify `templates/index.html` to update the form appearance or add additional fields.
