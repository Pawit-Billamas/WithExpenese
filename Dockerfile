# Tesseract OCR (with Thai) for reading Thai bank slips — free, no tokens.
# Render builds and runs this image entirely in the cloud (your PC is only
# needed for the one-time `git push`).
FROM python:3.11-slim

# Install the Tesseract binary + Thai & English language data.
# This is the piece pip cannot provide, which is why a plain Python
# service on Render reported {"available": false}.
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-tha \
        tesseract-ocr-eng \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Fail the build loudly if Tesseract or the Thai pack didn't install, so we
# never deploy an image that silently can't read slips.
RUN tesseract --version \
    && tesseract --list-langs \
    && tesseract --list-langs 2>&1 | grep -qx tha

WORKDIR /app

# Install Python deps first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application
COPY . .

# Render injects $PORT; default to 8000 for local runs
ENV PORT=8000
EXPOSE 8000

# Use shell form so $PORT is expanded at runtime
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
