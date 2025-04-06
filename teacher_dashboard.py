import streamlit as st
import pandas as pd
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import re
import os

# Cloud handles Tesseract and Poppler via requirements.txt

st.title("Teacher AI Agent - Biology, Chemistry, Earth Science")

st.header("Grade Quizzes")
quiz_file = st.file_uploader("Upload Scanned Quiz PDF", type="pdf")
key_input = st.text_input("Enter Quiz Key (e.g., A,C,B,B,D,C,A,B,D,C)")

if quiz_file and key_input:
    key = key_input.split(",")
    images = convert_from_path(quiz_file)
    student_data = []
    for i, img in enumerate(images):
        text = pytesseract.image_to_string(img)
        name = re.search(r"Name:\s*(.+)", text).group(1) if re.search(r"Name:\s*(.+)", text) else f"Student_{i+1}"
        answers = [re.search(r"\d+\.\s*([A-D])", line).group(1) for line in text.split("\n") if re.search(r"\d+\.\s*([A-D])", line)]
        if len(answers) == 10:
            student_data.append({"Student": name, "Answers": answers})

    if student_data:
        df = pd.DataFrame(student_data)
        df[["Q1","Q2","Q3","Q4","Q5","Q6","Q7","Q8","Q9","Q10"]] = pd.DataFrame(df["Answers"].tolist())
        df = df.drop("Answers", axis=1)
        key_series = pd.Series(key, index=["Q1","Q2","Q3","Q4","Q5","Q6","Q7","Q8","Q9","Q10"])
        df["Score"] = (df.iloc[:, 1:] == key_series).sum(axis=1)
        st.write("Grades:", df[["Student", "Score"]])
        st.download_button("Download Grades", df.to_csv(index=False), "graded_quiz.csv")
    else:
        st.write("Error: Couldn’t process some quizzes. Check scan quality.")

st.header("Generate Questions from Notes")
notes_file = st.file_uploader("Upload Board Notes Photo", type=["jpg", "png"])
if notes_file:
    img = Image.open(notes_file)
    text = pytesseract.image_to_string(img)
    st.write("Extracted Notes:", text)
    st.write("Question generation coming soon with Hugging Face!")
