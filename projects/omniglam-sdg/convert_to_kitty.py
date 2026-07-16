import json
import numpy as np
import os
import shutil

# Paths
OUTPUTS_DIR = "/root/Documents/physical-ai-learning-journey/projects/omniglam-sdg/outputs_v3"
DATASET_DIR = "/root/Documents/physical-ai-learning-journey/projects/omniglam-sdg/dataset_v3"

IMAGE_WIDTH  = 1024
IMAGE_HEIGHT = 1024

# Create dataset folders
for split in ["train", "val"]:
    os.makedirs(f"{DATASET_DIR}/images/{split}", exist_ok=True)
    os.makedirs(f"{DATASET_DIR}/labels/{split}", exist_ok=True)

# Get all frame numbers
frames = sorted([
    f.replace("bounding_box_2d_tight_", "").replace(".npy", "")
    for f in os.listdir(OUTPUTS_DIR)
    if f.startswith("bounding_box_2d_tight_") and f.endswith(".npy")
])

print(f"Found {len(frames)} frames")

split_idx    = int(len(frames) * 0.8)
train_frames = frames[:split_idx]
val_frames   = frames[split_idx:]

print(f"Train: {len(train_frames)} | Val: {len(val_frames)}")

def process_frame(frame_num, split):
    npy_path    = f"{OUTPUTS_DIR}/bounding_box_2d_tight_{frame_num}.npy"
    labels_path = f"{OUTPUTS_DIR}/bounding_box_2d_tight_labels_{frame_num}.json"
    rgb_path    = f"{OUTPUTS_DIR}/rgb_{frame_num}.png"

    if not all(os.path.exists(p) for p in [npy_path, labels_path, rgb_path]):
        print(f"Missing files for frame {frame_num}")
        return False

    # Load bounding boxes
    bboxes = np.load(npy_path, allow_pickle=True)

    # Load class labels — {"0": {"class": "pixar_pink"}}
    with open(labels_path) as f:
        labels = json.load(f)

    kitti_lines = []
    for i, bbox in enumerate(bboxes):
        semantic_id = str(int(bbox[0]))
        x_min = float(bbox[1])
        y_min = float(bbox[2])
        x_max = float(bbox[3])
        y_max = float(bbox[4])

        # Skip invalid boxes
        if x_max <= x_min or y_max <= y_min:
            continue

        # Get class name from labels JSON
        class_name = labels.get(semantic_id, {}).get("class", "unknown")
        if class_name == "unknown":
            continue

        # KITTI format
        kitti_line = f"{class_name} 0 0 0 {x_min:.2f} {y_min:.2f} {x_max:.2f} {y_max:.2f} 0 0 0 0 0 0 0"
        kitti_lines.append(kitti_line)

    if not kitti_lines:
        return False

    # Save label file
    with open(f"{DATASET_DIR}/labels/{split}/{frame_num}.txt", "w") as f:
        f.write("\n".join(kitti_lines))

    # Copy RGB image
    shutil.copy(rgb_path, f"{DATASET_DIR}/images/{split}/{frame_num}.png")

    return True

# Process all frames
train_success = sum(process_frame(f, "train") for f in train_frames)
val_success   = sum(process_frame(f, "val") for f in val_frames)

print(f"\nDataset created!")
print(f"Train: {train_success} frames")
print(f"Val:   {val_success} frames")
print(f"Location: {DATASET_DIR}")