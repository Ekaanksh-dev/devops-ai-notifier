import os
import smtplib
import groq
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Read all env variables
repo          = os.environ.get("REPO_NAME", "unknown")
branch        = os.environ.get("BRANCH", "unknown")
commit_sha    = os.environ.get("COMMIT_SHA", "")[:7]
commit_msg    = os.environ.get("COMMIT_MESSAGE", "No message")
author        = os.environ.get("COMMIT_AUTHOR", "unknown")
files_added   = os.environ.get("FILES_ADDED", "none")
files_modified= os.environ.get("FILES_MODIFIED", "none")
files_removed = os.environ.get("FILES_REMOVED", "none")
timestamp     = os.environ.get("TIMESTAMP", "unknown")

# Format timestamp nicely
try:
    from datetime import datetime, timezone
    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    timestamp_nice = dt.strftime("%d %B %Y, %I:%M %p UTC")
except:
    timestamp_nice = timestamp

# Build file summary for Groq
files_summary = f"""
Added:    {files_added}
Modified: {files_modified}
Removed:  {files_removed}
"""

# Ask Groq
client = groq.Groq(api_key=os.environ["GROQ_API_KEY"])

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {
            "role": "user",
            "content": f"""
Analyze this Git commit and give a short clear summary of what changed and why it matters.

Repo: {repo}
Branch: {branch}
Author: {author}
Commit: {commit_sha}
Message: {commit_msg}
Files Changed:
{files_summary}

Keep it under 6 lines. Be direct and useful.
"""
        }
    ]
)

ai_summary = response.choices[0].message.content

# Build HTML email
html = f"""
<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">

  <h2>🚀 New Push — {repo}</h2>

  <table border="1" cellpadding="10" cellspacing="0" style="border-collapse: collapse;">
    <tr style="background:#f0f0f0;">
      <td><b>📁 Repository</b></td>
      <td>{repo}</td>
    </tr>
    <tr>
      <td><b>🌿 Branch</b></td>
      <td>{branch}</td>
    </tr>
    <tr style="background:#f0f0f0;">
      <td><b>👤 Author</b></td>
      <td>{author}</td>
    </tr>
    <tr>
      <td><b>🔖 Commit</b></td>
      <td>{commit_sha}</td>
    </tr>
    <tr style="background:#f0f0f0;">
      <td><b>🕐 Timestamp</b></td>
      <td>{timestamp_nice}</td>
    </tr>
    <tr>
      <td><b>💬 Message</b></td>
      <td>{commit_msg}</td>
    </tr>
  </table>

  <h3>📂 Changed Files</h3>
  <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse;">
    <tr style="background:#d4edda;">
      <td><b>✅ Added</b></td>
      <td>{files_added if files_added else "none"}</td>
    </tr>
    <tr style="background:#fff3cd;">
      <td><b>✏️ Modified</b></td>
      <td>{files_modified if files_modified else "none"}</td>
    </tr>
    <tr style="background:#f8d7da;">
      <td><b>🗑️ Removed</b></td>
      <td>{files_removed if files_removed else "none"}</td>
    </tr>
  </table>

  <h3>🤖 AI Summary</h3>
  <p style="background:#e8f4fd; padding:15px; border-radius:8px;">{ai_summary}</p>

</body>
</html>
"""

# Send email
msg = MIMEMultipart("alternative")
msg["Subject"] = f"[{repo}] Push to {branch} by {author} — {commit_sha}"
msg["From"]    = os.environ["SENDER_EMAIL"]
msg["To"]      = os.environ["RECEIVER_EMAIL"]
msg.attach(MIMEText(html, "html"))

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
    smtp.login(os.environ["SENDER_EMAIL"], os.environ["SENDER_PASSWORD"])
    smtp.send_message(msg)

print("✅ Email sent successfully!")
