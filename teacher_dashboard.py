import streamlit as st
import pandas as pd
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import re
import os
from google.cloud import vision
import io
from google.oauth2 import service_account
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logging.info("Starting teacher_dashboard.py...")

st.title("Teacher AI Agent - Biology, Chemistry, Earth Science")

# Class Selection Dropdown
class_option = st.selectbox("Select Class", ["Biology", "Chemistry", "Earth Science"])
st.write(f"Selected class: {class_option}")

# Quiz Grading Section
st.header("Grade Quizzes")
quiz_file = st.file_uploader("Upload Scanned Quiz PDF", type="pdf")
key_input = st.text_input("Enter Quiz Key (e.g., A,C,B,B,D,C,A,B,D,C)")

if quiz_file and key_input:
    try:
        logging.info("Processing quiz PDF...")
        key = key_input.split(",")
        images = convert_from_bytes(quiz_file.read())
        student_data = []
        for i, img in enumerate(images):
            text = pytesseract.image_to_string(img)
            name_match = re.search(r"Name:\s*(.+)", text)
            name = name_match.group(1) if name_match else f"Student_{i+1}"
            answers = [re.search(r"\d+\.\s*([A-D])", line).group(1) for line in text.split("\n") if re.search(r"\d+\.\s*([A-D])", line)]
            if len(answers) == 10:
                student_data.append({"Student": name, "Answers": answers})
            else:
                logging.warning(f"Student {name} has {len(answers)} answers, expected 10.")
        if student_data:
            df = pd.DataFrame(student_data)
            df[["Q1","Q2","Q3","Q4","Q5","Q6","Q7","Q8","Q9","Q10"]] = pd.DataFrame(df["Answers"].tolist())
            df = df.drop("Answers", axis=1)
            key_series = pd.Series(key, index=["Q1","Q2","Q3","Q4","Q5","Q6","Q7","Q8","Q9","Q10"])
            df["Score"] = (df.iloc[:, 1:] == key_series).sum(axis=1)
            st.write("Grades:", df[["Student", "Score"]])
            st.download_button("Download Grades", df.to_csv(index=False), "graded_quiz.csv")
            logging.info("Quiz grading completed successfully.")
        else:
            st.write("Error: Couldn’t process some quizzes. Check scan quality.")
            logging.error("No valid student data extracted from quiz PDF.")
    except Exception as e:
        st.write("Error processing quiz:", str(e))
        logging.error(f"Quiz processing failed: {str(e)}")

# Notes Extraction Section
st.header("Generate Questions from Notes")
notes_file = st.file_uploader("Upload Board Notes (JPG, PNG, or PDF)", type=["jpg", "png", "pdf"])
if notes_file:
    try:
        logging.info("Extracting text from notes...")
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"]
        )
        client = vision.ImageAnnotatorClient(credentials=credentials)
        if notes_file.type == "application/pdf":
            images = convert_from_bytes(notes_file.read())
            content = images[0].tobytes()
        else:
            content = notes_file.read()
        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        text = response.text_annotations[0].description if response.text_annotations else "No text detected"
        st.write("Extracted Notes:", text)
        st.write("Question generation coming soon with Hugging Face!")
        logging.info("Notes extraction completed successfully.")
    except Exception as e:
        st.write("Error extracting notes:", str(e))
        logging.error(f"Notes extraction failed: {str(e)}")

# Question Bank Button
st.header("Question Bank")
if st.button("View Question Bank"):
    st.write(f"Showing question bank for {class_option} (coming soon!)")
