import os
import sys
import requests
from ics import Calendar
from datetime import datetime, timedelta, timezone
import smtplib
from email.mime.text import MIMEText
import pytz

ICS_URL = "https://calendar.google.com/calendar/ical/9csetts22iqc0iduial5obme3g%40group.calendar.google.com/public/basic.ics"
EMAIL_FROM = "astrobicocca.bot@gmail.com"


EMAIL_TO = ["astroall-groups@unimib.it","astrovisitor-groups@unimib.it"]
EMAIL_REPLY = "astroseminars-organizers-groups@unimib.it"

#Debug
#EMAIL_TO = ["davide.gerosa@unimib.it"] 
#EMAIL_REPLY = "davide.gerosa@unimib.it"

ROME_TZ = pytz.timezone("Europe/Rome")

print(
    "Email settings:\n",
    f"TO: {EMAIL_TO}\n",
    f"FROM: {EMAIL_FROM}\n",
    f"REPLY-TO: {EMAIL_REPLY}\n",
)

footer ="<br>See you there!"
footer2="<br>Astroseminars organizers"
footer2+="<br><br><i>Our seminar schedule is available at: https://calendar.google.com/calendar/embed?src=9csetts22iqc0iduial5obme3g%40group.calendar.google.com&ctz=Europe%2FRome</i>"
footer2+="<br><i>Replies to this address are not monitored, you can contact us at astroseminars-organizers-groups@unimib.it</i>"
footer+=footer2

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
        f"- {ev.begin.format('YYYY-MM-DD HH:mm')}: {ev.name}" for ev in events_sorted
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
    return [e for e in fetch_events() if now <= e.begin <= end]


def format_event(e):
    local_dt = e.begin.astimezone(ROME_TZ)
    #date_str = local_dt.strftime("%-d %B %Y, %-I:%M %p").lower()  # e.g. 1 January 2025, 8:30 am
    date_str = local_dt.strftime("%A, %-d %B, %-I:%M %p")
    date_str = date_str[:-2] + date_str[-2:].lower()
    parts = [
        f"<p><b>{date_str}</b><br>",
        f"<b>{e.name}</b><br><br>",
    ]
    if e.location:  # only add location if not empty
        parts.append(f"{e.location}<br><br>")
    if e.description:  # only add description if not empty
        parts.append(f"{e.description}".replace("\n", "<br>"))
    parts.append("</p>")
    return "".join(parts)

def send_email(subject, body):
    msg = MIMEText(body, "html")  # send as HTML
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_REPLY
    msg["Bcc"] = "; ".join(EMAIL_TO)
    msg["Reply-To"] = EMAIL_REPLY
    msg["Subject"] = subject
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL_FROM, os.getenv("SMTP_PASS"))
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())


if __name__ == "__main__":
    mode = sys.argv[1]
    now = datetime.now(timezone.utc)

if mode == "weekly":
    events = upcoming_events(days=8)
    if events:
        body = (
            "Hi all,<br><br>"
            "here are the astrobicocca events happening next week:<br><br><hr>"
            + "<br><hr>".join([format_event(e) for e in events])
            +"<br><hr>"+footer
        )
    else:
        body = "Hi all,<br><br>No events next week."+footer2
    print(body)
    send_email("[Astroseminars] Next week's events", body)

if mode == "daily":
    today = now.astimezone(ROME_TZ).date()
    events = upcoming_events(days=1)
    todays_events = [e for e in events if e.begin.astimezone(ROME_TZ).date() == today]
    if todays_events:
        body = (
            "Hi all,<br><br>"
            "here is a reminder of the astrobicocca event(s) happening today:<br><br><hr>"
            + "<hr>".join([format_event(e) for e in todays_events])
            +"<hr>"+footer
        )
        print(body)
        send_email("[Astroseminars] Today's events", body)
    else:
        print("No events today. No email sent.")

if mode == "readme":
    update_readme()






