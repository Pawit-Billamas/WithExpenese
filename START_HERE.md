# 🎉 Your FREE LINE Expense Tracker Bot is Ready!

## ✅ What's Done:
- ✅ All code created and tested
- ✅ Dependencies installed  
- ✅ Channel credentials configured
- ✅ **NO API KEYS NEEDED** - Completely FREE!

## 🚀 Quick Start (3 Steps):

### Step 1: Start the Bot Server

Open PowerShell in `e:\Projects\LineBot\` and run:

```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
✅ Database initialized.
```

**Keep this terminal open!**

---

### Step 2: Expose with ngrok

1. Download ngrok: https://ngrok.com/download
2. Extract and open **another PowerShell** in the ngrok folder
3. Run:

```powershell
.\ngrok http 8000
```

4. Copy the **HTTPS URL** (looks like: `https://abc123.ngrok-free.app`)

---

### Step 3: Configure LINE Webhook

1. Go to: https://developers.line.biz/console/
2. Select your Provider → Click channel **2010529677**
3. Click **"Messaging API"** tab
4. Find **"Webhook settings"**
5. Click **"Edit"**
6. Enter: `https://YOUR_NGROK_URL/webhook`
   - Example: `https://abc123.ngrok-free.app/webhook`
7. Click **"Update"**
8. Click **"Verify"** → Should show ✅ **Success**
9. Toggle **"Use webhook"** → **ON**

---

## 🧪 Test Your Bot!

1. Open LINE app on your phone
2. Go to your Official Account page
3. Click the QR code to add as friend
4. Send a message: `recent`
5. Bot should reply: `📭 No transactions.`

**It works!** 🎉

---

## 💰 How to Use:

### Log a Cash Expense:
```
cash 120 lunch
```
Bot will show category buttons → Click one → Done!

### View Recent Expenses:
```
recent
```

### Monthly Summary:
```
summary
```

### Send a Slip Photo:
1. Take photo of payment slip
2. Send to bot
3. Bot replies: "📸 Image received! Type amount: edit [amount]"
4. You type: `edit 150`
5. Bot shows categories → Pick one → Done!

### Create New Category:
1. When selecting category, click "➕ New Category"
2. Type the name (e.g., "Gym")
3. Done!

### Export All Data:
```
export
```

### List Categories:
```
categories
```

---

## 🎨 Optional: Rich Menu

Go to https://manager.line.biz/ → Your account → Chat → Rich menus

Create 4 buttons:
| Button | Action | Text |
|--------|--------|------|
| 📊 Summary | Message | summary |
| 📋 Recent | Message | recent |
| 💰 Log Cash | Message | log cash |
| 📂 Categories | Message | categories |

---

## 🔧 Troubleshooting

### Bot doesn't respond?
- Check both terminals are running (uvicorn + ngrok)
- Verify webhook URL is correct in LINE console
- Click "Verify" in webhook settings

### "Invalid signature" error?
- Restart uvicorn: `Ctrl+C` then run command again
- Check `.env` file has correct channel secret

### ngrok session expired?
- Free ngrok URLs change every 8 hours
- Just restart ngrok and update webhook URL

---

## 📂 Project Structure

```
e:\Projects\LineBot\
├── app/
│   ├── main.py              # FastAPI server ✅
│   ├── config.py            # Settings ✅
│   ├── database.py          # SQLite DB ✅
│   ├── line_handlers.py     # Bot logic ✅
│   └── ocr_service.py       # FREE (no APIs) ✅
├── .env                     # Your credentials ✅
├── expenses.db              # (auto-created)
├── requirements.txt         # Dependencies ✅
└── START_HERE.md           # This file
```

---

## 🎯 Features:

✅ Log cash expenses with categories  
✅ Send slip photos (manual amount entry)  
✅ Monthly budget tracking & alerts  
✅ Quick replies for categories  
✅ Create custom categories  
✅ Export transaction history  
✅ Monthly summaries  
✅ Recent transactions  
✅ **100% FREE - No API costs!**

---

## 🚀 You're All Set!

Your bot is **LIVE** once you complete the 3 steps above!

No more setup needed. Just use it! 🎉

---

## 📱 Your Bot Info:

- **Channel ID:** 2010529677
- **Channel Secret:** d964ef69ff35da377cb1e86914009e0c
- **Webhook:** `https://YOUR_NGROK_URL/webhook` (update after Step 2)

---

**Need help?** Check the terminal logs for any errors.
