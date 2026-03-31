import difflib


class PronunciationScorer:
    """Pronunciation scorer using transcript comparison (MVP approach)."""

    def score_transcript(self, spoken: str, reference: str) -> dict:
        spoken_clean = spoken.strip().replace(" ", "")
        reference_clean = reference.strip().replace(" ", "")
        similarity = difflib.SequenceMatcher(None, spoken_clean, reference_clean).ratio()
        score = int(similarity * 100)
        return {
            "overall_score": score,
            "spoken": spoken,
            "reference": reference,
            "feedback": self._get_feedback(score),
        }

    def _get_feedback(self, score: int) -> str:
        if score >= 90:
            return "Perfect pronunciation! すごい！"
        elif score >= 75:
            return "Very good! Just a small adjustment needed."
        elif score >= 60:
            return "Good effort! Let's practice that one more time."
        else:
            return "Let's try again slowly. Listen carefully and repeat after me."
