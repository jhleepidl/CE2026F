"""Published fictional scenarios for travel planning and replanning."""
import hashlib
import json
import random

FP_VERSION = 'travel-2026f-v8'
FP_TIERS = ('basic', 'reactive', 'forecast')
FP_FAMILIES = ('meeting_update', 'budget_update', 'temporary_preference',
               'conditional_waiver', 'quote_expiry', 'confirmation_interruption',
               'transfer_update', 'traveler_scope')
FP_SCORE_VERSION = "travel-score-2026f-v3-100"
FP_GRADING_COST_BASIS = "uncached_token_rates"
FP_OUTCOME_POINTS = dict(arrival=40, requests=20, fee_waiver=10, safety=10, reliability=10)
FP_OUTCOME_MAX = sum(FP_OUTCOME_POINTS.values())
FP_EFFICIENCY_MAX = 10
FP_SCORE_MAX = FP_OUTCOME_MAX + FP_EFFICIENCY_MAX


def fp_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def transfer_text(transfers, city, variant=0):
    f,t,c = (transfers[k] for k in ('flight','train','coach'))
    if variant % 2:
        return (f'Current transfers for {city}: a flight arrival still needs {f} minutes to the client; '
                f'rail passengers should allow {t} minutes after arrival, and coach passengers {c}. '
                'These are additional minutes, not clock times. The archived 20-minute blanket '
                'allowance below is withdrawn. Weekend excursion transfers do not apply to this business trip.')
    return (f'Use these weekday transfers in {city}: flight {f} minutes, train {t} minutes, '
            f'coach {c} minutes. Add the applicable value to terminal arrival. '
            'Last month all transfers were 20 minutes; that guide is obsolete. '
            'The 45-minute hotel shuttle is not the journey to the client.')


def waiver_text(category, code, deadline, city, variant=0):
    if variant % 2:
        return (f'The cancelled reservation in {city} keeps its room. For that booking, attach '
                f'a {category} marked {code}. We need it before virtual minute {deadline}. '
                'An automatic waiver is not available. A disruption-letter marked proof-0000 '
                'was used in an unrelated example; it is not evidence for this claim. '
                'Use the version number of this source, not the example number.')
    return (f'Archive: last year guests submitted type cancel-reference with code proof-0000. '
            f'That procedure is withdrawn. Current {city} booking: submit evidence of type '
            f'{category} with code {code} before virtual minute {deadline}. '
            'Acceptance removes the USD 55 disruption charge while keeping the room. '
            'Claims accepted under an earlier version stay accepted.')


def make_travel_case(seed, family, variant=0, split='dev', numeric_variation=True):
    if family not in FP_FAMILIES:
        raise ValueError('Unknown travel situation.')
    rng = random.Random(seed)
    suffix = str(rng.randrange(10000,99999))
    city = rng.choice(('Luma City','Port Amber','Northbridge'))
    carriers = ('Aster','Birch','Cedar')
    budget = rng.choice((245,265,285)) if numeric_variation else 265
    deadline = 690 if variant%2==0 else 705
    transfers = dict(zip(('flight','train','coach'),rng.choice(((15,25,35),(30,10,25),(10,35,20)))))
    consent = 'consent-'+suffix
    requires_step_free = bool(variant%2)
    avoided = ['Birch'] if variant%2 else []
    preferred = 'flight' if variant%2==0 else 'train'
    options=[]
    for mode,stem in (('flight','air'),('train','rail'),('coach','coach')):
        for j,(arrival,price) in enumerate(((620,95),(565,135),(515,145),(535,145),(525,145))):
            options.append(dict(id=f'{stem}-{suffix}-{j}',mode=mode,
                price=price+(10 if mode=='flight' else -10 if mode=='coach' else 0)+rng.choice((0,5)),
                arrival_minute=arrival+rng.choice((0,3,5)),
                carrier=carriers[j%3],step_free=j in (0,2,3,4),comfort=2+j,
                inventory=2,expires_at=36,connection='terminal'))
    rng.shuffle(options)
    category = 'cancel-reference' if variant%2==0 else 'disruption-letter'
    proof='proof-'+suffix
    event_rng=random.Random(seed ^ 82631)
    waiver_deadline=event_rng.choice((11,18,24))
    final_update_at=event_rng.choice((18,22))
    if variant%2:
        request=(f'My outbound to {city} has been cancelled. Keep our existing hotel and my '
            f"colleague's return ticket. The client needs me by {deadline//60:02d}:{deadline%60:02d}; "
            f'USD {budget} is the ceiling for extra transport plus the USD 55 hotel charge. '
            'Please get that charge waived. I favor rail for this journey. I need step-free '
            'travel from now until handoff, and Birch is excluded for my replacement only. '
            'My colleague is still flying Birch; leave that reservation alone. '
            f'Approval {consent} authorizes my replacement outbound and refundable exchanges.')
    else:
        request=(f'Repair my cancelled outbound to {city}. The client meeting is at 11:30. '
            f'Spend no more than USD {budget} extra including the hotel disruption fee. '
            'Waive that fee, keep the room, and preserve the colleague-return reservation. '
            'I prefer a flight if feasible. Stairs are fine and no carrier is excluded. '
            f'Approval {consent} covers only my replacement outbound and refundable exchanges.')
    request += (' Confirm a first replacement outbound by virtual minute 14; '
                'later approved exchanges remain permitted. Monitor changes through '
                'virtual minute 24, then finish by minute 36. '
                'A budget reduction applies to new commitments; previous approved charges remain valid. '
                'The hotel and colleague booking are never covered by outbound approval.')
    documents={
        'transport-guide':dict(id='transport-guide',title=f'Weekday transfers in {city}',version=1,
            text=transfer_text(transfers,city,variant),related=[]),
        'hotel-terms':dict(id='hotel-terms',title='Existing room and disruption charge',version=1,
            text='Keep the confirmed room. USD 55 is pending. Read hotel-bulletin for the current evidence and deadline. Claims never cancel the room.',related=['hotel-bulletin']),
        'hotel-bulletin':dict(id='hotel-bulletin',title='Current waiver procedure',version=2,
            text=waiver_text(category,proof,waiver_deadline,city,variant),related=[]),
        'traveler-profile':dict(id='traveler-profile',title='Durable preferences and scope',version=1,
            text='Booking platform operators: Aster, Birch, Cedar. Default for later journeys: flight, all carriers allowed, no access requirement. Current-trip notices override this profile only for this trip. Do not overwrite the colleague booking or infer that another traveler shares a new restriction.',related=[])}
    events=[]
    def event(at,kind,text,**changes):events.append(dict(at=at,kind=kind,text=text,changes=changes))
    if family=='meeting_update':
        event(8,'user_update','The client has advanced our meeting to 09:30 today. The hotel check-in stays at 12:00. Exchange any replacement that cannot get me to the client in time.',deadline=570)
    elif family=='budget_update':
        event(8,'user_update','Finance now allows only USD 155 for any new commitment. Already confirmed charges remain approved. Tomorrow’s USD 400 allowance cannot be used today.',budget=155)
    elif family=='temporary_preference':
        mode='train' if preferred=='flight' else 'coach'
        event(8,'user_update',f'For this journey only I now prefer {mode}. Exchange the replacement if a feasible {mode} option exists. Next month I still prefer flying.',preferred=mode)
    elif family=='conditional_waiver':
        replacement='disruption-letter' if category=='cancel-reference' else 'cancel-reference'
        event(6,'document_update','The hotel revised hotel-bulletin. New claims need the current procedure; claims already accepted remain accepted.',waiver=replacement,waiver_version=3,
            document_text=waiver_text(replacement,proof,waiver_deadline,city,1-variant%2))
    elif family=='quote_expiry':
        target=next(o['id'] for o in options if o['mode']==preferred and o['carrier']=='Aster' and 530<=o['arrival_minute']<550)
        event(8,'stock_update',f'A competing buyer will take unheld inventory for {target} at virtual minute 12. A valid hold protects seats.')
        event(12,'sellout',f'Unheld inventory for {target} has sold out.',option_id=target)
    elif family=='confirmation_interruption':
        event(8,'provider_notice','Missing confirmation replies may follow a committed booking. Inspect the request key before booking again.')
    elif family=='transfer_update':
        revised=dict(flight=60,train=35,coach=40)
        event(9,'transport_update','A road closure changed the journey to the client. Re-read transport-guide. Airport and station arrival times themselves have not changed.',transfer=revised,
            document_text=transfer_text(revised,city,1-variant%2))
    else:
        event(8,'user_update','For my replacement outbound only, use step-free access and exclude Aster. These restrictions also apply to your already booked replacement; exchange it if needed. Do not change my colleague’s Aster return.',requires_step_free=True,avoid_carriers=['Aster'])
    # Every case combines an initial scope distinction with a later independent update.
    # The secondary update is announced in the same observable way as the primary one.
    if family not in ('traveler_scope','temporary_preference'):
        allowed='Aster' if family=='quote_expiry' else rng.choice(carriers)
        excluded=[x for x in carriers if x!=allowed]
        text=(f'For this outbound only, do not use {excluded[0]} or {excluded[1]}. '
              f'{allowed} is permitted again if it was previously excluded. The client now needs me by 10:00. '
              'Keep access needs unchanged; the colleague’s existing return is unaffected.')
        if variant%2:
            text=(f'From now on, {allowed} is the only permitted operator for my replacement outbound. '
                  'This replaces every earlier carrier exclusion for my outbound; it does not authorize changing my colleague’s return. '
                  'The client now needs me by 10:00. Keep my access requirements unchanged.')
        event(final_update_at,'user_update',text,avoid_carriers=excluded,deadline=600)
    else:
        event(final_update_at,'user_update','The client changed the appointment to 10:00. The 11:45 lunch is optional and is not the arrival deadline. All other current-trip conditions still apply.',deadline=600)
    for option in options:
        option.update(change_policy='flexible', cancel_fee_usd=0,
                      weather_exposed=False, available_from=0)
    return dict(version=FP_VERSION,case_id=f'{split}-{suffix}',seed=seed,family=family,variant=variant,
        difficulty='reactive',
        city=city,initial_request=request,consent=consent,budget=budget,deadline=deadline,preferred=preferred,
        requires_step_free=requires_step_free,avoid_carriers=avoided,transfer=transfers,
        hold_minutes=9 if family=='quote_expiry' else 14,interrupt_confirmation=family=='confirmation_interruption',
        waiver_type=category,waiver_code=proof,waiver_deadline=waiver_deadline,
        documents=documents,options=options,events=sorted(events,key=lambda e:e['at']),
        booking_deadline=14,handoff_minute=24,horizon=36)


def fare_terms_text():
    return ('Each search result states its fare contract. A locked fare cannot be '
            'cancelled or exchanged after confirmation. A fee fare can be cancelled '
            'with approval: the refund is its paid fare minus cancel_fee_usd. A '
            'flexible fare is fully refundable. Cancel an approved replacement '
            'before confirming another; preserve the hotel and colleague-return. '
            'Nonrefunded amounts count toward extra spending. Search also states '
            'when an offer opens and closes; a held offer can be confirmed only '
            'while the hold remains valid. These terms do not authorize changing '
            'another traveler or the existing room.')


def make_basic_case(seed, variant=0, split='dev'):
    """Stable external circumstances; booking operations still change local state."""
    c = make_travel_case(seed, FP_FAMILIES[variant % len(FP_FAMILIES)], variant, split)
    c.update(family='stable_planning', difficulty='basic', events=[],
             handoff_minute=0, interrupt_confirmation=False, waiver_deadline=36,
             deadline=690, hold_minutes=14)
    c.pop('booking_deadline', None)
    mode = 'rail' if c['preferred'] == 'train' else 'a flight'
    access = ('I need step-free travel. Birch must not carry my replacement outbound; '
              'my colleague may still use Birch.' if c['requires_step_free'] else
              'Stairs are fine and any listed operator is allowed for my outbound.')
    c['initial_request'] = (
        f"Plan my replacement outbound to {c['city']}. The client appointment is at "
        f"11:30 today. Extra spending may not exceed USD {c['budget']}, including "
        'the pending USD 55 hotel charge and any nonrefunded change fee. Keep our '
        "hotel and my colleague's return ticket; please waive the hotel charge. "
        f'I prefer {mode} if feasible. {access} '
        f"Approval {c['consent']} covers my replacement outbound and permitted fare "
        'changes under the published contract. This is a stable scenario: no '
        'external updates are scheduled. Finish as soon as your confirmed booking '
        'and current requirements are verified; the episode horizon is minute 36.')
    c['documents']['hotel-bulletin']['text'] = waiver_text(
        c['waiver_type'], c['waiver_code'], c['waiver_deadline'], c['city'], variant)
    c['documents']['fare-terms'] = dict(id='fare-terms', title='Replacement fare contracts',
                                       version=1, text=fare_terms_text(), related=[])
    for option in c['options']:
        term = ('locked', 'fee', 'flexible')[int(option['id'].rsplit('-', 1)[1]) % 3]
        option.update(change_policy=term, cancel_fee_usd=35 if term == 'fee' else 0)
    return c


def forecast_text(risk, city, variant=0, observed=False, storm=False,
                  mode='flight', delay=120):
    """Current scoped evidence, distinct from an already observed physical delay."""
    label = dict(flight='flight', train='rail', coach='coach')[mode]
    if observed:
        return (f'Operations report for the lead current outbound to {city}: '
                + (f'weather-exposed {mode} services have now acquired {delay} extra '
                   'minutes beyond their original terminal arrivals. ' if storm else
                   f'The predicted {mode} disruption did not materialize; no extra '
                   'arrival minutes were added. ')
                + 'This observed result is already included in current search and '
                'booking arrivals. Do not add it again. Other transport modes are '
                'unaffected by this weather report. There is no further predicted '
                'change: future additional risk is zero percent, additional delay '
                'is zero, and no mode is under a future watch. Check the current '
                'trip restrictions and transfer guide before any permitted repair.')
    if variant % 2:
        return (f'Lead-traveler current outbound watch for {city}: there is a {risk} '
                f'percent chance of the {label} leg acquiring another {delay} minutes '
                'before handoff. This warning applies only to weather_exposed '
                f'{mode} offers for this journey. Other modes are outside this '
                'watch. A companion weekend forecast mentioned 80 percent; ignore '
                'that different traveler and journey. The possible extra duration '
                'is not the appointment clock or an observed delay. Dispatch may '
                'revise the applicable mode and estimate; this is uncertain evidence.')
    return (f'Current forecast for the lead outbound to {city}: {mode} disruption '
            f'probability {risk} percent, with a possible additional {delay}-minute '
            'arrival delay before handoff. Apply this only to weather_exposed '
            f'{mode} options on this journey; the other modes are outside this '
            'watch. The archived 80-percent warning concerns a companion weekend '
            'excursion and does not apply. The percentage is uncertain evidence, '
            'not an observed delay or a promise. A later dispatch update can '
            'replace the estimated risk, duration or applicable mode.')


def make_forecast_case(seed, variant=0, split='dev'):
    """Four integrated situations, each paired with disruption and false alarm.

    Event tapes are author data. A solver sees only notices and sources that have
    actually arrived; observing an uncertain forecast does not reveal realization.
    """
    c = make_travel_case(seed, 'meeting_update', variant, split)
    suffix = c['case_id'].rsplit('-', 1)[1]
    family, storm = (variant % 8)//2, variant % 2 == 0
    # Scenario mechanics may share a family; the later operator instruction is
    # drawn separately, rather than being a function of the spending ceiling.
    allowed = random.Random(seed ^ 20261011).choice(('Aster', 'Birch', 'Cedar'))
    excluded = [name for name in ('Aster', 'Birch', 'Cedar') if name != allowed]
    # Pair ancillary initial wording/waiver facts across weather outcomes. Their
    # evidence category, cutoff or prose style must not reveal realized weather.
    style = family % 2
    preferred = ('flight', 'train', 'coach', 'flight')[family]
    budgets = (225, 185, 200, 205)
    prices = ((105, 125, 160), (100, 120, 220), (95, 110, 145), (100, 125, 240))[family]
    fee = (20, 15, 10, 20)[family]
    initial_risk = (15, 75, 10, 75)[family]
    current_risk = (75, 20, 70, 15)[family]
    initial_mode = ('flight', 'train', 'coach', 'train')[family]
    current_mode = ('flight', 'train', 'coach', 'flight')[family]
    current_delay = (120, 120, 90, 90)[family]
    forecast_at = (8, 9, 7, 10)[family]
    weather_at = ((16, 16), (18, 20), (16, 18), (20, 18))[family][variant % 2]
    recovery_open = (14, 16, 14, 18)[family]
    recovery_close = (24, 28, 26, 28)[family]
    recovery_price = (175, 150, 180, 165)[family]
    transfer = dict(flight=20, train=20, coach=20)
    c.update(family='weather_planning', difficulty='forecast',
             advanced_situation=('flight_watch_and_access', 'rail_watch_and_carrier',
                                 'coach_watch_and_transfer', 'changed_watch_and_trip_scope')[family],
             budget=budgets[family], deadline=620, preferred=preferred,
             requires_step_free=family == 2, avoid_carriers=[], transfer=transfer,
             booking_deadline=12, hold_minutes=5, interrupt_confirmation=False,
             waiver_type='cancel-reference' if style == 0 else 'disruption-letter',
             waiver_deadline=(11, 18, 11, 18)[family], handoff_minute=24, horizon=36)
    preference = dict(flight='a flight', train='rail', coach='a coach')[preferred]
    access = ('I need step-free access.' if c['requires_step_free'] else
              'Stairs are currently fine.')
    c['initial_request'] = (
        f"Plan my replacement outbound to {c['city']}; the client needs me by 10:20 "
        f"today. The additional-spending ceiling is USD {c['budget']}, including "
        'the USD 55 hotel charge and all nonrefunded fare changes. Please waive '
        'that charge and preserve our room and the colleague-return booking. '
        f'I prefer {preference} when feasible; all listed operators are currently '
        f"allowed. {access} Approval {c['consent']} covers my outbound and permitted "
        'fare changes, including their stated penalties. A first outbound must be '
        'confirmed by virtual minute 12; later approved repairs may use new offers. '
        'Read weather-forecast before choosing a fare; dispatch can revise its '
        'risk, possible delay and applicable mode, and forecasts can be wrong. '
        f'Current initial offers close at minute 12. Recovery offers open at minute '
        f'{recovery_open} and close at minute {recovery_close}; a valid hold protects '
        'its quoted fare until the hold deadline. Stay responsive to traveler and '
        'source updates through minute 24, then finish by minute 36. A new spending limit '
        'applies to new commitments; previously approved charges remain valid. '
        'Hotel check-in at 13:00 is unrelated to the client arrival deadline.')
    c['documents']['transport-guide']['text'] = transfer_text(transfer, c['city'], style)
    c['documents']['hotel-bulletin']['text'] = waiver_text(
        c['waiver_type'], c['waiver_code'], c['waiver_deadline'], c['city'], style)
    c['documents']['fare-terms'] = dict(id='fare-terms', title='Replacement fare contracts',
                                       version=1, text=fare_terms_text(), related=[])
    c['documents']['weather-forecast'] = dict(id='weather-forecast',
        title=f'Lead outbound weather watch in {c["city"]}', version=1,
        text=forecast_text(initial_risk, c['city'], style, mode=initial_mode, delay=60), related=[])
    options = []
    stem = dict(flight='air', train='rail', coach='coach')[preferred]
    for carrier_index, carrier in enumerate(('Aster', 'Birch', 'Cedar')):
        for term, price in zip(('locked', 'fee', 'flexible'), prices):
            step_free = ((carrier == 'Cedar') if family == 0 else
                         (carrier == 'Birch') if family == 1 else
                         (term != 'flexible' and carrier != 'Aster') if family == 2 else
                         carrier != 'Aster')
            options.append(dict(id=f'{stem}-{suffix}-{carrier_index}-{term}', mode=preferred,
                price=price, arrival_minute=(545 if family == 2 else 540)+carrier_index,
                carrier=carrier, step_free=step_free, comfort=3, inventory=2,
                expires_at=12, available_from=0, connection='terminal',
                change_policy=term, cancel_fee_usd=fee if term == 'fee' else 0,
                weather_exposed=True))
        for mode in ('flight', 'train', 'coach'):
            if mode == preferred:
                continue
            arrival = ({'train': 540, 'coach': 550} if family == 0 else
                       {'flight': 545, 'coach': 550} if family == 1 else
                       {'flight': 570, 'train': 540} if family == 2 else
                       {'train': 550, 'coach': 555})[mode]
            options.append(dict(id=f'{mode}-{suffix}-{carrier_index}-recovery', mode=mode,
                price=recovery_price, arrival_minute=arrival+carrier_index,
                carrier=carrier, step_free=True, comfort=3, inventory=2,
                expires_at=recovery_close, available_from=recovery_open,
                connection='terminal', change_policy='flexible', cancel_fee_usd=0,
                weather_exposed=False))
    random.Random(seed ^ 49163).shuffle(options)
    c['options'] = options
    events = [dict(at=forecast_at, kind='forecast_update',
        text='Dispatch replaced the current lead-outbound weather watch. Read weather-forecast; its estimate or applicable mode has changed, not merely its wording.',
        changes=dict(document_text=forecast_text(current_risk, c['city'], 1-style,
                     mode=current_mode, delay=current_delay)))]
    if family == 0:
        events.append(dict(at=14, kind='user_update',
            text=f'The client now needs me by 09:40 today. I now need step-free access for my replacement outbound, including any ticket already booked. {allowed} is the only permitted operator for my outbound; this replaces every earlier carrier restriction. Leave my colleague’s return and the room alone.',
            changes=dict(deadline=580, requires_step_free=True, avoid_carriers=excluded)))
    elif family == 1:
        events.append(dict(at=14, kind='user_update',
            text=f'For my current outbound, the client now needs me by 09:50 and I require step-free access. {allowed} is the only permitted operator; it is permitted again even if an earlier request excluded it. These current-trip rules apply to a confirmed replacement too. Do not change my colleague’s return.',
            changes=dict(deadline=590, requires_step_free=True, avoid_carriers=excluded)))
    elif family == 2:
        events.extend([
            dict(at=12, kind='user_update',
                text=f'The client appointment is now 09:40 for this journey. {allowed} is now the only permitted operator for my outbound, replacing prior exclusions. Keep my step-free requirement and leave my colleague’s return alone.',
                changes=dict(deadline=580, avoid_carriers=excluded)),
            dict(at=14, kind='transport_update',
                text='A road closure changed onward transfers, not terminal arrival clocks. Read the current transport-guide before selecting or retaining a replacement.',
                changes=dict(transfer=dict(flight=0, train=55, coach=15),
                    document_text=transfer_text(dict(flight=0, train=55, coach=15), c['city'], 1-style)))])
    else:
        events.append(dict(at=16, kind='user_update',
            text=f'For this outbound only, I now prefer rail when feasible and need step-free access. {allowed} is the only permitted operator, replacing the earlier carrier list. The client appointment is now 10:00. Finance allows USD 195 for new commitments including retained change fees; already confirmed charges stay approved. Future journeys still use my flight default; leave the companion return alone.',
            changes=dict(preferred='train', requires_step_free=True, avoid_carriers=excluded, deadline=600, budget=195)))
    events.append(dict(at=weather_at, kind='weather_update',
        text='Dispatch resolved the current lead-outbound weather watch. Read the current report before handoff and inspect booked arrivals; current trip restrictions and recovery closing times still apply.',
        changes=dict(weather_delays={current_mode: current_delay if storm else 0},
                     forecast_text=forecast_text(current_risk, c['city'], observed=True,
                                    storm=storm, mode=current_mode, delay=current_delay))))
    c['events'] = sorted(events, key=lambda event: event['at'])
    return c


FP_DEV_CASES = ([make_basic_case(18100+i, i, 'dev') for i in range(3)]
    + [make_travel_case(8100+i, f, i % 2, 'dev')
       for i, f in enumerate(('meeting_update', 'budget_update', 'traveler_scope'))]
    + [make_forecast_case(28100+i, v, 'dev') for i, v in enumerate((0, 3, 4))])
FP_PUBLIC_CASES = ([make_basic_case(19100+i, i, 'public') for i in range(8)]
    + [make_travel_case(9100+i, f, i % 2, 'public') for i, f in enumerate(FP_FAMILIES)]
    + [make_forecast_case(29100+i, i, 'public') for i in range(8)])
FP_FINAL_CASES=FP_PUBLIC_CASES  # Compatibility name: this is the PUBLIC evaluation only.


def public_case_list(cases):
    return [dict(case_id=c['case_id'],request=c['initial_request']) for c in cases]


def travel_case_fingerprints(cases):
    return [fp_hash(c) for c in cases]
