import json
from collections import Counter

file_path = r"c:\Users\raghu\Desktop\FitCraveMain\fitcrave-datascience\app\engines\workout\data\exercises.json"

with open(file_path, "r", encoding="utf-8") as f:
    exercises = json.load(f)

print(f"Total Exercises: {len(exercises)}")

def analyze_field(field_name):
    counts = Counter()
    for ex in exercises:
        val = ex.get(field_name)
        if isinstance(val, list):
            for v in val:
                counts[v] += 1
        elif val is not None:
            counts[val] += 1
        else:
            counts["None"] += 1
    print(f"\n--- {field_name.capitalize()} ---")
    for k, v in counts.most_common():
        print(f"  {k}: {v}")

analyze_field("level")
analyze_field("equipment")
analyze_field("category")
analyze_field("primaryMuscles")
analyze_field("mechanic")
analyze_field("force")

print("\n--- Sample Structure ---")
if exercises:
    print(json.dumps(exercises[0], indent=2))
