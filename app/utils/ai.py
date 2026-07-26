import os;
from dotenv import load_dotenv;
from groq import Groq;
from pydantic import BaseModel
from json import loads

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
model="qwen/qwen3.6-27b"

class categoryModel(BaseModel):
    category: str
    confidence: float
    reason: str
categoryScema = categoryModel.model_json_schema()

class priorityModel(BaseModel):
    priority: str
    confidence: float
    reason: str
priorityScema = priorityModel.model_json_schema()

class SUBJECTModel(BaseModel):
    subject: str
subjectScema = SUBJECTModel.model_json_schema()

class SUMMARYModel(BaseModel):
    summary: str
summaryScema = SUMMARYModel.model_json_schema()

class DEADLINEModel(BaseModel):
    deadline: str
deadlineScema = DEADLINEModel.model_json_schema()

def getAiResponse(systemPrompt, userPromt):
    messages = []
    messages.append({"role": "system", "content": systemPrompt})
    messages.append({"role": "user", "content": userPromt})

    res = client.chat.completions.create(messages=messages, model=model, temperature=0)
    return res.choices[0].message.content


def getEmailCategory(emailBody, categories):
    text = emailBody['text']
    html = emailBody['html']

    categoriesText = ""

    for cat in categories:
        categoriesText += f'''- "{cat['name']}": {cat['desc']}.\n'''

    systemPrompt = f"""
    You are an automated, highly accurate email classification system. Your only task is to analyze the provided email text and categorize it.
    email text can be in plain text or html, so categorize the email accordingly
    
    CATEGORIES:
    {categoriesText}

    RULES:
    1. You must respond with EXACTLY one valid JSON object.
    2. Do not include markdown formatting (like ```json).
    3. Do not include greetings, explanations, or conversational text.
    4. If an email overlaps categories, choose the one requiring the most urgent user action (e.g., an email about an "event" that also contains a a mandatory "assignment" should be categorized as "assignment").

    #FALLBACK:
    if email should not categories in any of the given categories, return other 

    #OUTPUT FORMAT: 
    return output in a json object with specified schema that is OUTPUT SCHEMA -> {categoryScema}
    RULES:
    1) category -> should from the give. categories only. don't invent your own categries
    2) confidence -> should be from 0 to 1 telling how much confidence you have in categorizing this email
    3) reason -> simple one sentence providing reason why you choose this category

    EXAMPLES:
    Input: "Hi team, please review the attached Q3 slide deck and have your notes ready by Friday at 5 PM."
    Output: {{"category": "assignment", "confidence": "0.98", "reason": "Requests the recipient to review a document by a specific deadline."}}

    Input: "Join us this Thursday at 10 AM PST for our live workshop on AI automation."
    Output: {{"category": "event", "confidence": "0.95", "reason": "Contains an invitation to a scheduled live workshop."}}
    """
    userPrompt = f"""here's the user email: 
    {text}, {html}
   """
    res = getAiResponse(systemPrompt=systemPrompt, userPromt=userPrompt)
    categoryJson = loads(res)
    return categoryModel(**categoryJson)

def getEmailSummary(emailody):
    text = emailody['text']
    html = emailody['html']

    systemPrompt = f"""
    you are automated, highly accurate email summarizer. your only task is to summarize provided email text.
    NOTE: email text can plain text or html.

    OUTPUT: RETURN YOUR RESPONSE IN JSON FORMAT USING THIS SCHEMA {summaryScema}

    RULES:
    1) DO NOT INVENT THINGS YOURSELF
    2) PROVIDE IMPORTAND DETAILS IN YOUR SUMMARY LIKE DEADLINE (IF ANY), EVENT(DATE AND TIME)(IF ANY),
    3) SUMMARIZE THE EMAIL WITG ALL IMPORTANT DETAILS
    4) PROVIDE SHORT AND CRISP SUMMARY OF THE EMAIL WITH ALL IMPORTANT DETAILS USER MIGHT WANT
    """

    userPropmt = f"""here is the email for you summarize: 
    {text}, {html}
    """
    res = getAiResponse(systemPrompt=systemPrompt, userPromt=userPropmt)
    return SUMMARYModel(**loads(res))

def getEmailPrority(emailBody):
    text = emailBody['text']
    html = emailBody['html']

    systemPrompt = f"""
    you are accurate, expert email priotizer, which oly task is to priorize the given email text.
    NOTE: EMAIL TEXT CAN BE IN PLAN TEXT AS WELL AS HTML.

    PRIORITIES:
    - HIGH: IF THE DEADLINE/DUE DATE/EVENT-DATE IS IN 3-4 DAYS FROM TODAY OR THE EMAIL IS VERY IMPORTANT AND USER SHOULD READ AS SOON AS POSSIBLE THEN YOU SHOULD RETURN HIGH
    - MEDIUM: IF THE DEADLINE/DUE DATE/EVENT-DATE IS IN 5-6 DAYS FROM TODAY OR THE EMAIL IS NOT THAT IMPORTANT THAT USER HAVE TO READ AS SOON AS POSSIBLE THEN YOU SHOULD RETURN MEDIUM
    - LOW: IF THE DEADLINE/DUE DATE/ EVENT-DATE IS WEEK OR MORE WEEK AWAY FROM TODAY OR THE EMAIL IS NOT IMPORTANT TO READ LIKE APP PROMOTION OR SOMETHING THAT THEN YOU SHOULD RETURN LOW

    FALLBACK: IF THE GIVEN EMAIL IS NOT BE TO IN ANY PROIRITY RETURN OTHER

    #OUTPUT: RETURN YOUR OUTPUT IN JSON OBJECT DEFINED BY THIS SCHEMA {priorityScema}
    -> PRIORITY: SHOULD BE ONE I HAVE LISTED ABOVE
    -> CONFIDENCE: SHOULD BE FROM 0 TO 1, TELLING HOW ONFIDENT YOU ARE
    -> REASON: WHY YOU CHOOSE THIS PRIORITY FOR THIS EMAIL

    RULES:
    1) DON'T INVENT YOUR OWN PRIORITIES
    2) ANSWER IN THE GIVEN SCHEMA
    3) NO PRORITY MATCHES THE EMAIL RETUNR OTHER
    

    EXAMPLES:
    Input: "Hi team, please review the attached Q3 slide deck and have your notes ready by comming 2 days"
    Output: {{"priority": "HIGH", "confidence": "0.98", "reason": "Requests the recipient to review a document by a specific deadline."}}

    Input: "Join us this Thursday at 10 AM PST for our live workshop on AI automation."
    Output: {{"priority": "HIGH", "confidence": "0.95", "reason": "Contains an invitation to a scheduled live workshop in 2 days"}}
    """

    userPrompt = f""" here is the email to priotize:
             {text}, {html}
    """
    res = getAiResponse(systemPrompt=systemPrompt,userPromt=userPrompt)
    return priorityModel(**loads(res))

def getEmailSubject(emailBody):
    text = emailBody['text']
    html = emailBody['html']

    systemPromot = f"""
    you an expert, automated email subject/ title decider. you only task is to provide a subject of the given email text.
    NOTE: EMAIL TEXT CAN BE IN PLAN TEXT AS WELL AS HTML.

    RULES:
    1) DO NOT INVENT DETIALS BY YOURSELF
    2) SHORT AND CRISP SUBJECT IN ABOUT 20-30 WORDS
    3) NO FORMATTING IS REQUIRED

    OUTPUT: RETURN YOUR RESPONSE IN JSON FORMAT USING THIS SCHEMA {subjectScema}

    EXAMPLES:
    Input: "Hi team, please review the attached Q3 slide deck and have your notes ready by comming 2 days"
    Output: {{"subject": "review Q3 slide block"}}

    Input: "Join us this Thursday at 10 AM PST for our live workshop on AI automation."
    Output: {{"subject": "Live Ai automation workshop"}}
    """

    userPrompt = f""" use this email to provide the subject:
    {text}, {html}
    """

    res = getAiResponse(systemPrompt=systemPromot, userPromt=userPrompt)
    return SUBJECTModel(**loads(res))

def getDeadline(emailBody):
    text = emailBody['text']
    html = emailBody['html']

    systemPromot = f"""
    you an expert, automated email deadline getter. you only task is to get the deadline of any work that has to done from email text.
    NOTE: EMAIL TEXT CAN BE IN PLAN TEXT AS WELL AS HTML.

    RULES:
    1) DON'T INVENT DATE BY YOURSELF
    2) DONT'T ASSUME ANY DATE BY YOURSELF
    3) DON'T INVENT DATA BY YOURSELF

    #FALLBACK: IF NOT DEADLINE IS MENTIONED IN EMAIL, RETURN NULL

    #OUTPUT -> RETURN THE RESPONSE IN JSON OBJECT FOLLOWING THIS SCHEMA -> {deadlineScema}
    IMPORTANT: deadline SHOULB IN THIS FORM YYYY-MM-DD

    EXAMPLES:
    Input: "Hi team, please review the attached Q3 slide deck and have your notes ready by 28 july"
    Output: {{"deadline": "2026-07-28"}}
    """

    userPrompt = f""" here's the email to get deadline from:
    {text}, {html}
    """

    res = getAiResponse(systemPrompt=systemPromot, userPromt=userPrompt)
    return DEADLINEModel(**loads(res))