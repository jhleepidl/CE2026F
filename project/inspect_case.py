"""Browse public trip inputs and tool replies without a key or model calls."""
import argparse
import json
from pathlib import Path

from framework.fp_inputs import select_cases, load_local_cases
from framework.fp_world import TravelWorld, travel_action


def preview_case(case):
    world = TravelWorld(case)
    initial = world.observe()
    world.batch([travel_action("read", id=source) for source in
                 ("hotel-terms", "transport-guide", "traveler-profile")])
    already_read = {row["arguments"]["id"] for row in world.history if row["kind"] == "tool"}
    remaining = [source["id"] for source in world.observe()["source_catalog"]
                 if source["id"] not in already_read]
    world.batch([travel_action("read", id=source) for source in remaining]
                + [travel_action("search")])
    return dict(case_id=case["case_id"], tier=case["difficulty"], new_api_calls=0,
                initial_observation=initial, tool_history=world.history,
                final_observation=world.observe())


def preview_markdown(preview):
    initial = preview["initial_observation"]
    lines = ["# " + preview["case_id"] + " — " + preview["tier"],
             "", "Offline tool inspection. Zero model calls; no performance score.",
             "", "## Initial request", "", initial["notices"][0]["text"],
             "", "## Sources returned by read tools", ""]
    for row in preview["tool_history"]:
        if row.get("tool") == "read":
            source = row["result"]["source"]
            lines += ["### " + source["id"] + " (version " + str(source["version"]) + ")",
                      "", "Read completed at virtual minute " + str(row["completed_at"]) + ".",
                      "", source["text"], ""]
        elif row.get("tool") == "search":
            lines += ["## Available offers", "", "Search completed at virtual minute " + str(row["completed_at"]) + ".",
                "", "| ID | Mode | Carrier | USD | Terminal arrival | Step-free | Fare rule | Cancellation fee |",
                "|---|---|---|---:|---|---|---|---:|"]
            for option in row["result"]["options"]:
                minute = option["arrival_minute"]
                values = (option["id"], option["mode"], option["carrier"], option["price"],
                    f"{minute // 60:02d}:{minute % 60:02d}", option["step_free"],
                    option["change_policy"], option["cancel_fee_usd"])
                lines.append("| " + " | ".join(map(str, values)) + " |")
            lines.append("")
    lines += ["## Current observation after inspection", "", "```json",
              json.dumps(preview["final_observation"], indent=2), "```", "",
              "This preview contains only actual observations and tool replies. "
              "Inspection actions advance virtual time. Run the solver in a fresh world.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group()
    inputs.add_argument("--split", choices=("dev", "public"), help="Published case bank; default: dev.")
    inputs.add_argument("--local-cases", type=Path, help="Inspect student-authored local JSON cases.")
    parser.add_argument("--tier", choices=("basic", "reactive", "forecast"))
    parser.add_argument("--case", help="Case ID or one-based row number from the listing.")
    parser.add_argument("--output", type=Path, help="Fresh directory for readable Markdown and raw tool replies.")
    parser.add_argument("--export-case", type=Path, help="Save one selected complete case as a local JSON template.")
    args = parser.parse_args()
    try:
        cases = load_local_cases(args.local_cases) if args.local_cases else select_cases(args.split or "dev", args.tier)
        if args.local_cases and args.tier:
            cases = [case for case in cases if case["difficulty"] == args.tier]
        if not cases: raise ValueError("No cases match the selected difficulty.")
    except ValueError as error: parser.error(str(error))
    if args.case is None:
        if args.export_case: parser.error("Select one case with --case before exporting a template.")
        print("Case catalogue; zero API calls.")
        for index, case in enumerate(cases, 1):
            print(f"{index:2d}  {case['case_id']:24s} {case['difficulty']:8s}  {case['initial_request'][:85]}")
        print("Inspect one using --case <ID or row number>.")
        return
    if args.case.isdecimal() and 1 <= int(args.case) <= len(cases):
        case = cases[int(args.case) - 1]
    else:
        case = next((item for item in cases if item["case_id"] == args.case), None)
    if case is None: parser.error("Choose a case ID or row number from this split/tier listing.")
    if args.output and args.output.exists(): parser.error("Choose a fresh preview directory.")
    if args.export_case and args.export_case.exists(): parser.error("Choose a fresh local case file; preserve previous tests.")
    if args.export_case:
        args.export_case.parent.mkdir(parents=True, exist_ok=True)
        args.export_case.write_text(json.dumps([case], indent=2) + "\n")
        print("Saved local authoring template:", args.export_case)
        print("The template contains simulator events for test authoring. Never provide it to the solver.")
    preview = preview_case(case)
    print(preview_markdown(preview))
    if args.output:
        args.output.mkdir(parents=True)
        (args.output / "preview.md").write_text(preview_markdown(preview))
        (args.output / "preview.json").write_text(json.dumps(preview, indent=2) + "\n")


if __name__ == "__main__": main()
