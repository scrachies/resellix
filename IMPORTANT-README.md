# Resellix — IMPORTANT-README

**© Thomas Mikhline** · **https://github.com/scrachies/resellix** (scrachies)

---

## ⚠️ Legal / Rechtliches

**English:** Private software by Thomas Mikhline. **Do not** publish, redistribute, or share. Legal action for unauthorized distribution.

**Deutsch:** Nur private Nutzung. **Nicht** veröffentlichen oder weitergeben. Rechtliche Schritte bei Verstoß.

---

## Folder (only 3 + this file) / Nur diese Ordner

```
resellix/
├── IMPORTANT-README.md
├── windows/     → startwindows.bat, updatewindows.bat
├── apple/       → startapple.command, updateapple.command
└── dev/         → everything else (.env, targets, app code, logs, database)
```

---

## Install

### Requirements

- **Python 3.11+** ([python.org](https://www.python.org)) — Windows: check **Add to PATH**
- **Git** — [git-scm.com](https://git-scm.com) / Mac: `xcode-select --install`

### Clone

```bash
git clone https://github.com/scrachies/resellix.git
cd resellix
```

### Start

| OS | Action |
|----|--------|
| **Windows** | `windows\startwindows.bat` |
| **Mac** | `chmod +x apple/*.command` then `apple/startapple.command` |

First run installs packages (~5–15 min). Settings go in **`dev/.env`** (created automatically).

### Configure

Open the app **Settings** or edit **`dev/.env`**:

- `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`
- `VINTED_SESSION_COOKIE` (Vinted login)
- `SNIPER_PLATFORMS=vinted,kleinanzeigen,ebay`

Snipe targets → **`dev/targets.json`** (via app UI).

---

## Auto-updater

Every start checks **GitHub** for new commits:

- If an update exists → **downloads automatically** (`git pull`) and refreshes pip packages.
- Manual: `windows\updatewindows.bat` or `apple/updateapple.command`

Requires a **git clone** (not a plain ZIP without `.git`).

---

## Updates (Thomas)

```bash
git add .
git commit -m "Your fix"
git push origin main
```

Friends get it on next start or via update script.

---

## Cleanup old layout

If you still see `app\`, `vendor\`, logs in the **root**: close Resellix, then run:

```powershell
powershell -ExecutionPolicy Bypass -File dev\cleanup_to_dev.ps1
```

Root should then show only **dev**, **windows**, **apple**, **IMPORTANT-README.md**.

---

*Thomas Mikhline — private use only*
