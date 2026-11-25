# Task card — Cycle 4 — Builder: final corrections, Strategy v4.2

Two independent evaluators judged v4.1 "ready with conditions". The owner's arbiter consolidated their conditions below. Apply them with minimal edits and produce v4.2. This is the last pass of the cycle: do not add new content beyond these items.

## Owner principles (unchanged)
Protect what the project really controls; warn honestly about what it cannot control; never promise impossible protection. Objective 2 never depends on AI or on AI gates.

## Corrections to apply
1. **Sequence of legal and ethical approvals (both evaluators).** Before any live recording, for either objective: Law 81/2018 declaration filed (including Art. 96(12) transfers where applicable) and research ethics approval obtained. Move both to M0–3 and to G-1. "Non-retained trials" before G-1 may use only existing public or synthetic audio, never new recordings of people.
2. **Law 81/2018 also applies to cultural operations.** Add to the cultural gate (Annex E): filed declaration covering heritage recordings, including transfers if the depositary or backups are abroad. Replace "Article 97 counsel opinion" with "Article 97 licence, or exclusion of health data" (Art. 97 subjects health, genetic identity and sex-life data to licence).
3. **Withdrawn synthesis voice.** Clarify Annex D: if a private-synthesis contributor withdraws, their voice is retired from all project use, including K30 service, within 30 days. Existing weights still need not be erased.
4. **Archive capture before rights.** Single capture of endangered carriers during the audit requires the holder's written permission; the copy is sealed in escrow without access until rights and retention conditions are met.
5. **Household recordings of broadcasts.** Until counsel's opinion on third-party copying (to be obtained in M0–3), only inventory household recordings of broadcasts; do not digitise them. Household-created content proceeds normally.
6. **Cultural council independent of AI gates.** The permanent council for Objective 2 is constituted by M6 on its own schedule, not at G-2.
7. **Depositary and community repositories.** On transfer to the cultural depositary, community access rules (public, community-only, restricted, closed) remain in force; the depositary is custodian, not access authority.
8. **Payments and identity.** Keep payment records separate from contribution identifiers, with restricted access and limited retention.
9. **Withdrawal list.** State in consent and terms that synchronising with the public withdrawal list is a good-faith obligation that cannot be enforced on anonymous downloaders.
10. **Unverified sources.** Mark the 50-year broadcaster triage and the GDPR obligations as provisional pending counsel confirmation before G-1 and before cultural retention (Annex G, S9 and S10).
11. **Mixed programmes — pertinence.** Replace the seven parameters with this rule: eligibility = the programme contains audible spoken Lebanese of cultural value (no fixed minimum share); priority = carrier urgency, rarity and cultural value. Language share is estimated by a fixed human sample per programme (for example three 2-minute excerpts) by two listeners. The archive lead decides, with appeal to the cultural council; every exclusion is logged with its reason and reviewed yearly. Mixed programmes are preserved whole; Lebanese segments are catalogued, MSA segments are kept in context but not catalogued as targets.
12. **Length.** Body must be 1,600 words or fewer: remove the [A#] tags and the visual summary of section 1, and replace duplicated withdrawal and closure details in sections 5–6 with references to Annexes D and E. Remove the false trimming note in section 7. Do not remove sources (Annex G stays).

## Output
1. Strategy v4.2 in Markdown (body ≤ 1,600 words, annex ≤ 800 words excluding Annex G).
2. A single JSON code block: {"changes": [{"item": 1, "section": "...", "change": "..."}], "word_counts": {"body": 0, "annex": 0}}

## Strategy v4.1 (current text, with restored Annex G)

# **Lebanese in the AI Era: Strategy v4.1**

*Cycle 4 — Phase B — Builder version, corrected following owner dispositions*

## **1. Purpose: two objectives, one project**

The project pursues two independently valuable objectives, supported by common infrastructure but evaluated against different measures of success.

**Objective 1 — AI that serves Lebanese speakers.** Make spoken Lebanese, including everyday mixing with French and English, Arabic script and Arabizi, usable in AI and digital services. Prioritize Lebanese-only speakers with limited economic or educational resources, followed by the diaspora. Researchers and AI businesses remain secondary beneficiaries.

The planning forecast is that large AI models will probably speak common Lebanese reasonably well within approximately two years. The project's comparative value therefore shifts towards independent evaluation, accessible services, adoption and documented, consented data rather than ownership of a Lebanese foundation model.

**Objective 2 — Cultural preservation.** Preserve and sustain regional vocabulary, oral arts, occupational speech, cultural contexts and intergenerational transmission. AI remains an optional supporting instrument. The owner's position that cultural flattening is irreversible remains a value judgment, not an established empirical finding.

Objective 2 has its own institutional host, cultural depositary, budget line and continuity plan. Closing an AI route or Objective 1 does not close Objective 2. [A6, A7]

### **One project — two independent objectives**

**Objective 1**

AI access, evaluation and adoption

K30 · P-A · K07 · P-B · K21 · K16

Success: people complete real tasks.

AI institutional host

**Objective 2**

Living heritage and preservation

C-A · C-B · C-C · C-D

Success: heritage survives and remains in use.

Independent cultural host and depositary

Shared infrastructure

K02 governance · C35 consent · K22 provenance · K32 context · legal compliance

Shared standards, separate permissions and independent continuity.

## **2. Design principles**

1. Adoption is a deliverable; K30 owns real use.
2. No retention, publication or licensing before applicable gates pass.
3. Public ASR and private synthesis have distinct consent and access regimes.
4. Withdrawal stops future project uses; removal from existing model weights or uncontrolled copies is not promised. [A2, owner]
5. Wages precede speculative royalties.
6. Community authority never overrides individual rights.
7. Cultural preservation continues independently of AI performance or commercial revenue.
8. Protect what the project controls; disclose cloning, imitation and redistribution risks without promising voice-identity protection. [A2, A3, owner]

## **3. Objective 1 — AI access, evaluation and adoption**

**K30 — Human-AI hybrid access network.** Retain two desks, a telephone line and two user-selected low-risk digital tasks. Compare human-only, human+AI and speech-first AI through randomized validation samples. Measure completion, overrides, errors and bail-outs; correct and re-sample. Evaluation recordings remain non-public unless separately contributed through P-A. Human-only assistance survives AI failure. [A1]

**P-A — Inclusive paid collection.** Prioritize elderly, rural and non-literate speakers. Pay recording, transcription and validation work.

|                   | ASR                              | TTS / speech-to-speech |
| ----------------- | -------------------------------- | ---------------------- |
| Collection        | Crowdsourced                     | Few selected voices    |
| Environment       | Natural ambient noise            | Studio quality         |
| Audio             | Public after clearance           | Private                |
| Identity metadata | No names or identifying metadata | Pseudonyms             |
| Models            | Publication subject to gates     | Never published        |
| Consent           | Explicit public release          | Separate private use   |

Individuals may contribute to both. Prohibit public cross-collection metadata linkage, but explain that anyone obtaining public ASR audio may use it to imitate the speaker's voice. Quarantine third-party speech and sensitive disclosures. Retain trained-facilitator oversight for diaspora contributions. [A3, owner]

Pay through cash transfers or mobile wallets in available US dollars, with oral receipts for non-readers and a separate diaspora payment route. [Addition: payments]

**K07 — Mixing and Arabizi tools.** Retain language identification, transliteration, normalization and ASR-first prototypes. Compare third-party systems before local fine-tuning. Private synthesis proceeds by owner decision; K30 needs and third-party comparisons determine voice numbers and task coverage. [A11]

**P-B — Independent evaluation.** Retain native-speaker panels, paid cultural red-teaming, quarterly controlled tests and rankings. Evaluate third-party and project models under identical conditions, including noise, regional variation and code-switching. Protect hidden tests. Apply Annex B's iterative correction framework and serious-harm rule. [A1]

**K21 — Research network.** Retain participatory research and shared tasks using public ASR and separately authorized documentation. Private synthesis is not a general research-access resource.

**K16 — Levantine hub.** Retain annotation alignment and separate Lebanese evaluation. Defer joint models and regional data pooling.

## **4. Objective 2 — Cultural preservation**

Four integrated programmes retain the complete selected portfolio.

### **Programme C-A — Living heritage and transmission**

*Combines C21, C25, C26, C27 and C29.*

- Record crafts, farming, occupational speech, humour, games and oral traditions with paid participation and community-defined boundaries.
- Fund year-long apprenticeships, paid tradition bearers, apprentice stipends and transparent selection.
- Support recurring zajal, storytelling, theatre and sung-poetry gatherings.
- Protect gathering places through municipal cooperation, accessible venues, permits and small grants.
- Encourage household circles using optional spoken prompts without recording or registration requirements. Provide alternatives for isolated elders.

**Measure:** sustained apprenticeships, continued practice, accessible gatherings and community-defined transmission outcomes.

### **Programme C-B — Broadcaster archive rescue and rights clearance**

*Combines C01, C03, C05 and C02, supporting C10.*

Inventory public, private, regional and discontinued broadcasters and independent collections. Document ownership, formats, condition and accessibility; connect existing initiatives.

Audit programme-level language through human sampling. Include spoken Lebanese, everyday French/English mixing and mixed MSA/Lebanese programmes. Evaluate mixed programmes using Lebanese speech share, cultural value, separability and carrier condition, pending owner approval. Pure MSA programmes remain outside this rescue scope. [A9]

Capture endangered carriers once during audit. Language identification is an optional aid requiring human confirmation. [A10]

Prioritize endangered eligible recordings. Offer contractual preservation escrow without ownership transfer or compulsory publication. Pair paid regional preservation trainees with retired broadcaster technicians.

Retain four overlapping rights-triage categories: broadcasts older than 50 years; broadcaster-owned younger material; third-party works or performers; unknown rights. Publish a non-sensitive rights register distinguishing clearance from unresolved claims.

**Measure:** eligible collections inventoried, endangered recordings preserved, rights cleared and independent technician competence.

### **Programme C-C — Mobile rescue, listening and circulation**

*Combines C04, C13 and C10.*

Operate a mobile rescue-and-listening unit. Return originals and copies of household-created content, subject to applicable rights. Digitize household recordings of broadcasts for preservation of the original; withhold replacement copies pending counsel's opinion on third-party copying. Retention requires separate consent and rights clearance. [A15]

Provide facilitated, solar-backed offline listening points in libraries, municipalities and community centres without literacy, registration or device requirements.

Re-broadcast cleared spoken-Lebanese programming. Broadcasting does not prevent unauthorized recording.

**Measure:** household materials rescued, listening-point availability, underserved communities reached and cleared programmes circulated.

### **Programme C-D — Community archives and linguistic diversity**

*Combines C09, C16 and C33.*

Establish community-governed regional repositories with shared preservation services, local access authority, independent appeals and external reviews.

Enable diaspora cataloguing through Arabic script, Arabizi and spoken annotations. Preserve spelling and regional variation.

Invite Armenian, Syriac, Aramaic, Kurdish, Domari and other communities to define preservation priorities. Provide Deaf-led visual preservation of Lebanese Sign Language.

Collections may be public, community-only, restricted or temporarily closed. Heritage collections never become AI training material by default.

**Measure:** community-approved collections, contextual catalogue quality, representation and effective community control.

## **5. Shared infrastructure and legal safeguards**

**K02 — Governance.** Legally capable hosts hold controller responsibility for their respective operations. Constitute an interim community-majority council at M0, replaced at G-2. Quorum requires a majority of appointed seats, never fewer than three members, including a community majority. Legal and privacy vetoes remain absolute. Other disagreements suspend only the contested activity and must be resolved within 30 days; otherwise, including persistent lack of quorum, the independent reviewer decides. [A7, A8]

**C35 — Consent.** Use oral-first, comprehension-tested modules for ASR publication, private synthesis, heritage, listening, broadcasting and research. Provide anonymous withdrawal credentials, optional sealed contact records held by the privacy officer and accessible complaints. No voice-matching lookup. Failed comprehension or doubtful capacity excludes public ASR participation; lawful heritage participation with a trusted companion remains possible. [A2–A5, A14]

**K22/K32 — Provenance and context.** Retain lineage, contextual envelopes and release validation. Separate public manifests from protected compliance records.

**Legal and operational safeguards:**

- Law 81/2018: require filed declarations before collection, including Article 96(12) for foreign processing, backups or successors. Article 98 makes declared transfers public. Obtain Article 97 counsel opinion if health data survive quarantine. [A13]
- Review applicable diaspora privacy jurisdictions, including GDPR where directly applicable, before G-1. Retain applicable impact assessments and transfer safeguards. [A16]
- Verify secure storage at G-1; verify synthesis compute and associated access locations at G-3. Lebanese infrastructure remains the synthesis default. [A12]
- Obtain counsel's opinion on third-party copying. Broadcaster rights, underlying works and performers require separate clearance; fifty years alone does not establish unrestricted reuse. [A15]
- Provide energy resilience, encrypted offline backups at a second site and manual outage procedures. [Addition: resilience]

## **6. Delivery and continuity**

| Period    | Objective 1                           | Objective 2                                 |
| --------- | ------------------------------------- | ------------------------------------------- |
| M0–3      | Host, interim council, G-1            | Cultural host, depositary, inventory design |
| M3–6      | Ethics approval, pilot, G-2           | Audits, apprenticeships, mobile pilots      |
| M6–12     | ASR tools, benchmarks, synthesis, G-3 | Archive rescue, technician training         |
| M12–18    | G-4, adoption, K16                    | Escrow, listening, broadcasting             |
| M18–24    | G-5, independent review               | Funding and preservation review             |
| After M24 | Funded continuation or closure        | Independent cultural continuation           |

Before cultural retention, contract the cultural depositary as Objective 2's host and continuity anchor. Establish its own budget line and month-18 cultural funding plan, including apprenticeship continuity. [A6, A7]

Before AI collection, contract successor custody and residual compliance provision. Require a month-18 operating plan based on institutional support, grants and service agreements.

Without renewal, cease new collection and licensing in the closing operation. On project closure, transfer heritage to the depositary under existing consents. Securely delete private synthesis assets, quarantine, service logs and test sets; retain only necessary compliance evidence and residual public-ASR governance. [A6]

## **7. Outstanding gaps**

Adoption beyond pilot locations, actual compute infrastructure, institutional appointments, long-term financing, archive eligibility, carrier condition and rights remain unverified.

[A17: duplicated reasoning removed throughout the body.]

# **Annex**

## **A. Operational AI gates**

| Gate                   | Conditions                                                                                                                                                                                                                                                |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| G-1 — Retention        | Contracted host/successor; filed declaration including applicable foreign transfers; diaspora jurisdiction review; tested consent and withdrawal; verified secure storage; provenance; quarantine. Otherwise non-retained trials only. [A5, A12–A14, A16] |
| G-2 — Expansion        | Audit 10–15-speaker pilot; constitute permanent council; activate appeals; define validation sampling. Obtain research ethics committee approval for K30 randomization and P-A collection before their implementation and G-2. [A1, A8, addition: ethics] |
| G-3 — Release/training | Validator, datasheet, consent and rights clearance, resolved quarantine, test/train separation. Verify private synthesis compute, location, access and isolation. [A12]                                                                                   |
| G-4 — Commercial use   | K30 baseline and correction cycle; council approval; lawful purposes; applicable contracts; independently funded operations. Public ASR remains downloadable. [A1]                                                                                        |
| G-5 — Scaling          | Document validation, corrections, unresolved limitations, safety, withdrawal and continuity. Performance targets guide corrections, not authorization. [A1]                                                                                               |

## **B. Iterative validation and serious-harm rule [A1]**

Compare both AI routes with randomized human-only assistance across selected tasks. Sample Lebanese-only, non-literate, low-income, rural, elderly and phone-only users, including relevant intersections.

Reference targets—not pass/fail criteria:

| Indicator                        | Reference target                                                           |
| -------------------------------- | -------------------------------------------------------------------------- |
| Completion                       | At least 80%                                                               |
| AI–human completion difference   | At least −5 percentage points                                              |
| Excess errors                    | No more than 3 percentage points                                           |
| Excess re-contacts               | No more than 3 percentage points                                           |
| Human+AI completion time         | Shorter than human-only                                                    |
| Repeat use                       | At least 40% within 60 days, only for tasks recurring within that period   |
| Five leading remediable failures | Address all; reduce recurrence by 20%                                      |
| Bail-outs                        | Count as AI non-completion; record predefined minimal overrides separately |

Continuous validation; the serious-harm rule applies at every stage.

Report sample sizes, observed differences and uncertainty. Investigate disparities and document corrections. Inconclusive observations never count as failure. No confirmatory power, familywise-error or mandatory per-subgroup significance requirement applies.

One serious attributable privacy or task-related harm triggers immediate suspension and independent investigation. Human-only support continues. Repeated target shortfalls require further correction, not automatic closure.

## **C. Access and release contract**

Public ASR is not anonymous merely because names are absent. Publish cleared audio, transcripts, non-identifying context and purpose-specific terms. Exclude identifiable third-party material and hidden benchmarks. Downloads require no registration. [A3, A4, owner]

Private synthesis tiers:

- Tier 0: safe documentation and aggregates.
- Tier 1: restricted internal derivatives and embeddings.
- Tier 2: private recordings, training environments and models; authorized personnel only; no external audio or model publication.

Record opaque identifiers, lineage, asset class, consent version, purposes, context, annotation versions, script, restrictions and withdrawal status. Derivatives inherit restrictive permissions. Unknown origin, conflicting permissions, withdrawn sources and test/train overlap block release. JSON validation precedes PROV-O mapping.

## **D. Quarantine, withdrawal and appeals**

Mute separable incidental speech; purge originals within 14 days after quality assurance. Hold identifiable bystanders encrypted for at most 30 days; re-consent, mute or purge. Scrub sensitive disclosures within 14 days or purge. Immediately purge unconsented minors or evident distress.

Resolve appeals independently within seven days, without extending quarantine or delaying individual deletion.

Acknowledge withdrawal within seven days; immediately block future project uses of the withdrawn contribution, including private synthesis use on the contributor's behalf. Remove controlled source copies within 30 days unless lawful retention is necessary. Notify contracted recipients and require deletion attestations within 30 days. [A2]

Consent explains that existing weights need not be erased, voice identity may remain reproducible, and public copies may remain accessible or enable imitation. No voice-identity removal or segment-exclusion mechanism is promised. [A2, A3, owner]

Publish a non-identifying withdrawal list containing affected record identifiers, deprecated releases and checksums. Terms require users to synchronize with it. Offer optional sealed contact records for credential recovery; no voice matching. [A4, A5]

## **E. Cultural gates**

Before retention: contracted cultural depositary, applicable consent, language eligibility, community authority and preservation rights. Before listening, online access or broadcast: separate clearance.

Failed comprehension or doubtful capacity excludes public ASR; companion-supported heritage participation remains subject to lawful consent.

Review governance, preservation integrity and transmission annually. Failure stops only the affected cultural operation. Closure transfers heritage under existing consents. [A6, A7, A9, A14]

## **F. Support register**

**Reasoning — premises:**

- **R1:** Small validation samples support correction discovery, not comprehensive confirmatory inference. [A1]
- **R2:** Public audio and existing weights cannot be reliably recalled; project-controlled future uses can stop. [A2–A5, owner]
- **R3:** Contracted cultural custody and separate financing enable independent continuity. [A6, A7]
- **R4:** Absolute protective vetoes and bounded ordinary disputes serve different functions. [A8]
- **R5:** Mixed programmes may contain valuable Lebanese speech; single capture reduces fragile-carrier handling. [A9, A10]
- **R6:** Synthesis compute is distinct from secure retention. [A11, A12]
- **R7:** Apply owner-accepted legal, capacity, copyright and jurisdiction safeguards pending counsel verification. [A13–A16]
- **R8:** Payment accessibility, ethics approval and outage resilience support implementation. [Additions]

## **G. Source register (restored by the verifier; fragments checked on 24 Nov 2026 unless marked)**

| ID | Supports | Source | Exact fragment |
|---|---|---|---|
| S1 | §5 Law 81/2018, foreign transfers in declarations | https://lebaneselegislation.com/en/law/278573/article/96/ | «عند الاقتضاء، نقل البيانات ذات الطابع الشخصي الى دولة اخرى في اي شكل كان» |
| S2 | §5 Law 81/2018, licensed categories (state security, criminal, health/genetic/sex life) | https://lebaneselegislation.com/en/law/278573/article/97/ | «تخضع للترخيص معالجات البيانات ذات الطابع الشخصي المتعلقة» |
| S3 | §5 Article 98 publication of declared transfers | https://lebaneselegislation.com/en/law/278573/article/98/ | "the personal data intended to be transferred to a foreign State" (site translation) |
| S4 | §2 principle 8; §5 market practice | https://github.com/openai/whisper/blob/main/model-card.md | "audio and the corresponding transcripts collected from the internet" |
| S5 | Annex C, public ASR not anonymous | https://www.nature.com/articles/s41746-025-01987-3 | "balance privacy and utility" |
| S6 | §1 evaluation value | https://arxiv.org/abs/2505.00114 | "a new benchmark derived from native Lebanese content" |
| S7 | K07 Arabizi resources | https://aclanthology.org/R19-1138/ | "11.3K positive and 13.3K negative words" |
| S8 | K21 participatory research | https://arxiv.org/abs/2010.02353 | "MT benchmarks for over 30 languages" |
| S9 | §5 GDPR (Arts. 9, 35, 17(2)) | https://eur-lex.europa.eu/eli/reg/2016/679/oj | Statutory wording; fragment not retrieved by the verifier |
| S10 | C-B rights triage, 50-year broadcaster term | https://www.wipo.int/wipolex/en/legislation/details/2786 | Not retrieved by the verifier; counsel to confirm |

