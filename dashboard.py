import streamlit as st
import json
import os
from datetime import datetime, date
from google import genai

st.set_page_config(
    page_title="Jarvis Executive Study & Mock Scheduler", 
    page_icon="🤖", 
    layout="wide"
)

MEMORY_FILE = "study_memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {
        "scheduled_mocks": [],
        "mock1_results_logged": False,
        "logged_weaknesses": []
    }

def save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

memory = load_memory()

@st.cache_resource
def get_gemini_client():
    return genai.Client()

try:
    client = get_gemini_client()
except Exception as e:
    st.error(f"Failed to initialize Gemini Client: {e}")
    client = None

# Sidebar Knowledge Base Links
st.sidebar.title("🤖 Knowledge Base")
st.sidebar.markdown("🧪 [Chemistry Notebook](https://gemini.google.com/notebook/eceabc92-0f46-4bbc-8ca1-229186edd0a5)")
st.sidebar.markdown("🔬 [Physics Notebook](https://gemini.google.com/notebook/3eedb1fd-e99d-4078-9f96-c670a07853e1)")
st.sidebar.markdown("🔢 [Math Notebook](https://gemini.google.com/notebook/dc98c8ba-bb72-45c3-906a-e951ef9fb122)")

st.title("🌆 Jarvis Post-School Executive Planner (6:00 PM - 10:00 PM)")

tabs = st.tabs([
    "🌆 Tonight's Evening Plan", 
    "➕ Log Mock Exam Dates", 
    "📊 Log Mock 1 / Quiz Errors", 
    "📋 Memory & System Register"
])

# ---------------------------------------------------------
# TAB 1: TONIGHT'S STUDY PLAN
# ---------------------------------------------------------
with tabs[0]:
    st.header("🌆 Today's Evening Study Blueprint")
    st.info("⏰ Study Window: 6:00 PM – 10:00 PM | Bedtime: 10:00 PM strictly.")
    
    today_str = str(date.today())
    has_weaknesses = len(memory.get("logged_weaknesses", [])) > 0
    
    if st.button("🚀 Generate Tonight's Custom Plan", type="primary"):
        if client:
            with st.spinner("Checking mock schedule & analyzing study state..."):
                prompt = f"""
                You are Jarvis, an elite Edexcel IAL academic planner.
                
                CURRENT DATE: {today_str}
                STUDY WINDOW: 6:00 PM to 10:00 PM (4 Hours Total).
                BEDTIME: 10:00 PM.
                
                STUDY STATE:
                - Student has already completed revising all 9 units across Physics (U1-U3), Chemistry (U1-U3), and Math (P1, P2, S1).
                - Has logged specific weaknesses? {'YES' if has_weaknesses else 'NO (Awaiting Mock 1 diagnostic results / baseline practice)'}
                
                SCHEDULED MOCK EXAMS:
                {json.dumps(memory.get('scheduled_mocks', []), indent=2)}
                
                LOGGED WEAKNESSES:
                {json.dumps(memory.get('logged_weaknesses', []), indent=2)}
                
                RULES TO GENERATE PLAN:
                
                RULE A: IF AN EXAM IS SCHEDULED FOR TOMORROW (1 or 2 units):
                Follow the strict Pre-Exam Protocol:
                - 6:00 PM - 7:15 PM: Flashcards & interactive Quiz testing in NotebookLM for tomorrow's unit(s).
                - 7:15 PM - 8:30 PM: Read overall summary notes covering the full unit (PMT notes + teacher class notes).
                - 8:30 PM - 9:30 PM: Watch targeted videos or read textbook sections strictly for concepts missed during the quiz.
                - 9:30 PM - 10:00 PM: Quick review, pack bag, and wind down before 10:00 PM bedtime.
                
                RULE B: IF NO EXAM TOMORROW & WEAKNESSES ARE LOGGED (Post-Mock 1 results):
                - Allocate time based on high-priority logged errors from Mock 1 and past paper practice.
                
                RULE C: IF NO EXAM TOMORROW & NO WEAKNESSES LOGGED YET (Pre-Mock 1 results):
                - Focus on mixed past paper question sets across units to maintain retention and reveal weak spots.
                - Focus on active recall quiz sessions in NotebookLM.
                
                Output a clear, hour-by-hour breakdown from 6:00 PM to 10:00 PM.
                """
                response = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
                st.markdown("### 📋 Tonight's Target Schedule")
                st.write(response.text)

# ---------------------------------------------------------
# TAB 2: LOG MOCK EXAM DATES
# ---------------------------------------------------------
with tabs[1]:
    st.header("➕ Log Upcoming Mock Exam Dates")
    st.write("Enter mock exam dates as they are posted in Google Classroom.")
    
    col1, col2 = st.columns(2)
    with col1:
        mock_units = st.multiselect("Select Unit(s) for this Exam Day", [
            "IAS Physics Unit 1", "IAS Physics Unit 2", "IAS Physics Unit 3",
            "IAS Chemistry Unit 1", "IAS Chemistry Unit 2", "IAS Chemistry Unit 3",
            "IAS Math P1", "IAS Math P2", "IAS Math S1"
        ])
    with col2:
        mock_date = st.date_input("Exam Date")
        
    if st.button("Save Mock Exam Date"):
        if mock_units:
            memory.setdefault("scheduled_mocks", []).append({
                "units": mock_units,
                "date": str(mock_date)
            })
            save_memory(memory)
            st.success(f"Saved mock for {mock_units} on {mock_date}!")

# ---------------------------------------------------------
# TAB 3: LOG MOCK 1 RESULTS & WEAKNESSES
# ---------------------------------------------------------
with tabs[2]:
    st.header("📊 Log Mock 1 Results & Weak Spots")
    st.write("When you get your Mock 1 papers or quiz results back, log the areas where you lost marks.")
    
    sub = st.selectbox("Subject", ["Physics", "Chemistry", "Math"])
    unit = st.text_input("Unit & Topic (e.g., Physics U2 - Electricity & Internal Resistance)")
    detail = st.text_area("Describe the mistake or weak point (e.g., Lost 4 marks on circuit diagram calculation):")
    
    if st.button("Log Weakness to Jarvis Memory"):
        if detail:
            memory.setdefault("logged_weaknesses", []).append({
                "date": today_str,
                "subject": sub,
                "unit": unit,
                "detail": detail
            })
            memory["mock1_results_logged"] = True
            save_memory(memory)
            st.success("Weakness logged! Jarvis will now prioritize this in non-exam evening plans.")

# ---------------------------------------------------------
# TAB 4: MEMORY DUMP
# ---------------------------------------------------------
with tabs[3]:
    st.header("📋 Jarvis System Register")
    st.json(memory)