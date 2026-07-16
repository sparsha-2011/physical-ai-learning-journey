import json
import os
from collections import Counter

bbox_dir = "/root/Documents/physical-ai-learning-journey/projects/omniglam-sdg/outputs_v3"
label_counts = Counter()
total_frames = 0

for f in sorted(os.listdir(bbox_dir)):
    if f.startswith("bounding_box_2d_tight_labels") and f.endswith(".json"):
        total_frames += 1
        with open(os.path.join(bbox_dir, f)) as fp:
            data = json.load(fp)
            if isinstance(data, dict):
                for item in data.values():
                    label_counts[item.get("class", "unknown")] += 1

print(f"Total frames: {total_frames}")
print(f"\nLabel appearances:")
for label, count in sorted(label_counts.items(), key=lambda x: -x[1]):
    print(f"  {label}: {count}")

print(f"\nTotal annotations: {sum(label_counts.values())}")
if total_frames > 0:
    print(f"Average tubes per frame: {sum(label_counts.values()) / total_frames:.1f}")