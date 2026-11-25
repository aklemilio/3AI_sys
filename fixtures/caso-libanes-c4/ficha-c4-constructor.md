# Task card — Cycle 4, Phase B — Builder: Strategy v4

You are the builder. Produce Strategy v4 from Strategy v3 (below). Another model will attack your version afterwards, so every change must be traceable.

## What changes from v3
1. **Two objectives, one project.** Restructure the strategy around two distinct objectives that come from the same project:
   - Objective 1 — AI that serves Lebanese speakers: access, independent evaluation and real use, even when the models belong to third parties. Assume large AI models are likely to speak common Lebanese reasonably well within about two years (a forecast, not a fact); value shifts towards evaluation, adoption and consented, documented data.
   - Objective 2 — Cultural preservation: keep alive and preserve the spoken heritage that flattening erases, independently of what AI models do. Build it from the portfolio below. AI plays a minor role here.
2. **Owner decisions (binding):**
   - Speech-recognition (ASR) recordings are public by design, collected with ambient noise through crowdsourcing; no names are requested and metadata never includes them.
   - Speech-synthesis recordings (TTS and speech-to-speech) are few voices, studio quality, private use only: neither recordings nor models are published. Their speakers use pseudonyms.
   - The same person may contribute to both sets.
   - Broadcaster radio and TV archives are in the portfolio only for programmes in spoken Lebanese (including everyday mixing with French and English). Content in Modern Standard Arabic is out of scope: it does not serve this objective. The prior audit by programme classifies each programme by language (spoken Lebanese, MSA, mixed, other) and only spoken-Lebanese programmes enter rescue, cataloguing and re-broadcast (C03, C01, C05, C02, C10). Much of the public broadcaster's archive is expected to be MSA, so the audit is a filter, not a formality.
3. **Firm defects to fix:**
   - D1 (redefined): v3 assumes identifiable audio is never downloadable in open form (design principle 3, tier 2 by default, tier-1 speech embeddings). This contradicts the public ASR decision. Rewrite the access model: ASR audio is public, protected by explicit consent to publication, no names or identifying metadata, quarantine of sensitive and third-party content before publication, and withdrawal effective for future releases. Access tiers and restrictions on voice representations apply to synthesis data only.
   - D2: verify in which country compute runs and whether Lebanese Law 81/2018 requires authorisation to transfer data abroad; private synthesis data is trained locally or with authorised transfer.
4. **Disputed points to resolve (evaluators disagreed whether they block):**
   - H6: define the minimum AI performance floor and non-inferiority against the human-only route, so an AI that fails the most excluded cannot pass.
   - H14: financing and continuity after month 24, including who keeps deletion and withdrawal duties if funding stops.
   - H15: roles, tie-break between vetoes, and succession if the host institution closes.
5. **Non-blocking, fix if room:** H9 quarantine appeals with a maximum deadline; H12 statistical power and a harm-stopping rule.
6. **Faces of the problem** to cover explicitly: Lebanese law as written; GDPR required by foreign funders (voice for unique identification is special-category data; impact assessment for high-risk processing); market practice (public speech is harvested for training); copyright and broadcaster ownership of archives.

## Rules
- Objective 1: minimal edits to v3. Every change cites the item it addresses (D1, D2, H6, H14, H15, H9, H12, or an owner decision).
- Objective 2: integrate the portfolio below into a small number of programmes. You may merge options that share a mechanism; say which. Do not drop any; if one cannot fit, list it under "Deferred" with the reason. Include the two combinations proposed independently by two screeners: a mobile rescue-and-listening unit (C04 + C13) and paid training of regional audiovisual preservation technicians paired with retired broadcaster technicians.
- Show how the two objectives share infrastructure (consent protocol, provenance, governance) without merging their goals.
- Support: every factual claim declares "source" (URL plus exact short fragment; never invent) or "reasoning" (premises). Keep v3's verified sources where still relevant.
- Length: body up to 1,600 words; annex up to 800 words. English.
- Do not include budget figures, negotiation status or names of private individuals.

## Objective 2 portfolio (selected by rule after blind screening; no option was voted fatal)

**C21 — Record crafts, work and daily life in context** (rule)
Document spoken practices in their cultural settings rather than collecting isolated vocabulary or scripted sentences alone. Potential subjects include farming terminology, craft instruction, marketplace interaction, oral poetry, games, humour, lullabies and traditional forms of mediation. Let participating communities determine appropriate contexts, restrictions and whether documentation should occur at all.
Variants: Occupational Soundscapes and Craft Lexicon Field Recording.
Conditions raised by screeners: Preserves rich situational vocabulary and oral genres with community control over boundaries and meaning. / Preserves vocabulary, interaction and cultural meaning together. Compensate participants and allow them to exclude confidential, sacred or commercially sensitive practices. / Captura lo que más se pierde: el léxico ligado a prácticas. El veto comunitario previsto es correcto.

**C25 — Paid apprenticeships with tradition bearers** (rule)
Pay elderly bearers (zajal poets, storytellers, work-song singers, craft speakers) a stipend to train young apprentices for a year. This treats bearers as teachers rather than as subjects to be recorded.
Variants: Oral Heritage Apprenticeships; Live Zajal and Folk-Poetry Apprenticeship Stipends.
Conditions raised by screeners: Directly sustains low-income elderly tradition bearers and transfers embodied verbal arts across generations. / Directly transfers endangered embodied knowledge while compensating bearers. Transparent selection, apprentice stipends and flexible participation improve equitable access. / Transmisión viva con precedentes de tesoros humanos vivos (UNESCO). Requiere financiación plurianual y una selección transparente.

**C26 — Pay for living practice: zajal, storytelling, theatre** (rule)
Fund regular, low-cost evenings of zajal, storytelling and sung poetry in villages, neighbourhood cafés and diaspora clubs, with young performers paired with veterans. The aim is living use, not recording.
Variants: Pay for Living Cultural Practice.
Conditions raised by screeners: Keeps improvised oral poetry and storytelling alive as community social life rather than static museum artefacts. / Sustains living oral performance rather than passive storage. Support ordinary community participants alongside established performers and avoid imposing standardized repertoire. / Mantiene el uso real. Hay que evitar el formato de espectáculo folclórico y priorizar los espacios ya existentes.

**C10 — Re-broadcast archives on radio and TV** (rule)
Instead of putting the archive online first, schedule rights-cleared archive programmes on terrestrial TV and radio. Broadcast reaches older, low-income and rural audiences without internet access or literacy, and it is harder to scrape in bulk.
Variants: Radio as a Living Heritage Channel.
Conditions raised by screeners: Reaches older, rural, and non-reading audiences effortlessly through familiar broadcast media without internet barriers. / Established distribution mechanism with low literacy barriers. Broadcasting reduces some harvesting opportunities but cannot prevent unauthorized recording. / Llega a mayores y personas que no leen. Ante las limitaciones de Télé Liban, sumar emisoras privadas y regionales.

**C13 — Offline listening points** (rule)
Provide free listening stations in libraries, municipal buildings, community centres and mobile cultural facilities. Organize selections by recognizable spoken themes and provide facilitators who can guide visitors without requiring reading, registration or a personal device. Use only recordings cleared for the relevant form of public or supervised listening.
Variants: Solar-Powered Offline Village Audio Boxes.
Conditions raised by screeners: Solar-backed offline stations solve electricity and connectivity gaps for low-income and non-reading villagers. / Directly addresses device ownership, connectivity and literacy barriers. Mobile facilities and facilitated listening can reach people excluded from conventional libraries. / Accesible y seguro. Su éxito depende del mantenimiento, de los horarios y de la energía solar en zonas rurales.

**C29 — Intergenerational family circles without recording** (rule)
Support recurring household storytelling, shared meals, oral games, songs and conversations between generations. Offer optional spoken prompts through radio or community educators without requiring families to record, upload or submit evidence of participation. Allow each household to choose its own linguistic practices and traditions.
Conditions raised by screeners: Zero-surveillance household transmission that respects privacy and works well for non-literate and low-income families. / Low-cost, privacy-preserving transmission that respects household autonomy. Offer inclusive alternatives for isolated elders and families without intergenerational contact. / Muy seguro y respetuoso. Su impacto es difícil de verificar y puede diluirse sin estímulos concretos.

**C35 — Single oral-first consent protocol** (rule)
Write one plain-language, oral-first consent protocol that satisfies both GDPR (explicit, granular, revocable consent; no speaker identification unless agreed) and Lebanese law, so that foreign-funded projects do not each improvise. It includes a version read aloud for non-readers.
Conditions raised by screeners: Crucial ethical infrastructure that protects non-literate speakers through spoken consent while harmonizing international compliance. / Shared oral-first protocol reduces exclusion. Use modular jurisdiction-specific provisions and distinguish consent withdrawal from obligations concerning previously lawful processing and redistribution. / Bajo costo y efecto transversal. Debe articularse con la Ley 81/2018 y validarse con proyectos piloto.

**C04 — Rescue household tapes and videos** (rule)
Invite families to bring old VHS tapes, cassettes and reel recordings made from TV and radio, or of family gatherings, to mobile digitisation days. The family keeps the original and a copy. With consent, the archive keeps a copy for gaps in broadcaster holdings.
Variants: Community Attics and Forgotten Recordings; Municipal Library Cassette and VHS Rescue Kiosks; Mobile Recording and Rescue Workshops.
Conditions raised by screeners: Directly reaches non-literate, rural, and elderly households while filling major gaps in commercial archives. / Recovers everyday speech absent from institutional archives. Separate digitisation services from archive consent, including permissions concerning other recorded individuals. / Tiene amplio alcance popular y precedentes de jornadas comunitarias. Exige consentimiento claro y control familiar sobre la copia archivada.

**C09 — Community-governed regional sound archives** (rule)
Establish independent regional repositories governed by participating communities, with shared preservation services but local authority over access and interpretation. Permit public, community-only, restricted and temporarily closed collections. Draw on the FirstVoices model without assuming that Indigenous governance arrangements elsewhere transfer directly to Lebanon.
Conditions raised by screeners: Centers rural and regional communities with granular access tiers, requiring clear safeguards against local gatekeeping. / Strong regional representation and contextual authority. Shared technical infrastructure and individual appeals against community gatekeeping are important safeguards. / Buen gobierno local. Riesgos: financiación discontinua y captura por notables locales. Prever revisión externa periódica.

**C27 — Protect gathering spaces** (rule)
Reframe the heritage as the social practice (evening gatherings, village squares, cafés, seasonal festivals), not the recorded artefact. Support the times and places where people speak together, through municipal permits, small grants and safe venues.
Variants: Preserve Spaces Where Lebanese Lives.
Conditions raised by screeners: Tackles root social drivers of language shift by sustaining real village and neighborhood gathering places. / Protects social conditions supporting spontaneous transmission. Ensure accessible venues and participation beyond established local, gender, political or sectarian networks. / Ataca la causa social de la pérdida. Son microsubvenciones municipales de bajo costo, aunque vulnerables a la crisis.

**C33 — Include Lebanon's other spoken heritages** (rule: tie at the cut)
Widen the scope to Armenian, Syriac and Aramaic liturgical speech, Kurdish, Domari and Lebanese Sign Language, along with community-specific registers. Ask each community what it wants preserved and who should hold it.
Conditions raised by screeners: Essential for genuine equity across Lebanon's endangered minority and sign languages under community-led governance. / Addresses neglected linguistic communities. Sign language requires visual preservation and Deaf-led governance; communities must define their own identities, terminology and documentation priorities. / Incluye las herencias más amenazadas (domari, lengua de señas libanesa). El liderazgo comunitario es indispensable.

**C16 — Collaborative cataloguing by listening** (rule: chain-stage coverage (describe))
Run an online platform where volunteers anywhere transcribe and tag archive audio, in Arabic script or in an agreed Arabizi convention, and add place and context notes. This turns diaspora nostalgia into catalogue work.
Variants: Listening-Based Community Cataloguing.
Conditions raised by screeners: Engages diaspora volunteers effectively, though text-based transcription inherently excludes non-literate contributors. / Useful diaspora participation mechanism. Accept spoken annotations and spelling variation to avoid excluding non-writers or normalizing away regional linguistic differences. / Moviliza a la diáspora y tiene precedentes de colaboración masiva. Excluye a quienes no leen. Requiere una convención ortográfica previa.

**C03 — Rescue tapes at private and regional stations** (owner decision: broadcaster archives enter)
Survey private TV channels, regional and defunct radio stations, and their retired technicians for surviving tapes. Offer free transfer in exchange for a preservation copy and a basic rights agreement. Give priority to formats at physical risk.
Conditions raised by screeners: High-urgency physical rescue of decaying regional magnetic tapes before institutional memory and hardware vanish. / Addresses irreversible physical deterioration. Prioritize unique regional recordings, endangered formats and retired technicians' knowledge of undocumented collections. / Urgente por la degradación física de los soportes. La transferencia gratuita reduce el temor a perder valor comercial.

**C01 — National inventory of broadcaster archives** (owner decision: prerequisite of archive rescue)
Create an inventory of audiovisual collections held by public and private television stations, national and regional radio stations, discontinued broadcasters and independent production companies. Document collection-level information about formats, periods, programme types, preservation conditions, ownership and accessibility without publishing recordings or personal data. Connect this inventory to existing preservation initiatives rather than assuming that preservation work must start from zero.
Conditions raised by screeners: Essential foundational mapping that prevents duplication and locates endangered rural and regional broadcast holdings. / Strong enabling infrastructure. Include discontinued broadcasters and informal regional collections; assign responsibility for periodic updates. / Base para C02–C05. Impacto indirecto. Requiere un custodio institucional fijo que lo mantenga actualizado.

**C05 — Preservation escrow without publication** (owner decision: archive instrument)
Offer radio and television broadcasters contractual arrangements under which preservation copies are deposited with an independent custodian while ownership and publication rights remain separately governed. Establish permitted preservation operations, security arrangements, conditions for releasing material, succession procedures and responses to broadcaster closure. This route allows archival rescue without making public release a condition of participation.
Variants: Broadcaster Dark-Archive Escrow and Orphan-Work Safe Harbor.
Conditions raised by screeners: Proven dark-archive legal mechanism that overcomes broadcaster reluctance, though immediate community access remains limited. / Separating preservation from publication substantially reduces participation barriers. Contractual escrow must not be mistaken for statutory immunity from third-party claims. / Separa el rescate de la publicación. Depende de contratos que autoricen la migración y de un custodio estable.

**C02 — Rights triage and clearance for archives** (owner decision: archive instrument)
Reframe the bottleneck as legal uncertainty rather than technology. Sort every archive item into one of four buckets: over 50 years since broadcast; broadcaster-owned and under 50 years; contains performers or third-party works; unknown. Publish the register so that funders and users can act on the items that are already clear.
Variants: Broadcaster Rights and Licensing Clearinghouse.
Conditions raised by screeners: Unblocks usable archives without statutory reform, though best hosted outside ministries to survive turnover. / Age since broadcast alone cannot establish clearance. Require separate assessment of underlying works, performers, applicable rights periods and contractual restrictions. / Que hayan pasado más de 50 años desde la emisión no libera las obras subyacentes (autores, intérpretes). Las categorías necesitan revisión jurídica previa.

## Strategy v3 (current validated text)

# Lebanese in the AI Era: Strategy v3

## Purpose
Make spoken Lebanese Arabic, including everyday mixing with French and English in Arabic script or Arabizi, usable in AI and digital services, and ensure that people who rely on Lebanese alone can use what is built. Priority groups: Lebanese-only speakers with low economic or educational resources, the diaspora and future generations. Researchers and AI businesses, who lack a solid Lebanese corpus, are secondary users.

Owner stance: cultural flattening is irreversible; this is a value, not an empirical finding.

## Evidence base
- General benchmarks can overstate Lebanese performance: [one base model scored 85.5 on FLoRes but 68.7 on LebEval](https://arxiv.org/abs/2505.00114).
- Arabizi resources exist but are limited: [SenZi provides 3.4K annotated Lebanese Arabizi tweets and about 1M Facebook comments](https://aclanthology.org/R19-1138), and [word-level language identification exists for Arabizi mixed with English, French and Arabic, without specifying dialects](https://aclanthology.org/2022.wanlp-1.18).
- Law 81/2018 [generally requires a processing declaration; sensitive categories may require ministerial licences, not consent alone](https://www.dlapiperdataprotection.com/?t=law&c=LB). Legal review is mandatory.

## Design principles
1. Adoption is a deliverable: K30 is accountable for real use by excluded speakers.
2. Gates, not parallel tracks: nothing is retained, released or licensed before its gate passes (annex).
3. Controlled access by default, with no public download of raw identifiable audio, because [a 2025 npj Digital Medicine article finds speech data cannot be both fully useful and perfectly anonymous](https://www.nature.com/articles/s41746-025-01987-3).
4. Honest withdrawal: withdrawn data leaves future releases and training. Removal from already trained weights is never promised.
5. Wages before royalties: [Karya pays wages plus royalties](https://www.globalindian.com/story/manu-chopra/), but [its model remains small, royalties are thin and firms prefer buying data outright](https://www.policycircle.org/?p=48085). Contributors are paid for their work; any royalty is extra.
6. Community authority adapted from the [CARE principles of the Global Indigenous Data Alliance (2019): collective benefit, authority to control, responsibility and ethics](https://www.data.cam.ac.uk/policies-ethics-legal/care-principles). CARE was written for Indigenous data; this is an adaptation.

## 24-month sequence
- Months 0–3: secure legally capable host; legal review; K30 baseline, spoken-consent tests and non-retained trials; release validator; G-1.
- Months 3–6: P-A pilot with 10–15 speakers; council nominated through accessible channels; two K30 tasks live; G-2 at month 6.
- Months 6–12: P-A expansion; K07 ASR-first prototypes; first P-B ranking; G-3 before research release.
- Months 12–18: G-4 before commercial licensing; hosted tier-2 job access; K16 annotation alignment.
- Months 18–24: review against indicators; a second collection round only after G-5. Certification is deferred beyond month 24.

## Programmes
**K30 Human-AI hybrid access network (adoption owner).** One lead runs two desks and a phone line for Lebanese-speaking assistance with digital services. Two bounded low-risk tasks are chosen with users. Human-only support remains available. Consenting users are randomly routed to human-only, human+AI or speech-first AI; log ASR, suggestions, overrides and bail-outs separately with optional consent. Credit AI completion only without bail-out or with minimal override. Monthly failures inform K07; P-B tests quarterly. K30 counts task outcomes, not calls or recordings, in line with [GOV.UK guidance to offer assisted digital support and include assisted users in take-up figures](https://www.gov.uk/service-manual/helping-people-to-use-your-service/encouraging-people-to-use-your-digital-service). The desks also host council nominations and complaints.

**P-A Inclusive paid collection.** Elderly, rural and non-literate speakers; paid recording, transcription and validation; culture-in-context recording under K32. Consent is given in spoken Lebanese, with assistance and a comprehension test. Speakers make separate choices for public display, research and commercial use. Incidental speakers and sensitive disclosures follow timed quarantine (annex). Diaspora collection runs only through trained facilitators under the same rules; remote family recording is dropped.

**K07 Mixing and Arabizi tools.** Language identification, transliteration and normalisation support task logic; phase-one code-switched ASR is fine-tuned on consented P-A/K30 audio, with human-recorded Lebanese output prompts. Optional single-speaker consented TTS for confirmations/numbers follows an ASR task-quality gate and anti-cloning contract. A [2026 Lebanese code-switching study reports Whisper Medium WER falling from 44.37% to 35.32%](https://www.oajaiml.com/public/archive/low-resource-adaptation-of-whisper-and-mms-for-lebanese-arabic-automatic-speech-recognition); K30 results must be independently established.

**P-B Independent evaluation.** Lebanese benchmark and ranking with native panels; paid cultural red-teaming; quarterly controlled tests of human-only, human+AI and unaided speech-first routes.

**K21 Research network.** Participatory, following [Masakhane, which produced benchmarks for 30+ languages through participatory research](https://arxiv.org/abs/2010.02353). Members access data by tier. Shared tasks use P-B test sets with enforced test/train separation.

**K16 Levantine hub (reduced).** Annotation alignment and separate Lebanese evaluation only. Joint models and shared regional data are deferred, and Lebanese tests precede any pooling.

## Layers in operation
**K02 Data governance.** From month 0, an existing registered institution serves as legal host under ring-fenced stewardship; [data trusts require legal structures](https://theodi.org/insights/explainers/defining-a-data-trust/). An independent privacy and ethics reviewer advises, and the privacy officer holds a veto. A community-majority council has binding authority over commercial-use categories and sensitive protocols but never overrides individual consent. Paid council members are nominated offline, by phone or voice message. Decisions receive spoken Lebanese summaries and comprehension checks. Complaints and quarantine appeals go to an independent route. Licences adapt the [Kaitiakitanga licence, which keeps data sovereignty with the community and prohibits surveillance, discrimination and human-rights violations](https://www.itu.int/hub/2022/08/ai-indigenous-languages-maori-te-reo/).

Access tiers:
- Tier 0: public documentation and aggregates.
- Tier 1: de-identified text and speech embeddings under licence, with residual re-identification risk.
- Tier 2: raw audio for contracted institutional labs only; others submit approved code-to-data jobs run on rented compute without data egress, with memorisation checks and adapter/metric-only outputs; a small screen-only audit slice. This is lighter than [ICPSR restricted access](https://www.icpsr.umich.edu/web/NAHDAP/studies/36231).

A withdrawal registry sends exclusion manifests to licensees. Licensees and downstream recipients owe timed deletion attestations, audit access, licence termination and enforceable remedies, subject to host counsel review.

**K22 Provenance.** Every release passes the contract and validator in the annex. A JSON schema comes first and is later mapped to [W3C PROV-O, a provenance model for entities, activities, agents and derivations](https://www.w3.org/TR/prov-o/).

**K32 Context protocol.** Each recording has a context envelope (setting, topic, speaker roles, consent scope). Every segment references it, so context survives segmentation.

## Adoption indicators
- I1: verified task completion, separately for human-only, human+AI and unaided speech-first AI, among Lebanese-only, non-literate and phone-only users.
- I2: 60-day repeat use via AI, completion without bail-out, task time, errors and re-contacts against human-only control.
- I3: share of the five most frequent remediable failures that receive a deployed fix and show lower recurrence in P-B tests.

Before G-2, communities lock sample size, minimum excluded-user shares, completion and repeat-use floors, time advantage, non-inferiority on errors/re-contacts, and top-five failure recurrence ceiling. G-5 is pass/fail (annex), not a narrative review.

## Tensions
- Reuse vs privacy: tier-1 licences and restricted tier-2 jobs limit openness.
- Withdrawal vs trained models: exclusion applies only going forward, and this is stated plainly at consent.
- Council authority vs speed: binding on categories, not on individual projects.
- Revenue vs wages: funding must not depend on speculative licence income.

## Gaps
- G1 Adoption: owned by K30; uptake beyond two desks is untested.
- G2 Financing: the [Lacuna Fund 2024 NLP call focused on Africa and Latin America](https://www2.fundsforngos.org/?p=343994), so other routes are needed.
- G3 Audiovisual archives: out of scope until a rights and consent review.

## Owner decisions
- Legally capable host and ring-fenced charter.
- Council criteria and the list of high-risk uses.
- Licence pricing policy and royalty split (after G-4).
- K16 veto threshold.
- Deletion deadline and enforceable remedies.

## Annex

## Gates
- G-1, before retaining any corpus material (month 3). Conditions: legally capable host contracted from month 0; counsel verifies capacity, ring-fencing, spoken consent, ministry declaration/licence requirements and deletion enforcement; consent given in spoken Lebanese, with assistance, and comprehension-tested; timed quarantine and third-party rules; secure storage; end-to-end withdrawal test passed; provenance manifest; transcription guide. If not met, the independent ethics reviewer may authorise only non-retained protocol tests.
- G-2, before expanding P-A (month 6). Conditions: privacy and annotation audit of the 10–15-speaker pilot; council constituted; complaint route live. If not met, the reviewer holds expansion and the privacy officer may veto.
- G-3, before the first research release or external training. Conditions: validator passes; datasheet published; tiers assigned; quarantine queue resolved and contracted job isolation/memorisation checks passed. If not met, the custodian blocks the release.
- G-4, before commercial licences and royalties. Conditions: K30 baseline and one user-testing cycle complete; council has ruled on commercial-use categories; downstream-duty, deletion deadline, audit, termination and remedy clauses in every licence; operations funded independently of speculative licence revenue. If not met, the council ruling is binding and the privacy officer may veto.
- G-5, before scaling, certification or a new collection cycle. Pass only if preregistered sample and excluded-user quotas are met; unaided speech-first and minimally overridden human+AI completion clear community-set floors; human+AI beats human-only on time without excess errors/re-contacts; AI-route repeat use meets its floor; top-five failure recurrence stays below ceiling; withdrawals and attestations pass audit. Otherwise freeze new collection and commercial licences, retain K30 human-only service, fix top failures for one bounded cycle and retest once. Second failure ends AI pipeline and archives tier 0/1 assets; council and reviewer enforce the hold.
## Minimum release contract
Every release has an immutable manifest. Each record carries: stable pseudonymous ID and parent links; asset type and access tier (0, 1, 2); segment offsets and K32 context-envelope reference; speaker tokens and incidental-speaker status; consent version and allowed purposes; licence permissions and prohibitions; origin type (human, machine, translated, mixed); transformation and annotation versions; script tag (Arabic script, Arabizi, mixed); restriction flags and withdrawal status. Each release also has a private recipient register, a datasheet and a complaint route.
## Rules
- Derivatives inherit the most restrictive parent permissions; conflicts default to quarantine.
- Unknown origin is treated as unverified.
- The validator blocks missing lineage, unresolved consent, withdrawn sources and test/train overlap.
- Raw identifiable audio is tier 2 by default.
- Withdrawn records go into exclusion manifests and are excluded from future training. Already trained weights are never claimed to be cleaned.
- Format: JSON schema plus validation script first; PROV-O mapping later.

## Quarantine and enforcement
- Privacy officer decides within logged deadlines; council subcommittee hears appeals and audits samples. Isolated non-identifying incidental speech: mute and scrub, purge original within 14 days after QA.
- Identifiable bystander: encrypted hold up to 30 days; safely seek spoken re-consent only if contact does not disclose context. Otherwise mute if separable or purge; unresolved automatically purges.
- Sensitive disclosure: mute/scrub within 14 days or purge whole clip if inseparable; privacy officer veto applies. Unconsented minor or evident distress: immediate whole-clip purge and non-reversible blocklist fingerprint. Individual deletion overrides reviewer approval.
- Host logs licence deliveries, withdrawal notices and deadlines; audits attestations and downstream compliance; noncompliance triggers suspension/termination and contractual remedies after legal review.


## Output
1. Strategy v4 in Markdown (body + annex).
2. Then a single JSON code block:
```json
{"changes": [{"section": "...", "change": "...", "addresses": "D1|D2|H6|H14|H15|H9|H12|owner|portfolio", "support": [{"type": "source|reasoning", "claim": "...", "url": "...", "fragment": "...", "premises": ["..."]}]}],
 "merges": [{"programme": "...", "options": ["C.."]}],
 "deferred": [{"option": "C..", "reason": "..."}],
 "open_questions_for_owner": ["..."]}
```
