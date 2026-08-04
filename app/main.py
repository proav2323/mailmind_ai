import asyncio
import os
from fastapi import FastAPI, HTTPException, status
import app.utils.ai as ai # production
# import utils.ai as ai  # developemtn only
from pydantic import BaseModel
from json import loads
from upstash_workflow.fastapi import Serve
from upstash_workflow import AsyncWorkflowContext
from dotenv import load_dotenv
import requests

load_dotenv()
app = FastAPI()
serve = Serve(app)

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

def chunk_list(lst, size):
    return [lst[i:i + size] for i in range(0, len(lst), size)]

class emailItem(BaseModel):
    data: str

async def processEmails(email):
    try:
        data = await ai.getAiEmailResponse(email['body'], email['categories'])
        returnData = {"category": data.category, "id":  email['myGivenId'], "summary": data.summary, "deadline": data.deadline, "subject": data.subject, "priority": data.priority,     "importance": data.importance, "urgency": data.urgency,"senderImportance": data.senderImportance,
    "requireAction": data.requireAction, "tags": data.tags}
                
        return returnData
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=e)

@app.get("/")
def root():
    return "hello world"

@serve.post("/email")
async def workflow(context: AsyncWorkflowContext[emailItem]) -> None:
    results = []
    emailData = context.request_payload
    emails = loads(emailData.data)
    async def _step1() -> None:
        email_batches = chunk_list(emails, 10)
    
        for index, batch in enumerate(email_batches):
            print(f"Executing batch {index + 1}/{len(email_batches)}...")
        
            batch_tasks = [processEmails(e) for e in batch]
            batch_results = await asyncio.gather(*batch_tasks)
            results.extend(batch_results)
        
            if index < len(email_batches) - 1:
                print(f"Batch {index + 1} done. Sleeping 65 seconds to completely reset Google quota...")
                await asyncio.sleep(65)

    await context.run("step-1", _step1)

    async def _step2() -> None:
        print("Step 2: Processing results... and calling backend API to store results in database")
        try:
           response = requests.post(f"{os.getenv('BACKEND_API_URL')}/storeEmails", json={"data": results, "emails": emails})
           if (response.status_code == 200):
               print("Results successfully stored in the database.")
           else:
               print(f"Failed to store results in the database. Status code: {response.status_code}, Response: {response.text}")

        except requests.exceptions.Timeout:
           print("The request timed out.")
        except requests.exceptions.RequestException as e:
           print(f"An error occurred: {e}")

    await context.run("step-2", _step2)