import os;
from dotenv import load_dotenv;
from groq import Groq;
from pydantic import BaseModel
from json import loads
from google import genai
from google.genai import types

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
model="llama-3.1-8b-instant"

geminiClinet = genai.Client()
geminiModel="gemini-3.5-flash-lite"

MAX_TOKEN=1000

class EMAILMODEL(BaseModel):
    category: str
    priority: str
    subject: str
    summary: str
    deadline: str
    importance: int
    urgency: int
    senderImportance: int
    requireAction: bool
    tags: list[str]

emailScema = EMAILMODEL.model_json_schema()

async def getAiEmailResponse(emailBody, categories): # gemini response 
    text = emailBody['text']
    html = emailBody['html']

    userPrompt = f""" here's the email to analyze:
    {text}, {html}
    """

    categoriesText = ''
    for category in categories:
        categoriesText = f"{categoriesText} '{category['name']}',"

    systemPrompt = f"""
    You are an expert AI Email Assistant. Your task is to analyze an incoming email and extract structured key information.

    ### Core Guidelines:
    1. Output MUST be valid, raw JSON (no additional conversation, explanations, or preamble).
    2. Follow the key specifications strictly:
- "category": Choose exactly ONE from: [{categoriesText}]
- "subject": A concise, clear topic title summarizing the email (max 8 words). Do not simply repeat "Re:" headers—summarize the actual content.
- "priority": Assign "High", "Medium", or "Low" based on the Priority Rules below.
- "deadline": Extract any explicit or implied date/time constraint and return it like this "YYYY-MM-DD". If no deadline is present, set value to null.
- "summary": A crisp 1–2 sentence summary explaining the core message and any required action.
- "importance" (0-10): Measures HOW IMPORTANT this email is. Ignore deadlines.

    Consider:
    • Academic impact
    • Financial impact
    • Official announcements
    • Career impact
    • Whether ignoring it has serious consequences
    
    Examples:
    10
    Final exam notification
    Semester registration
    Fee deadline
    Placement interview

    8-9
    Assignment
    Lab submission
    Professor announcement

    5-7
    Workshop
    Club event
    Meeting invitation

    2-4
    Newsletter
    General update

    0-1
    Spam
    Advertisement

-"urgency": (0-10) Measures HOW SOON the user must act.

    Ignore importance.
    Examples:

    10
    Action required today

    9
    Tomorrow

    7
    Within 2-3 days

    5
    Within one week

    3
    Within one month

    1
    No deadline

    0
    No action needed

- "senderImportance": (0-10) How important is the sender?

    Examples:

     10
     Dean
     Head of Department
     Registrar
     Placement Cell

     8-9
     Professor
     Faculty
     Course Instructor

     6-7
     Teaching Assistant
     Club President

     3-5
     Student

     1-2
     Unknown sender

     0
     Spam sender

- "requiresAction": true if the student must do something.

  Examples:

  Submit assignment
  Pay fees
  Register
  Attend interview
  Fill form
  Reply
  Upload document

  false if the email is only informational.
- "tags": Return relevant keywords.
  
  Example:
  [
  "DBMS",
  "Assignment",
  "Semester 5"
  ]

#FALLABCK: IF YOUR CATEGORY NOT MATCHES IN ANY OF THE GIVEN CATEGORIES RETURN OTHER

    ### Priority Rules:
    - High: Urgent requests, immediate blockers, server/system issues, or strict deadlines within 24-48 hours.
    - Medium: Standard work requests, follow-ups requiring an answer, or task requests with flexible/longer deadlines.
    - Low: Informational (FYI) emails, newsletters, non-urgent updates, marketing, or general chat.
    - Expired: if the deadline is past todays date

    ---

    ### Few-Shot Examples

    Input:
    "Hi John, The client presentation is moved up to tomorrow morning at 10 AM. We need the final financial charts updated by 8 AM tomorrow so we can review. Let me know if you hit any roadblocks."

    Output:
    {{
    "category": "Action Required",
    "subject": "Client presentation moved to tomorrow morning",
    "priority": "High",
    "deadline": "2026-29-07",
    "summary": "The client presentation was moved to 10 AM tomorrow. Updated financial charts are required by 8 AM for review."
    "importance": 8,
    "urgency": 9,
    "senderImportance": 8,
    "requiresAction": true,
    "tags": ["Client Presentation", "Financial Charts", "Deadline"],
    }}

    Input:
    "Hey Team, Here is our monthly product newsletter! Check out our new features released in March, including dark mode support and performance     tweaks. Enjoy your weekend!"

    Output:
    {{
    "category": "other",
    "subject": "March product newsletter and new features",
    "priority": "Low",
    "deadline": null,
    "summary": "Monthly product update highlighting new March features including dark mode and performance updates."
    "importance": 2,
    "urgency": 0,
    "senderImportance": 1,
    "requiresAction": false,
    "tags": ["Product Newsletter", "New Features", "March Update","Newsletter"],
    }}
    """

    res = await geminiClinet.aio.models.generate_content(model=geminiModel,contents=userPrompt, config = types.GenerateContentConfig(
                system_instruction=systemPrompt,
                max_output_tokens=MAX_TOKEN,
                response_mime_type="application/json",
                response_schema=emailScema,
    ))

    return EMAILMODEL(**loads(res.text))