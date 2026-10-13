"""Thread-safe paid requests with original inputs, outputs, and complete usage."""
import copy
import json
import math
import threading
import time
from datetime import datetime, timezone

from .common import ResponseFailure, BudgetExceeded, object_schema, validate_json
from .settings import PRICES, EFFORTS, validate_settings
from .fp_cases import fp_hash, FP_GRADING_COST_BASIS


def grading_cost_from_record(record):
    """Use published uncached rates without changing observed cache discounts."""
    if not isinstance(record, dict) or not isinstance(record.get("settings"), dict):
        return None
    model = record["settings"].get("model")
    if model not in PRICES or record.get("mode") == "fixture":
        return None
    inputs, outputs = record.get("input_tokens"), record.get("output_tokens")
    if any(type(value) is not int or value < 0 for value in (inputs, outputs)):
        return None
    prices = PRICES[model]
    try:
        cost = (inputs * prices[0] + outputs * prices[2]) / 1e6
    except OverflowError:
        return None
    return cost if math.isfinite(cost) else None


class TravelAPI:
    mode = "actual_api"
    def __init__(self, client, max_calls=1000, max_usd=2.0):
        if type(max_calls) is not int or max_calls<1:
            raise ValueError("max_calls must be a positive integer.")
        if type(max_usd) not in (int,float) or not math.isfinite(max_usd) or max_usd<=0:
            raise ValueError("max_usd must be a finite positive estimate.")
        self.client = client
        self.max_calls = max_calls
        self.max_usd = max_usd
        self.records = []
        self._lock = threading.Lock()
        self._reserved_usd = 0.0
        self._submitted = 0

    def pending_requests(self):
        """Return submitted requests whose response/accounting is not yet saved."""
        with self._lock:
            return self._submitted - len(self.records)

    def snapshot_records(self, start_index=0):
        """Capture completed records and outstanding requests under one lock.

        A request finishing between separate record and pending-count reads must
        not disappear from both. Pending requests remain unknown-cost attempts.
        """
        with self._lock:
            return dict(records=copy.deepcopy(self.records[start_index:]),
                        pending_requests=self._submitted - len(self.records))

    def json(self, config, instructions, payload, schema, label):
        validate_settings(config)
        text = json.dumps(payload, ensure_ascii=False)
        import tiktoken
        tokens = len(tiktoken.get_encoding("o200k_base").encode(instructions+text+json.dumps(schema)))+1024
        p = PRICES[config["model"]]
        reservation = (tokens*p[0]+config["max_output_tokens"]*p[2])/1e6
        with self._lock:
            spent = sum(r["estimated_usd"] or 0 for r in self.records)
            if any(r["estimated_usd"] is None for r in self.records):
                raise BudgetExceeded("A previous request has unknown cost. Inspect it before authorizing new spending.")
            if self._submitted >= self.max_calls or spent+self._reserved_usd+reservation > self.max_usd:
                raise BudgetExceeded("The explicit call or estimated-dollar guard would be exceeded.")
            self._submitted += 1
            request_number = self._submitted
            self._reserved_usd += reservation
        kwargs = dict(model=config["model"], instructions=instructions, input=text,
            max_output_tokens=config["max_output_tokens"], store=False, service_tier="default",
            text=dict(format=dict(type="json_schema", name="travel_decision", strict=True, schema=schema)))
        if EFFORTS[config["model"]]:
            kwargs["reasoning"] = dict(effort=config["effort"])
        if config["verbosity"] is not None:
            kwargs["text"]["verbosity"] = config["verbosity"]
        for k in ("temperature", "top_p"):
            if config[k] is not None:
                kwargs[k] = config[k]
        row = dict(request_number=request_number, label=label, mode=self.mode,
            settings=copy.deepcopy(config), request_hash=fp_hash(kwargs),
            observed_at=datetime.now(timezone.utc).isoformat(), instructions=instructions,
            payload=copy.deepcopy(payload), status="request_error", input_tokens=None,
            cached_tokens=None, output_tokens=None, reasoning_tokens=None, estimated_usd=None,
            grading_usd=None, grading_cost_basis=FP_GRADING_COST_BASIS,
            raw_response=None)
        start = time.monotonic()
        try:
            response = self.client.responses.create(**kwargs)
            row["raw_response"] = response.model_dump(mode="json")
            row["status"] = response.status
            row["response_id"] = response.id
            row["returned_model"] = response.model
            if response.usage:
                u = response.usage.model_dump()
                it, ot = u["input_tokens"], u["output_tokens"]
                cached = (u.get("input_tokens_details") or {}).get("cached_tokens", 0)
                rt = (u.get("output_tokens_details") or {}).get("reasoning_tokens", 0)
                row.update(input_tokens=it, cached_tokens=cached, output_tokens=ot, reasoning_tokens=rt,
                    estimated_usd=((it-cached)*p[0]+cached*p[1]+ot*p[2])/1e6 if it <= 272000 else None)
                row["grading_usd"] = grading_cost_from_record(row)
            if response.status != "completed":
                raise ResponseFailure("The model response did not complete. No paid retry is automatic.")
            parsed = validate_json(json.loads(response.output_text), schema)
            row["parsed"] = copy.deepcopy(parsed)
            return parsed
        except Exception as exc:
            # Exception messages can contain request details; record only the type.
            row["error_type"] = type(exc).__name__
            raise
        finally:
            row["seconds"] = round(time.monotonic()-start, 4)
            with self._lock:
                self._reserved_usd -= reservation
                self.records.append(row)

    def usage(self, records=None):
        rows = self.records if records is None else records
        result = dict(mode=self.mode, calls=len(rows), grading_cost_basis=FP_GRADING_COST_BASIS)
        for key in ("input_tokens", "cached_tokens", "output_tokens", "reasoning_tokens", "estimated_usd"):
            result[key] = sum(r[key] for r in rows) if all(r[key] is not None for r in rows) else None
        result["actual_request_seconds"] = sum(r["seconds"] for r in rows)
        grading_costs = [grading_cost_from_record(row) for row in rows]
        result["grading_usd"] = sum(grading_costs) if all(cost is not None for cost in grading_costs) else None
        return result


class TravelFixtureAPI:
    """Offline control-flow checks only. These records never receive a model grade."""
    mode = "fixture"
    def __init__(self, responses):
        self.responses = iter(responses)
        self.records = []

    def json(self, config, instructions, payload, schema, label):
        result = next(self.responses)
        validate_json(result, schema)
        self.records.append(dict(label=label, settings=copy.deepcopy(config), mode=self.mode,
            payload=copy.deepcopy(payload), parsed=copy.deepcopy(result), status="fixture",
            input_tokens=None, cached_tokens=None, output_tokens=None, reasoning_tokens=None,
            estimated_usd=None, grading_usd=None, grading_cost_basis=FP_GRADING_COST_BASIS, seconds=0))
        return result

    def usage(self, records=None):
        rows = self.records if records is None else records
        return dict(mode=self.mode, calls=len(rows), input_tokens=None, cached_tokens=None,
                    output_tokens=None, reasoning_tokens=None, estimated_usd=None,
                    grading_usd=None, grading_cost_basis=FP_GRADING_COST_BASIS,
                    actual_request_seconds=0)
