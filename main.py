import os
from anthropic import Anthropic
from dotenv import load_dotenv
from app1 import run_chat as coco
from app2 import run_chat as roey

load_dotenv()

client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

print("do you want to use agent 1 or 2?")