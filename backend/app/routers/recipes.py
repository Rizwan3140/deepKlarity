from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.scraper import scrape_page
from app.llm import extract_recipe

router = APIRouter(prefix="/api/recipes", tags=["recipes"])


@router.post("/extract", response_model=schemas.RecipeResponse, status_code=status.HTTP_201_CREATED)
def extract_recipe_endpoint(request: schemas.ExtractRequest, db: Session = Depends(get_db)):
    """Scrape a recipe URL, extract structured data via LLM, and store it."""
    url = request.url.strip()

    # Return existing record if URL already processed
    existing = db.query(models.Recipe).filter(models.Recipe.url == url).first()
    if existing:
        return existing

    # Scrape page
    try:
        page_text = scrape_page(url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Extract via LLM
    try:
        data = extract_recipe(page_text, url)
    except RuntimeError as e:
        msg = str(e)
        if "RESOURCE_EXHAUSTED" in msg or "429" in msg:
            raise HTTPException(status_code=429, detail="Gemini API quota exceeded. Check your API key or wait and retry.")
        raise HTTPException(status_code=500, detail=msg)

    # Persist to database
    recipe = models.Recipe(
        url=url,
        title=data.get("title") or "Untitled Recipe",
        cuisine=data.get("cuisine"),
        prep_time=data.get("prep_time"),
        cook_time=data.get("cook_time"),
        total_time=data.get("total_time"),
        servings=data.get("servings"),
        difficulty=data.get("difficulty"),
        ingredients=data.get("ingredients"),
        instructions=data.get("instructions"),
        nutrition_estimate=data.get("nutrition_estimate"),
        substitutions=data.get("substitutions"),
        shopping_list=data.get("shopping_list"),
        related_recipes=data.get("related_recipes"),
    )
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    return recipe


@router.get("/", response_model=list[schemas.RecipeSummary])
def list_recipes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Return paginated list of all saved recipes."""
    return (
        db.query(models.Recipe)
        .order_by(models.Recipe.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{recipe_id}", response_model=schemas.RecipeResponse)
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    """Return full details of a single recipe."""
    recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found.")
    return recipe


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(recipe_id: int, db: Session = Depends(get_db)):
    """Delete a recipe from the database."""
    recipe = db.query(models.Recipe).filter(models.Recipe.id == recipe_id).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found.")
    db.delete(recipe)
    db.commit()
