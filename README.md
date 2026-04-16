# Recipe Extractor & Meal Planner

A full-stack application that extracts structured recipe data from blog URLs using web scraping (BeautifulSoup) and AI (Google Gemini via LangChain), stores results in PostgreSQL, and provides a clean tabbed UI for extraction, history, and meal planning.

---

## Project Structure

```
DeepKlarity/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app entry point
│   │   ├── database.py        # SQLAlchemy setup
│   │   ├── models.py          # PostgreSQL models
│   │   ├── schemas.py         # Pydantic schemas
│   │   ├── scraper.py         # BeautifulSoup page scraper
│   │   ├── llm.py             # LangChain + Gemini integration
│   │   └── routers/
│   │       ├── recipes.py     # Recipe CRUD + extraction endpoints
│   │       └── meal_planner.py# Meal plan generation endpoint
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── index.html             # Single-page app (2 tabs + modal)
│   ├── styles.css
│   └── app.js
├── prompts/
│   ├── recipe_extraction.txt  # Main extraction prompt template
│   ├── nutrition_estimation.txt
│   ├── substitutions.txt
│   └── meal_planner.txt
└── sample_data/
    ├── urls.txt               # Example URLs tested
    └── example_output.json    # Example JSON API output
```

---

## Prerequisites

- Python 3.10+
- PostgreSQL 14+
- A free Google Gemini API key — get one at https://aistudio.google.com/app/apikey

---

## Setup

### 1. Clone & create the database

```bash
psql -U postgres -c "CREATE DATABASE recipe_db;"
```

### 2. Configure environment

```bash
cd backend
cp .env.example .env
# Edit .env: set DATABASE_URL and GEMINI_API_KEY
```

### 3. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Run the server

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

The app will be available at **http://localhost:8000**

- Frontend UI: http://localhost:8000/
- API docs (Swagger): http://localhost:8000/docs
- Health check: http://localhost:8000/health

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/recipes/extract` | Scrape URL, extract recipe with LLM, store in DB |
| `GET` | `/api/recipes/` | List all saved recipes (summary) |
| `GET` | `/api/recipes/{id}` | Get full recipe details by ID |
| `DELETE` | `/api/recipes/{id}` | Delete a recipe |
| `POST` | `/api/meal-planner/` | Generate combined shopping list for selected recipes |

### POST /api/recipes/extract

**Request body:**
```json
{ "url": "https://www.allrecipes.com/recipe/23891/grilled-cheese-sandwich/" }
```

**Response:** Full recipe JSON (see `sample_data/example_output.json`)

### POST /api/meal-planner/

**Request body:**
```json
{ "recipe_ids": [1, 2, 3] }
```

**Response:**
```json
{
  "combined_shopping_list": { "dairy": ["3 tbsp butter", "cheddar cheese"], "bakery": ["white bread"] },
  "meal_plan_summary": "...",
  "recipes": [{"id": 1, "title": "Grilled Cheese"}, ...]
}
```

---

## Features

**Tab 1 – Extract Recipe**
- Paste any recipe blog URL
- Backend scrapes the page with BeautifulSoup
- Gemini LLM extracts: title, cuisine, times, servings, difficulty, ingredients (qty/unit/item), instructions
- Generates: nutritional estimate, 3 substitutions, shopping list by category, 3 related recipes
- Results displayed in a card-based layout
- Cached: re-submitting the same URL returns the stored record

**Tab 2 – Saved Recipes (History)**
- Table listing all extracted recipes with title, cuisine, difficulty, date
- "Details" button opens a modal with the full recipe card

**Tab 3 – Meal Planner**
- Select 2–10 saved recipes
- LLM merges and deduplicates shopping lists across recipes
- Generates a combined shopping list grouped by category + a preparation summary

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Invalid URL | HTTP 400 with descriptive message |
| Non-recipe page | HTTP 422 with "content too short" message |
| Network timeout | HTTP 422 with timeout message |
| LLM invalid JSON | HTTP 500 with partial raw response for debugging |
| Recipe not found in DB | HTTP 404 |
| Duplicate URL | Returns existing record (no duplicate processing) |

---

## Testing Steps

1. Start the server (`uvicorn app.main:app --reload`)
2. Open http://localhost:8000 in a browser
3. In Tab 1, paste any URL from `sample_data/urls.txt` and click "Extract Recipe"
4. Verify the card shows ingredients, instructions, nutrition, substitutions, shopping list
5. Switch to Tab 2 — the recipe should appear in the history table
6. Click "Details" — the modal should open with the full recipe
7. Go to Tab 3, check 2+ recipes, click "Generate Meal Plan"
8. Verify a combined shopping list and summary appear

---

## LangChain Prompt Design

All prompt templates are in the `prompts/` folder.

The main extraction uses a **single-shot structured output prompt** that:
- Grounds all extraction in the scraped page text (minimizes hallucination)
- Returns a complete JSON object covering all required fields in one LLM call
- Uses strict output rules (JSON only, no markdown fences) for reliable parsing
- Falls back gracefully with `null` values for fields not found on the page
