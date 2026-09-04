import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Full read/write scopes for coursework, announcements, and user profile details
SCOPES = [
    'https://www.googleapis.com/auth/classroom.courses.readonly',
    'https://www.googleapis.com/auth/classroom.coursework.students',
    'https://www.googleapis.com/auth/classroom.announcements',
    'https://www.googleapis.com/auth/classroom.profile.emails'
]
TOKEN_FILE = 'token_classroom.json'

def get_classroom_service():
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

    return build('classroom', 'v1', credentials=creds)

def list_coursework():
    """Fetches all active courses and their assigned coursework."""
    service = get_classroom_service()
    try:
        courses_result = service.courses().list(pageSize=10).execute()
        courses = courses_result.get('courses', [])
    except HttpError as e:
        return f"Error fetching courses: {e}"

    if not courses:
        return "No active courses found."

    summary_list = []

    for course in courses:
        course_id = course['id']
        course_name = course.get('name', 'Unnamed Course')
        
        try:
            coursework_result = service.courses().courseWork().list(courseId=course_id).execute()
            assignments = coursework_result.get('courseWork', [])

            summary_list.append(f"\nCourse: {course_name} (ID: {course_id})")
            if assignments:
                for item in assignments:
                    title = item.get('title', 'Untitled Assignment')
                    due_date = item.get('dueDate', {})
                    
                    if due_date:
                        year = due_date.get('year')
                        month = due_date.get('month')
                        day = due_date.get('day')
                        due_str = f"{year}-{month:02d}-{day:02d}"
                    else:
                        due_str = "No due date specified"

                    summary_list.append(f"  - [Assignment ID: {item.get('id')}] {title} (Due: {due_str})")
            else:
                summary_list.append("  - No active coursework posted.")
        except HttpError:
            summary_list.append(f"\nCourse: {course_name} (ID: {course_id})")
            summary_list.append("  - [Access Restricted] Unable to read coursework for this class.")

    return "\n".join(summary_list)

def post_announcement(course_id: str, text: str):
    """Posts a text announcement or note into a specific Google Classroom course stream."""
    service = get_classroom_service()
    announcement = {
        'text': text,
        'state': 'PUBLISHED'
    }
    try:
        res = service.courses().announcements().create(courseId=course_id, body=announcement).execute()
        return f"Announcement posted successfully to course {course_id}."
    except HttpError as e:
        return f"Failed to post announcement: {e}"

def get_account_email():
    """Fetches the authenticated Google account email for Google Classroom safely."""
    service = get_classroom_service()
    try:
        profile = service.userProfiles().get(userId='me').execute()
        return profile.get('emailAddress', 'Unknown Email')
    except HttpError:
        # Fallback if the Google domain or user role restricts direct userProfiles endpoint
        try:
            courses = service.courses().list(pageSize=1).execute().get('courses', [])
            if courses:
                return f"Authenticated (Owner ID: {courses[0].get('ownerId', 'Active')})"
        except HttpError:
            pass
        return "Authenticated (Profile email endpoint restricted by domain policy)"

if __name__ == "__main__":
    print("\n--- CLASSROOM ACCOUNT INFO ---")
    print("Account Status:", get_account_email())
    print("\n--- GOOGLE CLASSROOM ASSIGNMENTS ---")
    print(list_coursework())
    print("------------------------------------\n")