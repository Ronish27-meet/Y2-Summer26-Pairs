import os
import sys
from anthropic import Anthropic
from dotenv import load_dotenv
from app1 import run_chat as coco
from app2 import run_chat as roey

load_dotenv()

print("Hello! If you're feeling sad, this app gives you two options.")
print("1 - Emotional eater")
print("2 - Talk with a therapist")

while True:
    choice = input("What do you want to choose? (1/2) or exit the app by writing -exit-: ")
    if choice == "1":
        coco()
    elif choice == "2":
        roey()
    elif choice.lower() == "exit":
        break 
    else:
        print("Please enter 1 or 2.")