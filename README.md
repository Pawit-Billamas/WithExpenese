# Personal Expense Tracker LINE Bot

Send payment slip photos to a LINE bot → OCR reads the amount → pick a category → it's logged. Built with **FastAPI**, **PostgreSQL/SQLite**, and **Tesseract OCR** (free, runs locally — no API key or tokens).

---

## Features

| Feature | Description |
|---------|-------------|
| 📸 **Slip OCR** | Snap a bank/PromptPay slip → auto-detect amount & description |
| 💰 **Cash Logging** | Type `cash 120 lunch` to log cash expenses |
| 📂 **Categories** | Default: Food, Transport, Bills, Shopping, Entertainment, Health. Create your own! |
| 📊 **Monthly Summary** | Type `summary` — see totals by category + budget tracking |
| 📋 **Recent Expenses** | Type `recent` — last 5 transactions |
| 📤 **CSV Export** | Type `export` — get all data as CSV |
| ✏️ **Edit Amount** | If OCR reads wrong, type `edit 150` to correct before categorizing |
| ⚠️ **Budget Alerts** | Warnings at 50%, 80%, and 100% of monthly budget |
| 🧭 **Rich Menu** | Bottom tab with Summary / Recent / Log Cash / Categories |

---

## Prerequisites

1. **Python 3.10+** installed
2. **LINE Developer account** — [developers.line.biz](https://developers.line.biz)
3. **Tesseract OCR** installed with the Thai language pack (`tha`) — free, no API key
   - Windows: install [Tesseract at UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) and select the **Thai** language during setup
   - Debian/Ubuntu/Render: `apt-get install -y tesseract-ocr tesseract-ocr-tha`
4. **Public HTTPS URL** — for LINE webhook (use [ngrok](https://ngrok.com) or deploy to Render/Railway)

---

## Setup

### 1. Clone & install

```bash
cd e:\Projects\LineBot
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and fill in your credentials:

```env
LINE_CHANNEL_SECRET=your_channel_secret_here
LINE_CHANNEL_ACCESS_TOKEN=your_channel_access_token_here
MONTHLY_BUDGET=20000
```

### 3. Run locally

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Expose with ngrok (for webhook)

```bash
ngrok http 8000
```

Copy the ngrok HTTPS URL (e.g., `https://abc123.ngrok.io`).

### 5. Configure LINE Bot

Go to **[LINE Developers Console](https://developers.line.biz/console/)**

1. Select your Provider → **Channel (Messaging API)**
2. Set **Webhook URL** to: `https://your-ngrok-url.ngrok.io/webhook`
3. Enable **Use webhook**
4. Issue **Channel Access Token** (long string) and copy it to `.env`
5. Copy the **Channel Secret** from the Basic settings tab to `.env`
6. Disable **Auto-reply messages** (or keep enabled, but bot handles replies)

---

## Commands

| Command | Action |
|---------|--------|
| *(send photo)* | OCR the slip, prompt for category |
| `cash 120 lunch` | Log a cash expense |
| `edit 150` | Fix the OCR amount before categorizing |
| `summary` | Monthly spend by category + budget status |
| `recent` | Last 5 transactions |
| `export` | Download all data as CSV |
| `categories` | List all categories |
| *(tap Quick Reply)* | Select existing category |
| *(tap "➕ New Category")* | Create a new category |
| *(type new name)* | Finalize with the new category |

---

## Rich Menu Setup (LINE Official Account Manager)

In **[manager.line.biz](https://manager.line.biz)** → Chat → Rich Menu:

1. Create a new Rich Menu with 4 buttons
2. Button 1 (**Summary**) — Action: Text → Value: `Summary`
3. Button 2 (**Recent**) — Action: Text → Value: `Recent`
4. Button 3 (**Log Cash**) — Action: Text → Value: `Log Cash`
5. Button 4 (**Categories**) — Action: Text → Value: `Categories`

---

## Deployment Options

> **Important:** OCR needs the **Tesseract binary** (with the Thai pack), which
> `pip` cannot install. A plain Python web service on Render therefore reports
> `/ocr-status` → `{"available": false}`. Deploy with the included **Dockerfile**
> so the Thai-enabled Tesseract is installed in the image. The build/run happens
> entirely on the host's cloud — your PC is only needed for the one-time push.

### Render (Docker — recommended)

1. Push to GitHub (the repo already contains a `Dockerfile` and `render.yaml`).
2. On render.com create a **Web Service** from this repo.
3. Set **Runtime / Environment = Docker** (Render auto-detects the `Dockerfile`).
   If the service was previously "Python", change it to Docker (or recreate it),
   then **Clear build cache & deploy**.
4. Add env vars: `LINE_CHANNEL_SECRET`, `LINE_CHANNEL_ACCESS_TOKEN`,
   `MONTHLY_BUDGET`, `DATABASE_URL`.
5. After deploy, open `https://<your-app>.onrender.com/ocr-status` — it should show
   `"available": true` and `"lang": "tha+eng"`.

> **Why slip replies feel slow on the free plan:** Render's free tier spins
> the service down after ~15 minutes of no traffic. The *next* message after
> a spin-down pays a 30–60s cold-start before OCR even starts — OCR itself
> runs in well under a second once the service is warm. To avoid this without
> paying for Render's always-on plan, set up a free external cron
> (e.g. [cron-job.org](https://cron-job.org) or
> [UptimeRobot](https://uptimerobot.com)) to `GET https://<your-app>.onrender.com/health`
> every 10 minutes, which keeps the service warm 24/7.

### Railway / any Docker host

Build the included `Dockerfile` — no extra start command needed (it runs uvicorn
on `$PORT`). Add the same env vars.

### Run the Docker image locally (optional)

```bash
docker build -t withexpense .
docker run -p 8000:8000 --env-file .env withexpense
```

---

## Project Structure

```
e:\Projects\LineBot\
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI server entrypoint
│   ├── config.py            # Environment variable loader
│   ├── database.py          # SQLite models & helpers
│   ├── line_handlers.py     # LINE event handlers & bot logic
│   └── ocr_service.py       # Tesseract OCR + Thai amount extraction (local, free)
├── .env                     # Your secrets (git-ignored)
├── .env.example             # Template for env vars
├── requirements.txt
└── README.md
```

---

## Tech Stack

| Component | Choice |
|-----------|--------|
| Framework | FastAPI (async) |
| Database | PostgreSQL (pg8000) / SQLite |
| LINE SDK | line-bot-sdk-python v3 |
| OCR | Tesseract (`tha+eng`) — local, free, no tokens |
| Deployment | Render / Railway / any VPS |

---

## License

MIT
