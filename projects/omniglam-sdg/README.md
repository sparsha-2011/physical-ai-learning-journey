# 💄 OmniGlam — Synthetic Data Generation for Retail Beauty Robotics



A synthetic data generation pipeline built with NVIDIA Isaac Sim and Omniverse Replicator, designed to train robots to identify lipstick shades by name in retail environments.



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

  *The vision: a robot arm that can scan and identify each OmniGlam lipstick shade by name. This project builds the synthetic data pipeline that makes that possible i.e. generating the training data a robot would need to get there.*
  
</p>



**Brand:** OmniGlam  
**Built with:** NVIDIA Isaac Sim 5.1.0 · Omniverse Replicator · OpenUSD · Brev Cloud · L40S GPU  
**By:** Sparsha Srinath

---

## 🎯 What is this project?

OmniGlam is a synthetic data generation pipeline that produces annotated training images for a retail beauty robot — one that can identify specific lipstick shades by name on a shelf or vanity surface.

Instead of manually photographing thousands of lipstick tubes in different lighting conditions and angles, this pipeline generates them automatically inside NVIDIA Isaac Sim — producing photorealistic, perfectly labelled training data at scale.

**The problem it solves:**
Retail robots need to identify specific product SKUs — not just "lipstick" but "Neural Nude" vs "Deep Learning Red." Real-world data collection for this is slow, expensive, and hard to scale. Synthetic data generation makes it instant and infinite.

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
| Shade names and colours defined | ✅ | 6 tech-inspired shades |
| Lipstick asset sourced | 🔄 | FBX from Sketchfab |
| Asset converted to USD | ⏳ | |
| Scene built in Isaac Sim | ⏳ | Vanity surface + HDRI lighting |
| 6 shade instances created | ⏳ | OmniPBR materials per shade |
| Semantic labels added | ⏳ | Per shade class labels |
| Camera + render product set up | ⏳ | Randomised position |
| Randomisers configured | ⏳ | Lighting · positions · camera |
| SDG pipeline running | ⏳ | BasicWriter + annotators |
| Output reviewed + documented | ⏳ | |

---

## 🔧 Tech Stack

```
OpenUSD          ← scene description and asset format
NVIDIA Omniverse ← platform and rendering engine
Isaac Sim 5.1.0  ← simulation environment
Replicator API   ← randomisation and data capture
BasicWriter      ← annotated dataset output
OmniPBR          ← physically based materials per shade
Brev Cloud       ← L40S GPU cloud instance
```

---

## 🎨 Scene Design

**Environment:**
- Flat vanity surface with marble/brushed material
- HDRI dome light randomised each frame — morning light, studio white, warm evening, cool blue
- 6 lipstick tubes scattered on the surface with collision-checked randomisation

**What gets randomised every frame:**
- Tube positions on the vanity surface
- Camera angle and distance
- Dome light texture (HDRI environment)
- Light intensity and colour temperature

**3 cameras:**
- Top-down view — full vanity overview
- Close-up view — individual shade detail
- Angled view — natural shopping perspective

---

## 📊 Dataset Output

For each captured frame the pipeline generates:

| File | Contents | Purpose |
|---|---|---|
| `rgb_*.png` | Photorealistic scene | Training image |
| `semantic_seg_*.png` | Colour-coded shade map | Pixel-level shade identification |
| `bounding_box_*.json` | Shade location + label | Object detection training |
| `depth_*.png` | Distance map | 3D position of each tube |

---

## 💼 Why this matters

**For retail companies:**
A robot that can identify specific lipstick shades by name enables automated shelf restocking, order fulfilment, and inventory management in beauty retail — Sephora, Ulta, MAC stores globally.

**For NVIDIA:**
Demonstrates Isaac Sim's SDG pipeline applied to retail beauty — a market segment where fine-grained product recognition (shade-level, not just category-level) is the key technical challenge.

**The sim-to-real story:**
Synthetic data trained on OmniGlam shades transfers to real-world lipstick recognition because NVIDIA's RTX renderer produces photorealistic images that close the sim-to-real gap — the same lighting physics, material reflectance, and shadow behaviour as a real camera.

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
```bash
mkdir -p ~/Documents/physical-ai-learning-journey/projects/omniglam-sdg/assets
cp /path/to/lipstick.usd ~/Documents/physical-ai-learning-journey/projects/omniglam-sdg/assets/
```

### Step 4 — Run the pipeline
Open Isaac Sim Script Editor (**Window → Script Editor**) and run the pipeline script.
*Full script coming soon as the project progresses.*

### Step 5 — Check output
```bash
ls ~/Documents/physical-ai-learning-journey/projects/omniglam-sdg/outputs/
```

### Step 6 — Push to GitHub before stopping Brev
```bash
cd ~/Documents/physical-ai-learning-journey
git add .
git commit -m "OmniGlam SDG output - session $(date +%Y-%m-%d)"
git push
```

> ⚠️ Always push to GitHub before stopping your Brev instance — storage does not persist between sessions.

---

## 📸 Screenshots

*Will be added as the project progresses*

| Screenshot | Description |
|---|---|
| Scene setup | Vanity surface with 6 OmniGlam tubes |
| RGB output | Sample generated training image |
| Semantic segmentation | Shade-coded output |
| Bounding boxes | Annotated shade detection |
| Dataset overview | Full output folder structure |

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

---

*Updated as the project progresses · Built by Sparsha Srinath*