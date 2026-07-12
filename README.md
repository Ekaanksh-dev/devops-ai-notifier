# Punk Records — AI-Powered DevOps Commit Notifier

![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3_70B-orange?style=for-the-badge)
![License](https://img.shields.io/badge/License-Apache_2.0-blue?style=for-the-badge)

A centralized notification system that watches GitHub repositories and uses an LLM to analyze and summarize every commit, with fully automatic onboarding for new repositories.

## Overview

Most teams check multiple repositories manually after every push. Punk Records removes that step entirely. The moment a push happens in any connected repository, it automatically:

- Detects the branch that was pushed to
- Identifies exactly which files were added, modified, or removed
- Records the precise timestamp of the push
- Sends the commit context to Groq (LLaMA 3.3 70B) for analysis
- Delivers a structured HTML email with an AI-generated summary of what changed and why it matters

When a new repository is created, a GitHub App and a Flask webhook server connect it automatically. No manual setup is required after the initial installation.

## Architecture

```
repo-a (push)  ----+
repo-b (push)  ----+----> devops-ai-notifier ----> Groq API ----> Email
repo-c (push)  ----+         (central workflow)      LLaMA 3.3
       ^
   autopwflow CLI ----> manually connect any repo in one command
       ^
   GitHub App ----> fires on repo creation ----> Render webhook server
                     ----> pushes notify.yml + secrets ----> repo connected
```

Each repository runs an independent caller workflow. All of them invoke a single reusable workflow that holds the actual logic. This is a hub-and-spoke pattern: one central definition, many independent callers.

## Features

- AI-generated commit summaries using LLaMA 3.3 70B via Groq
- Multi-repository support through a reusable GitHub Actions workflow
- Branch detection on every push
- File-level change detection (added, modified, removed) computed directly via `git diff` rather than relying on the GitHub event payload, which proved unreliable inside reusable workflows
- Full UTC timestamps on every notification
- Structured HTML email reports
- A CLI tool (`autopwflow`) for manually connecting, updating, or auditing which repositories are wired into the system
- A GitHub App and Flask server that automatically detect new repository creation and connect the repository without any manual step

## Email Report Example

```
Subject: [user/my-app] Push to main by user - a3f9c12

Repository:  user/my-app
Branch:      main
Author:      user
Commit:      a3f9c12
Timestamp:   03 June 2026, 02:30 PM UTC
Message:     added docker support

Changed Files
  Added:     Dockerfile, docker-compose.yml
  Modified:  README.md
  Removed:   none

AI Summary
This commit containerizes the my-app project using Docker and Docker
Compose, enabling consistent deployment across environments. The README
update suggests documentation was added alongside the setup.
```

## Repository Structure

```
devops-ai-notifier/
  .github/
    workflows/
      ai-notify.yml      Central reusable workflow
      notify.yml         Caller workflow for this repo
  auto-init/
    app.py               Flask server, handles GitHub App webhook
    requirements.txt
    render.yaml
  autopwflow/
    __init__.py
    cli.py                CLI tool for manual repo management
  setup.py
  README.md
  TROUBLESHOOTING.md      Build issues encountered and how they were resolved
  LICENSE
  .env                    Local secrets, not committed
```

## How Automatic Onboarding Works

1. A new repository is created on GitHub.
2. The installed GitHub App receives a `repository.created` event.
3. GitHub sends a webhook to the Flask server running on Render.
4. The server verifies the webhook signature, then:
   - Pushes `notify.yml` into the new repository via the GitHub Contents API
   - Encrypts and pushes the four required secrets (`GROQ_API_KEY`, `SENDER_EMAIL`, `SENDER_PASSWORD`, `RECEIVER_EMAIL`) via the GitHub Secrets API, using PyNaCl sealed-box encryption against the repository's own public key
5. The repository is now connected. The next push triggers a notification automatically.

This was the most difficult part of the project to get working reliably. The full debugging history, including a GitHub account flag that temporarily blocked the integration, is documented in `TROUBLESHOOTING.md`.

## CLI Tool

Install:

```bash
git clone https://github.com/Ekaanksh-dev/devops-ai-notifier.git
cd devops-ai-notifier
pip install -e .
```

Commands:

```bash
autopwflow add <repo>     Connect a specific repository
autopwflow detach <repo>    Remove Punk Records from a repo (asks about secrets too)
autopwflow update         Push the latest notify.yml to all connected repos
autopwflow status         Show connected vs. unconnected repositories
autopwflow list           List all repositories currently being watched
autopwflow secrets-all    Push secrets to all connected repositories
autopwflow help           Show available commands
```

## Setup

1. Clone the repository and create a `.env` file with the following variables:

```
GITHUB_TOKEN=
GITHUB_USERNAME=
GROQ_API_KEY=
SENDER_EMAIL=
SENDER_PASSWORD=
RECEIVER_EMAIL=
WEBHOOK_SECRET=
```

2. Install the CLI:

```bash
pip install -e .
```

3. Connect a repository manually if needed:

```bash
autopwflow add <repo-name>
```

4. For automatic onboarding, deploy `auto-init/app.py` (Flask) to a host such as Render, then create a GitHub App with a webhook pointed at `/webhook`. Grant Read & Write access to Contents, Secrets, and Workflows, and subscribe to the Repository event. Install the app on the account. New repositories will connect themselves from that point forward.

## Tech Stack

| Component | Purpose |
|---|---|
| GitHub Actions (`workflow_call`) | Reusable CI/CD workflow pattern |
| GitHub App | Detects repository creation account-wide |
| Groq API / LLaMA 3.3 70B | Commit analysis |
| Python 3.11 | Core scripting, CLI, email formatting |
| Flask | Webhook receiver |
| Render | Hosting for the webhook server |
| Gmail SMTP | Email delivery |
| PyNaCl | Secret encryption for the GitHub Secrets API |

## Known Limitations and Build Notes

This project was built solo and debugged in public. Several non-obvious issues came up during development, including a reusable-workflow quirk that silently broke file-change detection, and a temporary account-level restriction from GitHub that blocked the automated onboarding flow for several days. All of these are documented with root cause and fix in `TROUBLESHOOTING.md`.

## Author

Ekaanksh — [github.com/Ekaanksh-dev](https://github.com/Ekaanksh-dev)

BSc IT student. DevOps and AI integration developer.

## License

Apache License 2.0. See `LICENSE` for details.
