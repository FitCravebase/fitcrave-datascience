import json
from collections import Counter

file_path = r"c:\Users\raghu\Desktop\FitCraveMain\fitcrave-datascience\app\engines\workout\data\exercises.json"
out_path = r"c:\Users\raghu\Desktop\FitCraveMain\fitcrave-datascience\analysis_report.txt"

with open(file_path, "r", encoding="utf-8") as f:
    exercises = json.load(f)

lines = []
lines.append(f"Total Exercises: {len(exercises)}")

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
    lines.append(f"\n--- {field_name.capitalize()} ---")
    for k, v in counts.most_common():
        lines.append(f"  {k}: {v}")

analyze_field("level")
analyze_field("equipment")
analyze_field("category")
analyze_field("primaryMuscles")
analyze_field("mechanic")
analyze_field("force")

lines.append("\n--- Sample Structure ---")
if exercises:
    for k, v in exercises[0].items():
        if isinstance(v, list) and k in ["instructions", "images"]:
            lines.append(f"  {k}: <list of {len(v)} items>")
        else:
            lines.append(f"  {k}: {v}")

with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
