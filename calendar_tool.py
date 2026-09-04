import os.path
from typing import Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']
TOKEN_FILE = 'token_calendar.json'

def get_calendar_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)

def list_upcoming_events(max_results: int = 10) -> str:
    """Lists upcoming calendar events."""
    service = get_calendar_service()
    events_result = service.events().list(
        calendarId='primary',
        maxResults=max_results,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])
    if not events:
        return "No upcoming events found."
    
    event_list = []
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        summary = event.get('summary', 'No Title')
        event_id = event.get('id')
        event_list.append(f"- [{event_id}] {start}: {summary}")
        
    return "\n".join(event_list)

def create_event(summary: str, start_time: str, end_time: str, description: str = "", recurrence_rule: Optional[str] = None) -> str:
    """Creates a new event on Google Calendar.
    start_time and end_time must be ISO formatted strings (e.g., '2026-09-03T19:45:00+05:30').
    recurrence_rule is an optional list format rule, e.g., 'RRULE:FREQ=DAILY' for daily repetition.
    """
    service = get_calendar_service()
    event_body = {
        'summary': summary,
        'description': description,
        'start': {'dateTime': start_time, 'timeZone': 'Asia/Kolkata'},
        'end': {'dateTime': end_time, 'timeZone': 'Asia/Kolkata'},
    }
    
    if recurrence_rule:
        event_body['recurrence'] = [recurrence_rule]

    event = service.events().insert(calendarId='primary', body=event_body).execute()
    return f"Event created successfully: {event.get('summary')} (ID: {event.get('id')})"

def delete_event(event_id: str) -> str:
    """Deletes an event from Google Calendar given its event ID."""
    service = get_calendar_service()
    service.events().delete(calendarId='primary', eventId=event_id).execute()
    return f"Event {event_id} deleted successfully."