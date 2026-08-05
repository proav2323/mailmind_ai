from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from dotenv import load_dotenv
from json import loads
import app.utils.ai as ai
import asyncio
import requests
import os
import inngest
import inngest.fast_api
import logging

load_dotenv()
app = FastAPI()

inngest_client = inngest.Inngest(
    app_id="my_fastapi_app",
    logger=logging.getLogger("uvicorn"),
)

@inngest_client.create_function(
    fn_id="email_process",
    trigger=inngest.TriggerEvent(event="app/emailprocessing"),
)

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


load_dotenv()   
def chunk_list(lst, size):
    return [lst[i:i + size] for i in range(0, len(lst), size)]

async def processEmails(email):
        data = await ai.getAiEmailResponse(email['body'], email['categories'])
        returnData = {"category": data.category, "id":  email['myGivenId'], "summary": data.summary, "deadline": data.deadline, "subject": data.subject, "priority": data.priority,     "importance": data.importance, "urgency": data.urgency,"senderImportance": data.senderImportance,
    "requireAction": data.requireAction, "tags": data.tags}
        return returnData

async def emailWorkflow(ctx: inngest.Context):
    data = ctx.event.data.get("data", "User")
    userId = ctx.event.data.get("userId", "User")
    results = []
    emails = loads(data)
    print(emails)
    print(userId)
    if (len(emails) == 0):
        print("no emails")
        results = []
    else:             
       email_batches = chunk_list(emails, 10)
        
       for index, batch in enumerate(email_batches):
           print(f"Executing batch {index + 1}/{len(email_batches)}...")
            
           batch_tasks = [processEmails(e) for e in enumerate(batch)]
           batch_results = await asyncio.gather(*batch_tasks)
           results.extend(batch_results)
            
           if index < len(email_batches) - 1:
               print(f"Batch {index + 1} done. Sleeping 65 seconds to completely reset Google quota...")
               await asyncio.sleep(65)

    print("Step 2: Processing results... and calling backend API to store results in database")
    response = requests.post(f"{os.getenv('BACKEND_API_URL')}/emails/store", json={"data": results, "emails": emails, "userId": userId}, headers={"Content-Type": "application/json"})
    print(f"done {response.status_code}")

inngest.fast_api.serve(app, inngest_client, [emailWorkflow])

@app.get("/")
def root():
    return "hello world"

@app.post("/email")
async def emailProcess(emailItem: emailItem):
     print("working")
     await inngest_client.send(
        inngest.Event(
            name="app/emailprocessing",
            data={"data": emailItem.data, "userId": emailItem.userId}
        )
    )
     return "done"