import json
import os
from collections import Counter

bbox_dir = "/root/Documents/physical-ai-learning-journey/projects/omniglam-sdg/outputs_v2"
shade_counts = Counter()
total_frames = 0

shade_names = [
    "deep_learning_red", "render_rose", "null_mauve", "softmax",
    "runtime_berry", "pixar_pink", "cudiva"
]

for f in sorted(os.listdir(bbox_dir)):
    if f.startswith("bounding_box_2d_tight") and f.endswith(".json"):
        total_frames += 1
        with open(os.path.join(bbox_dir, f)) as fp:
            data = json.load(fp)
            if isinstance(data, list):
                for path in data:
                    for shade in shade_names:
                        if shade in path:
                            shade_counts[shade] += 1

print(f"Total frames: {total_frames}")
print(f"\nShade appearances:")
for shade, count in sorted(shade_counts.items(), key=lambda x: -x[1]):
    print(f"  {shade}: {count}")

print(f"\nTotal annotations: {sum(shade_counts.values())}")
if total_frames > 0:
    print(f"Average shades per frame: {sum(shade_counts.values()) / total_frames:.1f}")