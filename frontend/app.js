const API_BASE = "";  // same-origin; change to "http://localhost:8000" for dev

// ── Utilities ──────────────────────────────────────────────────────────────

function show(el) { el.classList.remove("hidden"); }
function hide(el) { el.classList.add("hidden"); }
function setHTML(el, html) { el.innerHTML = html; }

function showError(el, msg) {
  el.textContent = msg;
  show(el);
}

async function apiFetch(path, options = {}) {
  const res = await fetch(API_BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

// ── Tab Navigation ─────────────────────────────────────────────────────────

const tabBtns = document.querySelectorAll(".tab-btn");
const tabPanels = document.querySelectorAll(".tab-panel");

tabBtns.forEach((btn) => {
  btn.addEventListener("click", () => {
    tabBtns.forEach((b) => b.classList.remove("active"));
    tabPanels.forEach((p) => { p.classList.remove("active"); hide(p); });
    btn.classList.add("active");
    const panel = document.getElementById("tab-" + btn.dataset.tab);
    panel.classList.add("active");
    show(panel);
    if (btn.dataset.tab === "history") loadHistory();
    if (btn.dataset.tab === "meal-planner") loadPlannerRecipes();
  });
});

// ── Recipe Rendering ───────────────────────────────────────────────────────

function diffBadge(difficulty) {
  const d = (difficulty || "").toLowerCase();
  return `<span class="badge difficulty-${d}">${difficulty || "—"}</span>`;
}

function renderRecipe(r) {
  const ingredients = (r.ingredients || [])
    .map(
      (ing) =>
        `<li><span class="ing-qty">${ing.quantity || ""}</span><span class="ing-unit">${ing.unit || ""}</span><span>${ing.item || ""}</span></li>`
    )
    .join("");

  const instructions = (r.instructions || [])
    .map(
      (step, i) =>
        `<li><span class="step-num">${i + 1}</span><span>${step}</span></li>`
    )
    .join("");

  const nutrition = r.nutrition_estimate || {};
  const nutritionHTML = `
    <div class="nutrition-grid">
      <div class="nutrition-item"><div class="nutrition-value">${nutrition.calories ?? "—"}</div><div class="nutrition-label">Calories</div></div>
      <div class="nutrition-item"><div class="nutrition-value">${nutrition.protein ?? "—"}</div><div class="nutrition-label">Protein</div></div>
      <div class="nutrition-item"><div class="nutrition-value">${nutrition.carbs ?? "—"}</div><div class="nutrition-label">Carbs</div></div>
      <div class="nutrition-item"><div class="nutrition-value">${nutrition.fat ?? "—"}</div><div class="nutrition-label">Fat</div></div>
    </div>`;

  const substitutions = (r.substitutions || [])
    .map((s) => `<div class="tag">${s}</div>`)
    .join("");

  const relatedRecipes = (r.related_recipes || [])
    .map((name) => `<div class="tag">${name}</div>`)
    .join("");

  const shoppingList = r.shopping_list || {};
  const shoppingHTML = Object.entries(shoppingList)
    .map(
      ([cat, items]) =>
        `<div class="shopping-category"><h4>${cat}</h4><ul>${items.map((i) => `<li>${i}</li>`).join("")}</ul></div>`
    )
    .join("");

  return `
    <div class="recipe-grid">
      <div class="card recipe-hero">
        <div class="recipe-title">${r.title}</div>
        <div style="color:var(--muted);font-size:.85rem;margin-top:4px"><a href="${r.url}" target="_blank" rel="noopener">${r.url}</a></div>
        <div class="recipe-meta">
          <span class="badge">${r.cuisine || "Unknown cuisine"}</span>
          ${diffBadge(r.difficulty)}
          ${r.prep_time ? `<span class="badge" style="background:#f0fdf4;color:#166534">Prep: ${r.prep_time}</span>` : ""}
          ${r.cook_time ? `<span class="badge" style="background:#fff7ed;color:#9a3412">Cook: ${r.cook_time}</span>` : ""}
          ${r.total_time ? `<span class="badge" style="background:#f0f9ff;color:#075985">Total: ${r.total_time}</span>` : ""}
          ${r.servings ? `<span class="badge" style="background:#faf5ff;color:#6b21a8">Serves ${r.servings}</span>` : ""}
        </div>
      </div>

      <div class="section-card">
        <h3>Ingredients</h3>
        <ul class="ingredient-list">${ingredients || "<li>No ingredients found</li>"}</ul>
      </div>

      <div class="section-card">
        <h3>Nutrition (per serving)</h3>
        ${nutritionHTML}
      </div>

      <div class="section-card" style="grid-column:1/-1">
        <h3>Instructions</h3>
        <ol class="instructions-list">${instructions || "<li>No instructions found</li>"}</ol>
      </div>

      <div class="section-card">
        <h3>Ingredient Substitutions</h3>
        <div class="tag-list">${substitutions || "None suggested"}</div>
      </div>

      <div class="section-card">
        <h3>Related Recipes</h3>
        <div class="tag-list">${relatedRecipes || "None suggested"}</div>
      </div>

      <div class="section-card" style="grid-column:1/-1">
        <h3>Shopping List</h3>
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px">
          ${shoppingHTML || "No shopping list available"}
        </div>
      </div>
    </div>`;
}

// ── TAB 1: Extract Recipe ──────────────────────────────────────────────────

const urlInput = document.getElementById("url-input");
const extractBtn = document.getElementById("extract-btn");
const extractError = document.getElementById("extract-error");
const recipeResult = document.getElementById("recipe-result");
const recipeDisplay = document.getElementById("recipe-display");
const extractLoader = document.getElementById("extract-loader");

extractBtn.addEventListener("click", async () => {
  const url = urlInput.value.trim();
  if (!url) return showError(extractError, "Please enter a URL.");
  if (!url.startsWith("http")) return showError(extractError, "Please enter a valid URL starting with http:// or https://");

  hide(extractError);
  hide(recipeResult);
  show(extractLoader);
  extractBtn.disabled = true;

  try {
    const recipe = await apiFetch("/api/recipes/extract", {
      method: "POST",
      body: JSON.stringify({ url }),
    });
    setHTML(recipeDisplay, renderRecipe(recipe));
    show(recipeResult);
  } catch (err) {
    showError(extractError, err.message);
  } finally {
    hide(extractLoader);
    extractBtn.disabled = false;
  }
});

urlInput.addEventListener("keydown", (e) => { if (e.key === "Enter") extractBtn.click(); });

// ── TAB 2: History ─────────────────────────────────────────────────────────

const historyLoader = document.getElementById("history-loader");
const historyEmpty = document.getElementById("history-empty");
const historyError = document.getElementById("history-error");
const historyTable = document.getElementById("history-table");
const historyTbody = document.getElementById("history-tbody");
const refreshHistoryBtn = document.getElementById("refresh-history-btn");

async function loadHistory() {
  hide(historyEmpty);
  hide(historyError);
  hide(historyTable);
  show(historyLoader);

  try {
    const recipes = await apiFetch("/api/recipes/");
    hide(historyLoader);

    if (!recipes.length) {
      show(historyEmpty);
      return;
    }

    historyTbody.innerHTML = recipes
      .map(
        (r) => `
          <tr>
            <td>${r.id}</td>
            <td style="font-weight:600">${r.title}</td>
            <td>${r.cuisine || "—"}</td>
            <td><span class="diff-badge diff-${(r.difficulty || "").toLowerCase()}">${r.difficulty || "—"}</span></td>
            <td>${formatDate(r.created_at)}</td>
            <td><button class="btn-details" data-id="${r.id}">Details</button></td>
          </tr>`
      )
      .join("");

    show(historyTable);

    historyTbody.querySelectorAll(".btn-details").forEach((btn) => {
      btn.addEventListener("click", () => openModal(btn.dataset.id));
    });
  } catch (err) {
    hide(historyLoader);
    showError(historyError, err.message);
  }
}

refreshHistoryBtn.addEventListener("click", loadHistory);

// ── Modal ──────────────────────────────────────────────────────────────────

const modalOverlay = document.getElementById("modal-overlay");
const modalContent = document.getElementById("modal-content");
const modalClose = document.getElementById("modal-close");

async function openModal(id) {
  setHTML(modalContent, `<div class="loader-container"><div class="spinner"></div><p>Loading…</p></div>`);
  show(modalOverlay);

  try {
    const recipe = await apiFetch(`/api/recipes/${id}`);
    setHTML(modalContent, renderRecipe(recipe));
  } catch (err) {
    setHTML(modalContent, `<p class="error-msg" style="display:block">${err.message}</p>`);
  }
}

modalClose.addEventListener("click", () => hide(modalOverlay));
modalOverlay.addEventListener("click", (e) => { if (e.target === modalOverlay) hide(modalOverlay); });
document.addEventListener("keydown", (e) => { if (e.key === "Escape") hide(modalOverlay); });

// ── TAB 3: Meal Planner ────────────────────────────────────────────────────

const plannerRecipesContainer = document.getElementById("planner-recipes");
const plannerError = document.getElementById("planner-error");
const plannerLoader = document.getElementById("planner-loader");
const generatePlanBtn = document.getElementById("generate-plan-btn");
const mealPlanResult = document.getElementById("meal-plan-result");

async function loadPlannerRecipes() {
  plannerRecipesContainer.innerHTML = "";
  hide(plannerError);
  show(plannerLoader);

  try {
    const recipes = await apiFetch("/api/recipes/");
    hide(plannerLoader);

    if (!recipes.length) {
      plannerRecipesContainer.innerHTML = `<p class="empty-state">No saved recipes yet. Extract some first!</p>`;
      return;
    }

    plannerRecipesContainer.innerHTML = recipes
      .map(
        (r) => `
          <label class="planner-item">
            <input type="checkbox" value="${r.id}" />
            <div class="planner-item-info">
              <div class="planner-item-title">${r.title}</div>
              <div class="planner-item-meta">${r.cuisine || "Unknown"} · ${r.difficulty || "—"}</div>
            </div>
          </label>`
      )
      .join("");
  } catch (err) {
    hide(plannerLoader);
    showError(plannerError, err.message);
  }
}

generatePlanBtn.addEventListener("click", async () => {
  const checked = [...plannerRecipesContainer.querySelectorAll("input[type=checkbox]:checked")];
  const ids = checked.map((c) => parseInt(c.value));

  if (ids.length < 2) return showError(plannerError, "Select at least 2 recipes.");
  if (ids.length > 10) return showError(plannerError, "Select no more than 10 recipes.");

  hide(plannerError);
  hide(mealPlanResult);
  generatePlanBtn.disabled = true;
  generatePlanBtn.textContent = "Generating…";

  try {
    const plan = await apiFetch("/api/meal-planner/", {
      method: "POST",
      body: JSON.stringify({ recipe_ids: ids }),
    });

    const shoppingHTML = Object.entries(plan.combined_shopping_list || {})
      .map(
        ([cat, items]) =>
          `<div class="shopping-category"><h4>${cat}</h4><ul>${items.map((i) => `<li>${i}</li>`).join("")}</ul></div>`
      )
      .join("");

    const recipeTitles = (plan.recipes || []).map((r) => `<span class="tag">${r.title}</span>`).join("");

    mealPlanResult.innerHTML = `
      <div class="section-card" style="margin-top:20px">
        <h3>Selected Recipes</h3>
        <div class="tag-list" style="margin-bottom:16px">${recipeTitles}</div>
        <h3>Combined Shopping List</h3>
        <div class="meal-plan-shopping">${shoppingHTML || "No items"}</div>
        <div class="summary-box">${plan.meal_plan_summary || ""}</div>
      </div>`;
    show(mealPlanResult);
  } catch (err) {
    showError(plannerError, err.message);
  } finally {
    generatePlanBtn.disabled = false;
    generatePlanBtn.textContent = "Generate Meal Plan";
  }
});
