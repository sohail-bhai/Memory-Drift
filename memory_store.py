from datetime import datetime
from data_source import BrightDataSource


class MemoryStore:
    def __init__(self, user_id="user_001"):
        self.user_id = user_id
        self.past_interactions = []
        self.current_interactions = []

    def load_from_source(self, data_source):
        data = data_source.fetch_all_interactions()
        self.past_interactions = data["past"]
        self.current_interactions = data["current"]
        print(f"✅ Memory loaded — Past: {len(self.past_interactions)} records | Current: {len(self.current_interactions)} records")

    def get_past(self):
        return self.past_interactions

    def get_current(self):
        return self.current_interactions

    def extract_preferences(self, interactions):
        if not interactions:
            return {}
        counts = {}
        for item in interactions:
            cat = item["category"]
            counts[cat] = counts.get(cat, 0) + 1
        total = sum(counts.values())
        distribution = {cat: round(count / total, 4) for cat, count in counts.items()}
        return dict(sorted(distribution.items(), key=lambda x: x[1], reverse=True))

    def get_past_preferences(self):
        return self.extract_preferences(self.past_interactions)

    def get_current_preferences(self):
        return self.extract_preferences(self.current_interactions)

    def get_memory_summary(self):
        return {
            "user_id"             : self.user_id,
            "past_interactions"   : self.past_interactions,
            "current_interactions": self.current_interactions,
            "past_preferences"    : self.get_past_preferences(),
            "current_preferences" : self.get_current_preferences()
        }


if __name__ == "__main__":
    source = BrightDataSource(user_id="user_001")
    memory = MemoryStore(user_id="user_001")
    memory.load_from_source(source)

    past_prefs = memory.get_past_preferences()
    current_prefs = memory.get_current_preferences()

    print("\n" + "=" * 45)
    print("   MEMORY STORE — PREFERENCE DISTRIBUTIONS")
    print("=" * 45)

    print("\n📦 PAST PREFERENCES:")
    for cat, score in past_prefs.items():
        bar = "█" * int(score * 30)
        print(f"  {cat:<12} {bar} {score:.2%}")

    print("\n📦 CURRENT PREFERENCES:")
    for cat, score in current_prefs.items():
        bar = "█" * int(score * 30)
        print(f"  {cat:<12} {bar} {score:.2%}")

    print("\n" + "=" * 45)
    print("✅ memory_store.py working correctly.")
    print("   Pass get_memory_summary() to core_logic.py next.\n")
