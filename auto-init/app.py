import os
import hmac
import hashlib
import base64
import requests
from flask import Flask, request, jsonify
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey
from cryptography.hazmat.primitives import serialization
from nacl.public import PublicKey, SealedBox

app = Flask(__name__)

GITHUB_TOKEN    = os.environ.get("GITHUB_TOKEN")
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME")
WEBHOOK_SECRET  = os.environ.get("WEBHOOK_SECRET")

# Secrets to auto-add to every new repo
SECRETS = {
    "GROQ_API_KEY":    os.environ.get("GROQ_API_KEY"),
    "SENDER_EMAIL":    os.environ.get("SENDER_EMAIL"),
    "SENDER_PASSWORD": os.environ.get("SENDER_PASSWORD"),
    "RECEIVER_EMAIL":  os.environ.get("RECEIVER_EMAIL"),
}

NOTIFY_YML = """name: Notify on Push

on:
  push:
    branches: ['**']

jobs:
  prepare:
    runs-on: ubuntu-latest
    outputs:
      files_added: ${{ steps.changes.outputs.files_added }}
      files_modified: ${{ steps.changes.outputs.files_modified }}
      files_removed: ${{ steps.changes.outputs.files_removed }}
    steps:
      - name: Checkout
        uses: actions/checkout@v3
        with:
          fetch-depth: 2

      - name: Get changed files
        id: changes
        run: |
          ADDED=$(git diff --name-only --diff-filter=A HEAD~1 HEAD | tr '\\n' ',' | sed 's/,$//')
          MODIFIED=$(git diff --name-only --diff-filter=M HEAD~1 HEAD | tr '\\n' ',' | sed 's/,$//')
          REMOVED=$(git diff --name-only --diff-filter=D HEAD~1 HEAD | tr '\\n' ',' | sed 's/,$//')
          echo "files_added=${ADDED:-none}" >> $GITHUB_OUTPUT
          echo "files_modified=${MODIFIED:-none}" >> $GITHUB_OUTPUT
          echo "files_removed=${REMOVED:-none}" >> $GITHUB_OUTPUT

  call-notifier:
    needs: prepare
    uses: Ekaanksh-dev/devops-ai-notifier/.github/workflows/ai-notify.yml@master
    with:
      repo_name: ${{ github.repository }}
      branch: ${{ github.ref_name }}
      commit_sha: ${{ github.sha }}
      commit_message: ${{ github.event.head_commit.message }}
      pusher: ${{ github.actor }}
      files_added: ${{ needs.prepare.outputs.files_added }}
      files_modified: ${{ needs.prepare.outputs.files_modified }}
      files_removed: ${{ needs.prepare.outputs.files_removed }}
      timestamp: ${{ github.event.head_commit.timestamp }}
    secrets:
      GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
      SENDER_EMAIL: ${{ secrets.SENDER_EMAIL }}
      SENDER_PASSWORD: ${{ secrets.SENDER_PASSWORD }}
      RECEIVER_EMAIL: ${{ secrets.RECEIVER_EMAIL }}
"""

def verify_signature(payload, signature):
    mac = hmac.new(
        WEBHOOK_SECRET.encode(),
        msg=payload,
        digestmod=hashlib.sha256
    )
    return hmac.compare_digest(f"sha256={mac.hexdigest()}", signature)

def get_repo_public_key(repo_name):
    url = f"https://api.github.com/repos/{repo_name}/actions/secrets/public-key"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    return response.json()

def encrypt_secret(public_key_str, secret_value):
    public_key_bytes = base64.b64decode(public_key_str)
    public_key = PublicKey(public_key_bytes)
    sealed_box = SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode())
    return base64.b64encode(encrypted).decode()

def push_secret(repo_name, secret_name, secret_value, key_id, public_key):
    encrypted_value = encrypt_secret(public_key, secret_value)
    url = f"https://api.github.com/repos/{repo_name}/actions/secrets/{secret_name}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    data = {
        "encrypted_value": encrypted_value,
        "key_id": key_id
    }
    response = requests.put(url, headers=headers, json=data)
    return response.status_code in [201, 204]

def push_all_secrets(repo_name):
    key_data   = get_repo_public_key(repo_name)
    key_id     = key_data["key_id"]
    public_key = key_data["key"]

    results = {}
    for secret_name, secret_value in SECRETS.items():
        if secret_value:
            success = push_secret(repo_name, secret_name, secret_value, key_id, public_key)
            results[secret_name] = "✅" if success else "❌"
        else:
            results[secret_name] = "⚠️ not set in env"

    return results

def file_exists(repo_name):
    url = f"https://api.github.com/repos/{repo_name}/contents/.github/workflows/notify.yml"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    return response.status_code == 200

def push_notify_yml(repo_name):
    url = f"https://api.github.com/repos/{repo_name}/contents/.github/workflows/notify.yml"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    content = base64.b64encode(NOTIFY_YML.encode()).decode()
    data = {
        "message": "chore: auto-add Punk Records notifier",
        "content": content
    }
    response = requests.put(url, headers=headers, json=data)
    return response.status_code in [200, 201]

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not verify_signature(request.data, signature):
        return jsonify({"error": "Invalid signature"}), 401

    event   = request.headers.get("X-GitHub-Event")
    payload = request.json

    if event == "repository" and payload.get("action") == "created":
        repo_name = payload["repository"]["full_name"]
        owner     = payload["repository"]["owner"]["login"]

        if owner != GITHUB_USERNAME:
            return jsonify({"message": "Not your repo"}), 200

        if file_exists(repo_name):
            return jsonify({"message": "Already connected"}), 200

        # Push notify.yml
        yml_success = push_notify_yml(repo_name)

        # Push all secrets
        secret_results = push_all_secrets(repo_name)

        print(f"✅ Auto-connected: {repo_name}")
        print(f"📁 notify.yml: {'✅' if yml_success else '❌'}")
        print(f"🔐 Secrets: {secret_results}")

        return jsonify({
            "message": f"Connected {repo_name}",
            "notify_yml": yml_success,
            "secrets": secret_results
        }), 200

    return jsonify({"message": "Event ignored"}), 200

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "Punk Records Auto-Init is running 🎛️"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
