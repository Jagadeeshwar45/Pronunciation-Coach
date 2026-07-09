"""
Pronunciation scoring engine.

Approach
--------
This is an *unscripted* pronunciation assessment (no reference text is given
by the user), so we can't do a direct "expected vs spoken" phoneme diff like
scripted read-aloud tools (e.g. Azure Pronunciation Assessment) do. Instead we
use three independent, cheap-to-compute signals that correlate well with poor
pronunciation / unclear articulation:

1. ASR word-level confidence (faster-whisper's per-word probability).
   Whisper is a large, robustly-trained acoustic+language model; when a word
   is mispronounced or slurred, the decoder's probability for that word drops
   noticeably even if it still guesses correctly from context. This is the
   primary signal.

2. Lexicon check (CMU Pronouncing Dictionary via `pronouncing`).
   If the recognized token isn't a real English word in CMUdict at all, it's
   a sign the pronunciation was garbled enough that ASR could not map it to
   any known English word.

3. Disfluency / long pause detection.
   Long gaps between words often indicate hesitation, self-correction, or
   articulation struggle -- useful context for a learner even if the word
   itself was eventually recognized correctly.

None of this claims to be a clinically precise phoneme-level score. It's a
practical, explainable proxy that is genuinely useful to a learner: it tells
them *which words* to go back and practice, and gives a reason why.
"""

import soundfile as sf
from faster_whisper import WhisperModel
import pronouncing

MIN_DURATION = 30
MAX_DURATION = 45
# small tolerance around the hard limits so a 29.5s or 46s clip isn't
# rejected for trivial reasons, while still enforcing the spirit of the rule
DURATION_TOLERANCE = 3

LOW_CONF_THRESHOLD = 0.55
MID_CONF_THRESHOLD = 0.75
LONG_PAUSE_SECONDS = 0.6

_model = None


def get_model() -> WhisperModel:
    """Lazily load the model once per process (cold start cost, then cached)."""
    global _model
    if _model is None:
        # "small.en" on CPU int8 is a deliberate trade-off: good enough
        # accuracy for word-level confidence, small enough to run on a
        # free-tier CPU dyno without a GPU. See ARCHITECTURE.md.
        _model = WhisperModel("small.en", device="cpu", compute_type="int8")
    return _model


def get_duration_seconds(path: str) -> float:
    with sf.SoundFile(path) as f:
        return len(f) / f.samplerate


def analyze_audio(path: str) -> dict:
    duration = get_duration_seconds(path)
    if duration < (MIN_DURATION - DURATION_TOLERANCE) or duration > (MAX_DURATION + DURATION_TOLERANCE):
        raise ValueError(
            f"Recording is {duration:.1f}s long. Please upload audio between "
            f"{MIN_DURATION} and {MAX_DURATION} seconds."
        )

    model = get_model()
    segments, _info = model.transcribe(
        path,
        word_timestamps=True,
        vad_filter=True,
        language="en",
    )

    words = []
    all_probs = []
    prev_end = None

    for seg in segments:
        for w in seg.words:
            token = (w.word or "").strip()
            if not token:
                continue
            prob = float(w.probability)
            all_probs.append(prob)

            issues = []
            if prob < LOW_CONF_THRESHOLD:
                issues.append("mispronounced_or_unclear")
            elif prob < MID_CONF_THRESHOLD:
                issues.append("slightly_unclear")

            clean = token.strip(".,!?;:\"'-").lower()
            if clean.isalpha() and len(clean) > 1 and not pronouncing.phones_for_word(clean):
                issues.append("not_recognized_as_english_word")

            if prev_end is not None and (w.start - prev_end) > LONG_PAUSE_SECONDS:
                issues.append("long_pause_before")

            words.append(
                {
                    "word": token,
                    "start": round(w.start, 2),
                    "end": round(w.end, 2),
                    "confidence": round(prob, 3),
                    "issues": issues,
                    "flagged": len(issues) > 0,
                }
            )
            prev_end = w.end

    if not words:
        raise ValueError("No speech was detected in the uploaded audio.")

    transcript = " ".join(w["word"] for w in words).strip()

    mean_conf = sum(all_probs) / len(all_probs)
    flagged_count = sum(1 for w in words if w["flagged"])
    flagged_ratio = flagged_count / len(words)

    # Score formula: start from mean ASR confidence (0-100), then apply an
    # extra penalty proportional to the *fraction* of words that had a
    # concrete issue, so one bad word in a 60-word clip doesn't tank the
    # score, but a clip where a third of words were unclear scores much lower.
    score = 100 * mean_conf - (flagged_ratio * 25)
    score = max(0, min(100, round(score)))

    if score >= 85:
        band = "Excellent"
    elif score >= 70:
        band = "Good"
    elif score >= 50:
        band = "Fair"
    else:
        band = "Needs practice"

    summary_points = []
    low_words = [w["word"] for w in words if "mispronounced_or_unclear" in w["issues"]]
    if low_words:
        preview = ", ".join(dict.fromkeys(low_words[:6]))
        summary_points.append(f"Low-confidence words worth re-practicing: {preview}")

    oov_words = [w["word"] for w in words if "not_recognized_as_english_word" in w["issues"]]
    if oov_words:
        preview = ", ".join(dict.fromkeys(oov_words[:6]))
        summary_points.append(f"Words that didn't match any known English pronunciation: {preview}")

    pause_words = [w["word"] for w in words if "long_pause_before" in w["issues"]]
    if pause_words:
        preview = ", ".join(dict.fromkeys(pause_words[:6]))
        summary_points.append(f"Noticeable hesitation/pause before: {preview}")

    if not summary_points:
        summary_points.append("No major issues detected — clear and confident pronunciation throughout.")

    return {
        "duration_seconds": round(duration, 1),
        "transcript": transcript,
        "overall_score": score,
        "score_band": band,
        "mean_confidence": round(mean_conf, 3),
        "flagged_word_count": flagged_count,
        "total_word_count": len(words),
        "words": words,
        "feedback": summary_points,
    }
