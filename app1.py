import base64
import io
import json
import os
import urllib.parse
from anthropic import Anthropic
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# --- MODELS ---
TEXT_MODEL = "claude-3-haiku-20240307"  # Ultra cheap for normal text chat
VISION_MODEL = "claude-3-5-sonnet-20241022"  # Used for vision & complex tools

# --- TOKEN OPTIMIZATION HELPERS ---


def encode_and_compress_image(image_path: str, max_dim=1024) -> str:
    """Compresses image to ~1024px JPEG to save up to 80% of vision tokens."""
    with Image.open(image_path) as img:
        img.thumbnail((max_dim, max_dim))
        buffer = io.BytesIO()
        img.convert("RGB").save(buffer, format="JPEG", quality=80)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")


def get_optimized_history(history, max_messages=6):
    """Keeps only the most recent N messages to prevent context window bloat."""
    return history[-max_messages:]


# --- TOOL FUNCTIONS ---


def search_youtube(query: str) -> str:
    encoded_query = urllib.parse.quote(query)
    return f"YouTube search for '{query}': https://www.youtube.com/results?search_query={encoded_query}"


def search_web_or_recipes(query: str) -> str:
    encoded_query = urllib.parse.quote(f"{query} recipe")
    return f"Recipe search for '{query}': https://www.google.com/search?q={encoded_query}"


def start_cooking_timer(seconds: int, label: str = "Timer") -> str:
    return f"Timer set for {label} ({seconds} seconds)."


def execute_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "search_youtube":
        return search_youtube(tool_input.get("query", ""))
    elif tool_name == "search_recipe_web":
        return search_web_or_recipes(tool_input.get("query", ""))
    elif tool_name == "start_timer":
        return start_cooking_timer(
            tool_input.get("seconds", 60), tool_input.get("label", "Timer")
        )
    return "Tool not found."


# --- ANTHROPIC TOOL DEFINITIONS (CONCISE) ---

tools = [
    {
        "name": "search_youtube",
        "description": "Search YouTube cooking videos.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "search_recipe_web",
        "description": "Search web for recipes or cooking tips.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "start_timer",
        "description": "Set a cooking timer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "seconds": {"type": "integer"},
                "label": {"type": "string"},
            },
            "required": ["seconds"],
        },
    },
]

# --- MAIN APP ---


def run_chat():
    print("--- Chef Coco (Token-Optimized) ---")
    print("Commands: 'exit' to quit | 'image:<path>' to analyze dish photo\n")

    # Ultra-concise system prompt to save baseline tokens
    system_message = (
        "You are Chef Coco, a friendly culinary assistant. Keep answers concise and actionable. "
        "Provide direct cooking steps, substitutions, and basic nutrition estimates when asked."
    )

    history = []

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() == "exit":
            print("Chef Coco signing off. Happy cooking!")
            break

        if not user_input:
            continue

        selected_model = TEXT_MODEL

        # Handle image analysis
        if user_input.startswith("image:"):
            img_path = user_input.replace("image:", "").strip()
            if os.path.exists(img_path):
                b64_img = encode_and_compress_image(img_path)
                selected_model = (
                    VISION_MODEL  # Switch to Sonnet for vision processing
                )

                messages_to_send = get_optimized_history(history) + [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": b64_img,
                                },
                            },
                            {
                                "type": "text",
                                "text": "Identify this food, estimate nutrition, and suggest a recipe.",
                            },
                        ],
                    }
                ]

                # Store lightweight placeholder string in long-term history to avoid resending image data
                history.append(
                    {"role": "user", "content": f"[Analyzed image: {img_path}]"}
                )
            else:
                print(f"Error: File not found at '{img_path}'")
                continue
        else:
            history.append({"role": "user", "content": user_input})
            messages_to_send = get_optimized_history(history)

        # First API call
        response = client.messages.create(
            model=selected_model,
            max_tokens=350,
            temperature=0.7,
            system=system_message,
            tools=tools,
            messages=messages_to_send,
        )

        # Handle tool call
        if response.stop_reason == "tool_use":
            tool_use = next(
                block for block in response.content if block.type == "tool_use"
            )
            tool_name = tool_use.name
            tool_input = tool_use.input

            print(f"\n[Chef Coco used tool: {tool_name}]")
            tool_result = execute_tool(tool_name, tool_input)

            # Append assistant's tool intent and tool result back to history
            history.append({"role": "assistant", "content": response.content})
            history.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use.id,
                            "content": tool_result,
                        }
                    ],
                }
            )

            # Second API call to complete tool response (using Sonnet for tool synthesis)
            final_response = client.messages.create(
                model=VISION_MODEL,
                max_tokens=350,
                temperature=0.7,
                system=system_message,
                tools=tools,
                messages=get_optimized_history(history),
            )

            reply_text = final_response.content[0].text
            print(f"\nCoco: {reply_text}")
            history.append({"role": "assistant", "content": reply_text})

        else:
            reply_text = response.content[0].text
            print(f"\nCoco: {reply_text}")
            history.append({"role": "assistant", "content": reply_text})


if __name__ == "__main__":
    run_chat()