import streamlit as st
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import re
import pandas as pd
import io

# 🔐 Password Gate
def check_password():
    def password_entered():
        if st.session_state["password"] == "RLWteacher2024":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Enter Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Incorrect password")
        return False
    else:
        return True

if not check_password():
    st.stop()

# App title
st.title("Teacher Dashboard – Quiz Grader")

# Upload scanned quiz
uploaded_file = st.file_uploader("Upload a scanned student quiz (PDF only)", type="pdf")

if uploaded_file is not None:
    # Extract text from PDF
    with fitz.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        text = ""
        for page in doc:
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text += pytesseract.image_to_string(img)

    st.subheader("Extracted Text Preview:")
    st.text_area("Scanned Text", text, height=200)

    # Answer key input
    answer_key = st.text_input("Enter the 10-letter answer key (e.g., ABCDABCDAB)")

    if st.button("Grade Quiz") and answer_key:
        answers = re.findall(r'\b[A-Da-d]\b', text)
        score = sum([1 for i, ans in enumerate(answers[:10]) if ans.upper() == answer_key[i].upper()])
        st.success(f"Score: {score}/10")

        df = pd.DataFrame({"Extracted Answers": answers[:10], "Correct": [ans.upper() == answer_key[i].upper() for i, ans in enumerate(answers[:10])]})
        st.dataframe(df)

        # Export results
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Results as CSV", data=csv, file_name="quiz_results.csv", mime="text/csv")

# Optional: Clear session
if st.button("Clear Session"):
    st.experimental_rerun()
