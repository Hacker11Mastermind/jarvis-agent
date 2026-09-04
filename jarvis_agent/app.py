import streamlit as st
import json
import os
from datetime import datetime, date, timedelta
from google import genai
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

st.set_page_config(
    page_title="Jarvis Executive Assistant", 
    page_icon="🤖", 
    layout="wide"
)

SCOPES = ['https://www.googleapis.com/auth/calendar']

# ---------------------------------------------------------
# SESSION STATE MEMORY MANAGEMENT
# ---------------------------------------------------------
if "memory" not in st.session_state:
    st.session_state["memory"] = {
        "scheduled_mocks": [],
        "personal_events": [],
        "logged_weaknesses": [],
        "chat_history": []
    }

memory = st.session_state["memory"]

# 7-day chat history pruner
def prune_chat_history(history):
    cutoff = datetime.now() - timedelta(days=7)
    valid_history = []
    for msg in history:
        try:
            msg_time = datetime.fromisoformat(msg["timestamp"])
            if msg_time >= cutoff:
                valid_history.append(msg)
        except Exception:
            valid_history.append(msg)
    return valid_history

memory["chat_history"] = prune_chat_history(memory.get("chat_history", []))

# ---------------------------------------------------------
# GEMINI CLIENT INITIALIZATION
# ---------------------------------------------------------
@st.cache_resource
def get_gemini_client():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

client = get_gemini_client()

# ---------------------------------------------------------
# GOOGLE CALENDAR OAUTH (CLOUD)
# ---------------------------------------------------------
def get_calendar_service():
    if "oauth_credentials" in st.session_state:
        creds = Credentials.from_authorized_user_info(st.session_state["oauth_credentials"], SCOPES)
        return build('calendar', 'v3', credentials=creds)
    
    if "google_oauth" not in st.secrets:
        st.error("Google OAuth secrets are missing in Streamlit Cloud Secrets settings.")
        return None

    client_config = {
        "web": {
            "client_id": st.secrets["google_oauth"]["client_id"],
            "client_secret": st.secrets["google_oauth"]["client_secret"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [st.secrets["google_oauth"]["redirect_uri"]]
        }
    }
    flow = Flow.from_client_config(client_config, scopes=SCOPES)
    flow.redirect_uri = st.secrets["google_oauth"]["redirect_uri"]
    
    # Check for OAuth callback code in URL query params
    if "code" in st.query_params:
        code = st.query_params["code"]
        flow.fetch_token(code=code)
        creds = flow.credentials
        st.session_state["oauth_credentials"] = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }
        st.query_params.clear()
        st.rerun()

    auth_url, _ = flow.authorization_url(prompt='consent')
    st.info(f"👉 [Click here to connect Google Calendar]({auth_url})")
    return None

def add_event_to_google_calendar(summary, date_str, category="Exam"):
    try:
        service = get_calendar_service()
        if not service:
            return None
        
        color_id = '11' if category == "Exam" else '5'  # Red for Exams, Orange for Personal
        
        event = {
            'summary': f"[{category}] {summary}",
            'description': f"Managed by Jarvis Executive Assistant on Streamlit Cloud. Category: {category}",
            'start': {'date': date_str},
            'end': {'date': date_str},
            'colorId': color_id,
        }
        
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        return created_event.get('htmlLink')
    except Exception as e:
        st.error(f"Calendar Sync Error: {e}")
        return None

# ---------------------------------------------------------
# SIDEBAR KNOWLEDGE BASE LINKS
# ---------------------------------------------------------
st.sidebar.title("🤖 Knowledge Base")
st.sidebar.markdown("🧪 [Chemistry Notebook](https://gemini.google.com/notebook/eceabc92-0f46-4bbc-8ca1-229186edd0a5)")
st.sidebar.markdown("🔬 [Physics Notebook](https://gemini.google.com/notebook/3eedb1fd-e99d-4078-9f96-c670a07853e1)")
st.sidebar.markdown("🔢 [Math Notebook](https://gemini.google.com/notebook/dc98c8ba-bb72-45c3-906a-e951ef9fb122)")

st.title("🤖 Jarvis Executive Assistant")

# 4 MAIN TABS
tabs = st.tabs([
    "💬 Chat with Jarvis", 
    "📅 Add Mock Schedule", 
    "📊 Add Weak Spots", 
    "📋 Memory & System Register"
])

# ---------------------------------------------------------
# TAB 1: GENERAL CHAT WITH JARVIS
# ---------------------------------------------------------
with tabs[0]:
    st.header("💬 General Chat with Jarvis")
    st.caption("Tell Jarvis anything to do, ask for today's 6:00 PM - 10:00 PM study plan, or inform it of family events. Memory is kept for 7 days.")

    for msg in memory["chat_history"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            st.caption(f"_{msg['timestamp'][:16]}_")

    user_input = st.chat_input("Talk to Jarvis...")

    if user_input:
        timestamp_str = datetime.now().isoformat()
        
        memory["chat_history"].append({
            "role": "user", 
            "content": user_input, 
            "timestamp": timestamp_str
        })
        
        with st.chat_message("user"):
            st.write(user_input)

        if client:
            with st.chat_message("assistant"):
                with st.spinner("Jarvis processing..."):
                    context_prompt = f"""
                    You are Jarvis, an elite executive study assistant for Edexcel IAL exams.
                    
                    CURRENT TIME: {datetime.now().strftime('%Y-%m-%d %H:%M')}
                    SCHEDULED MOCKS: {json.dumps(memory['scheduled_mocks'])}
                    PERSONAL/FAMILY EVENTS: {json.dumps(memory['personal_events'])}
                    LOGGED WEAKNESSES: {json.dumps(memory['logged_weaknesses'])}
                    
                    CHAT HISTORY (LAST 7 DAYS):
                    {json.dumps([{'role': m['role'], 'content': m['content']} for m in memory['chat_history'][-10:]])}
                    
                    USER PROMPT: {user_input}
                    
                    INSTRUCTIONS:
                    1. If asked for today's study plan (6:00 PM - 10:00 PM):
                       - Check if an exam is tomorrow. If YES: Enforce Pre-Exam Protocol (NotebookLM flashcards/quizzes -> PMT notes -> targeted video/textbook -> sleep by 10:00 PM).
                       - If NO exam tomorrow: Plan 4 hours targeting logged weaknesses and mixed past papers.
                       - If a personal/family event is scheduled for today, shift overlapping study topics to tomorrow.
                    2. Maintain an executive, clear tone.
                    """
                    response = client.models.generate_content(model="gemini-2.5-flash", contents=context_prompt)
                    bot_reply = response.text
                    st.write(bot_reply)

                    memory["chat_history"].append({
                        "role": "assistant", 
                        "content": bot_reply, 
                        "timestamp": datetime.now().isoformat()
                    })
        else:
            st.error("Gemini API Client is not initialized. Please configure `GEMINI_API_KEY` in Streamlit Secrets.")

# ---------------------------------------------------------
# TAB 2: ADD MOCK SCHEDULE
# ---------------------------------------------------------
with tabs[1]:
    st.header("📅 Add Mock Exam Schedule")
    
    col1, col2 = st.columns(2)
    with col1:
        units = st.multiselect("Select Unit(s)", [
            "IAS Physics Unit 1", "IAS Physics Unit 2", "IAS Physics Unit 3",
            "IAS Chemistry Unit 1", "IAS Chemistry Unit 2", "IAS Chemistry Unit 3",
            "IAS Math P1", "IAS Math P2", "IAS Math S1"
        ])
    with col2:
        ex_date = st.date_input("Exam Date")
        
    if st.button("Save Mock Exam to Schedule & Calendar", type="primary"):
        if units:
            entry = {"units": units, "date": str(ex_date)}
            memory["scheduled_mocks"].append(entry)
            
            link = add_event_to_google_calendar(
                summary=", ".join(units), 
                date_str=str(ex_date), 
                category="Exam"
            )
            if link:
                st.success(f"Saved & synced to Google Calendar! [View Event]({link})")
            else:
                st.success("Saved to session memory!")

# ---------------------------------------------------------
# TAB 3: ADD WEAK SPOTS
# ---------------------------------------------------------
with tabs[2]:
    st.header("📊 Add Mock Weak Spots & Errors")
    
    sub = st.selectbox("Subject", ["Physics", "Chemistry", "Math"])
    unit = st.text_input("Unit / Topic")
    detail = st.text_area("Describe mistake:")
    
    if st.button("Save Weak Spot", type="primary"):
        if detail:
            memory["logged_weaknesses"].append({
                "date": str(date.today()),
                "subject": sub, 
                "unit": unit, 
                "detail": detail
            })
            st.success("Weak spot logged successfully!")

# ---------------------------------------------------------
# TAB 4: MEMORY REGISTER
# ---------------------------------------------------------
with tabs[3]:
    st.header("📋 Memory & System Register")
    st.json(memory)