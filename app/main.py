from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from dotenv import load_dotenv
from json import loads, dumps
import app.utils.ai as ai
import asyncio
import requests
import os
from upstash_workflow import AsyncWorkflowContext
from upstash_workflow.fastapi import Serve
from upstash_redis import Redis

load_dotenv()
app = FastAPI()
redis = Redis.from_env()


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
    print(email)
    data = await ai.getAiEmailResponse(email['body'], email['categories'])
    return {
        "category": data.category, 
        "id": email['myGivenId'], 
        "summary": data.summary, 
        "deadline": data.deadline, 
        "subject": data.subject, 
        "priority": data.priority,     
        "importance": data.importance, 
        "urgency": data.urgency,
        "senderImportance": data.senderImportance,
        "requireAction": data.requireAction, 
        "tags": data.tags
    }

# This is a standard async function that acts as a step execution helper
async def process_batch_step(batch):
    batch_results = []
    for e in batch:
        result = await processEmails(e)
        batch_results.append(result)
    return batch_results

def save_results_to_backend(userId, results):
    redis.set(f"{userId}-aiEmails", dumps(results), ex=3600)
    response = requests.post(
        f"{os.getenv('BACKEND_API_URL')}/emails/store", 
        json={"data": f"{userId}-aiEmails", "emails": f"{userId}-emails", "userId": userId}, 
        headers={"Content-Type": "application/json"}
    )
    print(f"done {response.status_code}")
    return response.status_code

async def my_failure_handler(context, fail_status, fail_response, fail_headers) -> None:
    print(f"Workflow {context.workflow_run_id} failed permanently!")
    print(f"Status Code: {fail_status}")
    print(f"Error Details: {fail_response}")

    return "Handled failure successfully"

serve = Serve(app)

@serve.post("/email",failure_function=my_failure_handler)
async def emailWorkflow(context: AsyncWorkflowContext):
    payload = context.request_payload
    userId = payload['userId']
    emailData = redis.get(payload['data'])
    emails = loads(emailData) if emailData else []
    
    if len(emails) == 0:
        print("no emails")
        return []

    results = []
    email_batches = chunk_list(emails, 10)
    
    for index, batch in enumerate(email_batches):
        print(f"Executing batch {index + 1}/{len(email_batches)}...")
        
        batch_output = await context.run(f"process-batch-{index + 1}", lambda b=batch: process_batch_step(b))
        results.extend(batch_output)
        
        if index < len(email_batches) - 1:
            print(f"Batch {index + 1} done. Sleeping 65 seconds to completely reset Google quota...")
            await context.sleep(f"quota-sleep-after-batch-{index + 1}", "65s")

    print("Step 2: Processing results... and calling backend API to store results in database")
    await context.run("save-to-backend", lambda: save_results_to_backend(userId, results))

@app.get("/")
def root():
    return "hello world"

