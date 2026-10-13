"""EDITABLE: routing, memory, planning and the agent interaction loop.

Keep additional policy functions/classes here. All model calls must use api.json;
all actions must use the supplied world interface. Do not import the evaluator,
read future events, inspect _spec/_rules, or choose actions by case-ID lookup.
"""
from framework.fp_agents import run_travel_agent as supplied_agent, travel_route


def route(observation, memory):
    """Choose transport, hotel and/or traveler from observed changes.

    The supplied loop passes a copy of its routing metadata, not its complete
    parsed trip state. Return domain names; edits to this argument do not persist.
    """
    return travel_route(observation, memory)


def solve(world, api, config, route_fn):
    """Retain the supplied agent, or implement your own observed-information loop.

    The delegate already owns episode-local document, trip-state, routing and
    search caches. Replace this body for a custom memory format or update policy;
    keep helper functions/classes in this file and initialize memory inside solve.
    Return serializable traces, working_memory and context for inspection. Memory
    content is not a separate scoring criterion; actual outcomes are evaluated.
    """
    return supplied_agent(world, api, config, route_fn)
