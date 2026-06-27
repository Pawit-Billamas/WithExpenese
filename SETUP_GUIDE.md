# 🚀 Complete Setup Guide for LINE Expense Tracker Bot

## ✅ Current Status

**Your LINE Bot Credentials:**
- **Channel ID:** `2010529677`
- **Channel Secret:** `d964ef69ff35da377cb1e86914009e0c`
- **Channel Access Token:** ⚠️ **NEEDED** - You need to issue this from LINE Developers Console

---

## 📋 Step-by-Step Setup

### Step 1: Get Your Channel Access Token

1. Go to [LINE Developers Console](https://developers.line.biz/console/)
2. Select your provider → Click on your channel (ID: 2010529677)
3. Go to **"Messaging API"** tab
4. Scroll down to **"Channel access token"**
5. Click **"Issue"** button (if not issued yet)
6. Copy the **long token** (it looks like: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`)
7. Update `e:\Projects\LineBot\.env` file:

```env
LINE_CHANNEL_SECRET=d964ef69ff35da377cb1e86914009e0c
LINE_CHANNEL_ACCESS_TOKEN=paste_your_long_token_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
MONTHLY_BUDGET=20000
```

### Step 2: Get OpenRouter API Key

1. Go to [OpenRouter](https://openrouter.ai/keys)
2. Sign up / Log in
3. Create a new API key
4. Copy the key and paste it into `.env` file

### Step 3: Run the Bot Locally

Open PowerShell in `e:\Projects\LineBot\` and run:

```powershell
# Activate virtual environment (optional but recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies (already done!)
pip install -r requirements.txt

# Run the server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
✅ Database initialized.
```

### Step 4: Expose with ngrok

1. Download [ngrok](https://ngrok.com/download)
2. Run in a new terminal:
```powershell
ngrok http 8000
```

3. Copy the HTTPS URL (e.g., `https://abc123.ngrok-free.app`)

### Step 5: Configure LINE Webhook

1. Go back to [LINE Developers Console](https://developers.line.biz/console/)
2. Select your channel → **Messaging API** tab
3. Find **"Webhook URL"**
4. Enter: `https://your-ngrok-url.ngrok-free.app/webhook`
5. Click **"Update"**
6. Click **"Verify"** - you should see ✅ Success
7. Enable **"Use webhook"** toggle

### Step 6: Configure Auto-Reply Settings

1. Go to [LINE Official Account Manager](https://manager.line.biz/)
2. Select your account
3. Go to **Response settings**
4. **Disable** "Greeting message" (or customize it)
5. **Disable** "Auto-response" (so bot handles all messages)
6. **Enable** "Webhooks"

---

## 🎨 Optional: Setup Rich Menu

In [manager.line.biz](https://manager.line.biz) → Chat → Rich Menu:

1. Create a new Rich Menu
2. Upload a background image (1200x810px or 2500x1686px)
3. Create 4 tap areas:

| Button | Action Type | Text to Send |
|--------|-------------|--------------|
| 📊 Summary | Message | `summary` |
| 📋 Recent | Message | `recent` |
| 💰 Log Cash | Message | `log cash` |
| 📂 Categories | Message | `categories` |

4. Set as default menu

---

## 🧪 Testing

1. Add your bot as a friend using QR code from LINE console
2. Send a message: `recent` → Should reply with "📭 No transactions yet."
3. Send: `cash 100 test` → Should show category quick replies
4. Click a category → Should save and confirm
5. Send a slip photo → Should OCR and ask for category

---

## 📤 Deployment (Optional)

### Deploy to Render.com

1. Push code to GitHub
2. Create account on [Render.com](https://render.com)
3. Create **New Web Service**
4. Connect your GitHub repo
5. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Add environment variables in Render dashboard
7. Deploy!
8. Update LINE webhook URL to Render URL

### Deploy to Railway.app

1. Push code to GitHub
2. Create account on [Railway.app](https://railway.app)
3. Create **New Project** → Deploy from GitHub
4. Add environment variables
5. Railway auto-detects Python and runs the app
6. Get the public URL
7. Update LINE webhook URL

---

## 🐛 Troubleshooting

### Bot doesn't respond
- Check ngrok is running
- Verify webhook URL is correct in LINE console
- Check `.env` file has correct tokens
- Look at terminal logs for errors

### OCR fails
- Verify OpenRouter API key is valid
- Check you have credits on OpenRouter
- Try a clearer slip image

### "Invalid signature" error
- Check `LINE_CHANNEL_SECRET` matches exactly
- Restart the server after changing `.env`

---

## 📂 Project Files

```
e:\Projects\LineBot\
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI server
│   ├── config.py            # Environment variables
│   ├── database.py          # SQLite operations
│   ├── line_handlers.py     # LINE webhook handlers
│   └── ocr_service.py       # OpenRouter vision API
├── .env                     # Your secrets (DO NOT COMMIT!)
├── .env.example             # Template
├── .gitignore
├── requirements.txt
├── README.md
└── SETUP_GUIDE.md          # This file
```

---

## 📞 Need Help?

1. Check LINE logs in console: https://developers.line.biz/console/
2. Check server logs in terminal
3. Test webhook: `curl -X POST http://localhost:8000/webhook`

---

## 🎉 You're All Set!

Once you complete Steps 1-6, your bot should be working! Send it a slip photo and watch the magic happen! 🪄
