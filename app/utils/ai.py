import os;
from dotenv import load_dotenv;
from groq import Groq;

load_dotenv()
client = Groq(os.getenv("GROQ_API_KEY"))