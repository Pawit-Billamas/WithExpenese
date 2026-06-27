# 🔧 Fix: ModuleNotFoundError 'uvicorn'

## ⚠️ Problem
Your error log shows:
```
ModuleNotFoundError: No module named 'uvicorn'
  File "/home/PawitBillamas/WithExpenese/app/main.py", line 1, in <module>
    import uvicorn
```

**Cause:** `app/main.py` still had `import uvicorn` which we removed from requirements (too heavy for PythonAnywhere free tier).

**Fix:** Already applied! Just pull the updated code from GitHub.

---

## 🚀 Fix Steps (2 minutes):

### Step 1: Pull Updated Code

Open PythonAnywhere **Bash console** and run:

```bash
cd ~/WithExpenese
git pull
```

You should see:
```
remote: Enumerating objects: X, done.
remote: Counting objects: 100% (X/X), done.
Updating XXXXX..XXXXX
Fast-forward
 app/main.py | X +++++-----
 1 file changed, X insertions(+), X deletions(-)
```

### Step 2: Reload Web App

1. Go to **"Web"** tab
2. Click the green **"Reload PawitBillamas.pythonanywhere.com"** button
3. Wait 5 seconds

### Step 3: Test

Open browser and visit:
```
https://PawitBillamas.pythonanywhere.com
```

Should show:
```json
{"status":"ok","message":"Expense Tracker Bot is running."}
```

✅ **Fixed!**

---

## 🔍 What Changed:

**File:** `app/main.py`

**Before (broken):**
```python
import uvicorn  # ❌ Not installed on PythonAnywhere
...
if __name__ == "__main__":
    uvicorn.run(...)  # ❌ Not needed for WSGI
```

**After (fixed):**
```python
# No uvicorn import needed!
# PythonAnywhere uses WSGI, not uvicorn
```

---

## 📋 Verify No Other Issues:

After pulling, run this in Bash console to test:

```bash
cd ~/WithExpenese
python -c "from app.main import app; print('✅ App loads OK!')"
```

Should output:
```
✅ App loads OK!
```

---

## 🐛 If You Still Get Errors:

### Error: "git pull" fails
**Fix:** Make sure you saved the updated `main.py` to GitHub first.

If you edited files locally on your computer:
```powershell
cd e:\Projects\LineBot
git add app/main.py
git commit -m "Remove uvicorn import"
git push
```

Then on PythonAnywhere:
```bash
cd ~/WithExpenese
git pull
```

### Error: "No module named 'httpx'"
**Fix:** This might be from `app/rich_menu.py`. But this file is only used by `setup_rich_menu.py` which we don't run on PythonAnywhere.

If it causes issues, run:
```bash
pip install --user httpx
```

(It's only ~5 MB, won't break your quota)

### Error: Different module not found
**Fix:** Install it:
```bash
pip install --user MODULE_NAME
```

---

## ✅ After Fix - Test Commands:

Visit in browser:
- `https://PawitBillamas.pythonanywhere.com` → Should show JSON ✅

In LINE app:
- Send `recent` → Bot responds ✅
- Send `cash 100 coffee` → Categories appear ✅

---

## 💡 Pro Tip:

To avoid future issues like this, always test your code locally before pushing:

```powershell
cd e:\Projects\LineBot
python -c "from app.main import app; print('OK')"
```

If it loads locally, it should work on PythonAnywhere! 🚀