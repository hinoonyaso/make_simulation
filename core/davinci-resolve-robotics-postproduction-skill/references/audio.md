# Audio pass

Read only for narration/SFX/BGM work.

## Narration
- Treat narration timing as the spine of the edit.
- Clean obvious noise and level inconsistencies conservatively.
- Use EQ/compression/de-essing only when they improve intelligibility.
- Avoid processing that makes the voice sound hyped, boomy, or obviously synthetic.

## SFX
Use a small vocabulary:
- soft tick/click: selection, state lock, target acquisition
- subtle whoosh: meaningful spatial transition or reveal
- restrained impact: key result/insight
- error cue: only for an actual failure/collision/invalid state

Silence is valid. Do not place an effect on every animation.

## BGM
- Low-information, non-vocal music is preferred under technical explanation.
- Duck or reduce BGM during dense derivations and important spoken conclusions.
- Never let music determine explanation timing.

## Loudness
Do not guess numerical loudness targets unless the user/project provides a delivery spec. Measure and report actual output when supported by the Resolve workflow.

## Divided viewer voice ratings

When ratings disagree without a named defect, retain the current voice as a candidate and collect the awkward word/phrase, time and playback conditions before changing it. Separate pronunciation, phrase boundaries, prosody, intelligibility and explanation density. Patch the identified cause at the smallest useful scope; a voice replacement or global rate change needs evidence that it helps. Regenerated speech requires new measured timing/captions and listening review of the changed range. With no listening access, state that naturalness remains unverified rather than inferring it from a score, ASR or waveform.
