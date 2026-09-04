import os
import sys
import time
import warnings
from datetime import date
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError, ServerError

import calendar_tool
import classroom_tool

warnings.filterwarnings("ignore", category=UserWarning, module="google.genai")

load_dotenv()
client = genai.Client()

def send_message_with_retry(chat, message, max_retries=3):
    """Sends a message to Gemini and retries automatically if a server error occurs."""
    for attempt in range(1, max_retries + 1):
        try:
            return chat.send_message(message)
        except (ServerError, APIError) as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                print(f"\n[Server busy (503). Retrying attempt {attempt}/{max_retries} in 2 seconds...]")
                time.sleep(2)
            else:
                raise e
    return chat.send_message(message)

def get_filtered_briefing_context():
    today = date.today().isoformat()
    
    print("Fetching calendar events...")
    calendar_data = calendar_tool.list_upcoming_events()
    
    print("Fetching classroom coursework...")
    classroom_data = classroom_tool.list_coursework()

    return calendar_data, classroom_data, today

def start_jarvis_chat():
    calendar_data, classroom_data, today_date = get_filtered_briefing_context()

    system_instruction = f"""
You are Jarvis, an executive AI assistant capable of managing Google Calendar and Google Classroom.
Today's date is {today_date}. Timezone is IST (+05:30).

STRICT RULES:
1. Ignore and filter out any assignments with due dates before {today_date}.
2. Focus on current and upcoming events or coursework.
3. You have tools to create/delete calendar events (including daily recurring events with RRULE:FREQ=DAILY) and post announcements. Use them when requested.
"""

    initial_prompt = f"""
Here is my real-time data feed:

--- UPCOMING CALENDAR EVENTS ---
{calendar_data}

--- GOOGLE CLASSROOM COURSEWORK ---
{classroom_data}

Please generate my initial Daily Briefing:
1. Executive Summary
2. Active Academic Priorities (Current/Upcoming only)
3. Schedule Overview
4. Recommended Immediate Action Plan
"""

    print("\n[Initializing Jarvis Interactive Session with Editing Tools...]\n")

    chat = client.chats.create(
        model="gemini-3.6-flash",
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=[
                calendar_tool.create_event,
                calendar_tool.delete_event,
                calendar_tool.list_upcoming_events,
                classroom_tool.post_announcement,
                classroom_tool.list_coursework
            ]
        )
    )

    response = send_message_with_retry(chat, initial_prompt)
    
    print("==================================================")
    print("             JARVIS DAILY BRIEFING                ")
    print("==================================================")
    print(response.text)
    print("==================================================\n")

    print("Jarvis is online with full read/write management. Type your command below (or 'exit' to quit).\n")
    while True:
        try:
            user_input = input("You > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                print("\nJarvis: Operational session ended. Have a productive day sir!")
                break

            response = send_message_with_retry(chat, user_input)
            print(f"\nJarvis > {response.text}\n")
            print("-" * 50)

        except (KeyboardInterrupt, EOFError):
            print("\nJarvis: Session terminated.")
            sys.exit()

if __name__ == "__main__":
    start_jarvis_chat()