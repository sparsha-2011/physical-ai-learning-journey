# 🤖 Physical AI Learning Journey — Sparsha Srinath

> Full stack developer with 2 years of experience transitioning into Physical AI and robotics simulation.
> Documenting my path from zero to NVIDIA Omniverse developer — honest notes, real friction points, and everything I build along the way.

<a href="https://www.credly.com/badges/493a815e-02bd-44e3-91da-aea56614b27d/public_url"><img src="./02-openUSD-cert/assets/certification/openusd-ncp-badge.png" alt="NVIDIA Certified Professional: OpenUSD Development Badge" width="170"/></a>
<a href="#"><img src="https://img.shields.io/badge/Isaac%20Sim-In%20Progress-0078D4?style=flat-square&logo=nvidia&logoColor=white" alt="Isaac Sim In Progress"/></a>
<a href="#"><img src="https://img.shields.io/badge/Omniverse-In%20Progress-7B2FBE?style=flat-square&logo=nvidia&logoColor=white" alt="Omniverse In Progress"/></a>
<a href="#"><img src="https://img.shields.io/badge/Physical%20AI-Learning-FF6B35?style=flat-square" alt="Physical AI Learning"/></a>

---

## 🗺️ Timeline

| Day | Date   | Topics                                                                                                                        | Domains Covered                                                                                                                           |
| :-: | ------ | ----------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
|  1  | Jun 24 | USD Foundations                                                                                                               | Stage · Layer · Prim · Properties · Paths · File Formats · Metadata · Time Samples                                                        |
|  2  | Jun 25 | Composition Arcs Part 1                                                                                                       | Opinions · Value Resolution · LIVERPS · Sublayers · References · Payloads                                                                 |
|  3  | Jun 26 | Composition Arcs Part 2 · Advanced Composition · Schemas and Data Modeling                                                    | Variants · Inherits · Specializes · Edit Target · Session Layer · Flatten · IsA/API schemas · usdGenSchema · TfType · Model Kinds         |
|  4  | Jun 27 | Visualization · Pipeline and Data Exchange · Content Aggregation                                                              | Mesh · Primvars · UsdLux · Exporters · Importers · Hooks · Build Config · Instancing · PointInstancer                                     |
|  5  | Jun 28 | Debugging and Troubleshooting · Practice Test 1                                                                               | PrimStack · PropertyStack · TfDebug · MuteLayer · Composition Errors · **Score: 58%**                                                     |
|  6  | Jun 29 | Custom Schemas · Practice Test 2                                                                                              | usdGenSchema · TfType · Variant Fallbacks · Model Kinds · **Score: 62% (+4%)** · patched schema registration gaps                         |
|  7  | Jun 30 | Gap Review                                                                                                                    | Revisited TFType · visualisation exercises · patched Practice Test 2 gaps                                                                 |
|  8  | Jul 1  | Deep Dives                                                                                                                    | `stage.Flatten()` vs `UsdUtils.FlattenLayerStack()` · change notification · custom Model Kind · variant fallback sets · plugin deployment |
|  9  | Jul 2  | Gap Review                                                                                                                    | Hooks · prepend vs append arc ordering · explicit prim path vs defaultPrim                                                                |
| 10  | Jul 3  | Practice Test 3                                                                                                               | **Score: 67% (+5%)** · custom exporters · build configuration                                                                             |
| 11  | Jul 5  | Practice Test 4                                                                                                               | **Score: 77% (+10%)**                                                                                                                     |
| 12  | Jul 7  | An Introduction to Developing With NVIDIA Omniverse                                                                           | Kit app template · extensions · developer workflow                                                                                        |
| 13  | Jul 8  | Watched Hailey Ahn talk on Content Aggregation ([YouTube Live](https://www.youtube.com/live/LFCauWTNBM4?si=xcmupaXIEMtCtvug)) | Content aggregation concepts · practical context from expert session                                                                      |
| 14  | Jul 9  | OpenUSD Final Certification Exam                                                                                              | **Passed (NVIDIA-Certified Professional: OpenUSD Development)**                                                                           |
| 15  | Jul 11 | Synthetic Data Generation Kickoff                                                                                             | Omniverse Replicator planning · custom writer scaffold · run config draft · screenshot checklist                                          |

> ↑ +19 points across 4 practice attempts · 10 topics covered

---

## 🔄 Jun 26 — Brev cloud setup

**Goal:** Get Isaac Sim running without a local NVIDIA GPU.

**Status:** In progress · Jun 26, 2026

Isaac Sim requires an NVIDIA RTX GPU — running on Intel Iris Xe on Mac locally, so set up NVIDIA Brev cloud to spin up a GPU instance on demand. This is the recommended path for developers without local RTX hardware.

- Created NVIDIA Brev account
- Located Isaac Sim 6.0.0 with ROS2 Jazzy launchable (L40S GPU · $2.27/hr)
- Connected to noVNC desktop successfully
- Confirmed Isaac Sim and Kit are installed on the instance
- Full deployment and coursework begins TBD

[📝 Setup notes →] | [📸 Screenshots →]

---

## ✅ Jul 9 — OpenUSD Certification Passed

**Goal:** Understand the foundational language of the entire Physical AI stack.

**Status:** Passed · Jul 9, 2026

OpenUSD (Universal Scene Description) is the file format and framework that underpins Omniverse, Isaac Sim, and every robot and simulation asset in the Physical AI ecosystem. Originally built by Pixar for film pipelines, adopted by NVIDIA as the foundation of Omniverse.

**Key concepts:**

- Stage composition and prim hierarchy
- USD schemas and typed prims
- Referencing, layering, and composition arcs
- Python scripting with the USD API
- Why USD enables interoperability across the entire Physical AI stack

### 📊 Practice test progression

The cert requires a passing score of 80%. Here's the iterative journey to get there — each attempt identified weak areas and informed the next study session.

| Attempt             | Score      | Status | Key takeaway                                                          |
| ------------------- | ---------- | ------ | --------------------------------------------------------------------- |
| Practice Test 1     | 58%        | ❌     | Baseline — identified gaps in schema definition and composition arcs  |
| Practice Test 2     | 62%        | ❌     | +4% — improved on composition arcs, still weak on schema registration |
| Practice Test 3     | 67%        | ❌     | +5% — schema concepts improving, gaps in USD API and layering         |
| Practice Test 4     | 77%        | ❌     | +10% — strong improvement, approaching passing threshold              |
| **Final Cert Exam** | **Passed** | **✅** | NVIDIA-Certified Professional: OpenUSD Development                    |

> Every failed attempt was a study session in disguise — each score gap pointed directly to the next concept to revisit. 19 points gained across 4 attempts.

[📸 Test 1 →](./02-openUSD-cert/practice-tests/exam-1.png) | [📸 Test 2 →](./02-openUSD-cert/practice-tests/exam-2.png) | [📸 Test 3 →](./02-openUSD-cert/practice-tests/exam-3.png) | [📸 Test 4 →](./02-openUSD-cert/practice-tests/exam-4.png)

[🏅 Credly badge →](https://www.credly.com/badges/493a815e-02bd-44e3-91da-aea56614b27d/public_url) | [📄 Certificate PDF →](./02-openUSD-cert/assets/certification/openusd-ncp-certificate-2026-07-09.pdf) | [📝 Cert notes →](./02-openUSD-cert/README.md) | [💡 Key concepts →](./02-openUSD-cert/notes/)

---

## ✅ Jul 7 — An Introduction to Developing With NVIDIA Omniverse

**Goal:** Understand how Omniverse applications are built and extended.

Omniverse is NVIDIA's platform built on top of OpenUSD — the runtime, renderer, and app ecosystem that powers Isaac Sim and the broader Physical AI stack. This course covers building a Kit-based application from a template and customizing it via extensions.

**Key concepts:**

- How `.kit` files define and assemble Omniverse applications
- Adding and configuring extensions
- How Omniverse supports OpenUSD workflows under the hood
- The relationship: OpenUSD → Omniverse → Isaac Sim

[📝 Notes →](./03-omniverse-intro-course/README.md) | [📸 Screenshots →](./03-omniverse-intro-course/screenshots)

---

## ⏳ TBD — Isaac Sim Beginner Course

**Goal:** Get comfortable with Isaac Sim UI, scenes, and Python scripting basics before hands-on workflows.

[📝 Notes →]| [📸 Screenshots →]

---

## 🔄 Jul 11 — Synthetic Data Generation

**Goal:** Build a data pipeline that generates training data for AI models at scale.

**Status:** In progress · Jul 11, 2026

Synthetic data generation (SDG) is one of the most critical use cases for Physical AI — it lets you train robot models on thousands of varied scenarios without real-world data collection. Using Omniverse Replicator to randomise lighting, object placement, and camera angles.

## [📝 Workflow →](./05-synthetic-data/notes.md) | [📸 Screenshots →]

## ⏳ TBD — Physics Simulation

**Goal:** Load a robot with real physics, sensors, and simulate its behaviour.

Physically accurate simulation is what makes Isaac Sim valuable for robotics — robots trained in simulation behave predictably in the real world because the physics match. Covers articulation, joint drives, rigid body dynamics, and sensor attachment.

[📝 Notes →]| [📸 Screenshots →]

---

## 🔗 Resources

| Resource                                          | Link                                                                                                                                                 |
| ------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| NVIDIA OpenUSD Cert                               | [developer.nvidia.com/usd](https://developer.nvidia.com/usd)                                                                                         |
| OpenUSD Practice Tests                            | [Udemy course](https://www.udemy.com/course-dashboard-redirect/?course_id=7020603)                                                                   |
| Complete Guide to Passing the NVIDIA OpenUSD Cert | [Medium — @chaubenz](https://medium.com/@chaubenz/your-complete-guide-to-passing-the-nvidia-certified-professional-openusd-development-b129777b0ed6) |
| OpenUSD Live Session                              | [YouTube](https://www.youtube.com/live/85gC4Vja5Uo?si=9VvJhl4K_z_jJKyD)                                                                              |
| Isaac Sim Docs                                    | [docs.isaacsim.omniverse.nvidia.com](https://docs.isaacsim.omniverse.nvidia.com)                                                                     |
| Omniverse DLI Courses                             | [learn.nvidia.com](https://learn.nvidia.com)                                                                                                         |
| Isaac Sim on Brev                                 | [Brev cloud setup](https://docs.isaacsim.omniverse.nvidia.com/latest/installation/install_advanced_cloud_setup_brev.html)                            |
| NVIDIA Developer Discord                          | [discord.gg/nvidiaomniverse](http://discord.gg/nvidiaomniverse)                                                                                      |

---

<p align="center">
  <i>Updated daily · Started Jun 26, 2026</i>
</p>
