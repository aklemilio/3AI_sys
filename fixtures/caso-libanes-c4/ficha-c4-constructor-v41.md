# Task card — Cycle 4, Phase B — Builder: Strategy v4.1 (apply corrections)

You built Strategy v4. An attacker reviewed it and the owner has decided how each finding is handled. Produce v4.1 by applying the dispositions below with minimal edits. Do not reopen decisions.

## Owner principle for privacy (applies throughout)
Common sense, no over-protection: once a model is trained, any voice can be cloned or created, so promising protection that cannot be delivered is misleading. Protect what can really be protected (no names or identifying metadata in public ASR, private synthesis, quarantine of third parties and sensitive content), and otherwise warn contributors clearly and honestly in the consent. Remove any wording that promises more than the project can deliver.

## Findings and dispositions
- **A1 — Annex B inalcanzable con el tamaño del piloto** (critical). Problem: Annex B pide potencia del 90% con error familiar del 5% para cada comparación: 2 rutas de IA × 2 tareas × 6 subgrupos más intersecciones × varios criterios (piso absoluto, no inferioridad de −5 pp, errores, recontactos, tiempo y repetición de uso). Con una proporción cercana a 0,85 y un margen de 0,05, cada brazo de cada subgrupo y tarea requiere del orden de 1.700 a 2.100 personas. El total llega a decenas de miles, frente a dos escritorios, una línea telefónica y un piloto de 10–15 hablantes en G-2. Como un subgrupo sin potencia suficiente es «inconcluso, no aprobado» y una segunda falla cierra la vía de IA, el diseño garantiza el cierre por tamaño muestral y no por desempeño ni por daño. Además, la repetición de uso a 60 días no puede medirse si las tareas elegidas no se repiten en ese plazo.
  Disposition: OWNER: replace the confirmatory statistical regime. AI routes are validated with validation samples used to find and apply corrections (iterative: sample, measure, correct, re-sample). Thresholds become reference targets that guide corrections, not pass/fail gates; inconclusive results never count as failure. Keep the serious-harm stop rule. Remove 90% power, familywise error and per-subgroup confirmatory requirements. Measure repeat use only for tasks that recur within 60 days.
- **A2 — Retiro no alcanza modelos de voz privados** (high). Problem: El arreglo de D1 excluye de forma general la eliminación de pesos ya entrenados. En síntesis privada eso implica que un modelo puede seguir generando la voz reconocible de alguien que retiró su consentimiento. Para la ASR pública es aceptable; para una voz de estudio, no. El problema se trasladó de los datos al modelo.
  Disposition: OWNER PRINCIPLE (common sense, no over-protection): once a model is trained any voice can be cloned or created; protection that cannot be delivered must not be promised. Do not add voice-identity removal mechanisms. Consent must state plainly what withdrawal can and cannot do; withdrawal stops the project's future uses.
- **A3 — ASR pública permite clonar la voz privada** (high). Problem: La misma persona puede contribuir a ambos conjuntos, y la estrategia lo resuelve solo prohibiendo la vinculación pública. Sin embargo, la propia voz es el vínculo: unos segundos de audio ASR público bastan a terceros para clonar con herramientas actuales. Los seudónimos y la privacidad de la síntesis dan una protección aparente que no existe frente a ese riesgo.
  Disposition: OWNER PRINCIPLE: warn, do not over-protect. Consent for people contributing to both sets explains plainly that public ASR audio can be used by anyone to imitate their voice. No segment-exclusion mechanism.
- **A4 — Retiro público ignora la obligación de informar** (high). Problem: Annex D solo notifica a receptores contratados y da por perdidas las copias públicas. Si la financiación exige GDPR, quien hizo públicos los datos debe tomar medidas razonables, incluidas medidas técnicas, para informar a otros responsables. Con descargas anónimas no hay a quién informar.
  Disposition: Apply the minimal version only: publish a public withdrawal list with deprecated versions and checksums, and ask users in the terms to sync with it. No registration for downloads.
- **A5 — Credenciales anónimas de retiro se pierden fácilmente** (medium). Problem: Quienes no leen, las personas mayores y quienes cambian de teléfono o sufren cortes de energía pierden con frecuencia sus credenciales. Sin nombres no hay otra forma de localizar sus grabaciones, de modo que el retiro existe en el papel pero no en la práctica.
  Disposition: OWNER PRINCIPLE: keep withdrawal simple and honest. Allow an optional sealed contact record held by the privacy officer; no voice-matching lookup.
- **A6 — El cierre borraría grabaciones patrimoniales** (high). Problem: Si la sucesión es imposible, se eliminan los activos personales. Las grabaciones de C-A y las cintas domésticas son datos personales, y solo los archivos de emisoras tienen un acuerdo de depósito. Eso contradice el principio 7. Además, Annex E no exige un sucesor contratado antes de retener material cultural, a diferencia de G-1.
  Disposition: OWNER: designate a cultural depositary from the start (before any cultural retention). On closure, heritage passes to it under existing consents; only private synthesis, quarantine, service logs and test sets are deleted. Add the depositary to the cultural gate.
- **A7 — Objetivo 2 depende del anfitrión del Objetivo 1** (high). Problem: El consentimiento, la procedencia, la gobernanza y el responsable legal son infraestructura compartida en manos de un solo anfitrión. Después del mes 24, el Objetivo 1 prevé una continuación financiada o un cierre ordenado, mientras el Objetivo 2 declara una continuación cultural independiente sin fuente de financiamiento ni anfitrión propio. Las becas y estipendios de aprendices tampoco tienen financiamiento posterior al mes 24.
  Disposition: OWNER: the cultural depositary also solves this: it is Objective 2's own host and continuity anchor, with its own budget line and a month-18 cultural funding plan. Closing the AI route never closes Objective 2.
- **A8 — Desacuerdos suspenden sin plazo ni salida** (high). Problem: Cualquier desacuerdo suspende la actividad sin plazo, sin quórum y sin desempate. Con vacantes en el consejo o renuncias, todo puede quedar paralizado. Además, el consejo se constituye en G-2, pero ya decide sobre protocolos sensibles antes de G-1. El arreglo de H15 solo traslada el bloqueo.
  Disposition: OWNER: legal and privacy vetoes stay absolute; any other disagreement is resolved within 30 days, otherwise the independent reviewer decides. Add minimum quorum and an interim council from month 0 to G-2.
- **A9 — Excluir programas mixtos debilita la decisión del propietario** (high). Problem: El propietario incluye todo programa en libanés hablado. El constructor excluye los programas mixtos MSA/libanés hasta clasificarlos, sin regla de clasificación, lo que en la práctica es una exclusión permanente. Así quedan fuera obras de teatro, variedades y programas de conversación con presentaciones en MSA, que son libanés hablado.
  Disposition: OWNER: mixed MSA/Lebanese programmes stay in scope. Replace the exclusion with parameters to evaluate pertinence (for example share of spoken Lebanese, cultural value of the Lebanese segments, separability, condition of the carrier). Propose the parameters; the owner will approve them.
- **A10 — La auditoría lingüística exige reproducir soportes frágiles** (medium). Problem: Para clasificar la lengua hay que reproducir el soporte. Las cintas en peligro pueden soportar una sola reproducción, y un mismo carrete suele contener varios programas. A la escala de varias emisoras, la auditoría manual es inviable y empuja a usar identificación de lengua (K07), una dependencia de la IA que no está declarada.
  Disposition: Apply attacker fix: single capture during audit for endangered carriers; human sampling for language audit; language identification only as optional aid with human confirmation.
- **A11 — Condición de necesidad debilita la síntesis decidida** (medium). Problem: La síntesis privada solo se desarrolla si una necesidad demostrada de forma independiente la justifica. Es una condición del constructor, sin un responsable de la decisión, que puede anular la colección de síntesis decidida por el propietario. Además, la ruta de IA con habla primero (K30) ya necesita salida de voz para no lectores.
  Disposition: Apply attacker fix: private synthesis proceeds by owner decision; only its scope (number of voices and tasks) is sized by K30 needs and third-party comparison.
- **A12 — G-1 bloquea ASR por cómputo de síntesis** (medium). Problem: G-1 exige verificar el cómputo para cualquier retención, aunque esa verificación solo es necesaria para la síntesis privada. Como la infraestructura sigue sin identificarse, la ASR pública y la retención cultural quedan bloqueadas.
  Disposition: Apply attacker fix: compute verification for synthesis moves to G-3; G-1 requires verified secure storage.
- **A13 — Declaración ante el Ministerio sin requisito explícito** (medium). Problem: G-1 dice tratamiento lícito, pero no exige presentar la declaración, con la entrada de transferencia del Art. 96(12), antes de recolectar. Tampoco advierte que la lista que publica el Ministerio según el Art. 98 hará pública cualquier transferencia al exterior. Un sucesor extranjero o un respaldo en el exterior también es una transferencia.
  Disposition: Apply attacker fix: G-1 requires the filed declaration (including Art. 96(12) where processing, backup or successor is abroad); counsel opinion on Art. 97 only if health data survive quarantine. Note that Art. 98 makes declared transfers public.
- **A14 — Sin protocolo de capacidad para consentir** (medium). Problem: Se da prioridad a personas mayores, pero la prueba de comprensión no distingue el deterioro cognitivo. El consentimiento para publicar audio de forma irreversible es especialmente delicado en ese caso.
  Disposition: Apply simply: if the comprehension check fails or capacity is doubtful, no public ASR contribution; heritage route with a trusted companion remains possible.
- **A15 — Copias de grabaciones domésticas de emisiones** (medium). Problem: La estrategia devuelve copias de cintas domésticas sin importar el consentimiento de archivo. Muchas son grabaciones de emisiones protegidas, y que el proyecto haga copias para terceros puede no quedar cubierto por la excepción de copia privada de la Ley 75/1999.
  Disposition: Apply attacker fix: counsel opinion on third-party copying; meanwhile return copies only of household-created content; broadcast recordings digitised for preservation of the original.
- **A16 — GDPR tratado solo como exigencia del financiador** (medium). Problem: Los contribuyentes de la diáspora que residen en la UE y reciben pago podrían quedar bajo el GDPR directamente, no solo por contrato con el financiador. Lo mismo vale para otras leyes de privacidad (Canadá, Australia, Brasil).
  Disposition: Apply attacker fix: diaspora jurisdiction review before G-1.
- **A17 — Cuerpo excede el límite de palabras** (low). Problem: El cuerpo tiene unas 1.685 palabras frente a un límite de 1.600.
  Disposition: Apply: trim to 1,600 words by removing reasoning paragraphs duplicated in the change register.

## Additions to include (attacker proposals accepted)
- Payments that work in the banking crisis: cash transfer or mobile wallet in available dollars, oral receipt for non-readers, separate route for diaspora.
- Research ethics committee approval (for example a Lebanese university committee) for K30 randomisation and P-A collection before G-2.
- Energy resilience and offline encrypted backups at a second site; manual procedures during outages.

## Rules
- Every change cites the finding (A1–A17), an addition, or the owner principle.
- Body up to 1,600 words; annex up to 800. English. No budget figures or names of private individuals.
- Support: "source" (URL plus exact short fragment, never invented) or "reasoning" (premises).

## Output
1. Strategy v4.1 in Markdown.
2. A single JSON code block: {"changes": [{"section": "...", "change": "...", "addresses": "A1..A17|addition|owner"}], "pertinence_parameters_for_mixed_programmes": ["..."], "open_questions_for_owner": ["..."]}

## Strategy v4 (your version)

Lebanese in the AI Era: Strategy v4
Cycle 4 — Phase B — Builder version
1. Purpose: two objectives, one project
The project pursues two independently valuable objectives, supported by common infrastructure but evaluated against different measures of success.

Objective 1 — AI that serves Lebanese speakers. Make spoken Lebanese, including everyday mixing with French and English, Arabic script and Arabizi, usable in AI and digital services. Prioritize Lebanese-only speakers with limited economic or educational resources, followed by the diaspora. Researchers and AI businesses remain secondary beneficiaries.

The planning forecast is that large AI models will probably speak common Lebanese reasonably well within approximately two years. Accordingly, the project's comparative value shifts towards independent evaluation, accessible services, adoption and documented, consented data rather than ownership of a Lebanese foundation model. [Owner decision]

Objective 2 — Cultural preservation. Preserve and sustain the spoken heritage that linguistic flattening erases: regional vocabulary, oral arts, occupational speech, cultural contexts and intergenerational transmission. Its success does not depend on AI development. AI remains an optional supporting instrument, not the objective.

The owner's position that cultural flattening is irreversible remains a value judgment, not an established empirical finding.

Reasoning: Better AI performance does not necessarily sustain linguistic diversity or the social practices through which heritage is transmitted. Separate objectives therefore require separate programmes, gates and indicators.
One project — two independent objectives
Objective 1

AI access, evaluation and adoption

K30 · P-A · K07 · P-B · K21 · K16
Success: people complete real tasks

Objective 2

Living heritage and preservation

Four integrated cultural programmes
Success: heritage survives and remains in use



Shared infrastructure

K02 governance · C35 consent · K22 provenance · K32 context · legal compliance · institutional continuity

Shared infrastructure does not imply shared data permissions or dependency on AI success.
2. Design principles
1. Adoption is a deliverable; K30 owns real use.
2. No retention, publication or licensing before applicable gates pass.
3. Public ASR and private synthesis have distinct consent and access regimes. [D1, owner]
4. Withdrawal excludes project-controlled future releases and training; removal from existing weights or uncontrolled copies is not promised. [D1]
5. Wages precede speculative royalties.
6. Community authority never overrides individual rights.
7. Cultural preservation continues independently of AI performance or commercial revenue. [Owner, H14]
Reasoning: Retain v3's adoption, gate, compensation and community-governance principles while separating incompatible access regimes and protecting independent cultural outcomes.
3. Objective 1 — AI access, evaluation and adoption
K30 — Human-AI hybrid access network. Retain two desks and a telephone line, two user-selected low-risk digital tasks, human-only assistance and randomized comparison with human+AI and speech-first AI. Record overrides, errors, bail-outs and completion separately. Evaluation recordings remain non-public unless separately contributed through P-A consent. Human-only assistance survives AI failure. [D1, H6]

P-A — Inclusive paid collection. Prioritize elderly, rural and non-literate speakers. Pay recording, transcription and validation work. Maintain two separate collections:
	ASR	TTS / speech-to-speech
Collection	Crowdsourced	Few selected voices
Environment	Natural ambient noise	Studio quality
Audio	Publicly downloadable after clearance	Private
Identity metadata	No names or identifying metadata	Pseudonyms
Models	Publication subject to applicable gates	Never published
Consent	Explicit public-release consent	Separate private-use consent

The same individual may contribute to both, but no public cross-collection linkage is permitted. Preserve ordinary environmental noise while quarantining sensitive disclosures and third-party speech. Diaspora contributions retain trained-facilitator oversight. [D1, owner]

K07 — Mixing and Arabizi tools. Retain language identification, transliteration, normalization and ASR-first task prototypes. Compare third-party systems before undertaking local fine-tuning. Develop private synthesis only where independently demonstrated task needs justify it. [Owner, D2]

P-B — Independent evaluation. Retain native-speaker panels, paid cultural red-teaming, quarterly controlled tests and rankings. Evaluate third-party and project models under identical conditions, including noisy speech, regional variation and code-switching. Protect hidden test sets against contamination. Apply the subgroup performance and harm gates in the annex. [Owner, H6, H12]

K21 — Research network. Retain participatory research and shared tasks. Researchers use public ASR releases and separately authorized documentation. Private synthesis is not a general research-access resource. [D1, owner]

K16 — Levantine hub. Retain annotation alignment and separate Lebanese evaluation. Joint models and regional data pooling remain deferred.

Reasoning: The model-improvement forecast favors reusable evaluation and accessible applications. Public training data must not be confused with confidential service interactions or held-out evaluation data.
4. Objective 2 — Cultural preservation
Four integrated programmes cover the complete selected portfolio.
Programme C-A — Living heritage and transmission
Combines C21, C25, C26, C27 and C29.
- Record crafts, farming, work, humour, games and oral traditions in their cultural contexts, with paid participation and community-defined boundaries.
- Fund year-long apprenticeships pairing young people with paid tradition bearers. Provide apprentice stipends and transparent selection.
- Support recurring zajal, storytelling, theatre and sung-poetry gatherings in existing community spaces.
- Protect gathering places through municipal cooperation, accessible venues, permits and small grants.
- Encourage intergenerational household circles through optional spoken prompts, without recording, registration or evidence-submission requirements. Offer alternatives for isolated elders.
Measure: sustained apprenticeships, continued practice, accessible gatherings and community-defined transmission outcomes—not recording volume.
Programme C-B — Broadcaster archive rescue and rights clearance
Combines C01, C03, C05 and C02, supporting C10.

Inventory public, private, regional and discontinued broadcasters and independent production collections. Record ownership, formats, condition and accessibility; connect existing preservation initiatives.

Mandatory programme-level language audit: classify programmes as spoken Lebanese, MSA, mixed or other. Everyday French and English mixing within Lebanese speech qualifies as spoken Lebanese. Mixed MSA/Lebanese programmes remain excluded pending classification. Only spoken-Lebanese programmes enter rescue, detailed cataloguing, escrow and re-broadcast.

The owner's expectation of substantial MSA holdings is a planning assumption, not a measured finding.

Prioritize endangered eligible recordings. Offer contractual preservation escrow without transferring ownership or requiring publication. Fund paid regional audiovisual-preservation trainees paired with retired broadcaster technicians.

Apply C02's four rights-triage categories: broadcasts older than 50 years; broadcaster-owned younger material; third-party works or performers; unknown rights. Categories may overlap. Publish a non-sensitive rights register distinguishing verified clearance from unresolved claims.

Measure: eligible collections inventoried, endangered recordings preserved, rights cleared and technicians demonstrating independent preservation competence.
Programme C-C — Mobile rescue, listening and circulation
Combines C04, C13 and C10.

Operate a mobile rescue-and-listening unit. Digitize household tapes and videos; return originals and copies regardless of archive consent. Retention requires separate contributor, third-party and copyright clearance.

Provide facilitated, solar-backed offline listening points in libraries, municipalities and community centres without requiring literacy, registration or personal devices.

Re-broadcast cleared spoken-Lebanese programmes through public, private and regional stations. Broadcasting is not represented as protection against unauthorized recording.

Measure: household materials rescued, listening-point availability, underserved communities reached and cleared programmes returned to circulation.
Programme C-D — Community archives and linguistic diversity
Combines C09, C16 and C33.

Establish community-governed regional repositories sharing technical preservation services but retaining local access authority. Provide independent appeals and external reviews against local gatekeeping.

Enable diaspora cataloguing through Arabic script, Arabizi and spoken annotations. Preserve spelling and regional variation.

Invite Armenian, Syriac, Aramaic, Kurdish, Domari and other communities to define their own preservation priorities. Lebanese Sign Language receives Deaf-led visual preservation.

Collections may be public, community-only, restricted or temporarily closed. No heritage collection becomes AI training material by default.

Measure: community-approved collections, contextual catalogue quality, representation and effective community control.

Reasoning for C-A–D: The portfolio covers transmission, rescue, description, access and circulation. Merging complementary mechanisms reduces organizational duplication without eliminating options. Minority-language preservation is a distinct community-led strand, not an exception permitting MSA broadcaster archives.
5. Shared infrastructure and legal safeguards
K02 — Governance. A legally capable host holds controller responsibility. A community-majority council controls permitted commercial categories and sensitive protocols; the privacy officer controls privacy compliance; the independent reviewer hears appeals and validates gates. Individual consent, legality and protective vetoes prevail over permission to proceed. Disagreements suspend the contested activity. [H15]

C35 — Consent. One oral-first, comprehension-tested protocol with distinct ASR publication, private synthesis, heritage preservation, public listening, broadcasting and research modules. Provide anonymous withdrawal credentials and accessible complaint channels.

K22/K32 — Provenance and context. Retain release validation, lineage and contextual envelopes. Separate public manifests from protected internal records. Cultural materials never inherit AI permissions merely through shared infrastructure. [D1]

Legal and market safeguards:
- Lebanese Law 81/2018: Articles 94–98 distinguish exemptions, declarations and sensitive-data licences. Article 96(12) expressly includes foreign transfers in declarations. The reviewed text does not establish a universal separate transfer-authorization requirement. Obtain counsel's determination and any required filings or permissions. [D2] [S1]
- Compute: private synthesis defaults to physically Lebanese infrastructure. Verify processing, backups, subprocessors, remote access and support locations before use. Foreign processing requires documented legal clearance and applicable authorizations. Actual infrastructure location remains unverified. [D2]
- GDPR: adopt funder-required GDPR safeguards; distinguish ordinary voice personal data from biometric processing for unique identification. Complete high-risk impact assessments and applicable international-transfer safeguards. [D1, D2] [S2]
- Market practice: internet audio is used in model training. Public ASR consent must explicitly explain harvesting, redistribution and the limits of withdrawal. [D1] [S3–S4]
- Copyright: broadcaster rights, underlying works, performers and contractual restrictions require separate clearance. Fifty years since broadcast does not establish unrestricted reuse. Escrow grants only contracted rights, not statutory immunity. [Owner] [S5]
6. Delivery and continuity
Period	Objective 1	Objective 2
M0–3	Host, baseline, consent, G-1	Inventory design; community consultation
M3–6	Pilot, two tasks, council, G-2	Language audit; apprenticeships and mobile pilots
M6–12	ASR tools, benchmark, G-3	Eligible archive rescue; technician training
M12–18	G-4; adoption; K16 alignment	Escrow, listening points, cleared broadcasting
M18–24	G-5; independent review	Transmission and preservation review
After M24	Funded continuation or orderly closure	Independent cultural continuation

Continuity [H14, H15]. Before collection, contract a successor custodian and protected provision for withdrawal, deletion, security and preservation. By month 18, require a funded post-month-24 operating plan, drawing on institutional support, grants and service agreements—not speculative licensing revenue.

Without renewal, stop new collection and licensing. The host or contracted successor retains residual duties while relevant assets remain. If lawful succession is impossible, securely delete personal assets rather than abandon them; rights-restricted archives follow their deposit agreements.
7. Outstanding gaps
G1: adoption beyond pilot locations remains untested. G2: long-term financing and compute procurement remain unresolved. G3: archive eligibility, physical condition and rights require actual audits.

Annex
A. Binding AI gates
The following numerical thresholds are proposed policy choices, not empirical findings. Communities may strengthen them before G-2; subsequent weakening cannot rescue a failed evaluation.
Gate	Conditions
G-1 — Retention	Contracted host/successor; lawful processing; tested oral consent and withdrawal; secure storage; provenance; compute verification; quarantine. Otherwise non-retained trials only.
G-2 — Expansion	Audit 10–15-speaker pilot; constitute council; activate appeals; preregister evaluation and subgroup quotas.
G-3 — Release/training	Validator, datasheet, consent and rights clearance, quarantine resolved, test/train separation; verify private synthesis isolation.
G-4 — Commercial use	K30 baseline and testing cycle; council approval; lawful purposes; applicable downstream contracts; independently funded operations. Public ASR remains downloadable.
G-5 — Scaling	All performance, subgroup, safety, withdrawal and continuity conditions below pass.

B. Performance and statistical rules [H6, H12]
Evaluate both AI routes against randomized human-only assistance for each task and priority subgroup: Lebanese-only, non-literate, low-income, rural, elderly and phone-only users, including preregistered high-exclusion intersections.
- Completion: lower confidence bound at least 80%; AI–human difference at least −5 percentage points.
- Errors and re-contacts: upper confidence bound on excess risk no greater than 3 percentage points each.
- Human+AI: demonstrate shorter completion time than human-only.
- Repeat use: at least 40% of eligible users with recurring task needs return to an AI route within 60 days.
- Top-five remediable failures: all addressed; recurrence reduced at least 20% relative to baseline.
- Bail-outs count as AI failures; minimal overrides are predefined.
Power every required comparison at 90%, controlling familywise error at 5%; incorporate clustering, attrition and subgroup overlap. An underpowered subgroup is inconclusive, not passing.

One serious attributable privacy or task-related harm triggers immediate suspension and independent investigation. Preregister interim statistical stopping boundaries.

G-5 failure freezes expansion and new licences; retain human-only support, fix failures and retest once. Second failure ends the failed AI deployment pipeline, not cultural programmes or residual governance duties.
C. Access and release contract [D1, D2]
Public ASR audio is not anonymous merely because names are absent. Publish cleared audio, transcripts, non-identifying context and purpose-specific terms. No identifiable third-party material or hidden benchmark audio enters releases.

Synthesis-only tiers:
- Tier 0: safe documentation and aggregates.
- Tier 1: approved internal derivatives, including restricted embeddings.
- Tier 2: private raw recordings, training environments and models; authorized personnel only; no external model or audio publication.
Each release records opaque record identifiers, parent links, asset class, consent version, purposes, context reference, annotation versions, script, restrictions and withdrawal status. Protected manifests retain additional compliance evidence.

Derivatives inherit restrictive parent permissions. Unknown origin, conflicting permissions, withdrawn sources and test/train overlap block release. Use JSON validation first; PROV-O mapping later.
D. Quarantine, withdrawal and appeals [H9, H15]
Mute separable incidental speech; purge original within 14 days after quality assurance. Hold identifiable bystanders encrypted for at most 30 days; safely re-consent, mute or purge. Scrub sensitive disclosures within 14 days or purge. Immediately purge unconsented minors or evident distress.

Decide appeals independently within seven days, inside the original quarantine limit. No appeal stays individual deletion or extends retention.

Acknowledge withdrawal within seven days; block further release/training immediately; remove controlled copies within 30 days unless lawful retention is necessary. Notify contracted recipients and require deletion attestations within 30 days. Public downstream copies cannot be guaranteed recoverable. Preserve only necessary compliance evidence.
E. Cultural gates
Before retention: applicable consent, language eligibility, community authority and preservation rights. Before listening, online access or broadcast: separate clearance. Review local governance, preservation integrity and transmission annually. Failure stops the affected cultural operation only.
F. Source register
ID	Source and exact fragment
S1	Law 81/2018, Art. 96(12): “نقل البيانات ذات الطابع الشخصي الى دولة اخرى في اي شكل كان.”  Electronic transactions and…
S2	GDPR, Arts. 9 and 35: “for the purpose of uniquely identifying a natural person”; “likely to result in a high risk”.
S3	Speech anonymization, 2025: “balance privacy and utility”.  Nature
S4	Whisper model card: “audio and the corresponding transcripts collected from the internet”.  GitHub
S5	Law 75/1999: “The term of protection granted to broadcasting organizations shall be 50 years”.  WIPO
S6	LebEval: “a new benchmark derived from native Lebanese content”.  arXiv
S7	SenZi: “11.3K positive and 13.3K negative words”.  ACL Anthology
S8	Masakhane: “MT benchmarks for over 30 languages”.  arXiv
