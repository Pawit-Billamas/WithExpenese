# 🚀 Deploy to Render (FREE & Online!)

## ✅ Why Render?
- ✅ **FREE forever** (no credit card needed)
- ✅ **Always online** (no ngrok restarts)
- ✅ **HTTPS URL** (permanent)
- ✅ **Auto-deploy** from GitHub
- ✅ **Easy setup** (5 minutes)

---

## 📦 Step 1: Prepare Your Code

### 1.1 Initialize Git (if not done):
```powershell
cd e:\Projects\LineBot
git init
git add .
git commit -m "Initial commit - LINE Expense Tracker Bot"
```

### 1.2 Create GitHub Repository:
1. Go to https://github.com/new
2. Repository name: `linebot-expense-tracker`
3. **Public** or **Private** (both work)
4. **Don't** add README, .gitignore (we have them)
5. Click **Create repository**

### 1.3 Push to GitHub:
```powershell
git remote add origin https://github.com/YOUR_USERNAME/linebot-expense-tracker.git
git branch -M main
git push -u origin main
```

---

## 🌐 Step 2: Deploy to Render

### 2.1 Sign Up for Render:
1. Go to https://render.com/
2. Click **"Get Started for Free"**
3. Sign up with **GitHub** (easiest)
4. Authorize Render to access your repos

### 2.2 Create New Web Service:
1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub repository: `linebot-expense-tracker`
3. Click **"Connect"**

### 2.3 Configure Service:
```
Name: linebot-expense-tracker
Region: Singapore (or closest to Thailand)
Branch: main
Root Directory: (leave empty)
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Instance Type: Free
```

### 2.4 Add Environment Variables:
Click **"Advanced"** → **"Add Environment Variable"**

Add these 2 variables:

| Key | Value |
|-----|-------|
| `LINE_CHANNEL_SECRET` | `d964ef69ff35da377cb1e86914009e0c` |
| `LINE_CHANNEL_ACCESS_TOKEN` | `FukAtAe4lVENttlUwGp3nL2rTO2HgMdN0zf8+6HDMlEvQddds85hKO1zdfvylYC1ZSfFHdBv7PfKYew/nZPjWglXcW9te6O0u5C72OVSXLUysOjUxfIl5CXDtzGZQSqbkAZeM+9VaEuLl69oB1UzvAdB04t89/1O/w1cDnyilFU=` |

### 2.5 Deploy:
Click **"Create Web Service"**

Render will:
- Clone your repo ✅
- Install packages ✅
- Start your bot ✅

Wait 2-3 minutes... 

---

## 🎉 Step 3: Get Your URL

Once deployed, Render gives you a URL like:
```
https://linebot-expense-tracker.onrender.com
```

**This is your permanent bot URL!** 🎉

---

## 🔗 Step 4: Update LINE Webhook

1. Go to https://developers.line.biz/console/
2. Select channel **2010529677**
3. **Messaging API** tab
4. **Webhook URL:** 
   ```
   https://linebot-expense-tracker.onrender.com/webhook
   ```
5. Click **"Update"**
6. Click **"Verify"** → ✅ Should show Success
7. Enable **"Use webhook"** toggle

---

## 🧪 Step 5: Test Your Bot

1. Open LINE app
2. Send message: `recent`
3. Bot should reply! 🎉

**Your bot is now LIVE 24/7!** ✨

---

## 📊 Monitor Your Bot

### Render Dashboard:
- https://dashboard.render.com/
- View logs in real-time
- See requests and errors
- Check uptime

### View Logs:
Click your service → **"Logs"** tab
- See all bot activity
- Debug errors
- Monitor performance

---

## 🔄 Update Your Bot

### When you make changes:

```powershell
git add .
git commit -m "Updated feature X"
git push
```

**Render auto-deploys!** No manual steps needed! 🚀

---

## ⚠️ Important Notes:

### Free Plan Limitations:
- ✅ **Free forever**
- ⚠️ **Sleeps after 15 min inactivity** (wakes on first request ~30 sec)
- ✅ **750 hours/month** (enough for 24/7 if you don't have other services)
- ✅ **100 GB bandwidth/month**

### Keep Bot Awake (Optional):
Use a free uptime monitor:
- **UptimeRobot** (https://uptimerobot.com)
- Ping your bot every 10 minutes
- Keeps it awake 24/7

---

## 🐛 Troubleshooting:

### Deploy Failed?
- Check **Logs** in Render dashboard
- Make sure `requirements.txt` is correct
- Verify Python version compatibility

### Bot Not Responding?
- Check webhook URL is correct
- Verify environment variables are set
- Look at Render logs for errors

### Database Issues?
- SQLite file persists on Render
- For production, consider PostgreSQL (Render offers free tier)

---

## ✅ Checklist:

- [ ] Git initialized & committed
- [ ] Pushed to GitHub
- [ ] Render account created
- [ ] Web service deployed
- [ ] Environment variables added
- [ ] Deployment successful
- [ ] Webhook URL updated in LINE
- [ ] Webhook verified ✅
- [ ] Bot tested and working! 🎉

---

## 🎯 Your Bot is LIVE!

**Permanent URL:**
```
https://linebot-expense-tracker.onrender.com
```

**No more ngrok!**
**No more local server!**
**Always online!** 🚀✨

---

## 📚 Next Steps:

1. **Setup Rich Menu** - See `RICH_MENU_6_BUTTONS.md`
2. **Test OCR** - Send slip photos
3. **Share with friends!** - Your bot is public now!

**Enjoy your production-ready expense tracker!** 💰📊
