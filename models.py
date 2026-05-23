from pydantic import BaseModel, Field
from typing import List, Optional, Literal

# Standardized culinary units
ValidUnits = Literal[
    "cup", "tbsp", "tsp", "oz", "g", "ml", "lb", "pinch", 
    "unit", "clove", "can", "bunch", "dash", "item", "kg"
]

# --- 1. The Unified Requirement Pattern ---
class Requirement(BaseModel):
    primary: str = Field(description="The primary item name, e.g., 'Pot', 'Butter'.")
    alternatives: List[str] = Field(default_factory=list, description="Valid substitutions, e.g., ['Dutch Oven', 'Margarine'].")

# --- 2. Heat State Machine ---
class HeatPhase(BaseModel):
    heat_setting: Optional[Literal["low", "medium-low", "medium", "medium-high", "high"]] = Field(
        None, description="The burner dial position."
    )
    target_state: Optional[str] = Field(
        None, description="The outcome (e.g., 'simmer', 'boil', 'keep warm')."
    )
    duration_context: Optional[str] = Field(
        None, description="Context for this phase (e.g., 'bring to boil', 'until serving')."
    )

# --- 3. Atomic Action System ---
class Action(BaseModel):
    text: str = Field(description="The specific imperative instruction.")
    action_type: Literal["add", "cook", "transfer", "wait", "season", "other"] = Field(
        description="Categorization for UI icons."
    )
    is_timer: bool = Field(default=False, description="True if this action implies a duration.")
    duration_minutes: Optional[int] = Field(None, description="The timeframe for cook/wait actions.")

# --- 4. Ingredient Definitions (The Pantry) ---
class IngredientToken(BaseModel):
    id: str = Field(description="Lowercase joined name (kebab-case), e.g., 'extra-virgin-olive-oil'")
    name: str = Field(description="Clean capitalized name, e.g., 'Extra Virgin Olive Oil'")
    amount: Optional[float] = Field(None, description="The number quantity")
    unit: Optional[ValidUnits] = Field(None, description="Must match the ValidUnits list")
    prep_state: Optional[str] = Field(None, description="e.g., 'minced', 'cubed'")

# --- 5. Step Usage ---
class IngredientRequirement(Requirement):
    id: str = Field(description="Matches the ingredient id exactly from the ingredients list")
    amount: Optional[float] = None
    unit: Optional[ValidUnits] = None
    prep_state: Optional[str] = None
    role: str = Field(description="Single-word function, e.g., 'fat', 'aromatic'")

class CookingStep(BaseModel):
    step_number: int
    step_summary: str = Field(description="High-level title for the step.")
    actions: List[Action] = Field(description="Chronological, atomic actions for tap-to-advance.")
    
    active_time_minutes: int
    passive_time_minutes: int
    requires_continuous_attention: bool
    
    # Robust Requirement Lists
    cookware: List[Requirement] = Field(default_factory=list)
    implements: List[Requirement] = Field(default_factory=list)
    ingredients_used: List[IngredientRequirement] = Field(default_factory=list)
    
    # Heat and Temp
    heat_phases: List[HeatPhase] = Field(default_factory=list)
    target_temperature: Optional[int] = Field(None)
    temp_unit: Optional[str] = Field(None)

class RecipeSchema(BaseModel):
    recipe_name: str
    source_url: str
    tags: List[str]
    ingredients: List[IngredientToken]
    steps: List[CookingStep]