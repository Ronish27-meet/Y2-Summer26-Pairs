from app2 import ask_roey_for_gif
import os
import urllib.parse
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))


def search_youtube(query: str) -> str:
    """Helper function to create a YouTube search link."""
    encoded_query = urllib.parse.quote(query)
    return f"YouTube search for '{query}': https://www.youtube.com/results?search_query={encoded_query}"


tools = [
    {
        "name": "search_youtube",
        "description": "Search YouTube for cooking tutorial videos, recipes, or technique demonstrations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query for YouTube (e.g., 'how to julienne an onion')"
                }
            },
            "required": ["query"],
        }
    }
]


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
        user_input = input('>> ').strip()

        if user_input.lower() == "exit":
            print("Chef Coco signing off. Happy cooking!")
            break

        if not user_input:
            continue

        history.append({'role': 'user', 'content': user_input})

        # Send request with tool definition included
        response = client.messages.create(
            model='claude-3-5-sonnet-20241022',
            max_tokens=500,
            temperature=0.7,
            system=system_message,
            tools=tools,
            messages=history
        )

        # Handle tool call if Claude decides to search YouTube
        if response.stop_reason == "tool_use":
            # Append Claude's request to conversation history
            history.append({'role': 'assistant', 'content': response.content})

            # Process tool execution
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    if block.name == "search_youtube":
                        query = block.input.get("query", "")
                        result_str = search_youtube(query)

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_str
                        })

            # Send tool execution results back to Claude
            history.append({'role': 'user', 'content': tool_results})

            # Fetch final response after tool call
            response = client.messages.create(
                model='claude-3-5-sonnet-20241022',
                max_tokens=500,
                temperature=0.7,
                system=system_message,
                tools=tools,
                messages=history
            )

         if tool_name in [ "search_youtube"]:
                searched_dish = tool_input.get("query")
                roey_comment, roey_gif = ask_roey_for_gif(searched_dish)
                print(f"Roey: {roey_comment}")
                if roey_gif:
                    print(f"GIF: {roey_gif}")

        # Extract text response blocks
        reply = "".join([block.text for block in response.content if block.type == "text"])

        print(f'\nClaude: {reply}\n')
        history.append({'role': 'assistant', 'content': reply})


if __name__ == "__main__":
    run_chat()