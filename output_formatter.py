from drift_engine import DRIFT_DETECT_THRESHOLD


def format_output(drift_rate, drift_label, top_changes, ai_response, confidence_score):
    return {
        "drift_detected": drift_rate > DRIFT_DETECT_THRESHOLD,
        "drift_rate": round(drift_rate, 4),
        "drift_label": drift_label,
        "top_changes": top_changes,
        "ai_explanation": ai_response,
        "recommendations": [],
        "confidence_score": round(confidence_score, 4),
    }