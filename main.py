import json
from parser import parse_raw_recipe

# A messy, unformatted recipe string you might get from a web scraper
messy_web_recipe = """
Easy Honey Garlic Salmon
Tags: seafood, quick, dinner, salmon
Ingredients:
- Two fresh salmon fillets
- 1 tablespoon of olive oil
- 3 tablespoons of raw honey
- 2 garlic cloves, crushed with a knife

Directions:
First, heat your olive oil in a skillet over medium-high heat. Let the oil get hot for about 1 minute.
Put the salmon fillets skin-side down into the pan. Leave it completely alone for 4 minutes so the skin crisps up perfectly.
Turn the heat down to low. Pour the honey and crushed garlic right on top of the salmon. Use a spoon to constantly scoop up the warm honey and pour it back over the salmon for 2 minutes so it glazes beautifully. Watch it like a hawk so the honey doesn't burn! Serve immediately.
"""

if __name__ == "__main__":
    # Updated: Now includes the required source_url argument
    parsed_data = parse_raw_recipe(messy_web_recipe, "https://example.com/honey-garlic-salmon")
    
    # Convert the Python data object into clean, readable text
    clean_json = json.dumps(parsed_data.model_dump(), indent=2)
    
    print("\n✅ Success! Database-Ready Output (Atomic Actions Included):")
    print(clean_json)