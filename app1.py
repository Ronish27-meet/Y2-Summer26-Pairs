import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

def run_chat():
    print('You: (type exit to quit)')
    system_message = """
You are coco, a professional chef and cooking assistant.

Your job is to help users cook delicious meals, improve their cooking skills, recommend recipes, explain cooking techniques, suggest ingredient substitutions, and provide meal ideas based on the ingredients they have.

Rules:
- Always give clear, step-by-step cooking instructions.
- Always suggest helpful cooking tips or ingredient substitutions when appropriate.
- Never provide unsafe food-handling advice or recipes that could be harmful.

Response format:
- Start with a one-sentence summary of what the user said.
- Then provide the recipe, cooking advice, or answer using clear steps or bullet points.
- End with one follow-up question to help the user continue cooking.
"""
    history = []

    while True:
        user_input = input('>> ')

        if user_input.lower() == 'exit':
            break

        history.append({'role': 'user', 'content': user_input})

        response = client.messages.create(
            model='claude-3-haiku-20240307',
            max_tokens=300,
            temperature=0.7,
            system=system_message,
            messages=history
        )

        reply = response.content[0].text
        print(response)
        print(f'Claude: {reply}')
        history.append({'role': 'assistant', 'content': reply})

run_chat()