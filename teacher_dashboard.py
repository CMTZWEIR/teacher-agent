import streamlit as st
from google.cloud import vision
from transformers import pipeline
import pandas as pd
import os
from pdf2image import convert_from_bytes
from PIL import Image
import io

# Extract text from image (JPEG or PDF-converted)
def extract_text(file, file_type):
    client = vision.ImageAnnotatorClient()
    if file_type == "pdf":
        # Convert PDF to images
        images = convert_from_bytes(file.read())
        content = images[0].tobytes()  # First page only for now
    else:
        content = file.read()  # JPEG
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    return response.text_annotations[0].description if response.text_annotations else ""

# Streamlit app
st.title("Teacher Dashboard")
class_type = st.selectbox("Select Class", ["Biology", "Chemistry", "Earth Science"])
uploaded_file = st.file_uploader(f"Upload {class_type} Notes (JPEG or PDF)", type=["jpg", "jpeg", "pdf"])

if uploaded_file:
    # Determine file type
    file_type = uploaded_file.type.split('/')[-1]  # e.g., "jpeg" or "pdf"
    extracted_text = extract_text(uploaded_file, file_type)
    st.write(f"{class_type} Extracted Notes:", extracted_text)

    # Generate question with Hugging Face
    generator = pipeline("text2text-generation", model="t5-small")
    question = generator(f"generate question: {extracted_text.split('.')[0]}", max_length=50)
    q_text = question[0]['generated_text']
    answer = extracted_text.split('.')[0]
    st.write(f"Question: {q_text}")
    st.write(f"A. {answer}")

    # Save to Test Bank
    if st.button("Save to Test Bank"):
        data = {"Class": class_type, "Question": q_text, "Answer": f"A. {answer}"}
        df = pd.DataFrame([data])
        if os.path.exists("test_bank.csv"):
            df.to_csv("test_bank.csv", mode="a", header=False, index=False)
        else:
            df.to_csv("test_bank.csv", index=False)
        st.success("Saved to Test Bank!")

# View Test Bank
if st.checkbox("View Test Bank"):
    if os.path.exists("test_bank.csv"):
        df = pd.read_csv("test_bank.csv")
        st.dataframe(df[df["Class"] == class_type])
    else:
        st.write("No Test Bank yet!")
