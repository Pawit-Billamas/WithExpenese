# 🚂 Deploy to Railway (BEST for SQLite!)

## ✅ Why Railway Better Than Render?

| Feature | Railway | Render |
|---------|---------|--------|
| **SQLite Persistence** | ✅ YES | ❌ NO (deleted on restart!) |
| **Data Safety** | ✅ Safe forever | ❌ Lost every restart |
| **Free Tier** | $5/month credit | Truly free |
| **Credit Card** | Required (but won't charge) | Not required |
| **Best For** | LINE bots with DB | Stateless apps |

**For your bot: Railway wins!** 🏆 Your data will be SAFE!

---

## 🚂 Quick Deploy (5 Minutes):

### Step 1: Push to GitHub
```powershell
cd e:\Projects\LineBot
git init
git add .
git commit -m "LINE Bot"
# Create repo on github.com/new then:
git remote add origin YOUR_GITHUB_URL
git push -u origin main
```

### Step 2: Deploy to Railway
1. **Go to:** https://railway.app/
2. **Sign up** with GitHub
3. **Add credit card** (won't charge under $5)
4. **New Project** → Deploy from GitHub
5. Select `linebot-expense-tracker`
6. Add **Variables:**
   - `LINE_CHANNEL_SECRET` = `d964ef69ff35da377cb1e86914009e0c`
   - `LINE_CHANNEL_ACCESS_TOKEN` = `FukAtAe4lVENttlUwGp3nL2rTO2HgMdN0zf8+6HDMlEvQddds85hKO1zdfvylYC1ZSfFHdBv7PfKYew/nZPjWglXcW9te6O0u5C72OVSXLUysOjUxfIl5CXDtzGZQSqbkAZeM+9VaEuLl69oB1UzvAdB04t89/1O/w1cDnyilFU=`
7. **Settings** → Networking → **Generate Domain**

### Step 3: Update LINE Webhook
1. Copy Railway URL: `https://yourbot.up.railway.app`
2. LINE Console → Webhook: `https://yourbot.up.railway.app/webhook`
3. Verify → ✅

---

## 💰 Cost: FREE!

- **Free credit:** $5/month
- **Your bot uses:** ~$1-2/month
- **You pay:** $0 (under free credit)

---

## ✅ Database Persists Forever!

Unlike Render:
- ✅ Data **NEVER deleted**
- ✅ Survives restarts
- ✅ Survives deploys
- ✅ **Your expenses are SAFE!**

---

## 🧪 Test:
1. Log expenses in LINE
2. Railway Dashboard → Restart
3. Check data → **Still there!** ✅

**Railway = No data loss!** 🎉

Read full guide above for details.
