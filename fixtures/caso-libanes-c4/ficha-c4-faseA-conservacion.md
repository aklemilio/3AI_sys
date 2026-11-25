# Task card — Cycle 4, Phase A (open options) — Cultural preservation

You are one of three independent explorers. You will not see the others' work and they will not see yours. Your only job is to WIDEN the set of options. Do not critique, rank or converge.

## Objective
Preserve the spoken Lebanese cultural and linguistic heritage that is at risk of being flattened or lost. This objective is independent of whether large AI models learn to speak Lebanese. It is NOT about making AI speak Lebanese; AI may be a tool or play no role at all.

## Framing
- Decision this serves: open options. A later phase will validate them.
- Fixed: the objective above. Everything else, including the premise that something is being lost, can be questioned.
- Must cover: audiovisual archives held by broadcasters (radio and television), with their rights questions. Beyond that, cover the whole chain: find → record or rescue → preserve → describe → give access → keep it alive in real use → transmit to next generations.
- For whom and who could be left out: consider people who do not read or write, low-income groups, rural and regional communities, older people, the diaspora, and future generations.
- Faces of the problem (each can impose different rules): Lebanese law as written; EU data protection (GDPR) required by foreign funders; real market practice (large companies harvest public web data, including voice); copyright and broadcaster ownership of archives. Add any face you find.
- Do not use or reveal: personal data, names of private individuals.

## Mandatory techniques (at least one option per technique; tag each option with the technique used)
- T1 Actors: who else holds, creates or could carry this heritage?
- T2 Scales: household, neighbourhood, region, nation, diaspora, global.
- T3 Premise inversion: what if the loss is not happening, or not where we think?
- T4 Analogies: what did other languages, dialects or cultures do (successes and failures)?
- T5 Alternative routes: different paths to the same end, including routes without technology.
- T6 Reframing: restate the problem in another way and derive options from that.
- T7 No-intervention scenario: what happens in 5–10 years if nobody does anything, and what value remains to act on?

## Quantity and diversity
- 15–25 options.
- At least one third must not depend on AI.
- At least one option per chain stage listed above.

## Support for claims
Every claim declares its support type:
- "source": empirical fact. Give the URL and an exact short fragment from the source. Never invent a source. If you cannot give a fragment, use "reasoning" instead.
- "reasoning": give the premises explicitly.
- "position": a value or stance, declared as such.

## Output
A single JSON object inside ONE code block, nothing else:

```json
{
  "no_intervention_scenario": {
    "summary": "...",
    "what_is_lost": ["..."],
    "what_value_remains": ["..."],
    "support": [{"type": "source|reasoning|position", "claim": "...", "url": "...", "fragment": "...", "premises": ["..."]}]
  },
  "faces_found": [{"face": "...", "what_it_requires": "..."}],
  "options": [
    {
      "id": "O1",
      "name": "max 8 words, readable",
      "description": "2–4 sentences",
      "technique": "T1..T7",
      "chain_stage": "find|record_or_rescue|preserve|describe|access|keep_alive|transmit",
      "scale": "household|neighbourhood|region|nation|diaspora|global",
      "depends_on_ai": true,
      "actors": ["..."],
      "who_benefits": ["..."],
      "who_could_be_left_out": ["..."],
      "faces_affected": ["..."],
      "what_would_make_it_fail": "...",
      "support": [{"type": "source|reasoning|position", "claim": "...", "url": "...", "fragment": "...", "premises": ["..."]}]
    }
  ]
}
```
