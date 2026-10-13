"""Outcome-only evaluation, partial reports, and cost-calibrated automatic grades."""
import copy
import time
import marshal
import math
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from .fp_cases import (fp_hash, travel_case_fingerprints, FP_VERSION, FP_OUTCOME_POINTS,
                       FP_SCORE_VERSION, FP_OUTCOME_MAX, FP_EFFICIENCY_MAX, FP_SCORE_MAX,
                       FP_GRADING_COST_BASIS)
from .fp_api import grading_cost_from_record
from .fp_world import TravelWorld
from .fp_agents import run_travel_agent, travel_route


def travel_policy_fingerprint(config,route_fn):
    """Detect edits in the current runtime, not authorship or output authenticity."""
    return fp_hash(dict(config=config,route_bytecode=marshal.dumps(route_fn.__code__).hex()))


def evaluate_travel(cases, api, config, repeats=1, route_fn=travel_route, concurrency=3,
                    case_workers=1, progress=None, solver_fn=None):
    if type(repeats) is not int or repeats < 1:
        raise ValueError("Choose a positive repeat count.")
    if not cases or type(case_workers) is not int or case_workers<1:
        raise ValueError("Provide cases and a positive case_workers count.")
    result = dict(version=FP_VERSION, scoring_version=FP_SCORE_VERSION,
        grading_cost_basis=FP_GRADING_COST_BASIS,
        status="running", config=copy.deepcopy(config),
        route_source=None, configuration_fingerprint=fp_hash(config),
        policy_fingerprint=travel_policy_fingerprint(config,route_fn),
        case_fingerprints=travel_case_fingerprints(cases), distinct_cases=len(cases),
        concurrency=concurrency, case_workers=case_workers,
        situations=len({c["family"] for c in cases}), repeats=repeats, rows=[],
        requests=[], complete=False, mode=api.mode if api and config["architecture"]!="rules" else "deterministic")
    import inspect
    try:
        result["route_source"] = inspect.getsource(route_fn)
    except (OSError, TypeError):
        result["route_source"] = "Source unavailable; keep the executed routing cell in the submitted notebook."
    start = time.monotonic()
    start_records = len(api.records) if api else 0
    jobs = [(copy.deepcopy(c), repeat) for repeat in range(repeats) for c in cases]
    pending_observed_after_solver = 0
    def run(job):
        case, repeat = job
        world = TravelWorld(case, concurrency=concurrency)
        failed = None
        try:
            solver = (solver_fn or run_travel_agent)(world, api, config, route_fn)
            if not isinstance(solver, dict):
                raise TypeError("solve must return a JSON-serializable dictionary.")
            json.dumps(solver, allow_nan=False)
        except Exception as exc:
            failed = type(exc).__name__
            solver = dict(traces=[], working_memory={}, context={})
            if not world.finished:
                world.call("finish")
        row = world.evaluate()
        row.update(repeat=repeat+1, error_type=failed, solver=solver)
        return row
    # Every world is isolated. Paid requests can overlap across cases; each
    # case's virtual chronology and tool ordering remain deterministic.
    if case_workers > 1:
        with ThreadPoolExecutor(max_workers=case_workers) as pool:
            futures={pool.submit(run,job):i for i,job in enumerate(jobs)}
            completed={}
            for future in as_completed(futures):
                row=future.result();completed[futures[future]]=row
                if progress:progress(row)
            rows=[completed[i] for i in range(len(jobs))]
    else:
        rows = []
        for job in jobs:
            row = run(job)
            rows.append(row)
            # A sequential solver must join its own model requests before
            # returning. Do not start another episode with unaccounted calls.
            pending = api.pending_requests() if api and hasattr(api, "pending_requests") else 0
            pending_observed_after_solver = max(pending_observed_after_solver, pending)
            if progress:
                progress(row)
            if pending:
                break
            if row["error_type"] in ("APITimeoutError", "APIConnectionError", "AuthenticationError", "RateLimitError", "BudgetExceeded"):
                break
    result["rows"] = rows
    if api and hasattr(api, "snapshot_records"):
        snapshot = api.snapshot_records(start_records)
        result["requests"] = snapshot["records"]
        pending = snapshot["pending_requests"]
    else:
        result["requests"] = copy.deepcopy(api.records[start_records:]) if api else []
        pending = 0
    result["usage"] = api.usage(result["requests"]) if api else dict(mode="deterministic", calls=0,
        input_tokens=0, cached_tokens=0, output_tokens=0, reasoning_tokens=0, estimated_usd=0,
        actual_request_seconds=0, grading_usd=0, grading_cost_basis=FP_GRADING_COST_BASIS)
    result["usage"]["mode"]=result["mode"]
    result["usage"]["pending_count"] = pending
    result["pending_requests"] = pending
    result["pending_observed_after_solver"] = pending_observed_after_solver
    if pending:
        # Count submitted attempts while retaining actual completed records.
        # Missing responses cannot be reported as free calls or a numeric cost.
        result["usage"]["calls"] += pending
        for key in ("input_tokens", "cached_tokens", "output_tokens", "reasoning_tokens", "estimated_usd", "grading_usd", "actual_request_seconds"):
            result["usage"][key] = None
    infrastructure = any(r["error_type"] in ("APITimeoutError", "APIConnectionError", "AuthenticationError", "RateLimitError", "BudgetExceeded") for r in rows)
    result["complete"] = len(rows) == len(jobs) and not infrastructure and not pending and not pending_observed_after_solver
    result["status"] = "complete" if result["complete"] else "interrupted"
    result.update(travel_outcome_summary(rows))
    result["tiers"] = travel_tier_summary(rows)
    result["wall_seconds"] = round(time.monotonic()-start, 3)
    return result


def travel_outcome_summary(rows):
    """Aggregate the published outcome checks; efficiency is always bank-wide."""
    components = {key: sum(row["components"][key] for row in rows)/len(rows) if rows else None
                  for key in FP_OUTCOME_POINTS}
    points = {key: weight*components[key] if rows else None
              for key, weight in FP_OUTCOME_POINTS.items()}
    outcome = sum(points.values()) if rows else None
    return dict(episodes=len(rows), components=components, criterion_points=points,
        outcome_points=outcome, outcome_max=FP_OUTCOME_MAX,
        quality=outcome/FP_OUTCOME_MAX if rows else None,
        success_rate=sum(row["success"] for row in rows)/len(rows) if rows else None,
        successful_episodes=sum(row["success"] for row in rows),
        mean_net_transport_spend_usd=sum(row.get("net_transport_spend_usd",0) for row in rows)/len(rows) if rows else None,
        mean_virtual_minutes=sum(row["virtual_minutes"] for row in rows)/len(rows) if rows else None)


def travel_tier_summary(rows):
    """Same 90-point outcome rubric for each tier; no duplicated efficiency term."""
    groups = {}
    for row in rows:
        groups.setdefault(row.get("tier", "reactive"), []).append(row)
    summaries = {tier: travel_outcome_summary(group) for tier, group in groups.items()}
    for summary in summaries.values():
        share = summary["episodes"]/len(rows)
        summary["outcome_contribution"] = summary["outcome_points"]*share
        summary["contribution_max"] = FP_OUTCOME_MAX*share
    return summaries


def rescore_travel_result(recorded):
    """Explicitly reweight recorded checks; retain API usage, actions and completeness.

    This performs no model request or simulator replay. Callers must preserve the
    original record and identify this operation as a rescore, not a new experiment.
    The baseline check in grade_travel still enforces the exact bank and protocol.
    """
    if recorded.get("version") != FP_VERSION or not recorded.get("rows"):
        raise ValueError("Rescoring requires recorded rows from the current case-bank version.")
    result = copy.deepcopy(recorded)
    for row in result["rows"]:
        components = row["components"]
        if any(not isinstance(components[key], (int, float))
               or not math.isfinite(components[key]) or not 0 <= components[key] <= 1
               for key in FP_OUTCOME_POINTS):
            raise ValueError("Recorded outcome components must be finite values in [0, 1].")
        row["outcome_points"] = sum(weight*components[key] for key, weight in FP_OUTCOME_POINTS.items())
        row["outcome_max"] = FP_OUTCOME_MAX
        row["quality"] = round(row["outcome_points"]/FP_OUTCOME_MAX, 9)
        row["scoring_version"] = FP_SCORE_VERSION
    result["scoring_version"] = FP_SCORE_VERSION
    result["grading_cost_basis"] = FP_GRADING_COST_BASIS
    usage = result.setdefault("usage", {})
    usage["grading_cost_basis"] = FP_GRADING_COST_BASIS
    requests = result.get("requests")
    deterministic_records = requests is None or (isinstance(requests, list) and all(
        isinstance(request, dict) and request.get("mode") == "deterministic" for request in requests))
    if result.get("mode") == "deterministic" and usage.get("calls") == 0 and deterministic_records:
        usage["grading_usd"] = 0
    elif (result.get("mode") == "actual_api" and isinstance(requests, list)
            and type(usage.get("calls")) is int and usage["calls"] == len(requests)):
        costs = [grading_cost_from_record(request) for request in requests]
        consistent = all(cost is not None for cost in costs)
        for key in ("input_tokens", "output_tokens"):
            if consistent and usage.get(key) != sum(request[key] for request in requests):
                consistent = False
        usage["grading_usd"] = sum(costs) if consistent else None
    else:
        # Aggregates alone cannot price a mixture of models or prove which
        # requests were made. Unknown records do not become free work.
        usage["grading_usd"] = None
    result.update(travel_outcome_summary(result["rows"]))
    result["tiers"] = travel_tier_summary(result["rows"])
    return result

def grade_travel(result, baseline):
    if not result.get("complete"):
        raise ValueError("Final evaluation is incomplete or interrupted. No numeric grade is available.")
    if result.get("pending_requests", 0) or result.get("pending_observed_after_solver", 0) or result.get("usage", {}).get("pending_count", 0):
        raise ValueError("Unfinished model requests cannot receive a numeric grade.")
    if result["mode"] == "fixture" or result["usage"]["estimated_usd"] is None:
        raise ValueError("Fixtures and unknown API costs cannot receive a measured grade.")
    if result.get("scoring_version") != FP_SCORE_VERSION:
        raise ValueError("Scoring version mismatch. Explicitly rescore preserved outcomes before grading.")
    if baseline.get("version") != result["version"] or baseline.get("case_fingerprints") != result["case_fingerprints"] or baseline.get("repeats") != result["repeats"]:
        raise ValueError("The baseline must match this case bank, version, and repeat protocol.")
    if result.get("concurrency",3)!=baseline.get("concurrency",3):
        raise ValueError("The common tool concurrency must match the recorded baseline.")
    if (baseline.get("scoring_version") != FP_SCORE_VERSION
            or baseline.get("grading_cost_basis") != FP_GRADING_COST_BASIS
            or result.get("grading_cost_basis") != FP_GRADING_COST_BASIS
            or result["usage"].get("grading_cost_basis") != FP_GRADING_COST_BASIS):
        raise ValueError("Use the current cache-neutral grading cost basis and baseline.")
    B = baseline.get("grading_usd")
    S = result["usage"].get("grading_usd")
    if not isinstance(B, (int,float)) or not math.isfinite(B) or B <= 0:
        raise ValueError("A positive cache-neutral baseline grading cost is required.")
    if not isinstance(S, (int,float)) or not math.isfinite(S) or S < 0:
        raise ValueError("Solver grading cost must be known, finite and nonnegative.")
    observed_baseline, observed_solver = baseline.get("estimated_usd"), result["usage"].get("estimated_usd")
    if any(type(cost) not in (int, float) or not math.isfinite(cost) or cost < 0
           for cost in (observed_baseline, observed_solver)) or observed_baseline <= 0:
        raise ValueError("Observed baseline and solver API costs must be finite and nonnegative; baseline cost must be positive.")
    if any(not isinstance(result["components"][key], (int,float))
           or not math.isfinite(result["components"][key])
           or not 0 <= result["components"][key] <= 1 for key in FP_OUTCOME_POINTS):
        raise ValueError("Outcome components must be finite values in [0, 1].")
    points={k:FP_OUTCOME_POINTS[k]*result["components"][k] for k in FP_OUTCOME_POINTS}
    outcome = sum(points.values())
    points["efficiency"] = FP_EFFICIENCY_MAX*min(1,B/max(S,1e-12))
    raw=sum(points.values())
    return dict(scoring_version=FP_SCORE_VERSION, grading_cost_basis=FP_GRADING_COST_BASIS,max_score=FP_SCORE_MAX,
        outcome_max=FP_OUTCOME_MAX,efficiency_max=FP_EFFICIENCY_MAX,outcome_points=outcome,
        quality=outcome/FP_OUTCOME_MAX,success_rate=result["success_rate"],
        criterion_max_points=dict(FP_OUTCOME_POINTS,efficiency=FP_EFFICIENCY_MAX),
        criterion_points=points,tiers=copy.deepcopy(result.get("tiers", {})),
        baseline_usd=observed_baseline,solver_usd=observed_solver,
        baseline_grading_usd=B,solver_grading_usd=S,raw_score=raw,score=min(FP_SCORE_MAX,raw),
        usage=result["usage"],mean_virtual_minutes=result["mean_virtual_minutes"])


def combine_travel_results(public, hidden):
    """Equal-sized banks: concatenate all episodes and costs; no best-of selection."""
    if public.get("scoring_version") != FP_SCORE_VERSION or hidden.get("scoring_version") != FP_SCORE_VERSION:
        raise ValueError("Rescore both banks to the current scoring version before combining.")
    if public["version"]!=hidden["version"] or public["repeats"]!=hidden["repeats"] or public["concurrency"]!=hidden["concurrency"]:
        raise ValueError("Public and hidden protocols must match.")
    if public["policy_fingerprint"]!=hidden["policy_fingerprint"]:
        raise ValueError("Freeze one submitted policy for both banks.")
    if public["mode"]!=hidden["mode"]:
        raise ValueError("Do not mix fixtures, actual API runs and deterministic runs.")
    if public.get("grading_cost_basis") != FP_GRADING_COST_BASIS or hidden.get("grading_cost_basis") != FP_GRADING_COST_BASIS:
        raise ValueError("Both banks must use the current cache-neutral grading cost basis.")
    result=copy.deepcopy(public)
    result["rows"]+=copy.deepcopy(hidden["rows"])
    result["requests"]+=copy.deepcopy(hidden["requests"])
    result["case_fingerprints"]+=hidden["case_fingerprints"]
    result["distinct_cases"]+=hidden["distinct_cases"]
    result["complete"]=public["complete"] and hidden["complete"]
    result["status"]="complete" if result["complete"] else "interrupted"
    result.update(travel_outcome_summary(result["rows"]))
    for key in ("calls","input_tokens","cached_tokens","output_tokens","reasoning_tokens","estimated_usd","grading_usd","actual_request_seconds"):
        a,b=public["usage"].get(key),hidden["usage"].get(key)
        result["usage"][key]=a+b if a is not None and b is not None else None
    result["usage"]["pending_count"] = public["usage"].get("pending_count", 0) + hidden["usage"].get("pending_count", 0)
    result["pending_requests"] = public.get("pending_requests", 0) + hidden.get("pending_requests", 0)
    result["pending_observed_after_solver"] = max(public.get("pending_observed_after_solver", 0), hidden.get("pending_observed_after_solver", 0))
    result["tiers"]=travel_tier_summary(result["rows"])
    result["mean_virtual_minutes"]=sum(r["virtual_minutes"] for r in result["rows"])/len(result["rows"])
    result["wall_seconds"]+=hidden["wall_seconds"]
    return result
