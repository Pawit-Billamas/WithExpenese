# 🐍 Hosting Your LINE Bot on PythonAnywhere (FREE & PERMANENT)

This guide will take you from your local computer to a live, 24/7 bot with a persistent database. **No credit card needed.**

---

## 📋 Prerequisites

1. **GitHub Account** (to upload your code)
2. **PythonAnywhere Account** (Free tier)
3. **Your LINE Credentials** (Channel Secret and Access Token)

---

## 🚀 Step 1: Push Code to GitHub

Since PythonAnywhere is a remote server, the easiest way to get your code there is via GitHub.

1. **Create a GitHub Repository:**
   - Go to [github.com/new](https://github.com/new)
   - Name: `linebot-expense-tracker`
   - Set to **Private** (so your code is safe)
   - Create repository

2. **Push your code:**
   Open PowerShell in `e:\Projects\LineBot` and run:
   ```powershell
   git init
   git add .
   git commit -m "Final bot version"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/linebot-expense-tracker.git
   git push -u origin main
   ```

---

## ☁️ Step 2: PythonAnywhere Setup

### 2.1 Create Account & Dashboard
1. Go to [pythonanywhere.com](https://www.pythonanywhere.com/) and create a **Free Beginner** account.
2. Once logged in, go to the **"Consoles"** tab.

### 2.2 Clone Your Code
1. Open a **Bash Console**.
2. Clone your GitHub repo (Replace `USERNAME` and `REPO`):
   ```bash
   git clone https://github.com/USERNAME/linebot-expense-tracker.git
   cd linebot-expense-tracker
   ```

### 2.3 Install Dependencies
Run these commands in the Bash console:
```bash
# Create a virtual environment to keep storage low
mkvirtualenv --python=/usr/bin/python3.10 myenv
pip install -r requirements.txt
pip install fastapi.wsgi  # Crucial for PythonAnywhere
```
*Note: If `mkvirtualenv` isn't found, just use: `pip install -r requirements.txt fastapi.wsgi`*

---

## ⚙️ Step 3: Configure the Web App

1. Go to the **"Web"** tab in the PythonAnywhere dashboard.
2. Click **"Add a new web app"**.
3. **Step 1:** Click **Manual Configuration** (NOT FastAPI/Django).
4. **Step 2:** Select **Python 3.10**.

### 📦 Filling the Boxes (Crucial!):

#### Box 1: Virtualenv
- Find the **"Virtualenv"** section.
- Click "Enter path to a virtualenv".
- Enter: `/home/YOUR_USERNAME/.virtualenvs/myenv` (Replace `YOUR_USERNAME` with your actual PythonAnywhere username).
- Click the blue checkmark ✅.

#### Box 2: Code Path (Working Directory)
- Go to the **"Code"** section.
- **Source code:** `/home/YOUR_USERNAME/linebot-expense-tracker`
- Click the blue checkmark ✅.

---

## 🔐 Step 4: Environment Variables (`.env`)

Since you can't use a `.env` file easily on PythonAnywhere's Web tab, do this:

1. Go to the **"Files"** tab.
2. Navigate to `/home/YOUR_USERNAME/linebot-expense-tracker/`
3. Create a new file named `.env` (if it's not already there).
4. **Paste your credentials exactly like this:**
   ```env
   LINE_CHANNEL_SECRET=d964ef69ff35da377cb1e86914009e0c
   LINE_CHANNEL_ACCESS_TOKEN=FukAtAe4lVENttlUwGp3nL2rTO2HgMdN0zf8+6HDMlEvQddds85hKO1zdfvylYC1ZSfFHdBv7PfKYew/nZPjWglXcW9te6O0u5C72OVSXLUysOjUxfIl5CXDtzGZQSqbkAZeM+9VaEuLl69oB1UzvAdB0S...
   MONTHLY_BUDGET=20000
   ```
5. Click **Save**.

---

## 🛠️ Step 5: The WSGI Configuration

This is the "magic" that makes FastAPI work on PythonAnywhere.

1. In the **"Web"** tab, find the **"WSGI configuration file"** link.
2. Click the link to edit the file.
3. **Delete everything** inside the file and replace it with this:

```python
import os
import sys

# Path to your project
project_home = '/home/YOUR_USERNAME/linebot-expense-tracker'
if project_home not in sys.path:
    sys.path.append(project_home)

from app.main import app
from fastapi.wsgi import WSGIMiddleware

# This is what PythonAnywhere looks for
application = WSGIMiddleware(app)
```
*(Replace `YOUR_USERNAME` with your actual username)*

4. Click **Save**.

---

## 🚀 Step 6: Go Live!

1. Go back to the **"Web"** tab.
2. Click the big green **"Reload YOUR_USERNAME.pythonanywhere.com"** button.
3. Your bot is now LIVE!

---

## 🔗 Step 7: Update LINE Webhook

1. Copy your URL from the Web tab. It looks like: `https://YOUR_USERNAME.pythonanywhere.com`
2. Go to **LINE Developers Console** → **Messaging API**.
3. Set Webhook URL to: `https://YOUR_USERNAME.pythonanywhere.com/webhook`
4. Click **Verify** → ✅ Success!
5. Enable **"Use webhook"**.

---

## 🗄️ Storage & Database (Minimal Issue Guide)

### How PythonAnywhere handles your DB:
- Your `expenses.db` is stored in `/home/YOUR_USERNAME/linebot-expense-tracker/expenses.db`.
- **Unlike Render, this file is PERMANENT.** It will not be deleted.

### To keep storage minimal:
1. **Avoid large image uploads:** The current bot only uses images for OCR and doesn't save the image files to the disk (it only saves the URL). This keeps your storage very low.
2. **Periodic Backups:** Once a month, use the `export` command in your bot to save your data to a CSV file on your computer.

---

## ⚠️ Maintenance (The "Free Tier" Price)

**The only catch:**
PythonAnywhere's free tier requires you to "extend" your app once every 3 months.

1. You will receive an email from PythonAnywhere.
2. Go to your **Web tab**.
3. Click the button **"Run until [Date]"**.
4. **Done!** Your bot stays online for another 90 days.

---

## 🧪 Test Checklist:
- [ ] `recent` → Bot replies ✅
- [ ] `cash 100 coffee` → Category buttons appear ✅
- [ ] Send slip photo → Bot processes and asks for amount/category ✅
- [ ] Tap "Summary" on Rich Menu → Summary shows ✅
