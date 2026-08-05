import asyncio
from vercel import workflow
from json import loads
import requests
import os
from dotenv import load_dotenv;
import app.utils.ai as ai # production
from pydantic import BaseModel
from app.workflow import wf


load_dotenv()   

class emailItem(BaseModel):
    data: str
    userId: str

def chunk_list(lst, size):
    return [lst[i:i + size] for i in range(0, len(lst), size)]

async def processEmails(email):
        data = await ai.getAiEmailResponse(email['body'], email['categories'])
        returnData = {"category": data.category, "id":  email['myGivenId'], "summary": data.summary, "deadline": data.deadline, "subject": data.subject, "priority": data.priority,     "importance": data.importance, "urgency": data.urgency,"senderImportance": data.senderImportance,
    "requireAction": data.requireAction, "tags": data.tags}
        return returnData

@wf.workflow
async def emailWorkflow(*, data: emailItem):
    results = []
    emailData = data
    emails = loads(emailData.data)
    userId = emailData.userId
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
               await workflow.sleep(65)

    print("Step 2: Processing results... and calling backend API to store results in database")
    response = requests.post(f"{os.getenv('BACKEND_API_URL')}/emails/store", json={"data": results, "emails": emails, "userId": userId}, headers={"Content-Type": "application/json"})
    print(f"done {response.status_code}")