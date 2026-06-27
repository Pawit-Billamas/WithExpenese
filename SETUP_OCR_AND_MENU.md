# 🎨 Setup OCR & Rich Menu

## ✅ What's New:

1. **📸 OCR for Slip Images** - Automatically reads amounts from payment slips
2. **🎨 Rich Menu** - Bottom buttons for easy access to commands

---

## 🔧 Step 1: Install Tesseract OCR (FREE)

### For Windows:

1. **Download Tesseract installer:**
   - https://github.com/UB-Mannheim/tesseract/wiki
   - Download: `tesseract-ocr-w64-setup-5.3.3.20231005.exe`

2. **Install with Thai language:**
   - Run the installer
   - ✅ Check "Additional language data (download)"  
   - ✅ Select "Thai" language pack
   - Default install path: `C:\Program Files\Tesseract-OCR`

3. **Add to PATH:**
   ```powershell
   # Add to environment variables
   setx PATH "%PATH%;C:\Program Files\Tesseract-OCR"
   ```

4. **Verify installation:**
   ```powershell
   tesseract --version
   ```
   Should show: `tesseract 5.3.3`

---

## 📦 Step 2: Install Python Dependencies

```powershell
cd e:\Projects\LineBot
pip install -r requirements.txt
```

This installs:
- `pytesseract` - Python wrapper for Tesseract
- `Pillow` - Image processing
- `opencv-python` - Advanced image preprocessing

---

## 🎨 Step 3: Setup Rich Menu

### Option A: Automatic Setup (Recommended)

1. **Make sure your bot server is running**
2. **Run the setup script:**
   ```powershell
   python setup_rich_menu.py
   ```

3. **You should see:**
   ```
   ✨ Creating new rich menu...
   ✅ Rich Menu created: rmXXXXX
   ✅ Rich Menu set as default
   🎉 Rich Menu Created Successfully!
   ```

4. **Open LINE app** - You should see bottom buttons! 🎉

---

### Option B: Manual Setup (via LINE Manager)

If automatic setup doesn't work:

1. Go to https://manager.line.biz/
2. Select your account
3. **Chat** → **Rich menus** → **Create**
4. **Settings:**
   - Display: Always
   - Size: Large (2500 x 1686)
   - Chat bar text: "เมนู"

5. **Create 5 tap areas:**

| Area | Position | Size | Action Text |
|------|----------|------|-------------|
| Recent | Top-left | 833×843 | `recent` |
| Summary | Top-center | 834×843 | `summary` |
| Categories | Top-right | 833×843 | `categories` |
| Log Cash | Bottom-left | 1250×843 | `log cash` |
| Export | Bottom-right | 1250×843 | `export` |

6. **Upload background image** (or use solid color)
7. **Save & Set as default**

---

## 🧪 Step 4: Test OCR

1. **Take a photo of a payment slip** (like the MyMo slip)
2. **Send it to your LINE bot**
3. **Bot should:**
   - Reply: "📸 Processing slip... ⏳"
   - Then: "✅ Found amount: 140 THB\n\nSelect category:"
   - Show category buttons

4. **Click a category** → ✅ Saved!

---

## 📱 How Rich Menu Works:

### Bottom Buttons:

```
┌──────────┬──────────┬──────────┐
│  📋      │  📊      │  📂      │
│ Recent   │ Summary  │Categories│
├──────────────┬───────────────────┤
│   💰         │      📤          │
│  Log Cash    │     Export       │
└──────────────┴──────────────────┘
```

**Tap any button** → Sends command automatically!

---

## 🎯 Complete Workflow:

### 1. Send Slip Photo:
📸 Take photo → Send to bot → Bot reads amount → Pick category → Done!

### 2. Quick Cash Entry:
Tap "💰 Log Cash" → Type `cash 100 coffee` → Pick category → Done!

### 3. View Summary:
Tap "📊 Summary" → See monthly breakdown instantly!

### 4. Export Data:
Tap "📤 Export" → Get all transactions as text!

---

## 🐛 Troubleshooting:

### OCR not working?

**Check Tesseract installation:**
```powershell
tesseract --version
where tesseract
```

**If not found:**
- Reinstall Tesseract
- Add to PATH
- Restart PowerShell

**Test OCR manually:**
```powershell
tesseract test_slip.png output -l tha+eng
```

---

### Rich Menu not showing?

**Check bot setup:**
```powershell
python setup_rich_menu.py
```

**Or manually in LINE Manager:**
- https://manager.line.biz/
- Your account → Chat → Rich menus
- Make sure one menu is "Active"

**Clear LINE cache:**
- LINE Settings → Chats → Clear cache
- Restart LINE app

---

### OCR reads wrong amounts?

**Improve image quality:**
- Take clear, well-lit photos
- Avoid shadows and glare
- Crop to just the slip area
- Higher resolution = better results

**Manual correction:**
```
edit 140
```

---

## ✅ Success Checklist:

- [ ] Tesseract installed & in PATH
- [ ] Python packages installed
- [ ] Rich menu created (automatic or manual)
- [ ] Bot server running
- [ ] ngrok running
- [ ] LINE webhook configured
- [ ] Test: Send slip photo → Amount detected ✅
- [ ] Test: Tap bottom buttons → Commands work ✅

---

## 🎉 You're Done!

Your bot now has:
- ✅ **OCR** - Reads amounts from slip photos automatically
- ✅ **Rich Menu** - Easy-access buttons at the bottom
- ✅ **Category Quick Replies** - Fast expense logging
- ✅ **100% FREE** - No API costs!

**Enjoy your smart expense tracker! 💰📊**
