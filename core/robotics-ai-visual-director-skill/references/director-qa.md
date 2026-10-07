# Director QA

Before final render verify:
- Can the central question be stated in one sentence?
- Does every beat answer or advance that question?
- Is there one obvious attention target at each moment?
- Do important objects persist rather than repeatedly vanish?
- Does each equation emerge from an already visible relation when possible?
- Is 3D used only where depth/spatial relations matter?
- Are paper/results claims scoped and sourced?
- Does the robot consequence make the abstraction operational?
- Does the recap add zero new concepts?

## Explanation craft before expensive rendering

- Name what the viewer should be able to predict or explain at the end. A changed path alone does not explain a planner's choice.
- For the central decision, identify the visible cause, the relevant constraint/comparison, and the consequence. Locate each in `state_change` / `focus` in the existing manifest.
- Establish the physical situation, isolate the mechanism with a purposeful close-up/top view, then connect it back to the robot's action. Choose this structure only where it helps the topic.
- Keep alternatives in the same coordinates and color semantics. Reveal a decisive difference before declaring the winner. When the trace lacks candidate costs, do not fabricate a cost comparison or assert the exact reason for a selected optimum.
- Distinguish physical obstacle, detection, cost update, planning, and execution when the lesson depends on them. Synchronize to recorded phrase anchors, not arbitrary beat boundaries.
- Preserve enough context to orient the viewer across a cut; settle the camera before the decisive comparison. Reuse objects without making every shot identical.
- At delivery size, the decisive feature must be identifiable without subtitles. Use a short local label or legend if colors/geometry need interpretation; avoid persistent dashboards.
- Check padded vs spoken duration. Extend content with a useful example or supported comparison, not a longer camera move. Do not prescribe a universal video length.

Example for planning: show the old path intersecting newly blocked cells -> expose the relevant passage/clearance -> show a supported new route -> execute it. If data shows two routes but does not explain why the optimizer switched, state that limitation instead of inventing the comparison.

These are project adaptations. Source/provenance and access limits are recorded in `SOURCE_PATTERNS.md` at the bundle root.

## Discovery structure and critical excerpt

For a full explainer, identify the viewer's starting expectation, the evidence that tests it, the mechanism that explains the result, and a supported transfer question. Put the expectation/question in `text`, the observable test in `state_change`, and decisive evidence in `focus`. Use existing beat IDs; do not introduce a parallel script. A misconception or surprise is optional: never invent one to force drama.

Before declaring a result, give the viewer an opportunity to inspect the deciding relation. A prediction pause is useful only when enough evidence is visible; its length follows the task and measured speech. Explain new terminology after the concrete relation is established. A transfer can be a prediction about a changed condition rather than a second simulation; distinguish it from an observed result.

Select the contiguous portion where the key inference occurs, usually 15–25 seconds. Include necessary setup and the consequence even if it needs a different length. It must contain real moving picture and measured narration, not an animatic described in prose. Inspect this excerpt before committing to the full render. If it fails, change the cause of the failure: unsupported answer -> evidence/scope; hard-to-follow inference -> order/framing; rushed explanation -> speech/event timing.

The reviewer first sees only the excerpt and opening question, without the script or trace. Record their answers before checking the source:
- What changed?
- What visible evidence explains the result?
- Given one stated change of condition, what would you predict, and what remains unknown?

Then verify these answers against the evidence. Correct labels memorized from a caption do not prove understanding of the relation. Record a concrete misunderstanding and its time rather than an unexplained quality score. This is a diagnostic exercise, not a controlled learner study or proof of creator parity. No mandatory extra agent is implied.

Keep the same visual subjects across abstraction changes. Plan shared landmarks, orientation, scale, and color meaning at a 3D/2D handoff; specify a cut if a spatial transform would misrepresent geometry. Provide the decisive view before camera or robot motion resumes.

## Physical emphasis and duration decisions

For planning/control episodes, keep the successful chain visible: the constraint changes the reference, a controller uses actual state to choose an input, the physical robot responds, and feedback updates the next command. Preserve reference-versus-actual differences instead of smoothing them away for appearance. If plan and control are both enabled/disabled in a comparison, attribute the difference to that combined change; do not claim the experiment isolates either component.

Before assigning the physical view, identify the deciding feature and the viewer's task. Corridor context may need a wide view; direction error, wheel motion, near contact or stopping may need a closer settled view. A single wide view is sufficient when that relation remains readable. Keep close-up timing tied to recorded events and measured phrases, with enough stable landmarks to orient the viewer.

For a control-focused question, prefer one intelligible example cycle over an abstract loop alone: pose/heading differs from reference -> the implemented rule selects a turn/forward command -> actual heading/position changes. Source command values and achieved motion separately. A plausible visual arrow cannot substitute for missing execution data.

Allocate time by what the viewer needs to infer or inspect. Keep one concrete question within the requested runtime; add supported mechanism detail before extending runtime. The recap should resolve the opening question, expose a useful comparison and state the relevant scope. If the completed action already answers it, compress repeated outcome prose rather than showing a long static conclusion. No fixed ending percentage, camera count or universal duration is required.

These refinements follow the revision_06 frame/evidence review and user approval of its explanation pace. Whole-video normal-speed playback remained incomplete; the preference for closer physical emphasis and a tighter ending is a craft direction, not a measured learner-performance result.

## First-view learner check

For an introductory episode, state the assumed prior knowledge briefly in the existing manifest/episode document; avoid testing vocabulary the lesson has not introduced. Use the actual voiced critical excerpt with enough setup, not the script or source code. Obtain voluntary feedback from an available first-time human viewer without giving an explanation or answer beforehand. A familiar creator/user or an agent can provide useful review, but is a different evidence category.

For the steering example, use open prompts such as “Why did this robot turn here?” and “If it already pointed toward the selected target, what turn command would this rule choose?” Ask about the controller command, not a guarantee that the physical robot instantly stops turning. Adapt the changed condition to the implemented rule; near-goal stop or saturation may change the answer.

Record the initial answer before offering a hint, with a confusing timestamp if the viewer can identify one. Compare it against a private evidence-based interpretation: which direction/target is read, which difference leads to which correcting command, and what is measured after actuation. Merely repeating “31 degrees means +1” does not explain the relation. Distinguish “the drum forces a left turn,” “the line moves the robot,” and “command equals achieved motion” from the intended mechanism.

If a relation is missing or misunderstood, patch its cause: show target selection, establish robot-relative left/right, put plain meaning before units, or separate command from physical response. Recheck the changed interval on new media. A repeat with the same viewer is a repair check, not independent first-view evidence. One successful viewer is limited evidence, not a universal comprehension claim or learner study.

If no novice is available, record `not_assessed` and the specific question still unverified, while continuing independently authorized production. Do not recruit/contact people automatically or fabricate a novice response. Keep answers anonymous and limited to what diagnoses the lesson.

## Define refinement and finish it

For a requested quality upgrade, choose a small set of demonstrated weaknesses from the current render; put `weakness -> owner -> completion criterion -> evidence range` in the episode's existing README. Use existing manifest `focus` for the teaching intent and the optional review `craft_targets` for results; do not create another beat list, quality bureaucracy or overall parity score. Set the criteria before the candidate is rendered and carry them through handoffs.

For this control lesson, a useful target is that the viewer sees enough input to predict the turn before the answer is announced, then sees a supported condition change and the actual response. Inspectable geometry should do the explanatory work; prediction does not require a longer narrated question or a new simulation. Scope first-view human evidence as described above.

Choose refinement where it materially improves the inference or deciding view. Fix failed transitions, surface treatment and cut boundaries inside that scope; retain accepted beats and voice unless the target requires a change. End the iteration when the stated criteria and necessary gates are met. Reopen for a demonstrated regression, unresolved necessary defect or new user request, not merely because another style could be imagined. Missing learner/listening evidence is an unverified question and must not be described as a demonstrated comprehension/voice failure.

## Linked discoveries for a deeper short lesson

Use this for a requested narrative upgrade, rather than imposing a longer story on every lesson. Read the current episode as a sequence of inferences: after each result, identify what the viewer now knows and what necessary question remains. Put that relationship in the next existing beat's `state_change` / `focus`. A useful link reuses the previous result as input; a new heading that merely announces the next topic does not supply the link. Keep this audit in the episode's existing decision notes, not a second beat list.

For the planning/control example: the old path crosses a forbidden region, so a new reference is needed; a new reference alone cannot move the body, so a controller must read the current direction and target; its command is an input, so measured physical response and feedback are needed to judge execution. Choose the connections the opening question actually needs. Do not extend the lesson into every stage of robotics or force a fixed number of discoveries.

Give a supported changed-condition comparison a purpose: distinguish a plausible wrong rule from the implemented one, or explain a limit. Use an available recorded comparison or a clearly labeled command-level illustration; never invent a solver result, candidate cost or rejected trajectory. After it, return to the original physical case and resolve the opening question in the same visible terms. A comparison that only repeats the same answer adds runtime without explanatory depth.

Before changing accepted narration, define the precise missing link and the observable benefit. Reuse successful sentences, replace repetition when possible, and remeasure only changed speech. The voiced critical excerpt must include the adjacent discovery/handoff being changed. Judge whether the viewer can follow why the next question arises, not whether there are more cuts, equations or a longer runtime. Without fresh learner/playback evidence, keep that effect unverified.

## Design a mechanism across representations

For a reference-level episode, name the relation the viewer must infer and choose a worked example from the implemented model. Design physical part → simplified geometry → marked quantity → rule/notation → measured response when those representations help. Not every topic needs all five. In existing `focus`/`state_change` describe the source sample, corresponding part/quantity and what remains anchored; keep one manifest.

Expose how an input changes a decisive part before showing the whole outcome. A wheel-speed difference, contact radius, active memory address or matrix column deserves its own visual mechanism; do not reuse route-plus-arrows as every topic's explanation. Show terms coming from the already-visible example. Add a supported condition change that distinguishes the correct rule from a plausible mistaken one, then return to the physical result. Avoid extra formulas and runtime padding.

For differential drive, verify wheel order, track, radius and motor-axis sign from the implementation. Explain target tangential speeds `vR=v+ωb/2`, `vL=v−ωb/2` only after showing the two wheels and turn direction. These are command targets, not measured contact forces or achieved velocities. As a concrete educational-model example, R06 sample60 has v≈0.1723m/s, ω=+1rad/s, b=0.288m, r=0.033m: right/left targets≈0.3163/0.0283m/s. Its recorded right/left motor targets are negative because of local axes. Do not interpret that sign as reverse travel. Source `pilots/05_moving_obstacle/revision_06/physics_closed_loop.py` and its baseline trace; these dimensions are not universal TurtleBot3 specifications.

Holding v fixed while setting ω=0 is an actuation-conversion illustration. Recomputing the whole tracker may also change v. A claimed physical alternative requires an actual matched run; a contact-force claim requires collected force data. Keep frozen instructional states visibly distinct from solver-time motion.

Before production, inspect the central relation with explanatory subtitles hidden while retaining necessary labels. If the relation disappears, revise its geometry rather than adding narration. This is a diagnostic, not a claim that a silent diagram teaches every concept. Compare the same explanatory function against selected reference excerpts; identify an observable target in the existing episode decision record. Normal-speed rhythm and novice transfer require their own evidence.

## Repair a static-part or detached-equation gap

For a demonstrated static-component gap, allocate an actual component-action interval in the existing manifest: identify the part, input, recorded joint/body response, source interval and decisive visibility. Choose a view where displacement/rotation is observable; a larger still beside moving arrows does not meet this target. Return to whole-body context using the same run. If recorded articulation is absent, narrow the claim or collect it; an explicitly illustrative actuator demo is a separate evidence mode.

For a demonstrated quantity-to-equation gap, specify which already-visible value supplies each term and the ordered reveal that expresses the operation. Keep the source quantity visible while its copy moves into the term slot, then show the result and a supported condition change. A full equation fading in beside a picture does not meet this target. Reserve measured phrase time for the correspondence; preserve accepted narration when the existing utterance permits the added visual reasoning.

## Repair a lesson from small-sample viewer feedback

State the intended audience and prerequisites in the episode notes. For an introductory control lesson, explain an unfamiliar command term at its first use in plain language: a speed target is the speed requested from a wheel; the recorded response is what the simulation produced. Keep units after the meaning is established.

Diagnose the missing link from the answers. A viewer naming the obstacle/path has not yet explained how a direction error produces a turn command; a viewer explaining differential drive may still miss why this target requires a left turn. Show the selected nearby target relative to the current heading, then carry the same orientation and left/right roles into wheel commands and response. Define this repair in existing `focus`/`state_change` and the critical excerpt, with enough preceding context to understand it.

Allocate local time for locating inputs, following correspondence and inspecting the result. During a difficult derivation, avoid asking the viewer to read a long new caption while tracking moving numbers and a new formula. Split the explanation into measured phrases and retire resolved emphasis. Reallocate repeated outcome time first; if the requested runtime cannot hold the necessary explanation, propose a concrete scope/runtime tradeoff. A longer episode, a slower TTS rate or a fixed pause length alone does not establish a repair.

Use neutral questions that state what is held fixed. Keep first-pass free answers ahead of revealing hints; a later targeted clarification is a separate diagnostic check. An ambiguous or sparse answer leaves a distinction unconfirmed and can expose a survey problem. Retain useful physical views when their benefit is supported. Record sample size/background and episode-specific results; do not turn four responses into a universal threshold or creator-parity claim.

## From observed R14 craft gaps to bounded shot decisions

For a requested craft upgrade, vary composition when the viewer's task changes: orient with context, predict with a stable mechanism, derive with geometry, inspect notation, then return to response. Keep the same object, orientation and quantity roles across those views. Repeating a left-object/right-text layout is acceptable where it helps comparison; select another view when it hides the deciding feature or geometric inference. Record the reason in existing `focus`, without a cut quota or second shot list.

In a differential-drive derivation, expose the distance difference before introducing angular speed: in an explicitly ideal no-slip construction, equal-time wheel travel satisfies Δs = sR − sL = bθ, then divide by elapsed time to obtain ω = (vR − vL)/b. Show axle span, wheel travel arcs and body heading changing together; straight displacement bars alone leave the origin of θ unexplained. Handle equal travel as straight motion and opposing travel as a supported spin case. This construction explains geometry, not the Bullet run's slip/contact response; preserve that boundary and never force recorded trajectories onto ideal arcs.

For prediction shots, use one readable prompt outside the mechanism's swept arrows and final caption area. Retire redundant question text once the title establishes the task. Inspect the prompt before the answer is revealed. Define completion as readable arrows/labels plus the supported geometric link; video length and layout variety alone do not satisfy it.

## Mechanism relations and a complete worked example

Apply these decisions to demonstrated comparison gaps; adapt to the topic instead of imposing an episode template.

- Connected mechanism: removing housing must leave the deciding relation readable. For differential drive, retain wheel pair, an explicitly annotated axle/body center, local ground and heading. Source anchors and travel history from recorded transforms; do not invent hardware or forces.
- Derivation: expose the missing equality before adding notation. In ideal no-slip turning, show a common center/angle, both radii, their difference b, then sR=rRθ and sL=rLθ; visible subtraction gives (rR−rL)θ=bθ. Center midpoint travel explains the average and denominator 2. Reveal only the active relation within measured phrase time; revise speech if the necessary inference cannot fit.
- Worked feedback: follow one recorded run through pose/target comparison, command, observed response and next comparison. Keep world landmarks and source times. A separate stopping experiment can explain command/response, but must not masquerade as this feedback cycle.
- Changed condition: change geometry, not just its conclusion label. Hold wheel travel/time fixed and compare narrower/wider ideal bodies and their angles before highlighting b. This is a geometric prediction, not a new physical run.
- Surface: assign a diagnosed material/light weakness to Blender with fixed-pose candidates. Plate layers, rubber/metal separation and contact matter more than generic gloss. Preserve the bright studio and faithful meshes.
- Progression: the first experiment establishes how to read the evidence; later cases focus on differences. Choose context, mechanism, comparison, derivation or feedback composition by task while retaining identity. No cut quota or automatic runtime extension; accepted speech stays intact while picture uses its duration for supported inspection.

Keep applicable targets, source boundaries and verification ranges in the existing episode README/manifest focus. Actual rendered relations, rather than added instructions, establish completion. Direct playback/listening and novice evidence remain separate.

### Rebudget time when adding intermediate reasoning

Approved narration does not fix the reading budget for newly added algebra. Before keeping an old beat duration, count the new inferential steps and reserve settled reading time between them. If actual viewer feedback identifies a rushed derivation, reopen that beat's speech/event timing; preserve successful adjacent material and recover time from demonstrated repetition when appropriate. Local sentence-boundary pauses/cuts are eligible when they preserve meaning, avoid cutting words, and are disclosed; regenerate the audio manifest, sentence cues and all downstream offsets. Validate the new voiced excerpt and retain the user's pace answer with its exact scope. R16's 18.47→26.47-second derivation and shortened repeated recap are one observed repair, not a universal duration rule.
