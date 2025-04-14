import streamlit as st
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
import re
import pandas as pd
import io
import datetime
import time
from openai import OpenAI
import openai

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

# ✅ Set OpenAI API key from secrets
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# App title
st.title("Teacher Dashboard – Quiz Grader & AI Assistant")

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

    # Student name input
    student_name = st.text_input("Student Name")

    # Number of questions
    question_count = st.number_input("How many questions are on the quiz?", min_value=1, max_value=100, value=10)

    # Answer key input
    answer_key = st.text_input(f"Enter the {question_count}-letter answer key (e.g., ABCDABCDAB...)")

    if st.button("Grade Quiz") and answer_key and len(answer_key) == question_count:
        answers = re.findall(r'\b[A-Da-d]\b', text)
        trimmed_answers = answers[:question_count]
        score = sum([1 for i, ans in enumerate(trimmed_answers) if ans.upper() == answer_key[i].upper()])
        st.success(f"{student_name or 'Student'} scored {score}/{question_count}")

        df = pd.DataFrame({
            "Question #": list(range(1, question_count+1)),
            "Extracted Answer": trimmed_answers,
            "Correct Answer": list(answer_key.upper()),
            "Correct": [ans.upper() == answer_key[i].upper() for i, ans in enumerate(trimmed_answers)]
        })
        st.dataframe(df)

        # Export results with timestamp and student name
        now = datetime.datetime.now().strftime("%Y-%m-%d")
        name_tag = student_name.replace(" ", "") if student_name else "Student"
        filename = f"QuizResults_{name_tag}_{now}.csv"
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Results as CSV", data=csv, file_name=filename, mime="text/csv")

# Optional: Clear session
if st.button("Clear Session"):
    st.experimental_rerun()

# AI Chat Assistant Section
st.markdown("---")
st.header("💬 AI Teaching Assistant")
st.markdown("Ask for quiz ideas, reword questions, or get teaching help!")

# Maintain chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_input = st.text_input("Type your question or request here")

def get_ai_response(user_input):
    max_retries = 5  # Max retries for rate limit errors
    retry_delay = 2  # Initial retry delay (in seconds)

    for attempt in range(max_retries):
        try:
            # OpenAI API request to chat with AI
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_input}]
            )
            return response.choices[0].message.content
        except openai.error.RateLimitError:
            if attempt < max_retries - 1:
                # Wait before retrying
                st.warning(f"Rate limit hit. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                st.error("Rate limit exceeded after multiple attempts.")
                return None

if st.button("Ask AI") and user_input:
    system_prompt = (
        "You are a helpful teaching assistant for a high school science teacher. "
        "Answer using clear, supportive language. Be concise but creative. "
        "Provide ideas for multiple choice questions, analogies, or summaries for Chemistry, Biology, or Earth Science."
    )

    st.session_state.chat_history.append(("🧑 Teacher", user_input))

    # Call the function to get AI response with rate limiting and retry logic
    reply = get_ai_response(user_input)

    if reply:
        st.session_state.chat_history.append(("🤖 AI", reply))

# Display chat history
for speaker, message in st.session_state.chat_history:
    st.markdown(f"**{speaker}:** {message}")

      
