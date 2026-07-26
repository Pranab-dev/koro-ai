from openai import OpenAI
from dotenv import load_dotenv
import os
import random

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

# The mode currently being forced.
# None = use random mode.
forced_mode = None


def load_personality(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return file.read()


def choose_personality():
    global forced_mode

    if forced_mode == "normal":
        return load_personality("normal.txt")

    if forced_mode == "brainrot":
        return load_personality("brainrot.txt")

    if forced_mode == "socrates":
        return load_personality("socrates.txt")

    # Random mode: 10% Normal, 45% Brainrot, 45% Socrates
    personalities = [
        "normal.txt",
        "normal.txt",

        "brainrot.txt",
        "brainrot.txt",
        "brainrot.txt",
        "brainrot.txt",
        "brainrot.txt",
        "brainrot.txt",
        "brainrot.txt",
        "brainrot.txt",
        "brainrot.txt",

        "socrates.txt",
        "socrates.txt",
        "socrates.txt",
        "socrates.txt",
        "socrates.txt",
        "socrates.txt",
        "socrates.txt",
        "socrates.txt",
        "socrates.txt"
    ]

    return load_personality(random.choice(personalities))


def set_mode(mode):
    global forced_mode

    if mode in ["normal", "brainrot", "socrates"]:
        forced_mode = mode
        return True

    if mode == "random":
        forced_mode = None
        return True

    return False


def get_mode():
    if forced_mode is None:
        return "random"

    return forced_mode


def ask_friend(message):
    personality = choose_personality()

    response = client.chat.completions.create(
        model="nvidia/nemotron-nano-12b-v2-vl:free",
        messages=[
            {
                "role": "system",
                "content": personality
            },
            {
                "role": "user",
                "content": message
            }
        ]
    )

    return response.choices[0].message.content