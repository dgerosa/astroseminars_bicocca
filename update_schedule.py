import os
import sys
import requests
from ics import Calendar
from datetime import datetime, timedelta, timezone
import smtplib
from email.mime.text import MIMEText

ICS_URL = "https://calendar.google.com/calendar/ical/9csetts22iqc0iduial5obme3g%40group.calendar.google.com/public/basic.ics"
EMAIL_TO = "rodrigo.tenorio@unimib.it"
EMAIL_FROM = "astrobicocca.bot@gmail.com"
EMAIL_REPLY = "astroseminars-organizers-groups@unimib.it"

print(
"Email settings:\n",
f"TO: {EMAIL_TO}\n",
f"FROM: {EMAIL_FROM}\n",
f"REPLY-TO: {EMAIL_REPLY}\n",
)

def fetch_events():
    r = requests.get(ICS_URL)
    r.raise_for_status()
    c = Calendar(r.text)
    return list(c.timeline)

def update_readme():
    events = fetch_events()
    events_sorted = sorted(events, key=lambda e: e.begin, reverse=True)

    readme_path = "README.md"
    with open(readme_path) as f:
        content = f.read()

    marker_start = "<!-- EVENTS_START -->"
    marker_end = "<!-- EVENTS_END -->"

    start = content.find(marker_start)
    end = content.find(marker_end)
    if start == -1 or end == -1:
        raise ValueError("Missing markers in README")

    lines = [
        f"- {ev.begin.format('YYYY-MM-DD HH:mm')}: {ev.name}"
        for ev in events_sorted
    ]
    new_section = "\n".join(lines) if lines else "_No events in calendar_"

    new_content = (
        content[:start]
        + marker_start
        + "\n"
        + new_section
        + "\n"
        + marker_end
        + content[end + len(marker_end) :]
    )

    with open(readme_path, "w") as f:
        f.write(new_content)

def upcoming_events(days=7):
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days)
    return [e for e in fetch_events() if e.begin >= now and e.begin <= end]

def send_email(subject, body):
    msg = MIMEText(body)
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO
    msg["Reply-To"] = EMAIL_REPLY
    msg["Subject"] = subject
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL_FROM, os.getenv("SMTP_PASS"))
        server.sendmail(EMAIL_FROM, [EMAIL_TO], msg.as_string())

if __name__ == "__main__":
    mode=sys.argv[1]
    #mode = os.getenv("MODE")
    now = datetime.now(timezone.utc)

    if mode == "weekly":
        events = upcoming_events(days=7)
        body = "\n".join(
            [f"{e.begin.format('YYYY-MM-DD HH:mm')}: {e.name}" for e in events]
        ) or "No events next week."
        print(body)
        send_email("Weekly Calendar Summary", body)

    elif mode == "daily":
        today = now.date()
        events = upcoming_events(days=1)
        todays_events = [e for e in events if e.begin.date() == today]
        if todays_events:
            body = "\n".join(
                [f"{e.begin.format('YYYY-MM-DD HH:mm')}: {e.name}" for e in todays_events]
            )
            print(body)
            send_email("Today's Events", body)

    elif mode == "readme":
        update_readme()