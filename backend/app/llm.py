import json
import os
import re
from typing import Any, Dict, List

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyD5UFMwtGp9eY-XcCwS_CSwAYleSB7VkMs")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


def _get_llm() -> ChatGoogleGenerativeAI:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set in environment variables.")
    return ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        google_api_key=GEMINI_API_KEY,
        temperature=0.2,
    )


RECIPE_EXTRACTION_TEMPLATE = """You are an expert recipe analyst. Given the raw text scraped from a recipe blog page, extract and generate structured data.

SCRAPED PAGE TEXT:
{page_text}

SOURCE URL: {url}

Your task is to return a single valid JSON object with ALL of the following fields. Do NOT include markdown code fences or any text outside the JSON.

{{
  "title": "Recipe title as a string",
  "cuisine": "Cuisine type (e.g., Italian, American, Indian). Infer if not explicit.",
  "prep_time": "Preparation time as a string (e.g., '10 mins')",
  "cook_time": "Cooking time as a string (e.g., '20 mins')",
  "total_time": "Total time as a string (e.g., '30 mins')",
  "servings": <integer number of servings>,
  "difficulty": "one of: easy, medium, hard — based on technique complexity and time",
  "ingredients": [
    {{"quantity": "amount", "unit": "unit of measurement or empty string", "item": "ingredient name"}}
  ],
  "instructions": ["Step 1 text", "Step 2 text"],
  "nutrition_estimate": {{
    "calories": <integer per serving>,
    "protein": "Xg",
    "carbs": "Xg",
    "fat": "Xg"
  }},
  "substitutions": [
    "Substitution suggestion 1",
    "Substitution suggestion 2",
    "Substitution suggestion 3"
  ],
  "shopping_list": {{
    "dairy": ["item1"],
    "produce": ["item2"],
    "pantry": ["item3"],
    "meat": ["item4"],
    "bakery": ["item5"]
  }},
  "related_recipes": ["Recipe name 1", "Recipe name 2", "Recipe name 3"]
}}

Rules:
- Base ALL extractions strictly on the scraped text. Do not invent ingredients or steps not present.
- For nutrition, substitutions, shopping list, and related recipes — generate reasonable estimates grounded in the extracted recipe.
- Only include shopping_list categories that have items. Omit empty categories.
- Return exactly 3 substitutions and 3 related recipes.
- If a field cannot be determined from the text, use null for strings and 0 for integers.
- Return ONLY the JSON object. No extra text."""


MEAL_PLAN_TEMPLATE = """You are a meal planning assistant. Given a list of recipes, generate a combined shopping list that merges and deduplicates ingredients across all recipes.

RECIPES:
{recipes_json}

Return a single valid JSON object with this structure. No markdown fences, no extra text:

{{
  "combined_shopping_list": {{
    "dairy": ["merged item with combined quantity"],
    "produce": ["item"],
    "pantry": ["item"],
    "meat": ["item"],
    "bakery": ["item"]
  }},
  "meal_plan_summary": "A 2-3 sentence summary of this meal plan combination and any preparation tips."
}}

Rules:
- Merge quantities for the same ingredient (e.g., "2 tbsp butter" + "1 tbsp butter" = "3 tbsp butter").
- Only include categories that have items.
- Return ONLY valid JSON."""


def _extract_json(text: str) -> Dict[str, Any]:
    """Strip markdown fences and parse JSON from LLM response."""
    text = text.strip()
    # Remove ```json ... ``` or ``` ... ``` wrappers
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def extract_recipe(page_text: str, url: str) -> Dict[str, Any]:
    """Call LLM to extract full recipe data from scraped page text."""
    llm = _get_llm()
    prompt = PromptTemplate(
        input_variables=["page_text", "url"],
        template=RECIPE_EXTRACTION_TEMPLATE,
    )
    chain = prompt | llm
    result = chain.invoke({"page_text": page_text, "url": url})
    raw = result.content if hasattr(result, "content") else str(result)

    try:
        return _extract_json(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"LLM returned invalid JSON: {e}\nRaw response:\n{raw[:500]}")


def generate_meal_plan(recipes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate a combined shopping list for a set of saved recipes."""
    llm = _get_llm()
    prompt = PromptTemplate(
        input_variables=["recipes_json"],
        template=MEAL_PLAN_TEMPLATE,
    )
    chain = prompt | llm
    recipes_json = json.dumps(
        [{"title": r.get("title"), "ingredients": r.get("ingredients"), "shopping_list": r.get("shopping_list")} for r in recipes],
        indent=2,
    )
    result = chain.invoke({"recipes_json": recipes_json})
    raw = result.content if hasattr(result, "content") else str(result)

    try:
        return _extract_json(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"LLM returned invalid JSON for meal plan: {e}\nRaw:\n{raw[:500]}")
