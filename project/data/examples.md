# Three published scenario examples

These are actual local simulator observations, generated without model calls. They show inputs and changing information, not a solution or measured agent performance. The read-only walkthrough deliberately makes no bookings and earns no task score.

## public-81988 — basic

Offline tool inspection. Zero model calls; no performance score.

### Initial request

Plan my replacement outbound to Northbridge. The client appointment is at 11:30 today. Extra spending may not exceed USD 245, including the pending USD 55 hotel charge and any nonrefunded change fee. Keep our hotel and my colleague's return ticket; please waive the hotel charge. I prefer a flight if feasible. Stairs are fine and any listed operator is allowed for my outbound. Approval consent-81988 covers my replacement outbound and permitted fare changes under the published contract. This is a stable scenario: no external updates are scheduled. Finish as soon as your confirmed booking and current requirements are verified; the episode horizon is minute 36.

### Sources returned by read tools

#### hotel-terms (version 1)

Read completed at virtual minute 2.

Keep the confirmed room. USD 55 is pending. Read hotel-bulletin for the current evidence and deadline. Claims never cancel the room.

#### transport-guide (version 1)

Read completed at virtual minute 2.

Use these weekday transfers in Northbridge: flight 30 minutes, train 10 minutes, coach 25 minutes. Add the applicable value to terminal arrival. Last month all transfers were 20 minutes; that guide is obsolete. The 45-minute hotel shuttle is not the journey to the client.

#### traveler-profile (version 1)

Read completed at virtual minute 2.

Booking platform operators: Aster, Birch, Cedar. Default for later journeys: flight, all carriers allowed, no access requirement. Current-trip notices override this profile only for this trip. Do not overwrite the colleague booking or infer that another traveler shares a new restriction.

#### hotel-bulletin (version 2)

Read completed at virtual minute 4.

Archive: last year guests submitted type cancel-reference with code proof-0000. That procedure is withdrawn. Current Northbridge booking: submit evidence of type cancel-reference with code proof-81988 before virtual minute 36. Acceptance removes the USD 55 disruption charge while keeping the room. Claims accepted under an earlier version stay accepted.

#### fare-terms (version 1)

Read completed at virtual minute 4.

Each search result states its fare contract. A locked fare cannot be cancelled or exchanged after confirmation. A fee fare can be cancelled with approval: the refund is its paid fare minus cancel_fee_usd. A flexible fare is fully refundable. Cancel an approved replacement before confirming another; preserve the hotel and colleague-return. Nonrefunded amounts count toward extra spending. Search also states when an offer opens and closes; a held offer can be confirmed only while the hold remains valid. These terms do not authorize changing another traveler or the existing room.

### Available offers

Search completed at virtual minute 4.

| ID | Mode | Carrier | USD | Terminal arrival | Step-free | Fare rule | Cancellation fee |
|---|---|---|---:|---|---|---|---:|
| coach-81988-2 | coach | Cedar | 135 | 08:38 | True | flexible | 0 |
| rail-81988-2 | train | Cedar | 150 | 08:35 | True | flexible | 0 |
| air-81988-1 | flight | Birch | 150 | 09:28 | False | fee | 35 |
| air-81988-3 | flight | Aster | 160 | 08:58 | True | locked | 0 |
| coach-81988-4 | coach | Birch | 140 | 08:45 | True | fee | 35 |
| rail-81988-0 | train | Aster | 95 | 10:25 | True | locked | 0 |
| rail-81988-3 | train | Aster | 145 | 08:55 | True | locked | 0 |
| air-81988-4 | flight | Birch | 160 | 08:50 | True | fee | 35 |
| air-81988-0 | flight | Aster | 105 | 10:25 | True | locked | 0 |
| air-81988-2 | flight | Cedar | 155 | 08:35 | True | flexible | 0 |
| coach-81988-3 | coach | Aster | 140 | 09:00 | True | locked | 0 |
| rail-81988-1 | train | Birch | 140 | 09:30 | False | fee | 35 |
| coach-81988-1 | coach | Birch | 125 | 09:30 | False | fee | 35 |
| coach-81988-0 | coach | Aster | 85 | 10:20 | True | locked | 0 |
| rail-81988-4 | train | Birch | 150 | 08:48 | True | fee | 35 |

### Current observation after inspection

```json
{
  "case_id": "public-81988",
  "version": "travel-2026f-v8",
  "virtual_minute": 4,
  "horizon": 36,
  "handoff_minute": 0,
  "revision": 0,
  "tier": "basic",
  "difficulty": "basic",
  "booking_deadline": null,
  "notices": [
    {
      "at": 0,
      "kind": "initial_request",
      "text": "Plan my replacement outbound to Northbridge. The client appointment is at 11:30 today. Extra spending may not exceed USD 245, including the pending USD 55 hotel charge and any nonrefunded change fee. Keep our hotel and my colleague's return ticket; please waive the hotel charge. I prefer a flight if feasible. Stairs are fine and any listed operator is allowed for my outbound. Approval consent-81988 covers my replacement outbound and permitted fare changes under the published contract. This is a stable scenario: no external updates are scheduled. Finish as soon as your confirmed booking and current requirements are verified; the episode horizon is minute 36."
    }
  ],
  "bookings": [
    {
      "id": "original-outbound",
      "status": "cancelled",
      "traveler": "lead",
      "kind": "transport",
      "price": 0
    },
    {
      "id": "hotel",
      "status": "confirmed",
      "traveler": "lead",
      "kind": "hotel",
      "price": 0
    },
    {
      "id": "colleague-return",
      "status": "confirmed",
      "traveler": "colleague",
      "kind": "return",
      "price": 0
    }
  ],
  "holds": [],
  "hotel_fee": 55,
  "net_transport_spend_usd": 0,
  "transport_payments_usd": 0,
  "transport_refunds_usd": 0,
  "retained_cancel_fees_usd": 0,
  "transport_ledger": [],
  "source_catalog": [
    {
      "id": "transport-guide",
      "title": "Weekday transfers in Northbridge",
      "version": 1
    },
    {
      "id": "hotel-terms",
      "title": "Existing room and disruption charge",
      "version": 1
    },
    {
      "id": "hotel-bulletin",
      "title": "Current waiver procedure",
      "version": 2
    },
    {
      "id": "traveler-profile",
      "title": "Durable preferences and scope",
      "version": 1
    },
    {
      "id": "fare-terms",
      "title": "Replacement fare contracts",
      "version": 1
    }
  ],
  "finished": false
}
```

This preview contains only actual observations and tool replies. Inspection actions advance virtual time. Run the solver in a fresh world.


## public-14921 — reactive

Offline tool inspection. Zero model calls; no performance score.

### Initial request

Repair my cancelled outbound to Northbridge. The client meeting is at 11:30. Spend no more than USD 265 extra including the hotel disruption fee. Waive that fee, keep the room, and preserve the colleague-return reservation. I prefer a flight if feasible. Stairs are fine and no carrier is excluded. Approval consent-14921 covers only my replacement outbound and refundable exchanges. Confirm a first replacement outbound by virtual minute 14; later approved exchanges remain permitted. Monitor changes through virtual minute 24, then finish by minute 36. A budget reduction applies to new commitments; previous approved charges remain valid. The hotel and colleague booking are never covered by outbound approval.

### Sources returned by read tools

#### hotel-terms (version 1)

Read completed at virtual minute 2.

Keep the confirmed room. USD 55 is pending. Read hotel-bulletin for the current evidence and deadline. Claims never cancel the room.

#### transport-guide (version 1)

Read completed at virtual minute 2.

Use these weekday transfers in Northbridge: flight 15 minutes, train 25 minutes, coach 35 minutes. Add the applicable value to terminal arrival. Last month all transfers were 20 minutes; that guide is obsolete. The 45-minute hotel shuttle is not the journey to the client.

#### traveler-profile (version 1)

Read completed at virtual minute 2.

Booking platform operators: Aster, Birch, Cedar. Default for later journeys: flight, all carriers allowed, no access requirement. Current-trip notices override this profile only for this trip. Do not overwrite the colleague booking or infer that another traveler shares a new restriction.

#### hotel-bulletin (version 2)

Read completed at virtual minute 4.

Archive: last year guests submitted type cancel-reference with code proof-0000. That procedure is withdrawn. Current Northbridge booking: submit evidence of type cancel-reference with code proof-14921 before virtual minute 24. Acceptance removes the USD 55 disruption charge while keeping the room. Claims accepted under an earlier version stay accepted.

### Available offers

Search completed at virtual minute 4.

| ID | Mode | Carrier | USD | Terminal arrival | Step-free | Fare rule | Cancellation fee |
|---|---|---|---:|---|---|---|---:|
| rail-14921-1 | train | Birch | 135 | 09:25 | False | flexible | 0 |
| air-14921-3 | flight | Aster | 160 | 08:55 | True | flexible | 0 |
| rail-14921-0 | train | Aster | 100 | 10:23 | True | flexible | 0 |
| rail-14921-4 | train | Birch | 150 | 08:45 | True | flexible | 0 |
| coach-14921-1 | coach | Birch | 130 | 09:28 | False | flexible | 0 |
| air-14921-2 | flight | Cedar | 155 | 08:40 | True | flexible | 0 |
| coach-14921-0 | coach | Aster | 85 | 10:23 | True | flexible | 0 |
| coach-14921-3 | coach | Aster | 140 | 09:00 | True | flexible | 0 |
| air-14921-0 | flight | Aster | 110 | 10:23 | True | flexible | 0 |
| rail-14921-3 | train | Aster | 150 | 08:58 | True | flexible | 0 |
| coach-14921-4 | coach | Birch | 140 | 08:50 | True | flexible | 0 |
| air-14921-1 | flight | Birch | 145 | 09:28 | False | flexible | 0 |
| coach-14921-2 | coach | Cedar | 135 | 08:35 | True | flexible | 0 |
| air-14921-4 | flight | Birch | 155 | 08:48 | True | flexible | 0 |
| rail-14921-2 | train | Cedar | 150 | 08:40 | True | flexible | 0 |

### Current observation after inspection

```json
{
  "case_id": "public-14921",
  "version": "travel-2026f-v8",
  "virtual_minute": 4,
  "horizon": 36,
  "handoff_minute": 24,
  "revision": 0,
  "tier": "reactive",
  "difficulty": "reactive",
  "booking_deadline": 14,
  "notices": [
    {
      "at": 0,
      "kind": "initial_request",
      "text": "Repair my cancelled outbound to Northbridge. The client meeting is at 11:30. Spend no more than USD 265 extra including the hotel disruption fee. Waive that fee, keep the room, and preserve the colleague-return reservation. I prefer a flight if feasible. Stairs are fine and no carrier is excluded. Approval consent-14921 covers only my replacement outbound and refundable exchanges. Confirm a first replacement outbound by virtual minute 14; later approved exchanges remain permitted. Monitor changes through virtual minute 24, then finish by minute 36. A budget reduction applies to new commitments; previous approved charges remain valid. The hotel and colleague booking are never covered by outbound approval."
    }
  ],
  "bookings": [
    {
      "id": "original-outbound",
      "status": "cancelled",
      "traveler": "lead",
      "kind": "transport",
      "price": 0
    },
    {
      "id": "hotel",
      "status": "confirmed",
      "traveler": "lead",
      "kind": "hotel",
      "price": 0
    },
    {
      "id": "colleague-return",
      "status": "confirmed",
      "traveler": "colleague",
      "kind": "return",
      "price": 0
    }
  ],
  "holds": [],
  "hotel_fee": 55,
  "net_transport_spend_usd": 0,
  "transport_payments_usd": 0,
  "transport_refunds_usd": 0,
  "retained_cancel_fees_usd": 0,
  "transport_ledger": [],
  "source_catalog": [
    {
      "id": "transport-guide",
      "title": "Weekday transfers in Northbridge",
      "version": 1
    },
    {
      "id": "hotel-terms",
      "title": "Existing room and disruption charge",
      "version": 1
    },
    {
      "id": "hotel-bulletin",
      "title": "Current waiver procedure",
      "version": 2
    },
    {
      "id": "traveler-profile",
      "title": "Durable preferences and scope",
      "version": 1
    }
  ],
  "finished": false
}
```

This preview contains only actual observations and tool replies. Inspection actions advance virtual time. Run the solver in a fresh world.


### Later observations from a separate read-only walkthrough

**Notice delivered at virtual minute 8:** The client has advanced our meeting to 09:30 today. The hotel check-in stays at 12:00. Exchange any replacement that cannot get me to the client in time.

**Notice delivered at virtual minute 22:** For this outbound only, do not use Aster or Birch. Cedar is permitted again if it was previously excluded. The client now needs me by 10:00. Keep access needs unchanged; the colleague’s existing return is unaffected.

## public-54079 — forecast

Offline tool inspection. Zero model calls; no performance score.

### Initial request

Plan my replacement outbound to Port Amber; the client needs me by 10:20 today. The additional-spending ceiling is USD 205, including the USD 55 hotel charge and all nonrefunded fare changes. Please waive that charge and preserve our room and the colleague-return booking. I prefer a flight when feasible; all listed operators are currently allowed. Stairs are currently fine. Approval consent-54079 covers my outbound and permitted fare changes, including their stated penalties. A first outbound must be confirmed by virtual minute 12; later approved repairs may use new offers. Read weather-forecast before choosing a fare; dispatch can revise its risk, possible delay and applicable mode, and forecasts can be wrong. Current initial offers close at minute 12. Recovery offers open at minute 18 and close at minute 28; a valid hold protects its quoted fare until the hold deadline. Stay responsive to traveler and source updates through minute 24, then finish by minute 36. A new spending limit applies to new commitments; previously approved charges remain valid. Hotel check-in at 13:00 is unrelated to the client arrival deadline.

### Sources returned by read tools

#### hotel-terms (version 1)

Read completed at virtual minute 2.

Keep the confirmed room. USD 55 is pending. Read hotel-bulletin for the current evidence and deadline. Claims never cancel the room.

#### transport-guide (version 1)

Read completed at virtual minute 2.

Current transfers for Port Amber: a flight arrival still needs 20 minutes to the client; rail passengers should allow 20 minutes after arrival, and coach passengers 20. These are additional minutes, not clock times. The archived 20-minute blanket allowance below is withdrawn. Weekend excursion transfers do not apply to this business trip.

#### traveler-profile (version 1)

Read completed at virtual minute 2.

Booking platform operators: Aster, Birch, Cedar. Default for later journeys: flight, all carriers allowed, no access requirement. Current-trip notices override this profile only for this trip. Do not overwrite the colleague booking or infer that another traveler shares a new restriction.

#### hotel-bulletin (version 2)

Read completed at virtual minute 4.

The cancelled reservation in Port Amber keeps its room. For that booking, attach a disruption-letter marked proof-54079. We need it before virtual minute 18. An automatic waiver is not available. A disruption-letter marked proof-0000 was used in an unrelated example; it is not evidence for this claim. Use the version number of this source, not the example number.

#### fare-terms (version 1)

Read completed at virtual minute 4.

Each search result states its fare contract. A locked fare cannot be cancelled or exchanged after confirmation. A fee fare can be cancelled with approval: the refund is its paid fare minus cancel_fee_usd. A flexible fare is fully refundable. Cancel an approved replacement before confirming another; preserve the hotel and colleague-return. Nonrefunded amounts count toward extra spending. Search also states when an offer opens and closes; a held offer can be confirmed only while the hold remains valid. These terms do not authorize changing another traveler or the existing room.

#### weather-forecast (version 1)

Read completed at virtual minute 4.

Lead-traveler current outbound watch for Port Amber: there is a 75 percent chance of the rail leg acquiring another 60 minutes before handoff. This warning applies only to weather_exposed train offers for this journey. Other modes are outside this watch. A companion weekend forecast mentioned 80 percent; ignore that different traveler and journey. The possible extra duration is not the appointment clock or an observed delay. Dispatch may revise the applicable mode and estimate; this is uncertain evidence.

### Available offers

Search completed at virtual minute 6.

| ID | Mode | Carrier | USD | Terminal arrival | Step-free | Fare rule | Cancellation fee |
|---|---|---|---:|---|---|---|---:|
| air-54079-2-flexible | flight | Cedar | 240 | 09:02 | True | flexible | 0 |
| air-54079-0-locked | flight | Aster | 100 | 09:00 | False | locked | 0 |
| air-54079-1-flexible | flight | Birch | 240 | 09:01 | True | flexible | 0 |
| air-54079-0-flexible | flight | Aster | 240 | 09:00 | False | flexible | 0 |
| air-54079-1-fee | flight | Birch | 125 | 09:01 | True | fee | 20 |
| air-54079-0-fee | flight | Aster | 125 | 09:00 | False | fee | 20 |
| air-54079-2-locked | flight | Cedar | 100 | 09:02 | True | locked | 0 |
| air-54079-2-fee | flight | Cedar | 125 | 09:02 | True | fee | 20 |
| air-54079-1-locked | flight | Birch | 100 | 09:01 | True | locked | 0 |

### Current observation after inspection

```json
{
  "case_id": "public-54079",
  "version": "travel-2026f-v8",
  "virtual_minute": 6,
  "horizon": 36,
  "handoff_minute": 24,
  "revision": 0,
  "tier": "forecast",
  "difficulty": "forecast",
  "booking_deadline": 12,
  "notices": [
    {
      "at": 0,
      "kind": "initial_request",
      "text": "Plan my replacement outbound to Port Amber; the client needs me by 10:20 today. The additional-spending ceiling is USD 205, including the USD 55 hotel charge and all nonrefunded fare changes. Please waive that charge and preserve our room and the colleague-return booking. I prefer a flight when feasible; all listed operators are currently allowed. Stairs are currently fine. Approval consent-54079 covers my outbound and permitted fare changes, including their stated penalties. A first outbound must be confirmed by virtual minute 12; later approved repairs may use new offers. Read weather-forecast before choosing a fare; dispatch can revise its risk, possible delay and applicable mode, and forecasts can be wrong. Current initial offers close at minute 12. Recovery offers open at minute 18 and close at minute 28; a valid hold protects its quoted fare until the hold deadline. Stay responsive to traveler and source updates through minute 24, then finish by minute 36. A new spending limit applies to new commitments; previously approved charges remain valid. Hotel check-in at 13:00 is unrelated to the client arrival deadline."
    }
  ],
  "bookings": [
    {
      "id": "original-outbound",
      "status": "cancelled",
      "traveler": "lead",
      "kind": "transport",
      "price": 0
    },
    {
      "id": "hotel",
      "status": "confirmed",
      "traveler": "lead",
      "kind": "hotel",
      "price": 0
    },
    {
      "id": "colleague-return",
      "status": "confirmed",
      "traveler": "colleague",
      "kind": "return",
      "price": 0
    }
  ],
  "holds": [],
  "hotel_fee": 55,
  "net_transport_spend_usd": 0,
  "transport_payments_usd": 0,
  "transport_refunds_usd": 0,
  "retained_cancel_fees_usd": 0,
  "transport_ledger": [],
  "source_catalog": [
    {
      "id": "transport-guide",
      "title": "Weekday transfers in Port Amber",
      "version": 1
    },
    {
      "id": "hotel-terms",
      "title": "Existing room and disruption charge",
      "version": 1
    },
    {
      "id": "hotel-bulletin",
      "title": "Current waiver procedure",
      "version": 2
    },
    {
      "id": "traveler-profile",
      "title": "Durable preferences and scope",
      "version": 1
    },
    {
      "id": "fare-terms",
      "title": "Replacement fare contracts",
      "version": 1
    },
    {
      "id": "weather-forecast",
      "title": "Lead outbound weather watch in Port Amber",
      "version": 1
    }
  ],
  "finished": false
}
```

This preview contains only actual observations and tool replies. Inspection actions advance virtual time. Run the solver in a fresh world.


### Later observations from a separate read-only walkthrough

**Notice delivered at virtual minute 10:** Dispatch replaced the current lead-outbound weather watch. Read weather-forecast; its estimate or applicable mode has changed, not merely its wording.

**Notice delivered at virtual minute 16:** For this outbound only, I now prefer rail when feasible and need step-free access. Birch is the only permitted operator, replacing the earlier carrier list. The client appointment is now 10:00. Finance allows USD 195 for new commitments including retained change fees; already confirmed charges stay approved. Future journeys still use my flight default; leave the companion return alone.

**Read weather-forecast, version 2, completed at minute 18:**

Current forecast for the lead outbound to Port Amber: flight disruption probability 15 percent, with a possible additional 90-minute arrival delay before handoff. Apply this only to weather_exposed flight options on this journey; the other modes are outside this watch. The archived 80-percent warning concerns a companion weekend excursion and does not apply. The percentage is uncertain evidence, not an observed delay or a promise. A later dispatch update can replace the estimated risk, duration or applicable mode.

**Notice delivered at virtual minute 20:** Dispatch resolved the current lead-outbound weather watch. Read the current report before handoff and inspect booked arrivals; current trip restrictions and recovery closing times still apply.

**Read weather-forecast, version 3, completed at minute 26:**

Operations report for the lead current outbound to Port Amber: weather-exposed flight services have now acquired 90 extra minutes beyond their original terminal arrivals. This observed result is already included in current search and booking arrivals. Do not add it again. Other transport modes are unaffected by this weather report. There is no further predicted change: future additional risk is zero percent, additional delay is zero, and no mode is under a future watch. Check the current trip restrictions and transfer guide before any permitted repair.
