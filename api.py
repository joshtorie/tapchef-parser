from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from parser import parse_raw_recipe
from recipe_scrapers import scrape_me

app = FastAPI()

class URLRequest(BaseModel):
    url: str

@app.post("/parse")
async def parse(req: URLRequest):
    try:
        # 1. Scrape the URL
        scraper = scrape_me(req.url)
        text = f"{scraper.title()}\n\nINGREDIENTS:\n{scraper.ingredients()}\n\nINSTRUCTIONS:\n{scraper.instructions()}"
        
        # 2. Run your existing Logic
        data = parse_raw_recipe(text, req.url)
        
        # 3. Return JSON
        return data.model_dump() 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))