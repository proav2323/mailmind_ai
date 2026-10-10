from fastapi import FastAPI, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from dotenv import load_dotenv
from json import loads, dumps
import app.utils.ai as ai
import app.utils.email_agent as agent
# import utils.ai as ai
import asyncio
import requests
import os
from upstash_redis import Redis
import logging

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Adjust this to your specific NestJS URL later for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()
app = FastAPI()
redis = Redis.from_env()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#  prompt-6-things
#  1) role - role of agent (ex-1-you are a engineer responsible for reviewing code)(good) (ex-2-you are a genius enginner(bad)(should be genius))
#  2) task - what is work to the agent (classification of the email in different categories), (short summary of email),etc
#  3) constraints - boundary - give answer to give given things.
#  4) output-format - one word answer(ex. category classification), (100-150 words summary of email), (json)
#  5) zero/oneshot/example - give example to agent for more clarity to the ai
#  6) fallback - unralted thing/issue for the specific app to is unreleted return other/something-else

# good-prompt = "
# #ROLE: you are engineer who is responsible for reviewing code 
# #TASK: classify email into i category
# #CONSTRAINTS: you have to classify this email into these categories = [categpries]
# #OUTPUT FORMAT: you answer should be in one word and onw word should be one of categories give to you in constraints
# #Example: for instance - if user was charged more than the laptop price, it's a billing issue
# #FALLBACK: if the issue unreleted to any of the categories mentioned in constrainst then the anwer should be other
# "

# prompt chaining -> FOR DEBUGGING AND AI MODELS
# 1) get category -> done
# 2) get summary -> done
# 3) get deadline if any (if deadline -> place event in user calaender(react tool)) -> done diealine (not calender tool(later))
# 4) get subject -> done
# 5) get priority -> done



class emailItem(BaseModel):
    data: str
    userId: str
    noti: bool | None
    aiId: str

class emailResponse(BaseModel):
    messageId: str
    userId: str
    query: str


load_dotenv()   
def chunk_list(lst, size):
    return [lst[i:i + size] for i in range(0, len(lst), size)]

async def processEmails(email):
        data = await ai.getAiEmailResponse(email['body'], email['categories'])
        returnData = {"category": data.category, "id":  email['myGivenId'], "summary": data.summary, "deadline": data.deadline, "subject": data.subject, "priority": data.priority,     "importance": data.importance, "urgency": data.urgency,"senderImportance": data.senderImportance,
    "requireAction": data.requireAction, "tags": data.tags}
        return returnData

async def emailWorkflowRun(data: emailItem):
    logger.info(f"Task STARTED")
    emailData = redis.get(data.data)
    userId = data.userId
    aiId = data.aiId
    results = []
    emails = loads(emailData)
    if (len(emails) == 0):
        print("no emails")
        results = []
    else:             
       email_batches = chunk_list(emails, 10)
        
       for index, batch in enumerate(email_batches):
           print(f"Executing batch {index + 1}/{len(email_batches)}...")
            
           batch_tasks = [processEmails(e) for i, e in enumerate(batch)]
           batch_results = await asyncio.gather(*batch_tasks)
           results.extend(batch_results)
            
           if index < len(email_batches) - 1:
               print(f"Batch {index + 1} done. Sleeping 65 seconds to completely reset Google quota...")
               await asyncio.sleep(65)

    print("Step 2: Processing results... and calling backend API to store results in database")
    dataNoti = False
    if data.noti == None:
        dataNoti = False
    else:
        dataNoti = True

    redis.set(f"{aiId}-aiEmails", dumps(results), ex=3600)
    response = requests.post(f"{os.getenv('BACKEND_API_URL')}/emails/store", json={"data": f"{aiId}-aiEmails", "emails": f"{aiId}-emails", "userId": userId, "not": dataNoti}, headers={"Content-Type": "application/json"})
    logger.info(f"done {response.status_code}")
    logger.info(f"Task complted")


@app.post("/email")
async def email(email: emailItem, background_task: BackgroundTasks):
    background_task.add_task(emailWorkflowRun, email)
    print("done")

@app.post("/write")
async def write_email(email: emailResponse):
    messages = redis.get(email.messageId)
    if (messages == None):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
    data = await agent.getEmailWriteResponse(messages, email.query)
    redis.set(email.messageId, dumps(data['messages']))
    return {"success": "true"}

@app.get("/")
def root():
    return "hello world"

@app.post("/")
def root():
    return "hello world"