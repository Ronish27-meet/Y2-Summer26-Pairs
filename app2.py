import json
import os
import urllib.request
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
GIPHY_API_KEY = os.getenv("GIPHY_API_KEY")

def get_gif(search_term):
    # Convert spaces in search term to + for URL safety
    formatted_term = search_term.strip().replace(' ', '+')
    url = f"https://api.giphy.com/v1/gifs/search?api_key={GIPHY_API_KEY}&q={formatted_term}&limit=1&rating=g"
    try:
        req = urllib.request.urlopen(url)
        data = json.loads(req.read().decode('utf-8'))
        if data['data']:
            return data['data'][0]['images']['original']['url']
    except Exception:
        pass
    return ""

def ask_roey_for_gif(dish_name):
    roey_prompt = f"Coco found a recipe for '{dish_name}'. Give a 1-sentence funny reaction and add 'GIF_SEARCH: <words>' at the end."
    
    response = client.messages.create(
        model='claude-3-haiku-20240307',
        max_tokens=100,
        messages=[{'role': 'user', 'content': roey_prompt}]
    )
    
    reply = response.content[0].text
    gif_url = ""
    
    if "GIF_SEARCH:" in reply:
        text_part, search_part = reply.split("GIF_SEARCH:", 1)
        reply = text_part.strip()
        gif_url = get_gif(search_part.strip())

    return reply, gif_url

def run_chat():
    print('You: (type exit to quit)')
    
    # 1. We keep your original prompt, but append instructions for the hidden search tag at the end
    system_message = (
        "Your name is Roey. You are a conversation and advice forum. your job is to help  the user feel better and solve their problems. "
        "you are sarcastic, funny and understanding, you always give lighthearted respones and never lose pataince. "
        "You are also british. your answer is short and includes a summary of what the user said, then sharp advice or prespective, "
        "then a  sly lighthearted joke and a follow up. "
        "\nIMPORTANT: At the very end of every message, add a line with a search term for a GIF that matches the situation like this: "
        "\nGIF_SEARCH: <1 or 2 search words>"
    )
    history = []

    while True:
        user_input = input('>> ')

        if user_input.lower() == 'exit':
            break

        history.append({'role': 'user', 'content': user_input})

        response = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=300,
            temperature=0.7,
            system=system_message,
            messages=history
        )

        reply = response.content[0].text
        
        # 2. Extract the GIF search tag, call get_gif(), and clean the reply
        gif_url = ""
        if "GIF_SEARCH:" in reply:
            text_part, search_part = reply.split("GIF_SEARCH:", 1)
            reply = text_part.strip()
            search_query = search_part.strip()
            gif_url = get_gif(search_query)

        # 3. Print Roey's answer and the GIF URL
        print(f'Claude: {reply}')
        if gif_url:
            print(f'GIF: {gif_url}')

        # 4. Save the clean reply to conversation history
        history.append({'role': 'assistant', 'content': reply})

