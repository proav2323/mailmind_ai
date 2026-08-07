# workflows.py
from render_sdk.workflows import task, start
from app.main import emailWorkflowRun, emailItem

@task
async def process_user_emails(data: emailItem) -> dict:
    await emailWorkflowRun(data)
    return "done"

if __name__ == "__main__":
    start()
