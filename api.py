import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from recipe_scrapers import scrape_me

# Import your existing AI logic from your local files
from parser import parse_raw_recipe

app = FastAPI(title="TapChef Ingestion Engine API")

class URLRequest(BaseModel):
    url: str

@app.get("/")
async def root():
    return {"status": "healthy", "engine": "TapChef Kitchen OS Ingestion"}

@app.post("/parse")
async def parse(req: URLRequest):
    try:
        # 1. Extract raw data from the URL using recipe-scrapers
        scraper = scrape_me(req.url)
        
        # Build an exhaustive text block to feed your AI tokenization matrix
        ingredients_list = scraper.ingredients()
        ingredients_block = "\n".join(ingredients_list) if isinstance(ingredients_list, list) else str(ingredients_list)
        
        text_payload = (
            f"Title: {scraper.title()}\n\n"
            f"Description: {scraper.description()}\n\n"
            f"Yield/Servings: {scraper.yields()}\n\n"
            f"Ingredients:\n{ingredients_block}\n\n"
            f"Instructions:\n{scraper.instructions()}"
        )
        
        # 2. Run your existing structural AI parsing logic
        data = parse_raw_recipe(text_payload, req.url)
        
        # Convert Pydantic model or dict from your parser into a standard dictionary
        recipe_dict = data.model_dump() if hasattr(data, "model_dump") else dict(data)
        
        # 3. Inject explicit metadata fields Lovable requires for UI and DB rendering
        recipe_dict["image"] = scraper.image()
        recipe_dict["total_time"] = scraper.total_time()
        recipe_dict["yields"] = scraper.yields()
        recipe_dict["description"] = scraper.description()
        
        # Handle platform-dependent variations for categories/tags safely
        extracted_tags = []
        if hasattr(scraper, "tags") and scraper.tags():
            extracted_tags = scraper.tags()
        elif hasattr(scraper, "category") and scraper.category():
            category = scraper.category()
            extracted_tags = [category] if isinstance(category, str) else category
            
        recipe_dict["tags"] = extracted_tags
        
        # 4. Return the complete, enriched payload to the frontend client
        return recipe_dict
        
    except Exception as e:
        # Raise HTTP 500 error visible in Render logs if any part of the pipeline fails
        raise HTTPException(status_code=500, detail=str(e))