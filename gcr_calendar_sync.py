import datetime
from google import genai
import classroom_tool
import calendar_tool

client = genai.Client()

def sync_classroom_mocks_to_calendar():
    print("Checking Google Classroom for new mock schedules...")
    coursework = classroom_tool.list_coursework()
    
    prompt = f"""
    Analyze this Google Classroom data stream for mock exam schedules or upcoming test dates:
    
    {coursework}
    
    Extract any mentioned exams in JSON format:
    [
      {{"summary": "Mock Exam: IAS Physics U1", "date": "YYYY-MM-DD", "description": "Edexcel Unit 1 Mock"}}
    ]
    Return ONLY valid JSON.
    """
    
    response = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
    print("Extracted Exam Events:\n", response.text)
    
    # You can parse response.text with json.loads and pass each to calendar_tool.create_event()

if __name__ == "__main__":
    sync_classroom_mocks_to_calendar()