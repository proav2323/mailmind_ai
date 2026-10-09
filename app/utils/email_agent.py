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
    result: str
    feedback: str
    accuracy: float

response_schema = Response.model_json_schema()

async def getEmailWriteResponse(messages: list, query): # gemini response 
    systemPrompt = f"""
    you are exper Ai Agent which tasks is to write user Emails as per given instructions
    you will return your response in valid JSON format as per the following schema:
    {response_schema}
    
    - result: the output user you for
    - feedback: A brief explanation of the email's content and purpose. and how can it be improved.
    - accuracy: A score between 0 and 1 indicating how well the email meets the user's requirements.

    don't add your own opinions or explanations outside of the JSON structure. strictly adhere to the schema and provide only the requested information.
    don't add your own information apart from user has given you

    FALLBACK: IF USER QUESTIONS IS NOT RELATED TO EMAIL WRITING, RETURN RESULT: NULL, ACCURACY: 1, feedback: I CAN'T HELP YOU WITH THAT

    EXAMPLES:

    input: write a subject for regearding a replying email to my friend and saying sorry for not attending his wedding.
    output: {{
    "result": "suddent emergency makes me miss your wedding",
    "feedback": "you could be more specific why you can't attend your freinds weeding so, i can be accurate",
    "accuracy": 0.5
    }}

    input: i want ot buy a car.
    output: {{
    "result": null,
    "feedback": "I CAN'T HELP YOU WITH THAT",
    "accuracy": 1
    }}

    input: i want to buy a house, write a real estate agent, write a email body telling him/her that i want to buy a 3BHK house for my family.
    output: {{
    "result": "
    
    Dear [Agent's Name],
    I hope this email finds you well.
    My name is [Your Name], and I am currently looking to purchase a new home for my family. We are specifically looking for a 3BHK (3 Bedroom, Hall, and Kitchen) house.
    To help narrow down the search, here are a few key details of what we are looking for:
         • Preferred Locations: [Insert preferred neighbourhoods or areas, e.g., North Mohali, Zirakpur, etc.]
         • Budget Range: [Insert your maximum budget, e.g., ₹75 Lakhs to ₹1 Crore]
         • Timeline: We are looking to buy [Insert timeline, e.g., within the next 3 months / as soon as we find the right fit].
         • Key Features: A family-friendly neighborhood, proximity to good schools, and [mention any other needs like a parking space, park nearby, or balcony].
    Please let me know if you have any active listings that match these criteria or if we can schedule a quick call to discuss potential options. You can reach me at this email or via phone at [Your Phone Number].
    Thank you for your time and assistance. I look forward to hearing from you.
    Best regards,

    ",
    "feedback": "can be more specific with your family members, so i can be realistic if that house suits you or not or i tell the agent more details like what you should have in that house",
    "accuracy": 0.7
    }}
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