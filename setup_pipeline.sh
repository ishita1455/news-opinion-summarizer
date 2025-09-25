#!/bin/bash
# -------------------------------------------------------
# Newspaper Opinion/Editorial Pipeline Setup (Linux)
# -------------------------------------------------------
# This script installs Python dependencies, Tesseract OCR,
# Poppler utils, sets up folders, and configures GROQ_API_KEY
# -------------------------------------------------------

# -------------------------------
# 1. Update and install system packages
# -------------------------------
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv tesseract-ocr poppler-utils

# -------------------------------
# 2. Create Python virtual environment
# -------------------------------
python3 -m venv venv
source venv/bin/activate

# -------------------------------
# 3. Install Python dependencies
# -------------------------------
pip install --upgrade pip
pip install PyPDF2 pdf2image pytesseract groq

# -------------------------------
# 4. Create required folders
# -------------------------------
mkdir -p input_pdfs
mkdir -p output
mkdir -p final

# -------------------------------
# 5. Set Groq API key
# -------------------------------
# Replace with your actual key
read -p "Enter your GROQ_API_KEY: " GROQ_API_KEY
export GROQ_API_KEY=$GROQ_API_KEY
echo "GROQ_API_KEY exported successfully!"

# Optional: Add to ~/.bashrc so it persists
echo "export GROQ_API_KEY=$GROQ_API_KEY" >> ~/.bashrc

# -------------------------------
# 6. Run the summarizer pipeline
# -------------------------------
echo "Setup complete. You can now run:"
echo "source venv/bin/activate"
echo "python summarizer.py"

# Done
echo "✅ Setup finished!"
