# 💄 OmniGlam — Synthetic Data Generation for Retail Beauty Robotics

<p align="center">
  <a href="./assets/omniglam-vision.gif">
    <img
      src="./assets/omniglam-vision-poster.png"
      alt="OmniGlam synthetic vision — click to view animation"
      width="900"
    />
  </a>
  <br>
  <sub>▶ Click the preview to view the animation</sub>

  *The vision: a robot arm that can scan and identify each OmniGlam lipstick shade by name. This project builds the synthetic data pipeline that makes that possible by generating the training data a robot would need to get there.*

</p>

**Brand:** OmniGlam  
**Built with:** NVIDIA Isaac Sim 5.1.0 · Omniverse Replicator · OpenUSD · Brev Cloud · L40S GPU  
**By:** Sparsha Srinath

---

## 🎯 What is this project?

OmniGlam is a synthetic data generation pipeline that produces annotated training images for a retail beauty robot — one that can identify specific lipstick shades by name on a shelf or vanity surface.

Instead of manually photographing thousands of lipstick tubes in different lighting conditions and angles, this pipeline generates them automatically inside NVIDIA Isaac Sim — producing photorealistic, perfectly labelled training data at scale.

**The problem it solves:**
Retail robots need to identify specific product SKUs — not just "lipstick" but "Runtime Berry" vs "Deep Learning Red." Real-world data collection for this is slow, expensive, and hard to scale. Synthetic data generation makes it instant and infinite.

---

## 🏷️ OmniGlam Shade Collection

| Shade | Colour | Hex | RGB |
|---|---|---|---|
| Deep Learning Red | deep red | `#962121` | (0.59, 0.13, 0.13) |
| Runtime Berry | dark berry | `#64094b` | (0.39, 0.04, 0.29) |
| Render Rose | muted rose | `#a4707f` | (0.64, 0.44, 0.50) |
| Pixar Pink | vibrant pink | `#cd3a64` | (0.80, 0.23, 0.39) |
| Null Mauve | soft mauve | `#f4a3d8` | (0.96, 0.64, 0.85) |
| CuDiva | warm coral | `#e1765e` | (0.88, 0.46, 0.37) |
| Softmax | soft blush | `#ed9297` | (0.93, 0.57, 0.59) |

---

## 🏗️ Project Status

| Step | Status | Notes |
|---|---|---|
| Shade names and colours defined | ✅ | 7 tech-inspired shades |
| Lipstick asset sourced + converted to USD | ✅ | FBX from Sketchfab → USD via Omniverse asset converter |
| Scene built in Isaac Sim | ✅ | Vanity surface + 3-point lighting (KeyLight · FillLight · RimLight) |
| 7 shade instances created | ✅ | OmniPBR materials per shade · gold metallic cases · caps hidden |
| Semantic labels added | ✅ | Per shade class labels via `rep.functional.modify.semantics` |
| Camera + render product set up | ✅ | 5 angle presets + close-up single tube · focal_length=18.0 |
| Randomisers configured | ✅ | Lighting · positions · camera · backdrop (white 75% / black 25%) |
| SDG pipeline — 500 frames generated | ✅ | RGB + bounding boxes + semantic segmentation · BasicWriter |
| Dataset converted to KITTI format | ✅ | 397 train · 99 val · convert_to_kitti.py |
| YOLOv8 model training | 🔄 | In progress — ultralytics |
| Web app — OmniGlam shade finder | ⏳ | HTML + CSS + JS + FastAPI + model inference |
| Deploy online | ⏳ | |

---

## 🔧 Tech Stack

```
OpenUSD          ← scene description and asset format
NVIDIA Omniverse ← platform and rendering engine
Isaac Sim 5.1.0  ← simulation environment
Replicator API   ← randomisation and data capture
BasicWriter      ← annotated dataset output (RGB + bbox + semantic seg)
OmniPBR          ← physically based materials per shade
HTML · CSS · JS    ← web app frontend (shade finder store)
FastAPI          ← inference API backend
YOLOv8           ← object detection model training (ultralytics)
Brev Cloud       ← L40S GPU cloud instance
```

---

## 🎨 Scene Design

**Environment:**
- Flat display surface (30x30 plane) with glossy near-white material
- 3-point lighting setup — KeyLight (warm), FillLight (cool), RimLight (white) + ambient distant light
- Backdrop switches between clean white and dramatic black each frame

**Two row arrangement:**
- Back row: Deep Learning Red · Render Rose · Null Mauve · Softmax
- Front row: Runtime Berry · Pixar Pink · CuDiva

**What gets randomised every frame:**
- Tube visibility (1–7 tubes per frame · every 5th frame = single tube close-up)
- Tube positions (slight scatter within row)
- Tube rotation (±10° tilt)
- Camera angle (5 presets — front angled, side left/right, close-up + random variation)
- Lighting intensity and colour temperature (5 presets from warm golden to bright white)
- Backdrop colour (white 75% · black 25%)

---

## 📊 Dataset Output

For each captured frame the pipeline generates:

| File | Contents | Purpose |
|---|---|---|
| `rgb_*.png` | Photorealistic scene (1024×1024) | Training image |
| `semantic_segmentation_*.png` | Colour-coded shade map | Pixel-level shade identification |
| `bounding_box_2d_tight_*.npy` | Bounding box coordinates | Object detection training |
| `bounding_box_2d_tight_*.json` | Shade class labels | Annotation metadata |

**Dataset statistics:**
- Total frames: 500
- Train: 397 frames · Val: 99 frames
- Shade distribution: balanced (226–263 appearances per shade)
- Average shades per frame: 1.7

---

## 💼 Why this matters

**For retail companies:**
A robot that can identify specific lipstick shades by name enables automated shelf restocking, order fulfilment, and inventory management in beauty retail — Sephora, Ulta, MAC stores globally.

**For NVIDIA:**
Demonstrates Isaac Sim's SDG pipeline applied to retail beauty — a market segment where fine-grained product recognition (shade-level, not just category-level) is the key technical challenge.

**Research backing:**
- [Synthetica (NVIDIA, 2024)](https://arxiv.org/abs/2410.21153) — photorealistic synthetic data closes the sim-to-real gap
- [FLORA (2025)](https://arxiv.org/abs/2508.21712) — 500 quality synthetic images can outperform 5,000 poorly generated ones

---

## 🚀 How to run

### Prerequisites
- NVIDIA Brev account — [brev.nvidia.com](https://brev.nvidia.com)
- Isaac Sim 5.1.0 launchable deployed on Brev (L40S GPU)
- noVNC + VS Code browser open

### Step 1 — Deploy Brev instance
1. Go to `brev.nvidia.com`
2. Deploy **Isaac Sim 5.1.0 with ROS2 Jazzy** launchable
3. Connect via noVNC and VS Code browser

### Step 2 — Clone the repo
```bash
cd ~/Documents
git clone https://github.com/sparsha-2011/physical-ai-learning-journey.git
cd physical-ai-learning-journey/projects/omniglam-sdg
```

### Step 3 — Add the lipstick asset
The lipstick FBX asset is not included due to licensing. Download a free lipstick model from [Sketchfab](https://sketchfab.com/search?q=lipstick&features=downloadable&price=free) (CC license) and place it in `assets/lipstick.fbx`.

Convert FBX to USD in Isaac Sim Script Editor:
```python
import asyncio
import omni.kit.asset_converter as converter

async def convert():
    task = converter.get_instance().create_converter_task(
        "/path/to/assets/lipstick.fbx",
        "/path/to/assets/lipstick.usd"
    )
    await task.wait_until_finished()

asyncio.ensure_future(convert())
```

### Step 4 — Run the SDG pipeline
Open Isaac Sim Script Editor (**Window → Script Editor**) and run `omniglam_sdg.py`.

### Step 5 — Convert to KITTI format
```bash
python3 convert_to_kitti.py
```

### Step 6 — Train with YOLOv8
```bash
pip install ultralytics
python3 train.py
```

### Step 7 — Push to GitHub before stopping Brev
```bash
cd ~/Documents/physical-ai-learning-journey
git add .
git commit -m "OmniGlam SDG output - session $(date +%Y-%m-%d)"
git push
```

> ⚠️ Always push to GitHub before stopping your Brev instance — storage does not persist between sessions.

---

## 📖 Learning context

This project is part of my Physical AI learning journey. I'm a full stack developer pivoting into Physical AI and robotics simulation.

**Prerequisites I completed before building this:**
- NVIDIA OpenUSD Certification ✅
- Intro to NVIDIA Omniverse course ✅
- Isaac Sim SDG tutorials (Recorder · Getting Started · Workflows · Scene Based · Object Based · Augmentation) ✅

**Full learning journey:** [physical-ai-learning-journey](https://github.com/sparsha-2011/physical-ai-learning-journey)

---

## 🔗 Resources

| Resource | Link |
|---|---|
| NVIDIA Isaac Sim | [docs.isaacsim.omniverse.nvidia.com](https://docs.isaacsim.omniverse.nvidia.com) |
| Omniverse Replicator | [docs.omniverse.nvidia.com/extensions/latest/ext_replicator](https://docs.omniverse.nvidia.com/extensions/latest/ext_replicator.html) |
| Isaac Sim on Brev | [Brev cloud setup](https://docs.isaacsim.omniverse.nvidia.com/latest/installation/install_advanced_cloud_setup_brev.html) |
| OpenUSD | [openusd.org](https://openusd.org) |
| Synthetica paper | [arxiv.org/abs/2410.21153](https://arxiv.org/abs/2410.21153) |
| FLORA paper | [arxiv.org/abs/2508.21712](https://arxiv.org/abs/2508.21712) |
| YOLOv8 | [docs.ultralytics.com](https://docs.ultralytics.com) |

---

*Updated as the project progresses · Built by Sparsha Srinath*
