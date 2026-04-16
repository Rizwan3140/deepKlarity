from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, Dict

from app import models, schemas
from app.database import get_db
from app.llm import generate_meal_plan

router = APIRouter(prefix="/api/meal-planner", tags=["meal-planner"])


@router.post("/", response_model=Dict[str, Any])
def create_meal_plan(request: schemas.MealPlanRequest, db: Session = Depends(get_db)):
    """Generate a combined shopping list for 3–5 selected saved recipes."""
    if not (2 <= len(request.recipe_ids) <= 10):
        raise HTTPException(
            status_code=400,
            detail="Please select between 2 and 10 recipes for the meal plan.",
        )

    recipes = (
        db.query(models.Recipe)
        .filter(models.Recipe.id.in_(request.recipe_ids))
        .all()
    )

    if len(recipes) != len(request.recipe_ids):
        found_ids = {r.id for r in recipes}
        missing = [rid for rid in request.recipe_ids if rid not in found_ids]
        raise HTTPException(
            status_code=404,
            detail=f"Recipes not found: {missing}",
        )

    recipes_data = [
        {
            "title": r.title,
            "ingredients": r.ingredients,
            "shopping_list": r.shopping_list,
        }
        for r in recipes
    ]

    try:
        meal_plan = generate_meal_plan(recipes_data)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    meal_plan["recipes"] = [{"id": r.id, "title": r.title} for r in recipes]
    return meal_plan
