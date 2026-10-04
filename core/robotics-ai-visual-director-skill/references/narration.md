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
