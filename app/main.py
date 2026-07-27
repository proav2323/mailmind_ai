import asyncio
from fastapi import FastAPI
import app.utils.ai as ai # production
# import utils.ai as ai  # developemtn only
from pydantic import BaseModel
from time import sleep
from json import loads

app = FastAPI()

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

async def processEmails(email):
    await asyncio.sleep(1.5) 
    data = ai.getEmailResponse(email.body, email.categories, email.myGivenId)
    return data

@app.get("/")
def root():
    return "hello world"

@app.post("/email")
async def email(emailData: emailItem):
    emails = loads(emailData.data)
    print(emails)
    tasks = [processEmails(email) for email in emails]
    print("woring till here")
    result = await asyncio.gather(*tasks)
    return {"data": result}

