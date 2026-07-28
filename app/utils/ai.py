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

MAX_TOKEN=600

class EMAILMODEL(BaseModel):
    category: str
    priority: str
    subject: str
    summary: str
    deadline: str

emailScema = EMAILMODEL.model_json_schema()


# def getAiResponse(systemPrompt, userPromt): # groq response 
#     messages = []
#     messages.append({"role": "system", "content": systemPrompt})
#     messages.append({"role": "user", "content": userPromt})

#     res = client.chat.completions.create(messages=messages, model=model, temperature=0, max_tokens=MAX_TOKEN)
#     return res.choices[0].message.content

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
    - "deadline": Extract any explicit or implied date/time constraint (e.g., "YYYY-MM-DD", "Today by 5:00 PM", "End of Week"). If no deadline is present, set value to null.
    - "summary": A crisp 1–2 sentence summary explaining the core message and any required action.

    ### Priority Rules:
    - High: Urgent requests, immediate blockers, server/system issues, or strict deadlines within 24-48 hours.
    - Medium: Standard work requests, follow-ups requiring an answer, or task requests with flexible/longer deadlines.
    - Low: Informational (FYI) emails, newsletters, non-urgent updates, marketing, or general chat.

    ---

    ### Few-Shot Examples

    Input:
    "Hi John, The client presentation is moved up to tomorrow morning at 10 AM. We need the final financial charts updated by 8 AM tomorrow so we can     review. Let me know if you hit any roadblocks."

    Output:
    {{
    "category": "Action Required",
    "subject": "Client presentation moved to tomorrow morning",
    "priority": "High",
    "deadline": "Tomorrow by 8:00 AM",
    "summary": "The client presentation was moved to 10 AM tomorrow. Updated financial charts are required by 8 AM for review."
    }}

    Input:
    "Hey Team, Here is our monthly product newsletter! Check out our new features released in March, including dark mode support and performance     tweaks. Enjoy your weekend!"

    Output:
    {{
    "category": "Newsletter & Marketing",
    "subject": "March product newsletter and new features",
    "priority": "Low",
    "deadline": null,
    "summary": "Monthly product update highlighting new March features including dark mode and performance updates."
    }}
    """

    res = await geminiClinet.aio.models.generate_content(model=geminiModel,contents=userPrompt, config = types.GenerateContentConfig(
                system_instruction=systemPrompt,
                max_output_tokens=MAX_TOKEN,
                response_mime_type="application/json",
                response_schema=emailScema,
    ))

    return EMAILMODEL(**loads(res.text))
