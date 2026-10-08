import os;
from app.utils.ai import EMAILMODEL
from dotenv import load_dotenv;
from groq import Groq;
from pydantic import BaseModel
from json import loads
from google import genai
from google.genai import types

load_dotenv()
geminiClient = genai.Client()
geminiModel="gemini-3.5-flash-lite"

class Response(BaseModel):
    email: str
    feedback: str
    accuracy: float

response_schema = Response.model_json_schema()

async def getEmailWriteResponse(messages: list, query): # gemini response 
    systemPrompt = f"""
    you are exper Ai Agent which tasks is to write user Emails as per given instructions
    you will return your response in valid JSON format as per the following schema:
    {response_schema}
    
    - email: The email content you have written for the user.
    - feedback: A brief explanation of the email's content and purpose. and how can it be improved.
    - accuracy: A score between 0 and 1 indicating how well the email meets the user's requirements.

    don't add your own opinions or explanations outside of the JSON structure. strictly adhere to the schema and provide only the requested information.
    don't add your own information apart from user has given you
    """
    messages.insert(types.Content(role="user", parts=[types.Part.from_text(text=query)]))
    res = await geminiClient.aio.models.generate_content(model=geminiModel,contents=messages, config = types.GenerateContentConfig(
                system_instruction=systemPrompt,
                max_output_tokens=4000,
                response_mime_type="application/json",
                response_schema=response_schema,
                
    ))
    messages.append(types.Content(role="model", parts=[types.Part.from_text(text=res.text)]))
    return {"data": Response(**loads(res.text)), "messages": messages}