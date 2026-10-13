"""EDITABLE: instructions and role-specific extraction prompts."""
from framework.fp_agents import FP_EXTRACTION_ROLE_PROMPTS
from copy import deepcopy

PROJECT_PROMPT = "Help the traveler repair the trip. Use the available tools, then stop when done."
ROLE_PROMPTS = deepcopy(FP_EXTRACTION_ROLE_PROMPTS)

# TODO: replace PROJECT_PROMPT and/or edit ROLE_PROMPTS for your context design.
# PROJECT_PROMPT is appended to every supplied hybrid extraction request.
# ROLE_PROMPTS applies only to separately scoped, non-Basic hybrid_multi calls
# when the requested domain count meets ROUTE_THRESHOLD. Basic, hybrid_single
# and combined fallback requests use the provided combined extractor instead.
# Inspect the saved request role/instructions to check which prompt was used.
