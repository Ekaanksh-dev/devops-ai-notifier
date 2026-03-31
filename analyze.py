import os
import sys
import smtplib
from email.mime.text import MIMEText
from groq import Groq

def analyze_commit(commit_message, files_changed):
    client = Groq(api_key=os.environ["GROQ_API_KEY"]
    
    chat_completion = client.messages.create(
        messages[
            {
                "role": "user",
                "content": f"""Analyze this git commit and respond in exactly this format:
Type: [Bug Fix / Feature / Config Change / Refactor / Docs]
Risk: [Low / Medium / High]
Summary: [one sentence explanation of what changed]

Commit message: {commit_message}
Files changed: {files_changed}"""
            }
        ],
        model="llama-3.3-70b-versatile",
    )
    return chat_completion.choice[0].message.content

def send_email(analysis, commit_message, files_changed, author, branch, repo):
    sender = os.environ["SENDER_EMAIL"]
    password = os.environ["SENDER_PASSWORD"]
    receiver = os.environ["RECEIVER_EMAIL"]
    
    body = f"""
New commit detected in {repo}

{analysis}

Commit: {commit_message}
Branch: {branch}
Author: {author}
Files changed: {files_changed}
"""
    
    msg = MIMEText(body)
    msg["Subject"] = f"🚀 [{repo}] New commit detected"
    msg["From"] = sender
    msg["To"] = receiver
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.sendmail(sender, receiver, msg.as_string())
    
    print("Email sent successfully")

if __name__ == "__main__":
    commit_message = os.environ["COMMIT_MESSAGE"]
    files_changed = os.environ["FILES_CHANGED"]
    author = os.environ["COMMIT_AUTHOR"]
    branch = os.environ["BRANCH"]
    repo = os.environ["REPO_NAME"]
    
    analysis = analyze_commit(commit_message, files_changed)
    print(analysis)
    send_email(analysis, commit_message, files_changed, author, branch, repo)
