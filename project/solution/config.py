"""EDITABLE: model, supported controls and solver-policy budgets."""
from framework.settings import settings
from framework.fp_agents import travel_config
from . import prompts

MODEL = "gpt-5.6-luna"
EFFORT = "low"
VERBOSITY = "low"
MAX_OUTPUT_TOKENS = 4096
TEMPERATURE = None
TOP_P = None
ARCHITECTURE = "hybrid_multi"
# False freezes model-extracted fields after the first interpretation in the hybrid.
# True enables selective re-interpretation; live observations still update in both.
REFRESH_CONTEXT = False
CONCURRENT_INVESTIGATORS = True
ROUTE_THRESHOLD = 1
MAX_DECISIONS = 12
FORECAST_STRATEGY = "precaution"  # precaution, cheapest, or flexible


def make_config():
    """Create the evaluated configuration; None controls are omitted."""
    return travel_config(architecture=ARCHITECTURE, prompt=prompts.PROJECT_PROMPT,
        model_settings=settings(model=MODEL, effort=EFFORT, verbosity=VERBOSITY,
            max_output_tokens=MAX_OUTPUT_TOKENS, temperature=TEMPERATURE, top_p=TOP_P),
        route_threshold=ROUTE_THRESHOLD, max_decisions=MAX_DECISIONS,
        refresh_context=REFRESH_CONTEXT, concurrent_investigators=CONCURRENT_INVESTIGATORS,
        extraction_prompts=prompts.ROLE_PROMPTS, forecast_strategy=FORECAST_STRATEGY)
