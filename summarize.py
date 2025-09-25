# summarizer.py
import os
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path
import pytesseract
from groq import Groq
import logging
from time import sleep

# ---------------------------
# Logging setup
# ---------------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# ---------------------------
# Initialize Groq client
# ---------------------------
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# ---------------------------
# Folders
# ---------------------------
input_folder = Path("input_pdfs")
output_folder = Path("output")
output_folder.mkdir(exist_ok=True)
final_folder = Path("final")
final_folder.mkdir(exist_ok=True)

# ---------------------------
# Keywords to identify Opinion/Editorial pages
# ---------------------------
keywords = ["opinion", "editorial"]

# ---------------------------
# Step 1: Extract Opinion/Editorial Pages
# ---------------------------
pdf_writer = PdfWriter()
extracted_texts = []

for pdf_path in input_folder.glob("*.pdf"):
    logging.info(f"Processing: {pdf_path.name}")
    reader = PdfReader(str(pdf_path))
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""

        # OCR fallback if no text is detected
        if not text.strip():
            images = convert_from_path(str(pdf_path), first_page=i+1, last_page=i+1)
            text = pytesseract.image_to_string(images[0])

        # Check for keywords
        if any(k.lower() in text.lower() for k in keywords):
            pdf_writer.add_page(page)
            extracted_texts.append(text)
            logging.info(f"   -> Added page {i+1} from {pdf_path.name}: \"{text[:100]}...\"")

# ---------------------------
# Save merged Opinion/Editorial PDF
# ---------------------------
final_pdf = final_folder / "opinion_editorials.pdf"
with open(final_pdf, "wb") as f:
    pdf_writer.write(f)
logging.info(f"📄 Merged PDF saved at: {final_pdf}")

# ---------------------------
# Step 2: Summarize in batches to avoid token limit
# ---------------------------
def summarize_text(text):
    """Call Groq LLM to summarize text."""
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": f"Summarize the main points:\n{text}"}],
        max_tokens=300
    )
    return response.choices[0].message.content

# Dynamically batch text by character count (~24k chars per request to stay under 6000 token limit)
MAX_CHARS_PER_BATCH = 24000
batches = []
current_batch = ""
for text in extracted_texts:
    if len(current_batch) + len(text) > MAX_CHARS_PER_BATCH:
        batches.append(current_batch)
        current_batch = text
    else:
        current_batch += "\n\n" + text
if current_batch.strip():
    batches.append(current_batch)

# Summarize each batch with retry for rate limits or payload errors
all_summaries = []
for i, batch_text in enumerate(batches):
    for attempt in range(5):
        try:
            summary = summarize_text(batch_text)
            all_summaries.append(summary)
            break
        except Exception as e:
            logging.error(f"Error summarizing batch {i}: {e}")
            sleep_time = 5 * (attempt + 1)
            logging.info(f"Retrying in {sleep_time} seconds...")
            sleep(sleep_time)

# ---------------------------
# Step 3: Save summaries to text and markdown files
# ---------------------------
summary_txt = final_folder / "summaries.txt"
summary_md = final_folder / "summaries.md"

with open(summary_txt, "w", encoding="utf-8") as f:
    f.write("\n\n".join(all_summaries))
logging.info(f"📝 Summaries saved at: {summary_txt}")

with open(summary_md, "w", encoding="utf-8") as f:
    for s in all_summaries:
        f.write(f"- {s}\n\n")
logging.info(f"📘 Markdown summaries saved at: {summary_md}")
