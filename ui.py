import streamlit as st

from agent_system import analyze_user_drift, load_interactions_from_memory_store
from ai_module import get_ai_explanation
from output_formatter import format_output


def run_analysis(user_id: str = "user_001", past_days: int = 7, current_days: int = 2):
    interactions = load_interactions_from_memory_store(
        user_id=user_id,
        past_days=past_days,
        current_days=current_days,
    )
    return analyze_user_drift(
        interactions=interactions,
        past_days=past_days,
        current_days=current_days,
        include_chart=False,
    )


st.set_page_config(page_title="Agent with Memory Drift Detection", layout="wide")
st.title("Agent with Memory Drift Detection")

user_id = st.text_input("User ID", value="user_001")
past_days = st.slider("Past window (days)", min_value=3, max_value=30, value=7)
current_days = st.slider("Current window (days)", min_value=1, max_value=7, value=2)

if st.button("Run Analysis"):
    result = run_analysis(user_id=user_id, past_days=past_days, current_days=current_days)
    top_changes = {
        "top_increased": result.get("top_increased", []),
        "top_decreased": result.get("top_decreased", []),
    }

    explanation = get_ai_explanation(
        result["drift_rate"],
        result["drift_label"],
        top_changes,
        result["past_prefs"],
        result["current_prefs"],
    )

    output = format_output(
        result["drift_rate"],
        result["drift_label"],
        top_changes,
        explanation,
        result["confidence"],
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Drift Rate", output["drift_rate"])
    c2.metric("Drift Level", output["drift_label"])
    c3.metric("Confidence", output["confidence_score"])

    st.write("### AI Explanation")
    st.write(output["ai_explanation"])

    st.write("### Top Increases")
    st.write(output["top_changes"]["top_increased"])

    st.write("### Top Decreases")
    st.write(output["top_changes"]["top_decreased"])