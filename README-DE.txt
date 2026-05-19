================================================================================
  RESELLIX — WICHTIGE ANLEITUNG (Deutsch)
  (c) Thomas Mikhline — nur private Nutzung
  https://github.com/scrachies/resellix  (GitHub: scrachies)
================================================================================

RECHTLICHER HINWEIS
-------------------
Resellix wurde von Thomas Mikhline entwickelt. Du darfst die Software nur
privat und auf von Thomas freigegebenen Geräten nutzen.

Du darfst NICHT:
  - das Projekt öffentlich veröffentlichen oder teilen
  - den Bot weitergeben, verkaufen oder unterlizenzieren
  - Urheberhinweise entfernen oder die Software als deine eigene ausgeben

Unbefugte Weitergabe oder Veröffentlichung führt zu rechtlichen Schritten.
Updates erhältst du nur über das private GitHub-Repository oben.


ORDNERSTRUKTUR (so soll es aussehen)
-----------------------------------
resellix/
  README-EN.txt          (English version)
  README-DE.txt          (diese Datei)
  windows/               startwindows.bat, updatewindows.bat
  apple/                 startapple.command, updateapple.command
  dev/                   alles andere (.env, targets, Code, Logs, Datenbank)

Altes start.bat oder einen doppelten app/-Ordner im Hauptordner nicht verwenden.


VORAUSSETZUNGEN
---------------
  - Python 3.11+     https://www.python.org
                     Windows: Haken bei "Add python.exe to PATH" setzen
  - Git              https://git-scm.com/download/win
                     Mac: xcode-select --install
  - Internet         beim ersten Start werden Pakete geladen (ca. 5–15 Min.)


INSTALLATION (erstes Mal)
-------------------------
1. Rechtlichen Hinweis oben lesen.

2. Projekt klonen (empfohlen):

     git clone https://github.com/scrachies/resellix.git
     cd resellix

3. Bot starten:
     Windows:  Doppelklick auf  windows\startwindows.bat
     Mac:      chmod +x apple/*.command
               dann Doppelklick auf  apple/startapple.command

4. Beim ersten Start wird dev/app/.venv erstellt und Pakete installiert.
   Einstellungen: dev/.env  (wird aus dev/.env.example kopiert falls nötig)

5. Optional Desktop-Verknüpfung (Windows):
     windows\create_desktop_shortcut.bat


EINSTELLUNGEN
-------------
Im Programm unter Settings oder in dev/.env bearbeiten:

  TELEGRAM_BOT_TOKEN     von @BotFather
  TELEGRAM_CHAT_ID       von @userinfobot
  VINTED_SESSION_COOKIE  Vinted-Login-Cookie (Browser DevTools)
  KLEINANZEIGEN_API_URL  meist http://127.0.0.1:8000
  SNIPER_PLATFORMS       z.B. vinted,kleinanzeigen,ebay

Snipe-Ziele liegen in dev/targets.json (über das Dashboard).


WAS DER BOT MACHT
-----------------
  - Sucht auf Vinted, Kleinanzeigen und eBay nach deinen Snipe-Zielen
  - Min/Max-Preis, Größen, Plattformen pro Ziel
  - Telegram-Benachrichtigungen mit Foto, Preis, Link, geschätztem Gewinn
  - Dashboard zum Verwalten von Zielen, Pause, Einstellungen
  - Telegram-Suchmodus, z.B.:
      search for raspberry pi under 40 over 20
    Dann: Plattform -> Anzahl -> Sortierung -> Ergebnisse -> "continue" für Alerts


AUTO-UPDATE
-----------
Bei jedem Start wird GitHub (scrachies/resellix) auf neue Commits geprüft.

  - Gibt es Updates: git pull automatisch, danach pip-Pakete aktualisieren
  - Manuell: windows\updatewindows.bat  oder  apple/updateapple.command

Du brauchst einen Git-Clone (kein reines ZIP ohne .git-Ordner).


UPDATES (für Thomas / Maintainer)
---------------------------------
  git add .
  git commit -m "Beschreibung des Fixes"
  git push origin main

Freunde bekommen Updates beim nächsten Start oder über das Update-Skript.


PROBLEMLÖSUNG
-------------
  Problem: dev\app fehlt
    Lösung: git clone https://github.com/scrachies/resellix.git

  Problem: alter app\-Ordner im Hauptverzeichnis
    Lösung: Resellix schließen, root\app\ löschen (dev\app\ behalten)

  Problem: Python nicht gefunden
    Lösung: Python neu installieren mit PATH-Option

  Problem: Mac öffnet .command nicht
    Lösung: chmod +x apple/startapple.command

  Problem: Kleinanzeigen / Playwright
    Lösung: stabiles Internet, Startskript erneut ausführen

Logs: dev\resell.log , dev\kleinanzeigen_api.log


ALTES LAYOUT AUFRÄUMEN
----------------------
Wenn im Hauptordner noch app\, vendor\ oder Logdateien liegen:
  1. Resellix vollständig beenden
  2. In PowerShell ausführen:
       powershell -ExecutionPolicy Bypass -File dev\cleanup_to_dev.ps1
  Im Hauptordner sollten nur noch sein: dev, windows, apple, README-EN.txt, README-DE.txt


================================================================================
Thomas Mikhline — nur private Nutzung. Nicht öffentlich teilen.
================================================================================
