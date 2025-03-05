import streamlit as st
import cv2
import pytesseract
import numpy as np
import pandas as pd
from PIL import Image
import re
import shutil

# ✅ Ensure Tesseract is installed
tesseract_cmd = shutil.which("tesseract")
if tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
else:
    st.error("❌ Tesseract OCR is not installed. Ensure `packages.txt` includes `tesseract-ocr`.")
    st.stop()  # Stop execution if Tesseract is missing

# ✅ Initialize or load stored receipt data
if "receipt_data" not in st.session_state:
    st.session_state.receipt_data = pd.DataFrame(columns=["Vendor", "Date", "Amount (£)", "Category", "Raw OCR Text"])

# ✅ Function to extract vendor, date, and amount from OCR text
def extract_receipt_details(ocr_text):
    vendor, date, amount = None, None, None

    # Extract date (formats: DD/MM/YYYY, YYYY-MM-DD, etc.)
    date_match = re.search(r'(\d{2}[/-]\d{2}[/-]\d{4}|\d{4}[/-]\d{2}[/-]\d{2})', ocr_text)
    if date_match:
        date = date_match.group(0)

    # Extract amount (formats: £xx.xx, x.xx)
    amount_match = re.search(r'£?(\d+\.\d{2})', ocr_text)
    if amount_match:
        amount = f"£{amount_match.group(1)}"

    # Extract vendor name (assumes first uppercase word/phrase is vendor)
    vendor_match = re.search(r'^[A-Z][A-Z\s]+', ocr_text)
    if vendor_match:
        vendor = vendor_match.group(0).strip()

    return vendor, date, amount

# ✅ Function to process receipt image and extract text
def process_receipt(image):
    # Convert image to grayscale for better OCR accuracy
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    
    # Apply OCR
    ocr_text = pytesseract.image_to_string(gray)
    
    # Extract structured details
    vendor, date, amount = extract_receipt_details(ocr_text)
    
    return vendor, date, amount, ocr_text

# ✅ Streamlit UI
st.title("🧾 Receipt Scanner & OCR")

# 📸 Capture image from camera
image_file = st.camera_input("Take a picture of your receipt")

# 📂 Or upload manually
uploaded_file = st.file_uploader("Or upload an image", type=["png", "jpg", "jpeg"])

if image_file or uploaded_file:
    # Load the image
    image = Image.open(image_file if image_file else uploaded_file)
    
    st.image(image, caption="📸 Uploaded Receipt", use_container_width=True)

    # Process OCR
    vendor, date, amount, ocr_text = process_receipt(image)
    
    # Display extracted data
    st.subheader("📌 Extracted Receipt Details")
    st.write(f"**Vendor:** {vendor if vendor else 'Not detected'}")
    st.write(f"**Date:** {date if date else 'Not detected'}")
    st.write(f"**Amount:** {amount if amount else 'Not detected'}")

    # Select category
    category = st.selectbox("Select Receipt Category", ["Food", "Hotel", "Transport", "Other"])

    # Save receipt data
    if st.button("✅ Save Receipt"):
        new_data = pd.DataFrame([[vendor, date, amount, category, ocr_text]], columns=st.session_state.receipt_data.columns)
        st.session_state.receipt_data = pd.concat([st.session_state.receipt_data, new_data], ignore_index=True)
        st.success("Receipt added successfully!")

# 📊 Show stored receipts
st.subheader("📊 Stored Receipts")
st.dataframe(st.session_state.receipt_data)