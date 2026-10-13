"""Capability-aware settings; documented and probed on 2026-09-08.

Sampling controls depend on BOTH model and reasoning effort. Unsupported settings
raise locally, before a paid request.
"""
import math

COURSE_MODELS = ("gpt-5.6-luna", "gpt-5.4-nano", "gpt-5-mini", "gpt-5-nano", "gpt-4o-mini")
EFFORTS = {"gpt-5.6-luna": ("none", "low", "medium", "high", "xhigh", "max"),
           "gpt-5.4-nano": ("none", "low", "medium", "high", "xhigh"),
           "gpt-5-mini": ("minimal", "low", "medium", "high"),
           "gpt-5-nano": ("minimal", "low", "medium", "high"), "gpt-4o-mini": ()}
PRICES = {"gpt-5.6-luna": (.20, .02, 1.20), "gpt-5.4-nano": (.20, .02, 1.25),
          "gpt-5-mini": (.25, .025, 2.), "gpt-5-nano": (.05, .005, .40),
          "gpt-4o-mini": (.15, .075, .60)}


def settings(model="gpt-5-nano", **changes):
    if model not in COURSE_MODELS:
        raise ValueError("Choose a course model.")
    result = dict(model=model, effort=None if model == "gpt-4o-mini" else "low",
                  verbosity=None if model == "gpt-4o-mini" else "low",
                  max_output_tokens=1024, temperature=None, top_p=None)
    if set(changes)-set(result):
        raise ValueError(f"Unknown settings: {sorted(set(changes)-set(result))}")
    result.update(changes)
    validate_settings(result)
    return result


def validate_settings(config):
    expected = {"model", "effort", "verbosity", "max_output_tokens", "temperature", "top_p"}
    if set(config) != expected:
        raise ValueError("Use settings() to create a complete configuration.")
    model = config["model"]
    if model not in COURSE_MODELS:
        raise ValueError("Model is not in the course allowlist.")
    effort = config["effort"]
    if (EFFORTS[model] and effort not in EFFORTS[model]) or (not EFFORTS[model] and effort is not None):
        raise ValueError(f"reasoning.effort for {model}: {EFFORTS[model] or 'not supported; use None'}")
    verbosity = config["verbosity"]
    if verbosity not in (None, "low", "medium", "high") or (model == "gpt-4o-mini" and verbosity is not None):
        raise ValueError("text.verbosity supports low/medium/high on the GPT-5 course models; use None for GPT-4o mini.")
    cap = config["max_output_tokens"]
    if type(cap) is not int or not 16 <= cap <= 4096:
        raise ValueError("The classroom output budget is 16–4096 tokens (not the model's maximum).")
    sampling_ok = model == "gpt-4o-mini" or (model in ("gpt-5.6-luna", "gpt-5.4-nano") and effort == "none")
    for name, high in (("temperature", 2), ("top_p", 1)):
        value = config[name]
        if value is not None:
            if not sampling_ok:
                raise ValueError(f"{name} is not supported for {model} with effort={effort}. It will not be silently dropped.")
            if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= high:
                raise ValueError(f"{name} must be a finite number in [0, {high}].")
    if config["temperature"] is not None and config["top_p"] is not None:
        raise ValueError("For a controlled classroom experiment, set temperature OR top_p, not both. This is a course rule.")
    return config


def capability_rows():
    return [dict(model=m, reasoning_effort=list(EFFORTS[m]) or "unsupported",
                 verbosity="unsupported" if m == "gpt-4o-mini" else "low / medium / high",
                 sampling=("temperature / top_p" if m == "gpt-4o-mini" else
                           "only with effort=none" if m in ("gpt-5.6-luna", "gpt-5.4-nano") else "unsupported"),
                 structured_outputs=True, classroom_output_tokens="16–4096",
                 input_usd_per_million=PRICES[m][0], output_usd_per_million=PRICES[m][2]) for m in COURSE_MODELS]
