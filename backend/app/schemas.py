from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class Ingredient(BaseModel):
    quantity: str
    unit: str
    item: str


class NutritionEstimate(BaseModel):
    calories: int
    protein: str
    carbs: str
    fat: str


class RecipeBase(BaseModel):
    url: str
    title: str
    cuisine: Optional[str] = None
    prep_time: Optional[str] = None
    cook_time: Optional[str] = None
    total_time: Optional[str] = None
    servings: Optional[int] = None
    difficulty: Optional[str] = None
    ingredients: Optional[List[Dict[str, str]]] = None
    instructions: Optional[List[str]] = None
    nutrition_estimate: Optional[Dict[str, Any]] = None
    substitutions: Optional[List[str]] = None
    shopping_list: Optional[Dict[str, List[str]]] = None
    related_recipes: Optional[List[str]] = None


class RecipeCreate(RecipeBase):
    pass


class RecipeResponse(RecipeBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class RecipeSummary(BaseModel):
    id: int
    url: str
    title: str
    cuisine: Optional[str] = None
    difficulty: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ExtractRequest(BaseModel):
    url: str


class MealPlanRequest(BaseModel):
    recipe_ids: List[int]
