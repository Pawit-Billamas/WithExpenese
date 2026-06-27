# 🐍 Complete PythonAnywhere Deployment Guide
### For: PawitBillamas | Repo: WithExpenese

| Item | Value |
|------|-------|
| GitHub Repo | https://github.com/Pawit-Billamas/WithExpenese.git |
| PythonAnywhere Username | PawitBillamas |
| Your Bot URL | https://PawitBillamas.pythonanywhere.com |
| LINE Webhook URL | https://PawitBillamas.pythonanywhere.com/webhook |

---

## ✅ BEFORE YOU START — Push Latest Code

Run in **PowerShell** on your computer:

```powershell
cd e:\Projects\LineBot
git add .
git commit -m "Ready for PythonAnywhere"
git push
```

If it says **"Everything up to date"** that is fine too. ✅

---

## PART 1 — Create PythonAnywhere Account

1. Go to **https://www.pythonanywhere.com**
2. Click **"Pricing & signup"** → **"Create a Beginner account"**
3. Fill in **Username: PawitBillamas**, your email, password
4. Click **"Register"** → verify email → log in

---

## PART 2 — Get Your Code onto PythonAnywhere

### Step 2.1 — Open Bash Console

1. Click the **"Consoles"** tab in the top navigation bar
2. Under **"Start a new console"**, click **"Bash"**
3. A black terminal window opens

### Step 2.2 — Delete Old Folder (if exists)

Type this and press **Enter**:

```bash
rm -rf ~/WithExpenese
```

No output = success ✅

### Step 2.3 — Clone Your Repository

Type this and press **Enter**:

```bash
git clone https://github.com/Pawit-Billamas/WithExpenese.git
```

You will see files downloading. Wait for it to finish. ✅

### Step 2.4 — Go Into the Folder

```bash
cd ~/WithExpenese
```

### Step 2.5 — Install Dependencies

```bash
pip install --user -r requirements.txt
```

Wait 1–2 minutes. When done you will see:
```
---

## PART 3 — Create the Web App

### Step 3.1 — Go to Web Tab
Click the **"Web"** tab in the top navigation bar.
Click **"Add a new web app"**.

### Step 3.2 — Wizard Screen 1: Domain
You see: `PawitBillamas.pythonanywhere.com`
Click **"Next"** — do NOT change anything.

### Step 3.3 — Wizard Screen 2: Framework
You see: Flask, Django, Web2py, Bottle, Scratch...
👉 Click **"Manual configuration"** (the LAST option)
Click **"Next"**.

### Step 3.4 — Wizard Screen 3: Python Version
👉 Click **"Python 3.10"**
Click **"Next"** → **"Next"** until done.

You are now on the Web configuration page.

---

## PART 4 — Fill in the Configuration Boxes

### Box 1: Source Code

Find the **"Code"** section.
Next to **"Source code:"**, click the pencil icon.
Type:
```
/home/PawitBillamas/WithExpenese
```
Click the blue ✅ tick to save.

### Box 2: Working Directory

Just below Source code, next to **"Working directory:"**, click the pencil icon.
Type:
```
/home/PawitBillamas/WithExpenese
```
Click the blue ✅ tick to save.

### Box 3: Virtualenv

Leave this **completely empty**. Skip it.

### Box 4: WSGI Configuration File ⚠️ MOST IMPORTANT

Find the line that says:
> WSGI configuration file: `/var/www/pawitbillamas_pythonanywhere_com_wsgi.py`

Click on that **blue link**. A code editor opens.

**Press Ctrl+A to select ALL the existing code, then delete it.**

Paste this EXACT code (nothing else):

```python
import os
import sys

project_home = '/home/PawitBillamas/WithExpenese'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

---

## PART 6 — Launch & Test

### Step 6.1 — Reload the Web App
Click the **"Web"** tab.
Click the big green button: **"Reload PawitBillamas.pythonanywhere.com"**
Wait 10 seconds.

### Step 6.2 — Test in Browser
Open a new browser tab and visit:
```
https://PawitBillamas.pythonanywhere.com
```

✅ **SUCCESS** — you should see:
```json
{"status":"ok","message":"Expense Tracker Bot is running."}
```

❌ **If you see an error page** — go to the Web tab, click **"Error log"** and scroll to the bottom to see what went wrong.

---

## PART 7 — Connect LINE Webhook

1. Go to **https://developers.line.biz/console/**
2. Click your Provider → click channel **2010529677**
3. Click the **"Messaging API"** tab
4. Scroll to **"Webhook settings"**
5. Click **"Edit"** next to Webhook URL
6. Type this exactly:
   ```
   https://PawitBillamas.pythonanywhere.com/webhook
   ```
7. Click **"Update"**
8. Click **"Verify"** → you should see ✅ **Success**
9. Turn on **"Use webhook"** toggle (must be green/ON)

---

## PART 8 — Test the Bot in LINE

Add your bot as a friend (scan the QR code from LINE Developers Console).

Then send these messages:

| What you type | What bot should reply |
|---|---|
| `help` | Lists all commands |
| `recent` | 📭 No transactions. |
| `categories` | Lists Food, Transport, Bills, Shopping, Entertainment, Health |
| `cash 150 lunch` | Shows category quick-reply buttons |
| *(tap Food)* | ✅ 150 THB → Food |
| `summary` | 📊 Total: 150 THB |

✅ **If all of the above work, your bot is 100% ready!** 🎉

---

## PART 9 — Every 3 Months (Keep Alive)

PythonAnywhere free accounts need renewal every 90 days.
They will email you a reminder.

1. Log in to PythonAnywhere
2. Click the **"Web"** tab
3. Click **"Run until [date]"** button
4. Done! ✅

---

## PART 10 — How to Update Bot After Code Changes

**On your computer (PowerShell):**
```powershell
cd e:\Projects\LineBot
git add .
git commit -m "describe your change"
git push
```

**On PythonAnywhere (Bash console):**
```bash
cd ~/WithExpenese
git pull
```

Then **Web tab → Reload**. Done! ✅

---

## 🐛 TROUBLESHOOTING

### "No module named 'uvicorn'"
```bash
cd ~/WithExpenese && git pull
```
Then reload.

### "No module named 'app'"
The WSGI file has a wrong path. Re-open it and make sure the path is:
```python
project_home = '/home/PawitBillamas/WithExpenese'
```

### "Invalid signature" when verifying webhook
Open Files tab → `.env` → check this line is correct:
```
LINE_CHANNEL_SECRET=d964ef69ff35da377cb1e86914009e0c
```

### Bot does not respond in LINE
1. Visit `https://PawitBillamas.pythonanywhere.com` — does it show JSON? ✅
2. Is webhook URL exactly `https://PawitBillamas.pythonanywhere.com/webhook`? ✅
3. Is "Use webhook" toggle ON? ✅
4. Web tab → click Error log — any Python errors?

---

## ✅ Final Checklist

- [ ] Code pushed to GitHub
- [ ] Bash: `rm -rf ~/WithExpenese`
- [ ] Bash: `git clone https://github.com/Pawit-Billamas/WithExpenese.git`
- [ ] Bash: `cd ~/WithExpenese`
- [ ] Bash: `pip install --user -r requirements.txt`
- [ ] Bash: `python -c "from app.main import app; print('OK')"` → shows OK
- [ ] Web app created (Manual config + Python 3.10)
- [ ] Source code: `/home/PawitBillamas/WithExpenese`
- [ ] Working directory: `/home/PawitBillamas/WithExpenese`
- [ ] WSGI file: replaced with the 10-line code above
- [ ] .env file: created with the 3 credential lines
- [ ] Web app reloaded
- [ ] Browser shows JSON at `https://PawitBillamas.pythonanywhere.com` ✅
- [ ] LINE webhook set + verified ✅
- [ ] "Use webhook" toggle is ON ✅
- [ ] Bot responds to `cash 100 test` with category buttons ✅
from app.main import app
from fastapi.wsgi import WSGIMiddleware

application = WSGIMiddleware(app)
```

Click **"Save"** (top right of editor).

Click the **← back arrow** or **"Web"** tab to return.

---

## PART 5 — Add Your .env Credentials File

### Step 5.1 — Go to Files Tab
Click the **"Files"** tab at the top.

### Step 5.2 — Navigate to Project Folder
In the file browser, click through to:
```
/home/PawitBillamas/WithExpenese/
```

### Step 5.3 — Open or Create .env

- If `.env` is listed → click it to open it
- If NOT listed → in the text field that says **"Enter new file name"**, type `.env` and click **"New file"**

### Step 5.4 — Paste Credentials

Delete everything in the file. Paste this EXACTLY:

```
LINE_CHANNEL_SECRET=d964ef69ff35da377cb1e86914009e0c
LINE_CHANNEL_ACCESS_TOKEN=FukAtAe4lVENttlUwGp3nL2rTO2HgMdN0zf8+6HDMlEvQddds85hKO1zdfvylYC1ZSfFHdBv7PfKYew/nZPjWglXcW9te6O0u5C72OVSXLUysOjUxfIl5CXDtzGZQSqbkAZeM+9VaEuLl69oB1UzvAdB04t89/1O/w1cDnyilFU=
MONTHLY_BUDGET=20000
```

Click **"Save"**.
Successfully installed fastapi-0.115.6 line-bot-sdk-3.23.1 python-dotenv-1.0.1 python-multipart-0.0.20
```

✅ Only ~15 MB used out of 512 MB!

### Step 2.6 — Verify Everything Loads

```bash
python -c "from app.main import app; print('OK - app loaded successfully')"
```

Expected output:
```
OK - app loaded successfully
```

⚠️ If you see an error here, **stop and check the Troubleshooting section** before continuing.