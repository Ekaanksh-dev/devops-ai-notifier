#!/usr/bin/env python3

import os
import sys
import base64
import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

GITHUB_TOKEN    = os.environ.get("GITHUB_TOKEN")
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
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

def get_all_repos():
    url = f"https://api.github.com/users/{GITHUB_USERNAME}/repos?per_page=100"
    response = requests.get(url, headers=HEADERS)
    return response.json()
    return [r for r in repos if not r.get("fork")]

def file_exists(repo_name):
    url = f"https://api.github.com/repos/{repo_name}/contents/.github/workflows/notify.yml"
    response = requests.get(url, headers=HEADERS)
    return response.status_code == 200

def push_notify_yml(repo_name):
    url = f"https://api.github.com/repos/{repo_name}/contents/.github/workflows/notify.yml"
    content = base64.b64encode(NOTIFY_YML.encode()).decode()
    data = {
        "message": "chore: auto-add Punk Records notifier",
        "content": content
    }
    response = requests.put(url, headers=HEADERS, json=data)
    return response.status_code in [200, 201]

def push_secret(repo_name, secret_name, secret_value):
    from nacl.public import PublicKey, SealedBox
    # Get repo public key
    url = f"https://api.github.com/repos/{repo_name}/actions/secrets/public-key"
    key_data   = requests.get(url, headers=HEADERS).json()
    key_id     = key_data["key_id"]
    public_key = key_data["key"]

    # Encrypt
    pk        = PublicKey(base64.b64decode(public_key))
    box       = SealedBox(pk)
    encrypted = base64.b64encode(box.encrypt(secret_value.encode())).decode()

    # Push
    url = f"https://api.github.com/repos/{repo_name}/actions/secrets/{secret_name}"
    data = {"encrypted_value": encrypted, "key_id": key_id}
    response = requests.put(url, headers=HEADERS, json=data)
    return response.status_code in [201, 204]

def push_all_secrets(repo_name):
    secrets = {
        "GROQ_API_KEY":    os.environ.get("GROQ_API_KEY"),
        "SENDER_EMAIL":    os.environ.get("SENDER_EMAIL"),
        "SENDER_PASSWORD": os.environ.get("SENDER_PASSWORD"),
        "RECEIVER_EMAIL":  os.environ.get("RECEIVER_EMAIL"),
    }
    for name, value in secrets.items():
        if value:
            ok = push_secret(repo_name, name, value)
            print(f"  🔐 {name}: {'✅' if ok else '❌'}")
        else:
            print(f"  ⚠️  {name}: not found in .env")

# ── Commands ──────────────────────────────────────────

def cmd_add(repo_name):
    """Connect a specific repo to Punk Records"""
    full_name = f"{GITHUB_USERNAME}/{repo_name}"
    print(f"\n🔌 Connecting {full_name}...")

    url = f"https://api.github.com/repos/{full_name}"
    repo_data = requests.get(url, headers=HEADERS).json()
    if repo_data.get("fork"):
        print("⚠️  Skipping — this is a forked repo.")
        return

    if file_exists(full_name):
        print("✅ Already connected!")
        return

    ok = push_notify_yml(full_name)
    print(f"📁 notify.yml: {'✅ pushed' if ok else '❌ failed'}")

    print("🔐 Adding secrets...")
    push_all_secrets(full_name)
    print(f"\n🎛️ {full_name} is now connected to Punk Records!")

def cmd_update():
    """Push latest notify.yml to ALL connected repos"""
    repos = get_all_repos()
    print(f"\n🔄 Updating all connected repos...\n")

    updated = 0
    for repo in repos:
        full_name = repo["full_name"]
        if repo["full_name"] == f"{GITHUB_USERNAME}/devops-ai-notifier":
            continue
        if file_exists(full_name):
            # Get existing file SHA for update
            url      = f"https://api.github.com/repos/{full_name}/contents/.github/workflows/notify.yml"
            response = requests.get(url, headers=HEADERS).json()
            sha      = response.get("sha")
            content  = base64.b64encode(NOTIFY_YML.encode()).decode()
            data     = {
                "message": "chore: update Punk Records notifier",
                "content": content,
                "sha": sha
            }
            response = requests.put(url, headers=HEADERS, json=data)
            ok = response.status_code in [200, 201]
            print(f"  {'✅' if ok else '❌'} {full_name}")
            if ok:
                updated += 1

    print(f"\n🎛️ Updated {updated} repos!")

def cmd_status():
    """Show which repos are connected to Punk Records"""
    repos = get_all_repos()
    print(f"\n🎛️ Punk Records — Repo Status\n")

    connected     = []
    not_connected = []

    for repo in repos:
        full_name = repo["full_name"]
        if file_exists(full_name):
            connected.append(full_name)
        else:
            not_connected.append(full_name)

    print(f"✅ Connected ({len(connected)}):")
    for r in connected:
        print(f"   👁️  {r}")

    print(f"\n❌ Not connected ({len(not_connected)}):")
    for r in not_connected:
        print(f"   💤 {r}")

def cmd_list():
    """List all connected repos"""
    repos = get_all_repos()
    print(f"\n👁️  Punk Records is watching:\n")
    for repo in repos:
        if file_exists(repo["full_name"]):
            print(f"   🎛️  {repo['full_name']}")

def cmd_secrets_all():
    """Push secrets to ALL connected repos"""
    repos = get_all_repos()
    print(f"\n🔐 Pushing secrets to all connected repos...\n")
    for repo in repos:
        full_name = repo["full_name"]
        if file_exists(full_name):
            print(f"  📦 {full_name}")
            push_all_secrets(full_name)
    print(f"\n✅ All secrets updated!")

def cmd_help():
    print("""
🎛️  autopwflow — Punk Records CLI

Commands:
  autopwflow add <repo>   Connect a repo to Punk Records
  autopwflow update       Push latest notify.yml to all connected repos
  autopwflow status       Show connected vs not connected repos
  autopwflow list         List all watched repos
  autopwflow secrets-all  add the secrets/updates the secrets  
  autopwflow help         Show this message
""")

# ── Entry point ───────────────────────────────────────

def main():
    args = sys.argv[1:]

    if not args or args[0] == "help":
        cmd_help()
    elif args[0] == "add":
        if len(args) < 2:
            print("❌ Usage: autopwflow add <repo-name>")
        else:
            cmd_add(args[1])
    elif args[0] == "update":
        cmd_update()
    elif args[0] == "status":
        cmd_status()
    elif args[0] == "list":
        cmd_list()
    elif args[0] == "secrets-all":
        cmd_secrets_all()
    else:
        print(f"❌ Unknown command: {args[0]}")
        cmd_help()

if __name__ == "__main__":
    main()
