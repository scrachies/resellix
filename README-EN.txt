================================================================================
  RESELLIX — IMPORTANT README (English)
  (c) Thomas Mikhline — private license only
  https://github.com/scrachies/resellix  (GitHub user: scrachies)
================================================================================

LEGAL NOTICE
------------
Resellix was created by Thomas Mikhline. You may use it only for private
reselling on machines Thomas authorized.

You must NOT:
  - publish, upload, or share this project publicly
  - redistribute, resell, or sublicense the bot
  - remove copyright notices or claim authorship

Unauthorized distribution or publication will result in legal action.
Updates are only provided through the private GitHub repository above.


FOLDER LAYOUT (what you should see)
-----------------------------------
resellix/
  README-EN.txt          (this file)
  README-DE.txt          (German version)
  windows/               startwindows.bat, updatewindows.bat
  apple/                 startapple.command, updateapple.command
  dev/                   everything else (.env, targets, code, logs, database)

Do not use old start.bat or a duplicate app/ folder in the root.


REQUIREMENTS
------------
  - Python 3.11+     https://www.python.org
                     Windows: enable "Add python.exe to PATH" during install
  - Git              https://git-scm.com/download/win
                     Mac: xcode-select --install
  - Internet         first start downloads libraries (about 5–15 minutes)


INSTALL (first time)
--------------------
1. Read the legal notice above.

2. Clone the project (recommended):

     git clone https://github.com/scrachies/resellix.git
     cd resellix

3. Start the bot:
     Windows:  double-click  windows\startwindows.bat
     Mac:      chmod +x apple/*.command
               then double-click  apple/startapple.command

4. First run creates dev/app/.venv and installs packages automatically.
   Settings file: dev/.env  (copied from dev/.env.example if missing)

5. Optional Windows desktop shortcut:
     windows\create_desktop_shortcut.bat


CONFIGURE
---------
Open Settings in the app, or edit dev/.env:

  TELEGRAM_BOT_TOKEN     from @BotFather on Telegram
  TELEGRAM_CHAT_ID       from @userinfobot on Telegram
  VINTED_SESSION_COOKIE  Vinted login cookie (browser DevTools)
  KLEINANZEIGEN_API_URL  usually http://127.0.0.1:8000
  SNIPER_PLATFORMS       e.g. vinted,kleinanzeigen,ebay

Snipe targets are stored in dev/targets.json (via the dashboard).


WHAT THE BOT DOES
-----------------
  - Scans Vinted, Kleinanzeigen, and eBay for your snipe targets
  - Min/max price, sizes, platforms per target
  - Telegram alerts with photo, price, link, estimated profit
  - Dashboard to add targets, pause sniper, change settings
  - Telegram search mode, e.g.:
      search for raspberry pi under 40 over 20
    Then: platform -> count -> sort -> results -> type "continue" to resume alerts


AUTO-UPDATER
------------
Every start checks GitHub for new commits on scrachies/resellix.

  - If updates exist: git pull runs automatically, then pip packages refresh
  - Manual update: windows\updatewindows.bat  or  apple/updateapple.command

You need a git clone (not a plain ZIP without the .git folder).


UPDATES (for Thomas / maintainer)
---------------------------------
  git add .
  git commit -m "Describe your fix"
  git push origin main

Friends receive updates on their next start or when they run the update script.


TROUBLESHOOTING
---------------
  Problem: dev\app missing
    Fix: git clone https://github.com/scrachies/resellix.git

  Problem: old app\ folder still in root
    Fix: close Resellix, delete root\app\ (keep dev\app\)

  Problem: Python not found
    Fix: reinstall Python with PATH option

  Problem: Mac won't open .command file
    Fix: chmod +x apple/startapple.command

  Problem: Kleinanzeigen / Playwright errors
    Fix: stable internet, run start script again

Logs: dev\resell.log , dev\kleinanzeigen_api.log


CLEANUP OLD FOLDER LAYOUT
-------------------------
If you still see app\, vendor\, or log files in the root folder:
  1. Close Resellix completely
  2. Run in PowerShell:
       powershell -ExecutionPolicy Bypass -File dev\cleanup_to_dev.ps1
  Root should show only: dev, windows, apple, README-EN.txt, README-DE.txt


================================================================================
Thomas Mikhline — private use only. Do not share publicly.
================================================================================
