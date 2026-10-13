"""Select published cases or load student-authored local diagnostic cases."""
import copy
import json
import math
from pathlib import Path

from .fp_cases import FP_DEV_CASES, FP_PUBLIC_CASES, FP_VERSION, FP_TIERS
from .fp_world import TravelWorld


def select_cases(split="dev", tier=None):
    if split not in ("dev", "public"):
        raise ValueError("Choose the dev or public split.")
    if tier is not None and tier not in FP_TIERS:
        raise ValueError("Choose basic, reactive or forecast difficulty.")
    cases = FP_DEV_CASES if split == "dev" else FP_PUBLIC_CASES
    return copy.deepcopy([case for case in cases if tier is None or case["difficulty"] == tier])


def case_catalog(cases):
    """Show initial requests and source titles, without future events or labels."""
    return [dict(case_id=case["case_id"], tier=case["difficulty"],
        initial_request=case["initial_request"], source_titles=[dict(id=source["id"], title=source["title"])
            for source in case["documents"].values() if source["id"] != "hotel-bulletin"])
        for case in cases]


def _reject_constant(value):
    raise ValueError("Local case JSON must use finite numbers.")


def _nonnegative(value, integer=False):
    return type(value) in ((int,) if integer else (int, float)) and math.isfinite(value) and value >= 0


def load_local_cases(path):
    """Validate structural inputs before paid calls; prose meaning is not checked."""
    try:
        cases = json.loads(Path(path).read_text(), parse_constant=_reject_constant)
    except (OSError, ValueError) as error:
        raise ValueError("Could not read local cases as JSON: " + str(error)) from error
    if not isinstance(cases, list) or not cases:
        raise ValueError("Local cases must be a nonempty JSON list of complete case objects.")
    required = set(FP_DEV_CASES[0])
    seen = set()
    for index, case in enumerate(cases, 1):
        prefix = "Local case " + str(index) + ": "
        if not isinstance(case, dict) or required - set(case):
            raise ValueError(prefix + "export a complete dev/public case as the starting template.")
        case_id = case["case_id"]
        if not isinstance(case_id, str) or not case_id.strip() or case_id in seen:
            raise ValueError(prefix + "case_id must be a nonempty, unique string.")
        seen.add(case_id)
        if case["version"] != FP_VERSION or case["difficulty"] not in FP_TIERS:
            raise ValueError(prefix + "use the current project version and a published difficulty.")
        if not isinstance(case["initial_request"], str) or not case["initial_request"].strip():
            raise ValueError(prefix + "initial_request must be nonempty text.")
        try:
            if not _nonnegative(case["budget"]) or not _nonnegative(case["deadline"], integer=True):
                raise ValueError("budget and meeting clock minute must be finite and nonnegative.")
            if any(not _nonnegative(case["transfer"][mode], integer=True) for mode in ("flight", "train", "coach")):
                raise ValueError("transfers must be nonnegative integer minutes for every mode.")
            for field in ("consent", "waiver_type", "waiver_code"):
                if not isinstance(case[field], str) or not case[field].strip():
                    raise ValueError("approval and waiver evidence strings must be nonempty.")
            documents = case["documents"]
            if not isinstance(documents, dict) or not {"hotel-terms", "hotel-bulletin", "transport-guide", "traveler-profile"} <= set(documents):
                raise ValueError("keep the required source documents.")
            for source_id, source in documents.items():
                if source["id"] != source_id or not isinstance(source["text"], str) or not source["text"].strip() or not isinstance(source["title"], str) or type(source["version"]) is not int or source["version"] < 1:
                    raise ValueError("source IDs, titles, text and integer versions must be consistent.")
            if documents["hotel-bulletin"]["version"] != 2:
                raise ValueError("the current simulator starts hotel-bulletin at version 2.")
            options = case["options"]
            if not isinstance(options, list) or not options:
                raise ValueError("include at least one transport offer.")
            option_ids = [option["id"] for option in options]
            if any(not isinstance(value, str) or not value for value in option_ids) or len(set(option_ids)) != len(option_ids):
                raise ValueError("offer IDs must be nonempty and unique.")
            for option in options:
                if option["mode"] not in ("flight", "train", "coach"):
                    raise ValueError("use published transport modes.")
                if not _nonnegative(option["price"]) or not _nonnegative(option["arrival_minute"], integer=True) or not _nonnegative(option["inventory"], integer=True):
                    raise ValueError("offer prices, arrival clock minutes and seat counts must be nonnegative.")
                opening, closing = option.get("available_from", 0), option["expires_at"]
                if not _nonnegative(opening, integer=True) or not _nonnegative(closing, integer=True) or not opening < closing <= 36:
                    raise ValueError("offer windows need integer minutes: 0 <= opening < closing <= 36.")
            if case["horizon"] != 36 or not isinstance(case["events"], list):
                raise ValueError("keep the 36-minute horizon and an event list.")
            previous = 0
            for event in case["events"]:
                at = event["at"]
                if type(at) is not int or not previous <= at <= 36:
                    raise ValueError("event minutes must be sorted integers between zero and 36.")
                if not isinstance(event["text"], str) or not isinstance(event["changes"], dict):
                    raise ValueError("each event needs text and a changes object.")
                if event["kind"] not in ("user_update", "document_update", "transport_update", "forecast_update", "weather_update", "provider_notice", "stock_update", "sellout"):
                    raise ValueError("use a published event kind.")
                if event["kind"] in ("forecast_update", "weather_update") and "weather-forecast" not in documents:
                    raise ValueError("weather events need a weather-forecast source.")
                changes = event["changes"]
                if event["kind"] in ("document_update", "transport_update", "forecast_update"):
                    if not isinstance(changes.get("document_text"), str) or not changes["document_text"].strip():
                        raise ValueError("source updates need document_text.")
                if event["kind"] == "sellout" and changes.get("option_id") not in option_ids:
                    raise ValueError("sellout events need a valid option_id.")
                if "option_id" in changes and changes["option_id"] not in option_ids:
                    raise ValueError("event offer references must match an offer ID.")
                if "weather_delays" in changes:
                    delays = changes["weather_delays"]
                    if not isinstance(delays, dict) or any(mode not in ("flight", "train", "coach") or not _nonnegative(delay, integer=True) for mode, delay in delays.items()):
                        raise ValueError("weather_delays must map published modes to nonnegative integer minutes.")
                if "forecast_text" in changes and not isinstance(changes["forecast_text"], str):
                    raise ValueError("forecast_text must be text.")
                if "transfer" in changes and (not isinstance(changes["transfer"], dict) or any(not _nonnegative(changes["transfer"].get(mode), integer=True) for mode in ("flight", "train", "coach"))):
                    raise ValueError("updated transfers need nonnegative integer minutes for all modes.")
                for field in ("waiver_version", "forecast_version"):
                    if field in changes and (not _nonnegative(changes[field], integer=True) or changes[field] == 0):
                        raise ValueError("source versions must be positive integers.")
                previous = at
            TravelWorld(case)
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(prefix + "invalid simulator inputs: " + str(error)) from error
    return cases
