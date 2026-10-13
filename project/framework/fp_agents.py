"""Provided agent loops: single, one-shot, and independent investigators.

Keep this common framework fixed; customize the solution/policy.py entrypoints.
"""
import copy
import json
import re
from concurrent.futures import ThreadPoolExecutor

from .settings import settings, validate_settings
from .common import object_schema, ResponseFailure
from .fp_world import TravelWorld, travel_action, FP_TOOL_GUIDE, FP_TOOL_DURATIONS
from .fp_cases import fp_hash

FP_NULL_STRING = {"type": ["string", "null"]}
FP_ARGUMENTS_SCHEMA = object_schema(dict(id=FP_NULL_STRING, topic=FP_NULL_STRING,
    code=FP_NULL_STRING, key=FP_NULL_STRING, version={"type": ["integer", "null"]},
    minutes={"type": ["integer", "null"]}))
FP_ACTION_SCHEMA = object_schema(dict(tool={"type": "string", "enum": list(FP_TOOL_GUIDE)},
                                      arguments=FP_ARGUMENTS_SCHEMA))
FP_DECISION_SCHEMA = object_schema(dict(
    actions={"type": "array", "items": FP_ACTION_SCHEMA, "maxItems": 9},
    facts={"type": "array", "items": {"type": "string"}, "maxItems": 12},
    done={"type": "boolean"}))

FP_PLAN_SCHEMA = object_schema(dict(meeting_minute={"type":"integer"},
    spending_limit={"type":"integer"}, approval={"type":"string"},
    preferred_mode={"type":"string", "enum":["flight","train","coach"]},
    flight_transfer={"type":"integer"}, train_transfer={"type":"integer"},
    coach_transfer={"type":"integer"}, evidence_type={"type":"string"},
    evidence_code={"type":"string"}, bulletin_version={"type":"integer"},
    requires_step_free={"type":"boolean"}, avoid_carriers={"type":"array","items":{"type":"string"}},
    forecast_risk={"type":"integer","minimum":0,"maximum":100},
    forecast_delay={"type":"integer","minimum":0},
    forecast_mode={"type":"string","enum":["flight","train","coach","none"]}))


FP_STARTER_PROMPT = "Help the traveler repair the trip. Use the available tools, then stop when done."
FP_SPECIALIST_PROMPTS = {
    "transport": "Investigate feasible outbound transport. Read transport-guide and search. Report option IDs, prices, meeting arrival including transfers, expiry, and unresolved facts. Never book or cancel.",
    "hotel": "Investigate the fee waiver. Read hotel-terms and follow the current bulletin. Report exact evidence type, code, version, deadline, and preserved hotel scope. Never book or cancel.",
    "traveler": "Investigate latest user constraints and approval. Read traveler-profile and inquire traveler. Report current meeting time, spending limit, preferred mode, approval code and scope, and durable future-trip preference. Never book or cancel.",
}


def travel_config(architecture="single", prompt=FP_STARTER_PROMPT, model_settings=None,
                  max_decisions=12, investigator_rounds=2, route_threshold=2,
                  concurrent_investigators=True, context_history=8, specialist_prompts=None,
                  refresh_context=True, extraction_prompts=None, forecast_strategy="precaution"):
    if forecast_strategy not in ("precaution","cheapest","flexible"):
        raise ValueError("Choose precaution, cheapest or flexible as forecast_strategy.")
    if architecture not in ("single", "one_shot", "conservative", "late_one_shot", "deadline_snapshot", "multi", "rules", "hybrid_single", "hybrid_multi"):
        raise ValueError("Choose single, one_shot, conservative, late_one_shot, deadline_snapshot, multi, rules, hybrid_single, or hybrid_multi.")
    cfg = dict(architecture=architecture, prompt=prompt,
        model_settings=model_settings or settings(max_output_tokens=4096),
        max_decisions=max_decisions, investigator_rounds=investigator_rounds,
        route_threshold=route_threshold, concurrent_investigators=concurrent_investigators,
        context_history=context_history,
        refresh_context=refresh_context, forecast_strategy=forecast_strategy,
        extraction_prompts=copy.deepcopy(extraction_prompts or FP_EXTRACTION_ROLE_PROMPTS),
        specialist_prompts=copy.deepcopy(specialist_prompts or FP_SPECIALIST_PROMPTS))
    validate_settings(cfg["model_settings"])
    for name in ("max_decisions", "investigator_rounds", "context_history"):
        if type(cfg[name]) is not int or cfg[name] < 1:
            raise ValueError(f"{name} must be a positive integer.")
    if type(route_threshold) is not int or not 0 <= route_threshold <= 3:
        raise ValueError("route_threshold must be between 0 and 3 unresolved domains.")
    return cfg


def travel_route(observation, memory):
    """Provided routing default; override solution/policy.py::route to customize it."""
    if not memory.get("investigated"):
        return ["transport", "hotel", "traveler"]
    if memory.get("needs_hotel"):
        return ["hotel"]
    if memory.get("revision") == observation["revision"]:
        return []
    new = [n for n in observation["notices"] if n["at"] > memory.get("investigated_at", -1)]
    domains = set()
    for notice in new:
        text = notice["text"].lower()
        if "hotel" in text or "bulletin" in text:
            domains.add("hotel")
        if any(k in text for k in ("meeting", "spending", "preference", "rail")):
            domains.add("traveler")
        if notice["kind"]=="user_update":domains.add("traveler")
        if notice["kind"] in ("transport_update","forecast_update","weather_update") or "seat" in text or "booking provider" in text:
            domains.add("transport")
    return sorted(domains)


def _agent_payload(world, history, facts, role="coordinator"):
    return dict(role=role, observation=world.observe(), recent_tool_results=copy.deepcopy(history),
                working_facts=copy.deepcopy(facts), tools=FP_TOOL_GUIDE,
                tool_durations=FP_TOOL_DURATIONS,
                scheduling="Three common slots. External notices before tied completions; tools then in submitted order. Wait advances only virtual time.")


def _clean_actions(actions):
    return [dict(tool=a["tool"], arguments={k:v for k,v in a["arguments"].items() if v is not None}) for a in actions]


def _investigate(world, api, config, domains, context):
    contexts = {d: dict(history=[], facts=[]) for d in domains}
    traces = []
    for round_index in range(config["investigator_rounds"]):
        active = [d for d in domains if not contexts[d].get("done")]
        if not active or world.finished:
            break
        def decide(domain):
            instructions = config["specialist_prompts"][domain]+(
                " Use only read, search, inquire tools. After receiving evidence, return "
                "facts and done=true. At most three actions. Related source IDs can require "
                "a further read. The coordinator will handle writes."
            )
            payload = _agent_payload(world, contexts[domain]["history"], contexts[domain]["facts"], domain)
            output = api.json(config["model_settings"], instructions, payload,
                FP_DECISION_SCHEMA, dict(case_id=world.case_id, role=domain, round=round_index))
            return domain, output, payload
        if config["concurrent_investigators"]:
            with ThreadPoolExecutor(max_workers=3) as pool:
                decisions = list(pool.map(decide, active))
        else:
            decisions = [decide(d) for d in active]
        jobs, owners = [], []
        for domain, output, payload in decisions:
            contexts[domain]["facts"] = output["facts"]
            contexts[domain]["done"] = output["done"]
            traces.append(dict(role=domain, round=round_index, payload=payload, decision=copy.deepcopy(output)))
            for action in _clean_actions(output["actions"]):
                if action["tool"] not in ("read", "search", "inquire"):
                    raise ValueError("Investigators must not execute booking writes.")
                jobs.append(action)
                owners.append(domain)
        if jobs:
            if config["concurrent_investigators"]:
                rows = world.batch(jobs)
            else:
                rows = [world.batch([job])[0] for job in jobs]
            for domain, row in zip(owners, rows):
                contexts[domain]["history"].append(row)
        else:
            break
    # Tool evidence remains available; facts can be incomplete or wrong.
    for domain in domains:
        context[domain] = contexts[domain]
    return traces


def run_travel_agent(world, api, config, route_fn=travel_route):
    history, facts, traces, context = [], [], [], {}
    memory = {}
    if config["architecture"] == "rules":
        return run_travel_rules(world, config)
    if config["architecture"] in ("hybrid_single", "hybrid_multi"):
        return run_travel_hybrid(world, api, config, route_fn)
    if config["architecture"] in ("one_shot","conservative","late_one_shot","deadline_snapshot"):
        return run_travel_one_shot(world, api, config)
    for step in range(config["max_decisions"]):
        if world.finished:
            break
        if config["architecture"] == "multi":
            domains = route_fn(world.observe(), copy.deepcopy(memory))
            if any(d not in FP_SPECIALIST_PROMPTS for d in domains):
                raise ValueError("Route to transport, hotel, or traveler.")
            if len(domains) >= config["route_threshold"] and domains:
                traces.extend(_investigate(world, api, config, domains, context))
                memory.update(investigated=True, revision=world.revision, investigated_at=world.now)
                facts = [f"{domain}: {f}" for domain, pack in context.items() for f in pack["facts"]]
                history = [r for pack in context.values() for r in pack["history"]][-config["context_history"]:]
        payload = _agent_payload(world, history[-config["context_history"]:], facts)
        decision = api.json(config["model_settings"], config["prompt"], payload,
            FP_DECISION_SCHEMA, dict(case_id=world.case_id, role="coordinator", step=step))
        traces.append(dict(role="coordinator", step=step, payload=payload, decision=copy.deepcopy(decision)))
        facts = decision["facts"]
        actions = _clean_actions(decision["actions"])
        if actions:
            rows = world.batch(actions)
            history.extend(rows)
        if (decision["done"] or not actions) and world.now >= world.observe()["handoff_minute"]:
            if not world.finished:
                world.call("finish")
            break
    if not world.finished:
        world.call("finish")
    return dict(traces=traces, working_memory=memory, context=context)


def run_travel_one_shot(world, api, config):
    """A genuine one-extraction + local-optimizer comparator with stale context."""
    if config["architecture"]=="late_one_shot":world.call("wait",minutes=10)
    rows = world.batch([travel_action("search"), travel_action("read", id="transport-guide"),
                        travel_action("read", id="hotel-terms")])
    source_jobs=[travel_action("read",id="hotel-bulletin"),travel_action("read",id="traveler-profile")]
    if any(d["id"]=="weather-forecast" for d in world.observe()["source_catalog"]):
        source_jobs.append(travel_action("read",id="weather-forecast"))
    sources_read=world.batch(source_jobs)
    bulletin=sources_read[0]["result"]
    if config["architecture"]=="deadline_snapshot":
        # Strong comparator: choose a late snapshot from the OBSERVED waiver deadline,
        # reserving enough time for a changed guide read and the operational claim.
        limit=int(re.search(r"virtual minute (\d+)",bulletin["source"]["text"])[1])
        target=max(world.now,limit-5)
        if world.now<target:world.call("wait",minutes=target-world.now)
        latest={x["id"]:x["version"] for x in world.observe()["source_catalog"]}
        for row in rows:
            if "source" in row["result"]:
                doc=row["result"]["source"]
                if latest.get(doc["id"])!=doc["version"]:
                    row["result"]["source"]=world.call("read",id=doc["id"])["source"]
        target=max(world.now,limit-3)
        if world.now<target:world.call("wait",minutes=target-world.now)
    sources=[r["result"]["source"] for r in rows+sources_read if "source" in r["result"]]
    payload = dict(observation=world.observe(), read_sources=sources)
    plan = api.json(config["model_settings"],
        "Extract the applicable meeting time in minutes since midnight, extra-spending "
        "limit, outbound approval, preferred mode, transfer minutes by mode, and current "
        "hotel waiver evidence type/code/version. Use supplied source evidence only. "+config["prompt"],
        payload, FP_PLAN_SCHEMA, dict(case_id=world.case_id, role="one_shot"))
    options = rows[0]["result"]["options"]
    world.call("claim", topic=plan["evidence_type"], code=plan["evidence_code"], version=plan["bulletin_version"])
    candidates = travel_candidates(options,plan,world.observe()["hotel_fee"])
    if candidates:
        choice = min(candidates,key=lambda o:(o["mode"]!=plan["preferred_mode"],o["arrival_minute"],o["price"])) if config["architecture"]=="conservative" else candidates[0]
        held = world.call("hold", id=choice["id"])
        if held.get("ok"):
            reply = world.call("confirm", id=held["hold"]["id"], code=plan["approval"], key="one-shot-outbound")
            if reply.get("interrupted"):
                world.call("status", key="one-shot-outbound")
    if world.now < world.observe()["handoff_minute"]:
        world.call("wait", minutes=world.observe()["handoff_minute"]-world.now)
    world.call("finish")
    return dict(traces=[dict(role="one_shot", payload=payload, decision=plan)], working_memory={}, context={})


def run_travel_rules(world, config=None):
    """Transparent inexpensive comparator, not an optimality claim or gold access."""
    # Deliberately simple public-language parser: its known vocabulary is visible.
    rows = world.batch([travel_action("search"), travel_action("read", id="transport-guide"),
                        travel_action("read", id="hotel-terms")])
    options = rows[0]["result"]["options"]
    guide = rows[1]["result"]["source"]["text"]
    bulletin = world.call("read", id="hotel-bulletin")["source"]
    text = bulletin["text"]
    match = re.search(r"type (\S+) with code (\S+) before virtual minute (\d+)", text)
    if match:
        world.call("claim", topic=match[1], code=match[2], version=bulletin["version"])
    request = world.observe()["notices"][0]["text"]
    times = re.findall(r"(\d{2}):(\d{2})", request)
    deadline = int(times[0][0])*60+int(times[0][1]) if times else 660
    buffers = {"flight":20, "train":20, "coach":20}
    if "35 minutes" in guide:
        buffers = {"flight":0, "train":35, "coach":45}
    feasible = [o for o in options if o["arrival_minute"]+buffers[o["mode"]] <= deadline]
    chosen = min(feasible or options, key=lambda o:(o["mode"] != "flight", o["price"]))
    hold = world.call("hold", id=chosen["id"])
    consent = re.search(r"(?:approval|Approval) (consent-\d+)", request)
    if hold.get("ok") and consent:
        result = world.call("confirm", id=hold["hold"]["id"], code=consent[1], key="rules-outbound")
        if result.get("interrupted"):
            world.call("status", key="rules-outbound")
    if world.now < world.observe()["handoff_minute"]:
        world.call("wait", minutes=world.observe()["handoff_minute"]-world.now)
    world.call("finish")
    return dict(traces=[], working_memory={}, context={})


FP_ROLE_FIELDS = {
    "transport": ("flight_transfer", "train_transfer", "coach_transfer", "forecast_risk", "forecast_delay", "forecast_mode"),
    "hotel": ("evidence_type", "evidence_code", "bulletin_version"),
    "traveler": ("meeting_minute", "spending_limit", "approval", "preferred_mode", "requires_step_free", "avoid_carriers"),
}
FP_EXTRACTION_PROMPT = (
    "Extract current trip requirements into the exact JSON schema. Use the most recent "
    "applicable user notice, not a superseded initial value. Convert HH:MM to minutes "
    "since midnight. Preserve explicit scope: a new commitment limit is not a refund "
    "of an old charge; this-trip rail does not replace a future flight default. Approval "
    "is the literal consent code in the request, never an invented identifier. Hotel "
    "evidence_type and evidence_code are literal values from the newest read bulletin; "
    "bulletin_version is its source version. Extract transfer minutes separately for "
    "flight/train/coach. Extract requires_step_free and avoid_carriers for this lead outbound only. Interpret negation, lifted exclusions, and traveler scope; an unrelated colleague condition is not a lead constraint. A terminal arrival needs its stated transfer; a direct arrival "
    "at the meeting district needs zero. Extract forecast_risk as the applicable percentage (0..100), forecast_delay as possible additional arrival minutes and forecast_mode as the affected mode. A chance is not a realized delay; absent forecast uses 0, 0, none. Use memory only when no newer source changes it."
)

FP_EXTRACTION_ROLE_PROMPTS = {
    "transport": "Extract flight_transfer, train_transfer and coach_transfer from the read guide. They are minutes from arrival to the client meeting. If the guide gives one buffer for all arrivals, use it for every mode. A direct arrival in the meeting district needs zero. Also extract the applicable weather forecast percentage, possible extra arrival minutes and affected mode. A warning for an unrelated journey does not apply. If no forecast exists, use forecast_risk=0, forecast_delay=0, forecast_mode=none. Return only the requested fields.",
    "hotel": "Extract the newest read bulletin's required evidence_type, literal evidence_code, and source bulletin_version. The category is the required item, such as cancel-reference or disruption-letter; it is never the document ID hotel-bulletin. Ignore an expired automatic waiver promise. Return only the requested fields.",
    "traveler": "Extract the latest applicable meeting_minute (minutes since midnight), spending_limit (USD), literal outbound approval code, current-trip preferred_mode, requires_step_free, and avoid_carriers (exact names). Apply new or lifted restrictions to this lead outbound, including a confirmed replacement. Conditions for a colleague or later journey do not apply. Keep unrelated conditions when one field changes. New user notices supersede initial values. Convert written clock times. Distinguish hotel check-in from the client meeting. A one-trip train preference leaves future flight defaults intact. Return only the requested fields.",
}


def travel_candidates(options, state, pending_fee=0, now=None):
    """Free local optimization over observed numeric facts; no evaluator access."""
    return sorted([o for o in options
        if o["arrival_minute"]+state[o["mode"]+"_transfer"] <= state["meeting_minute"]
        and o["price"]+pending_fee+state.get("net_spent",0) <= state["spending_limit"]
        and (now is None or o.get("available_from",0)<=now<o["expires_at"])
        and (not state.get("requires_step_free",False) or o.get("step_free",False))
        and o.get("carrier") not in state.get("avoid_carriers",[])],
        key=lambda o:(o["mode"] != state["preferred_mode"], o["price"], o["id"]))


def travel_forecast_choice(candidates, state, strategy="precaution"):
    """Small visible precaution heuristic, not an optimal policy or gold lookup.

    A high applicable warning favors timely unaffected travel or a refundable
    affected fare. Low warnings use the normal price/preference ordering.
    """
    if strategy=="flexible":
        flexible=[o for o in candidates if o.get("change_policy","flexible")=="flexible"]
        safe=[o for o in candidates if not o.get("weather_exposed",False)]
        changeable=[o for o in candidates if o.get("change_policy")=="fee"]
        return (flexible or safe or changeable or candidates)[0]
    if strategy=="cheapest" or state.get("forecast_risk",0) < 50:
        return candidates[0]
    affected=state.get("forecast_mode","none")
    safe=[o for o in candidates if not o.get("weather_exposed",False) or o["mode"]!=affected
          or o["arrival_minute"]+state[o["mode"]+"_transfer"]+state.get("forecast_delay",0)<=state["meeting_minute"]]
    if safe:return safe[0]
    flexible=[o for o in candidates if o.get("change_policy","flexible")=="flexible"]
    changeable=[o for o in candidates if o.get("change_policy")=="fee"]
    return (flexible or changeable or candidates)[0]


def _extract_trip(world, api, config, documents, state, domains, traces):
    def extract(domain=None):
        if domain:
            fields=FP_ROLE_FIELDS[domain]
            schema=object_schema({k:FP_PLAN_SCHEMA["properties"][k] for k in fields})
            ids={"transport":["transport-guide","weather-forecast"],"hotel":["hotel-terms","hotel-bulletin"],
                 "traveler":["traveler-profile"]}[domain]
        else:
            fields=list(FP_PLAN_SCHEMA["properties"]);schema=FP_PLAN_SCHEMA;ids=list(documents)
        observation=world.observe()
        # Role contexts include only applicable observed evidence. A combined
        # extractor still has exactly the same evidence available.
        visible=dict(case_id=observation["case_id"],virtual_minute=observation["virtual_minute"])
        if domain in (None,"traveler"):visible["notices"]=observation["notices"]
        payload=dict(observation=visible, read_sources=[documents[k] for k in ids if k in documents],
                     prior_state={k:v for k,v in state.items() if k in fields})
        prompt=(config["extraction_prompts"][domain] if domain else FP_EXTRACTION_PROMPT)+" "+config["prompt"]
        output=api.json(config["model_settings"],prompt,payload,schema,
                       dict(case_id=world.case_id,role=domain or "combined_extractor"))
        return dict(role=domain or "combined_extractor",payload=payload,decision=output)
    if config["architecture"] == "hybrid_multi" and len(domains)>=config["route_threshold"] and world.observe().get("tier")!="basic":
        if config["concurrent_investigators"]:
            with ThreadPoolExecutor(max_workers=3) as pool: outputs=list(pool.map(extract,domains))
        else:outputs=[extract(d) for d in domains]
    else:outputs=[extract()]
    for row in outputs:state.update(row["decision"])
    traces.extend(outputs)


def run_travel_hybrid(world, api, config, route_fn=travel_route):
    """Shared reliable actuator; models interpret language, local code plans numbers.

    Single and multi use the same sources, optimizer, writes, waits, and slots.
    They differ in combined vs separately scoped interpretation and routing.
    """
    documents, state, traces, memory = {}, {}, [], {}
    rejected_claims = 0
    boot=world.batch([travel_action("search"),travel_action("read",id="transport-guide"),
                      travel_action("read",id="hotel-terms")])
    options=boot[0]["result"]["options"]
    for row in boot[1:]:documents[row["result"]["source"]["id"]]=row["result"]["source"]
    for row in world.batch([travel_action("read",id="hotel-bulletin"),travel_action("read",id="traveler-profile")]):
        documents[row["result"]["source"]["id"]]=row["result"]["source"]
    if any(d["id"]=="weather-forecast" for d in world.observe()["source_catalog"]):
        documents["weather-forecast"]=world.call("read",id="weather-forecast")["source"]
    search_revision=world.revision
    for step in range(config["max_decisions"]):
        if world.finished:break
        observation=world.observe()
        domains=list(dict.fromkeys(route_fn(observation,copy.deepcopy(memory))))
        if not state:domains=list(FP_ROLE_FIELDS)
        if any(d not in FP_ROLE_FIELDS for d in domains):raise ValueError("Unknown investigator domain.")
        latest={s["id"]:s["version"] for s in observation["source_catalog"]}
        reads=[]
        for source,domain in (("hotel-bulletin","hotel"),("transport-guide","transport"),
                              ("weather-forecast","transport")):
            if source not in documents or (domain=="hotel" and not observation["hotel_fee"]):
                continue
            if latest.get(source)!=documents[source]["version"]:
                reads.append(travel_action("read",id=source))
                if domain not in domains:domains.append(domain)
        # Independent refreshes share the same common slots for every design.
        # New offers and inventory can matter without a document-version change.
        if observation["revision"]!=search_revision:
            changed_market=any(n["at"]>memory.get("investigated_at",-1)
                and n["kind"] not in ("document_update","provider_notice")
                for n in observation["notices"])
            if changed_market:reads.append(travel_action("search"))
            else:search_revision=observation["revision"]
        if reads:
            for row in world.batch(reads):
                result=row["result"]
                if "source" in result:documents[result["source"]["id"]]=result["source"]
                if "options" in result:options=result["options"];search_revision=world.revision
            # Reads advance virtual time. Do not mark intervening traveler notices
            # handled before their domain has been interpreted.
            for domain in route_fn(world.observe(),copy.deepcopy(memory)):
                if domain not in FP_ROLE_FIELDS:raise ValueError("Unknown investigator domain.")
                if domain not in domains:domains.append(domain)
        # Waivers already accepted under an old bulletin remain accepted.
        if state and not world.observe()["hotel_fee"]:domains=[d for d in domains if d!="hotel"]
        if state and not config["refresh_context"]:domains=[]
        if domains:_extract_trip(world,api,config,documents,state,domains,traces)
        memory.pop("needs_hotel",None)
        memory.update(investigated=True,revision=world.revision,investigated_at=world.now)
        observation=world.observe()
        pending=[b for b in observation["bookings"] if b["status"]=="pending_verification"]
        if pending:
            for b in pending:world.call("status",key=b["request_key"])
            continue
        active=[b for b in observation["bookings"] if b["kind"]=="transport" and b["status"]=="confirmed"]
        state["net_spent"]=observation.get("net_transport_spend_usd",0)
        planning_state=dict(state,net_spent=state["net_spent"]-sum(b["price"]-b.get("cancel_fee_usd",0) for b in active if b.get("change_policy","flexible")!="locked"))
        candidates=travel_candidates(options,planning_state,0,world.now)
        has_preferred=any(o["mode"]==state["preferred_mode"] for o in candidates)
        if active:
            b=active[0]
            timely=b["arrival_minute"]+state[b["mode"]+"_transfer"]<=state["meeting_minute"]
            wanted=b["mode"]==state["preferred_mode"] or not has_preferred
            access=not state.get("requires_step_free",False) or b.get("step_free",False)
            carrier_ok=b.get("carrier") not in state.get("avoid_carriers",[])
            affected=(b.get("weather_exposed",False)
                      and b["mode"]==state.get("forecast_mode")
                      and state.get("forecast_risk",0)>=50
                      and b["arrival_minute"]+state[b["mode"]+"_transfer"]
                          +state.get("forecast_delay",0)>state["meeting_minute"])
            precaution=False
            if affected and candidates and config.get("forecast_strategy","precaution")!="cheapest":
                alternative=travel_forecast_choice(candidates,state,config.get("forecast_strategy","precaution"))
                precaution=(alternative["id"]!=b["option_id"]
                            and (not alternative.get("weather_exposed",False)
                                 or alternative["mode"]!=state.get("forecast_mode")))
            if (not timely or not wanted or not access or not carrier_ok or precaution) and candidates and b.get("change_policy")!="locked":
                cancelled=world.call("cancel",id=b["id"],code=state["approval"])
                if cancelled.get("ok"):
                    continue
                # Immutable fares remain committed. Preserve safe partial credit and
                # keep monitoring rather than pretending the cancellation succeeded.
        if observation["hotel_fee"] and rejected_claims<2:
            # Two visible operational attempts; if both fail, preserve a feasible booking with the fee.
            # No hidden API retry: a rejected operational claim causes a visible
            # source read and a charged semantic refresh on a later iteration.
            reply=world.call("claim",topic=state["evidence_type"],code=state["evidence_code"],version=state["bulletin_version"])
            if not reply["ok"]:
                rejected_claims+=1
                if world.finished:break
                documents["hotel-bulletin"]=world.call("read",id="hotel-bulletin")["source"]
                memory["needs_hotel"]=True
                continue
        if not active:
            state["net_spent"]=world.observe().get("net_transport_spend_usd",0)
            candidates=travel_candidates(options,state,world.observe()["hotel_fee"],world.now)
            if not candidates:
                options=world.call("search")["options"]
                state["net_spent"]=world.observe().get("net_transport_spend_usd",0)
            candidates=travel_candidates(options,state,world.observe()["hotel_fee"],world.now)
            if candidates:
                choice=travel_forecast_choice(candidates,state,config.get("forecast_strategy","precaution"))
                held=world.call("hold",id=choice["id"])
                if held.get("ok"):
                    world.call("confirm",id=held["hold"]["id"],code=state["approval"],key=f"outbound-{step}")
                else:options=world.call("search")["options"]
                continue
        observation=world.observe()
        if world.now>=observation["handoff_minute"]:
            world.call("finish");break
        world.call("wait",minutes=min(4,observation["handoff_minute"]-world.now))
    if not world.finished:world.call("finish")
    return dict(traces=traces,working_memory=memory,context=state)
