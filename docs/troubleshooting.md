# 🛠️ Troubleshooting Log — Punk Records

A running log of stuff that broke while I was building this and what I did about it. I'm keeping this in instead of cleaning it up, because honestly the debugging is half the project.

---

## 1. Pushed to `main`, got rejected

```
error: src refspec main does not match any
```

Turned out my local branch was `master`, not `main`. I'd just assumed it was `main` because that's the GitHub default now. Checked with `git branch`, switched the push target, done.

```bash
git push origin master
```

---

## 2. GitHub blocked my push because of token scope

```
refusing to allow a Personal Access Token to create or update workflow
`.github/workflows/notify.yml` without `workflow` scope
```

My PAT didn't have the `workflow` permission checked when I made it. GitHub specifically gates anything touching `.github/workflows/` behind that scope — makes sense in hindsight, it stops random tokens from rewriting CI pipelines. Went back, edited the token, checked the box, regenerated it, re-authed.

---

## 3. `analyze.py` was nowhere to be found

```
python: can't open file '.../Health-agent/analyze.py': [Errno 2] No such file or directory
```

This one tripped me up for a bit. I had the notifier set up as a reusable workflow (`workflow_call`) so other repos could call it. But `analyze.py` only lived in the notifier repo — when `Health-agent` called the workflow, it ran *inside Health-agent's checkout*, which obviously doesn't have my script.

I'd assumed a reusable workflow would somehow "bring its own files" with it. It doesn't. Fixed it by just inlining the whole Python script directly into the YAML using a heredoc block, so there's nothing external to fetch.

---

## 4. Forgot to update a pip install line

```
ModuleNotFoundError: No module named 'requests'
```

Switched from the `groq` package to plain `requests` calls and just... forgot to change `pip install groq` to `pip install requests`. Classic.

---

## 5. The "Changed Files" section was always blank

This was the most annoying one. I was using:

```yaml
${{ inputs.files_added || join(github.event.head_commit.added, ', ') }}
```

assuming if `inputs.files_added` was empty it'd fall back to reading the push event directly. But because the reusable workflow declares a default value (`"none"`) for that input, it's never actually "empty" from GitHub's point of view — so the `||` fallback never triggers, and the real commit data never gets through.

I tried fixing it by capturing the file list in a separate step in the *caller* workflow first, but the `join(...)` expression inside a bash `echo` line didn't resolve the way I expected either.

What actually worked: stop relying on the event payload entirely and just use `git diff` against the previous commit:

```bash
ADDED=$(git diff --name-only --diff-filter=A HEAD~1 HEAD | tr '\n' ',' | sed 's/,$//')
```

Needed `fetch-depth: 2` on checkout so there's a previous commit to diff against. This was more reliable than anything event-based.

---

## 6. Getting two emails per push

Once I added a caller `notify.yml` to the notifier repo itself, every push there fired the workflow twice — once from the leftover direct `push:` trigger still in `ai-notify.yml`, and once through the new `workflow_call`. Removed the direct trigger, left only `workflow_call:`, so there's one path in, always.

---

## 7. `pynac1` vs `pynacl`

Spent a few minutes confused why pip couldn't find a package that definitely exists. Turned out I'd typed `pynac1` (with a digit 1) instead of `pynacl` (lowercase L). Embarrassing, but fast to fix once I actually looked closely at the characters.

---

## 8. Forgot a dependency entirely

```
ModuleNotFoundError: No module named 'cryptography'
```

Added code that imports from `cryptography` for the secret-encryption logic but never added it to `requirements.txt`. Added it, redeployed.

---

## 9. CLI command not recognized

I wrote a whole `cmd_secrets_all()` function, tested it mentally, felt good about it — and then ran `autopwflow secrets-all` and got "unknown command." I'd written the function but never actually wired it into the `if/elif` chain in `main()`. The function just sat there, unused. Added the missing `elif`, reinstalled, worked.

---

## 10. There's no such thing as a personal GitHub webhook anymore

I wanted something that fires the moment I create a *new* repo, account-wide. Went looking for "Webhooks" in my personal GitHub settings — it's not there. GitHub removed account-level webhooks for personal users at some point. Webhooks now only exist per-repo or per-organization, and a per-repo webhook can't tell you about a repo that doesn't exist yet, obviously.

So the real options were: move everything into an Organization (org webhooks do support repo-creation events), or build a GitHub App (which can subscribe to account-wide `repository` events). I went with the GitHub App route since I didn't want to restructure my repos.

---

## 11. The GitHub App's "Install App" tab kept disappearing

This one I never fully solved. After creating the app, "Install App" wasn't showing in the settings sidebar. The usual advice is "generate a private key first" — I did that, didn't help. Then I tried making the app public, which *did* make the tab appear, but then installing it failed with "Install is prohibited." Tried to revert back to private and the toggle didn't give me a clean way back.

Ended up deleting and recreating the app with "Only on this account" selected up front. Still flaky. I think this is tied to issue #12 below.

---

## 12. My account got flagged and I genuinely didn't know what that meant at first

```
This account is flagged, and therefore cannot authorize a third party application.
```

First reaction: panic, thought I'd been banned. Looked into it — flagged isn't banned. I could still push code, create repos, do everything normal. It specifically blocks *authorizing third-party OAuth apps*, which happened to be exactly the two things I needed: Render's GitHub integration (to deploy the auto-init server) and the final install step of my own GitHub App.

I genuinely don't know why it got flagged — possibly just an automated trust check on a newer account doing a burst of API-adjacent activity in a short window. I haven't resolved this yet. I've left it open rather than fake a fix.

**What I did instead of getting stuck:** I stopped trying to force the automatic version through. The whole point of the auto-init system was "new repo gets connected with zero manual steps." I already had `autopwflow add <repo>` from the CLI, which does the exact same end result in one command, just not automatically triggered. So I shipped that as the real feature and left the GitHub App / Render auto-trigger as a documented "not done yet" rather than pretending it works.

---

## What I'd tell someone else hitting these

- Reusable workflows (`workflow_call`) do **not** inherit the caller's push event context the way you'd intuitively expect — test that assumption early.
- If something needs file-change data reliably, `git diff` against the previous commit beat anything event-payload based for me.
- Not every blocker is a code problem. Sometimes it's the platform (account flags, OAuth review states) and no amount of rereading your YAML will fix that — better to build a manual fallback and move on than burn hours on something outside your control.
