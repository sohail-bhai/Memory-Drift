import random
from datetime import datetime, timedelta

CATEGORIES = ["Action", "Romance", "Comedy", "Drama", "Thriller", "Horror", "Sci-Fi"]

class BrightDataSource:
    def __init__(self, user_id="user_001"):
        self.user_id = user_id

    def fetch_past_interactions(self, days=7, count=20):
        past_bias = ["Action", "Action", "Action", "Comedy", "Comedy", "Thriller", "Sci-Fi"]
        interactions = []
        for i in range(count):
            timestamp = datetime.now() - timedelta(days=random.uniform(3, days))
            interactions.append({"user_id": self.user_id, "category": random.choice(past_bias), "timestamp": timestamp})
        return sorted(interactions, key=lambda x: x["timestamp"])

    def fetch_current_interactions(self, days=2, count=10):
        current_bias = ["Romance", "Romance", "Drama", "Drama", "Romance", "Comedy"]
        interactions = []
        for i in range(count):
            timestamp = datetime.now() - timedelta(days=random.uniform(0, days))
            interactions.append({"user_id": self.user_id, "category": random.choice(current_bias), "timestamp": timestamp})
        return sorted(interactions, key=lambda x: x["timestamp"])

    def fetch_all_interactions(self):
        return {"past": self.fetch_past_interactions(), "current": self.fetch_current_interactions()}

if __name__ == "__main__":
    source = BrightDataSource(user_id="user_001")
    data = source.fetch_all_interactions()

    print("=" * 45)
    print("   BRIGHT DATA — USER INTERACTIONS")
    print("=" * 45)

    print(f"\nPAST INTERACTIONS ({len(data['past'])} records):")
    for item in data["past"]:
        print(f"  [{item['timestamp'].strftime('%Y-%m-%d %H:%M')}]  {item['category']}")

    print(f"\nCURRENT INTERACTIONS ({len(data['current'])} records):")
    for item in data["current"]:
        print(f"  [{item['timestamp'].strftime('%Y-%m-%d %H:%M')}]  {item['category']}")

    print("\ndata_source.py working correctly.")