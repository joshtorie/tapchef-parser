import sys
print(f"DEBUG: Running parser.py from {__file__}")
# Print the argument structure to the terminal
def test_signature(a, b): pass
print(f"DEBUG: Argument count check: {test_signature.__code__.co_argcount}")

import os
import instructor
from openai import OpenAI
from dotenv import load_dotenv
from models import RecipeSchema

# This loads your API key from the secret .env file
load_dotenv()

# We patch the OpenAI client with Instructor so it returns structured data
client = instructor.from_openai(OpenAI(api_key=os.getenv("OPENAI_API_KEY")))

def parse_raw_recipe(raw_text: str, source_url: str) -> RecipeSchema:
    print(f"🧠 AI Agent is tokenizing the recipe from {source_url}...")
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_model=RecipeSchema, 
        messages=[
            {
                "role": "system", 
                "content": (
                    "You are a meticulous culinary data engine. Map raw recipe text into a structured JSON schema.\n\n"
                    
                    "CRITICAL ATOMIZATION RULES:\n"
                    "- Do NOT provide one big instruction paragraph. Decompose paragraphs into an array of 'Action' objects.\n"
                    "- 'step_summary': Create a short, high-level title for this step.\n"
                    "- 'action_type': Classify each action into: 'add', 'cook', 'transfer', 'wait', 'season', 'other'.\n"
                    "- 'is_timer': Set to true ONLY if the action implies a wait/cooking duration (e.g., 'simmer 10 mins').\n"
                    "- 'duration_minutes': Extract numeric duration. Return null if no specific time is involved.\n\n"
                    
                    "CRITICAL ID & FORMATTING RULES:\n"
                    "- Ingredient 'id' must ALWAYS be kebab-case.\n"
                    "- Units: Map text to 'ValidUnits' literals. Use 'tbsp', 'tsp', 'oz', 'g', 'ml', 'lb', 'pinch', 'unit', 'clove', 'can', 'bunch', 'dash', 'item', 'kg'.\n\n"
                    
                    "CRITICAL INGREDIENT USAGE RULES:\n"
                    "- Populate 'ingredients_used' per step. Include 'amount', 'unit', and 'prep_state' (e.g., 'thawed').\n"
                    "- 'role' must be a single-word function (e.g., 'fat', 'aromatic', 'main').\n\n"
                    
                    "CRITICAL HEAT & STATE RULES:\n"
                    "- 'heat_phases': Capture sequences of heat changes (e.g., 'bring to boil, then lower to simmer').\n"
                    "- 'target_temperature': ONLY for specific numeric oven temperatures (e.g., 'preheat to 350F').\n\n"
                    
                    "CRITICAL LOGIC & TIME RULES:\n"
                    "- Active Time: Literal physical labor (cutting, stirring).\n"
                    "- Passive Time: Waiting times (baking, resting, simmering).\n"
                    "- Continuous Attention: Set to 'true' ONLY if food ruins if left unattended for > 2 mins."
                )
            },
            {
                "role": "user", 
                "content": f"URL: {source_url}\n\nRecipe Text:\n{raw_text}"
            }
        ]
    )
    return response