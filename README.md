# 🎛️ Punk Records — AI-Powered DevOps Commit Notifier

> *"Inspired by Vegapunk's satellite architecture from One Piece — one central brain, multiple repos, zero manual checking."*

![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3_70B-orange?style=for-the-badge)
![License](https://img.shields.io/badge/License-Apache_2.0-blue?style=for-the-badge)

---

## 🧠 What is Punk Records?

**Punk Records** is a centralized AI-powered commit intelligence system. Every time a push happens across any of your repositories, Punk Records automatically:

- Detects which **branch** was pushed to
- Identifies exactly which files were **added, modified, or removed**
- Records the precise **timestamp** of the push
- Sends the commit context to **Groq (LLaMA 3.3 70B)** for AI analysis
- Delivers a structured **HTML email report** with an intelligent summary

No more manually checking multiple repos. One brain handles everything.

---

## 🏗️ Architecture

```
Health-agent (push)  ──┐
my-app (push)        ──┤──→  devops-ai-notifier  ──→  Groq API  ──→  Gmail
portfolio (push)     ──┘         (Punk Records)       LLaMA 3.3
```

Each repository is a **satellite** — independent, does its own work. The notifier repo is **Punk Records** — the central brain that analyzes and reports everything.

This is a real distributed systems pattern called **Hub and Spoke Architecture**.

---

## ✨ Features

- 🔁 **Multi-repo support** — one central workflow, plugs into any repo with 20 lines
- 🤖 **AI-powered summaries** — LLaMA 3.3 70B analyzes what changed and why it matters
- 🌿 **Branch detection** — knows exactly which branch was pushed to
- 📂 **File-level diff** — added, modified, and removed files listed separately
- 🕐 **Full timestamps** — human-readable date and time in UTC
- 📧 **Rich HTML emails** — structured table layout, color-coded file changes
- ♻️ **Reusable workflow** — `workflow_call` pattern, add any future repo in seconds

---

## 📧 Email Report Preview

```
Subject: [Ekaanksh-dev/my-app] Push to main by Ekaanksh-dev — a3f9c12

📁 Repository    Ekaanksh-dev/my-app
🌿 Branch        main
👤 Author        Ekaanksh-dev
🔖 Commit        a3f9c12
🕐 Timestamp     30 May 2026, 02:30 PM UTC
💬 Message       added docker support

📂 Changed Files
✅ Added      Dockerfile, docker-compose.yml
✏️ Modified   README.md
🗑️ Removed    none

🤖 AI Summary
This commit containerizes the my-app project using Docker and Docker Compose,
enabling consistent deployment across environments. The README update suggests
documentation was added alongside the setup — good practice for maintainability.
```

---

## 🗂️ Repository Structure

```
devops-ai-notifier/
└── .github/
    └── workflows/
        └── ai-notify.yml    ← The central reusable workflow (Punk Records brain)
```

Each satellite repo contains:

```
any-repo/
└── .github/
    └── workflows/
        └── notify.yml       ← 20-line caller that triggers Punk Records
```

---

## 🚀 Setup Guide

### Step 1 — Fork or clone this repo

```bash
git clone https://github.com/Ekaanksh-dev/devops-ai-notifier.git
```

### Step 2 — Add secrets to this repo

Go to `Settings → Secrets and variables → Actions` and add:

| Secret | Description |
|---|---|
| `GROQ_API_KEY` | Get free at [console.groq.com](https://console.groq.com) |
| `SENDER_EMAIL` | Your Gmail address |
| `SENDER_PASSWORD` | Gmail App Password (not your login password) |
| `RECEIVER_EMAIL` | Where to receive notifications |

### Step 3 — Add the caller workflow to any repo

Create `.github/workflows/notify.yml` in any repo you want to monitor:

```yaml
name: Notify on Push

on:
  push:
    branches: ['**']

jobs:
  call-notifier:
    uses: Ekaanksh-dev/devops-ai-notifier/.github/workflows/ai-notify.yml@master
    with:
      repo_name: ${{ github.repository }}
      branch: ${{ github.ref_name }}
      commit_sha: ${{ github.sha }}
      commit_message: ${{ github.event.head_commit.message }}
      pusher: ${{ github.actor }}
      files_added: ${{ join(github.event.head_commit.added, ', ') }}
      files_modified: ${{ join(github.event.head_commit.modified, ', ') }}
      files_removed: ${{ join(github.event.head_commit.removed, ', ') }}
      timestamp: ${{ github.event.head_commit.timestamp }}
    secrets:
      GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
      SENDER_EMAIL: ${{ secrets.SENDER_EMAIL }}
      SENDER_PASSWORD: ${{ secrets.SENDER_PASSWORD }}
      RECEIVER_EMAIL: ${{ secrets.RECEIVER_EMAIL }}
```

Add the same 4 secrets to that repo. Push anything. Check your Gmail. ✅

---

## 🛠️ Tech Stack

| Tool | Purpose |
|---|---|
| GitHub Actions | CI/CD pipeline and workflow orchestration |
| `workflow_call` | Reusable workflow pattern (Hub and Spoke) |
| Groq API | Fast LLM inference |
| LLaMA 3.3 70B | AI commit analysis |
| Python 3.11 | Script logic and email formatting |
| Gmail SMTP | Email delivery |

---

## 💡 The Vegapunk Analogy

In One Piece, Dr. Vegapunk's satellites (Shaka, Lilith, Atlas, York, Edison, Pythagoras) are independent robots that each do specialized work — but all share one central brain called **Punk Records**.

This project works the same way:

| One Piece | This Project |
|---|---|
| Vegapunk Satellites | Your individual repos |
| Punk Records | `devops-ai-notifier` (this repo) |
| Den Den Mushi | Gmail notifications |
| Vegapunk's brain | Groq / LLaMA 3.3 70B |

---

## 👤 Author

**Ekaanksh** — [@Ekaanksh-dev](https://github.com/Ekaanksh-dev)

BSc IT Student | DevOps & AI Integration Developer

---

## 📄 License

This project is licensed under the **Apache License 2.0** — see the [LICENSE](LICENSE) file for details.
