# Narration & audio craft

Restored from V8's dedicated narration-audio-director-skill; consult when writing a beat's
`text`, `sec`, `sfx`, or `bgm` fields. Do not imitate a creator's exact voice, catchphrases, or persona.

## Writing
Prefer: question -> concrete observation -> explanation -> consequence.
Use short clauses and spoken connectors. Avoid stacked definitions and noun-heavy prose.
Technical terms stay exact, but define them at first meaningful use.
Do not restate what the viewer can already read verbatim unless the repetition adds interpretation.

## Timing
Use estimated duration only as a planning aid; final recorded/TTS audio is authoritative. `core/narration/prepare_audio.py tts` writes the measured length back into `sec`.
Typical explanatory delivery is often around 135-165 spoken words/minute, but clarity overrides the number.
Budget extra silence after a new equation, spatial reveal, surprising result, or dense diagram.
Sync the visual event to the phrase that names/causes it; do not fire every animation at sentence start.

## Audio cues
Narration > important SFX > BGM > ambience.
Use SFX for meaningful state changes, selection, reveal, error/collision, or resolved insight.
Avoid constant whooshes/clicks. Duck or lower BGM during dense derivations and important conclusions.
Cue intent here; final loudness/EQ/compression decisions belong to Resolve after listening.

## Phrase anchors and deliberate pauses

- Write a connected explanation rather than disconnected captions: observation -> why it matters -> mechanism -> consequence. A question should receive an observable answer later.
- For timing-critical beats, put phrase/event anchors into the manifest's existing `state_change` or `focus`: e.g. on “이 칸이 막히면”, reveal that blocked region; on “새 경로”, expose the route before the robot follows it. The renderer uses measured utterance timing, not equal subdivisions.
- Audit `min_sec` against raw speech and the named visual task. Cue gaps alone do not prove silence; use the audio manifest, raw clip durations, or listen. A reading/thinking pause is useful only while the relevant evidence remains visible.
- Korean TTS `text` uses intended pronunciation, while `caption` retains standard notation: A* -> 에이스타; DWB -> 디더블유비. Audition terminology and at least the central explanation before the expensive render; record anything not actually listened to.
- Keep file paths, kit names, and production jargon out of narration. Say “교육용 모형이며 실제 Nav2 실행은 아닙니다” when applicable; put detailed provenance in README/description.

## Delivery intent and listening

Use the existing `text` and phrase anchors in `focus` to distinguish a question, an observation, a discovery and a conclusion. Plan pace and pauses around the viewer's task, not fixed per-sentence gaps. A supported TTS rate may be adjusted; do not assume the engine supports emotion/SSML controls. For expressive delivery that the engine cannot produce, revise wording or use an authorized recorded voice rather than pretending a parameter exists.

Before full production, listen to the critical excerpt with its picture. Check terminology pronunciation, clause boundaries, unnatural stress, whether the deciding reveal has time to register, and whether the conclusion lands after its evidence. Record listened ranges and fixes. Use phonetic `text` with standard `caption` for notation, including A* = 에이스타 and DWB = 디더블유비; add episode-specific exceptions to the episode's existing documentation. Do not duplicate a global pronunciation list across skills.

Regenerating speech invalidates its previous measured timing and alignment: rerun audio/caption preparation and affected visual timing before final checks. Loudness, silence detection and ASR alignment are signal evidence; none certifies pronunciation or delivery. When listening is unavailable, mark voice review incomplete.
