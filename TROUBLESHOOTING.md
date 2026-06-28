# Troubleshooting Log — Punk Records

Real problems I hit while building this that weren't just my own mistakes — actual GitHub behavior that surprised me.

---

## 1. The notifier couldn't find its own script

When another repo called my reusable workflow, it ran inside *that* repo, not the notifier repo. So when it looked for `analyze.py`, it wasn't there — that file only existed in the notifier repo. I assumed calling a workflow from another repo would somehow still have access to my files. It doesn't.

**What I did:** Stopped using a separate file. Put the whole Python script directly inside the workflow YAML.

---

## 2. The "changed files" section was always empty

This one took me a while. I had a fallback like "use this value, or if it's empty, use the GitHub event data instead." But GitHub Actions inputs with a default value are never actually "empty" — so my fallback never ran, and the real file data never came through. No errors, it just silently sent blank data every single time.

**What I did:** Stopped trying to read it from GitHub's event data altogether. Just used `git diff` to compare the current commit to the last one and grab the file list directly. Way more reliable.

---

## 3. There's no webhook option for personal GitHub accounts anymore

I wanted something that fires the second I create a new repo, account-wide. Went looking for webhooks in my personal settings — not there. GitHub removed that for personal accounts. It only works per-repo or for organizations now, and a per-repo webhook obviously can't watch a repo that doesn't exist yet.

**What I did:** Built a GitHub App instead, since those can listen for "new repo created" account-wide.

---

## 4. The GitHub App's install button kept disappearing

After creating the app, the "Install App" tab just wasn't showing up. Tried generating a private key like everyone online suggested — didn't help. Made the app public to force it to show, which worked, but then it said installing was "prohibited." Tried switching back to private and couldn't find a clean way to do that either.

**What happened:** This basically fixed itself once issue #5 below got resolved. I think they were connected, but GitHub never actually told me that.

---

## 5. My account got flagged and blocked me from connecting things

Got this message:
```
This account is flagged, and therefore cannot authorize a third party application.
```

I could still push code and use GitHub completely normally — it only blocked me from connecting third-party stuff, which happened to be exactly what I needed: Render (to host my server) and installing my own GitHub App. No explanation given, no idea how long it'd last.

**What I did:** Couldn't fix this with code, so I stopped waiting on it. Built a simple command (`autopwflow add <repo>`) that does the same job manually — connect a repo in one command — so the whole project didn't depend on this working. Once the flag lifted on its own, I tested the automatic version again and it worked perfectly.
