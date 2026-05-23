import os
import json
import psycopg
from dotenv import load_dotenv
from models import RecipeSchema

# 1. Load environment variables
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, ".env")
load_dotenv(dotenv_path=env_path)

CONN_STR = os.getenv("DATABASE_URL")

if not CONN_STR:
    raise ValueError("❌ DATABASE_URL is missing!")

def init_local_tables():
    """Initializes the PostgreSQL database schema for Kitchen OS."""
    with psycopg.connect(CONN_STR) as conn:
        with conn.cursor() as cur:
            # Note: JSONB is schema-agnostic, so adding new fields to 
            # the models (like heat_phases) requires zero changes here.
            cur.execute("""
                CREATE TABLE IF NOT EXISTS local_recipes (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    source_url TEXT UNIQUE,
                    equipment_needed JSONB,
                    ingredients JSONB,
                    steps JSONB,
                    raw_payload JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)
            conn.commit()

def save_parsed_recipe(recipe: RecipeSchema, url: str):
    """
    Saves the structured recipe to the database. 
    The 'steps' column will automatically capture the new 'heat_phases' structure.
    """
    full_dict = recipe.model_dump()
    
    # Extract unique tools across all steps from the cookware and implements lists
    extracted_tools = set()
    for step in full_dict.get("steps", []):
        # Gather cookware (List of Requirement objects)
        for req in step.get("cookware", []):
            if req.get("primary"):
                extracted_tools.add(req["primary"].lower().strip())
        
        # Gather implements (List of Requirement objects)
        for req in step.get("implements", []):
            if req.get("primary"):
                extracted_tools.add(req["primary"].lower().strip())
    
    with psycopg.connect(CONN_STR) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO local_recipes (
                    title, 
                    source_url, 
                    equipment_needed, 
                    ingredients, 
                    steps,
                    raw_payload
                ) VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (source_url) DO UPDATE SET
                    title = EXCLUDED.title,
                    equipment_needed = EXCLUDED.equipment_needed,
                    ingredients = EXCLUDED.ingredients,
                    steps = EXCLUDED.steps,
                    raw_payload = EXCLUDED.raw_payload;
            """, (
                full_dict.get("recipe_name", "Untitled Recipe"),
                url,
                json.dumps(list(extracted_tools)),
                json.dumps(full_dict.get("ingredients", [])),
                json.dumps(full_dict.get("steps", [])),
                json.dumps(full_dict)
            ))
            conn.commit()