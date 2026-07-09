# Day 3 — Composition Arcs Part 2

> **OpenUSD NCP Certification Study Notes**  
> _Variants, Inherits, Specializes, and Advanced Composition Patterns_

---

## Table of Contents

1. [Variant Sets](#1-variant-sets)
2. [Variant Fallback Selections](#2-variant-fallback-selections)
3. [Inherits](#3-inherits)
4. [Specializes](#4-specializes)
5. [Inherits vs Specializes — The Critical Distinction](#5-inherits-vs-specializes-the-critical-distinction)
6. [Composition Arc Best Practices](#6-composition-arc-best-practices)
7. [Key Takeaways](#7-key-takeaways)

---

## 1. Variant Sets

A **variant set** is a named collection of alternative configurations for a prim. Each configuration is called a **variant**. Exactly one variant is active at any time — the selected variant. Switching the selection changes which data the prim presents.

```
def Xform "RaceCar"
├── variantSet "color"        variantSet "lod"
│   ├── "red"    → red paint      ├── "hero"   → 2M polygon mesh
│   ├── "blue"   → blue paint     ├── "medium" → 200K polygon mesh
│   └── "silver" → silver paint   └── "proxy"  → 500 polygon box
```

Variant sets are the **V in LIVERPS** — stronger than References and Payloads, weaker than Local opinions and Inherits.

### Why Variants Exist

Without variants, you would need a separate file for every combination: `car_red_hero.usda`, `car_red_medium.usda`, `car_blue_hero.usda` — combinatorial explosion. With variants, one file contains all combinations, and the selection is made at composition time without modifying the asset.

### USDA Syntax

The structure of a variant set in a USD file has two distinct parts:

1. **The metadata block `()`** — declares that the variant set exists and which variant is currently selected
2. **The data block `{}`** — defines what content each variant holds

```usda
#usda 1.0
(
    defaultPrim = "RaceCar"
)

def Xform "RaceCar" (
    # ── METADATA BLOCK ───────────────────────────────────────────────
    prepend variantSets = "color"          # declares the variant set exists
    variants = {
        string color = "red"               # currently selected variant
    }
) {
    # ── DATA BLOCK ────────────────────────────────────────────────────
    variantSet "color" = {
        "red" {
            # these opinions are ONLY active when color = "red"
            color3f[] primvars:displayColor = [(1, 0, 0)]
        }
        "blue" {
            color3f[] primvars:displayColor = [(0, 0, 1)]
        }
        "silver" {
            color3f[] primvars:displayColor = [(0.8, 0.8, 0.85)]
        }
    }
}
```

### Overriding Variant Selection from Outside

A referencing scene can choose a different variant **without touching the asset file**. This is possible because the V in LIVERPS means local opinions (including variant selections) in a stronger layer override the default selection in the asset.

```usda
# scene.usda — the referencing scene
def Xform "World" {
    def Xform "MyCar" (
        prepend references = @./car_asset.usda@
        variants = {
            string color = "blue"   # overrides the asset's default "red"
        }
    ) { }
}
```

### Python API — `Usd.VariantSets`

```python
from pxr import Usd, UsdGeom

stage = Usd.Stage.CreateNew("car_asset.usda")
car   = UsdGeom.Xform.Define(stage, "/RaceCar")
prim  = car.GetPrim()

# Create a variant set on the prim
vset = prim.GetVariantSets().AddVariantSet("color")

# Add variants and author content into each one
vset.AddVariant("red")
vset.SetVariantSelection("red")
with vset.GetVariantEditContext():
    # Anything authored here is scoped to the "red" variant
    prim.CreateAttribute(
        "primvars:displayColor",
        Sdf.ValueTypeNames.Color3fArray
    ).Set([(1, 0, 0)])

vset.AddVariant("blue")
vset.SetVariantSelection("blue")
with vset.GetVariantEditContext():
    prim.CreateAttribute(
        "primvars:displayColor",
        Sdf.ValueTypeNames.Color3fArray
    ).Set([(0, 0, 1)])

# Set the default selection in the asset
vset.SetVariantSelection("red")

# --- In the referencing scene, override the selection ---
scene = Usd.Stage.CreateNew("scene.usda")
my_car = scene.DefinePrim("/World/MyCar")
my_car.GetReferences().AddReference("./car_asset.usda")

# Override variant selection
my_car.GetVariantSets().GetVariantSet("color").SetVariantSelection("blue")
```

---

## 2. Variant Fallback Selections

**Variant fallback selections** define what USD should use when the requested variant does not exist in a given asset. They prevent hard failures when a pipeline environment requests a variant that wasn't authored.

### Three Things That Sound Similar But Are Different

Before the approaches, it is critical to understand three concepts that are easy to confuse:

```
1. Default variant selection on the prim
   variants = { string lod = "high" }    ← in the prim definition
   "if nobody overrides this, use high"
   → VALID and standard practice

2. variantFallbacks in layer metadata header
   #usda 1.0
   (
       variantFallbacks = { string[] "lod" = ["high", "medium"] }
   )
   → VALID — stage-wide policy in the layer header

3. variantFallbacks in PRIM metadata
   def Xform "Chair" (
       variantFallbacks = { ... }    ← inside a prim block
   ) { }
   → WRONG — has no effect, not standard practice
```

> The exam specifically tests the difference between (1) and (3). Setting a default selection **on the prim** is correct and is what "defining fallback variants at the prim definition layer" means. Putting `variantFallbacks` **in prim metadata** is wrong and has no effect.

---

### Approach 1 — Default variant selection on the prim (asset level)

Set a default selection directly in the variant set definition. This is the baseline — if no stronger layer overrides it, USD uses this selection.

```usda
def Xform "Chair" (
    prepend variantSets = "lod"
    variants = { string lod = "high" }   ← default selection on the prim
) {
    variantSet "lod" = {
        "high"   { ... }
        "medium" { ... }
        "low"    { ... }
    }
}
```

- Lives in the asset file itself
- Applies when no other layer overrides the selection
- This is what "defining fallback variants at the prim definition layer" means in exam language

---

### Approach 2 — `variantFallbacks` in root layer metadata

Stage-wide fallback policy. Goes in the **root layer metadata header** — the same block as `upAxis`, `metersPerUnit`, and `subLayers`. NOT in any prim definition.

```usda
#usda 1.0
(
    upAxis = "Y"
    variantFallbacks = {        ← layer metadata header — correct placement
        string[] "lod"   = ["high", "medium", "low"]
        string[] "color" = ["default"]
    }
    subLayers = [
        @./anim.usda@,
        @./layout.usda@
    ]
)
```

- Baked into the file on disk
- Applies whenever this file is opened as a root layer
- Persists across sessions automatically
- Equivalent to Approach 3 but authored in USDA instead of Python
  > Approach 2 and Approach 3 are **equivalent** — same policy, different interfaces. Approach 2 is in the file. Approach 3 is in Python code. Both set the same stage-wide fallback.

---

### Approach 3 — `Usd.Stage.SetGlobalVariantFallbacks()` (Python)

Must be called **before** `Usd.Stage.Open()`. Has no effect on already-open stages.

```python
from pxr import Usd

# Call BEFORE opening — has no effect on already-open stages
Usd.Stage.SetGlobalVariantFallbacks({
    "lod":   ["high", "medium", "low"],
    "color": ["default"],
})

stage = Usd.Stage.Open("scene.usda")   # fallbacks apply here
```

- Must be called before opening the stage
- Does not persist — must be set again each new process
- Use for environment-specific or tool-specific overrides at startup

---

### Approach 4 — Session layer (runtime changes)

The session layer is always the strongest layer and is never saved to disk. Use it for **runtime changes** — after the stage is already open — without touching any shared file.

```python
stage   = Usd.Stage.Open("shot.usda")
session = stage.GetSessionLayer()
stage.SetEditTarget(session)

# Override variant selection at runtime
prim = stage.GetPrimAtPath("/World/Car")
prim.GetVariantSets().GetVariantSet("lod").SetVariantSelection("proxy")
# Takes effect immediately — no file change, no reopen needed

# Clear when done
stage.GetSessionLayer().Clear()
```

- Strongest layer — overrides everything else
- In-memory only — `stage.Save()` never writes it to disk
- Discarded when process ends
- The correct mechanism for runtime variant changes — NOT "avoid runtime changes"
  > **Exam trap:** "Use fallback selections only during stage composition and avoid runtime changes" is **WRONG**. The session layer exists specifically to support runtime variant changes.

---

### Approach 5 — `variantFallbacks` per referencing layer

For consistency across departments, author `variantFallbacks` in each layer that references the asset:

```usda
# department_anim.usda
#usda 1.0
(
    variantFallbacks = {
        string[] "lod" = ["high", "medium", "low"]
    }
)
```

- Ensures consistent fallback behaviour regardless of which tool opens the stage
- Prevents failures when a tool's environment differs from the asset's defaults

---

### Comparison Table

| Approach                         | Where authored                       | Persists?        | When it applies                  | Use case                         |
| -------------------------------- | ------------------------------------ | ---------------- | -------------------------------- | -------------------------------- |
| Default selection on prim        | Inside prim definition in asset file | Yes — on disk    | When no stronger override exists | Asset-level baseline             |
| `variantFallbacks` in root layer | Root layer metadata header `()`      | Yes — on disk    | Stage composition                | Shared pipeline defaults         |
| `SetGlobalVariantFallbacks()`    | Python code before `Stage.Open()`    | No — per process | Stage composition                | Tool/environment startup         |
| Session layer                    | In-memory, never saved               | No — per session | Runtime, after stage open        | Interactive overrides, debugging |
| Per referencing layer            | Each sublayer metadata header        | Yes — on disk    | Per-layer composition            | Department consistency           |

---

### Wrong Approaches

| Wrong                                       | Why                                                                          |
| ------------------------------------------- | ---------------------------------------------------------------------------- |
| `variantFallbacks` in **prim metadata**     | Prim metadata has no effect for fallbacks — must be in layer metadata header |
| Rely only on default prim selection         | Does not cover cases where the requested variant doesn't exist at all        |
| Rely solely on session layer                | Session layer overrides selections but does not define fallback logic        |
| Duplicate prims with different variant sets | Increases complexity — `variantFallbacks` is the correct mechanism           |
| Assume USD auto-selects alphabetically      | USD does NOT auto-select variants — fallbacks must be explicitly defined     |
| Avoid runtime changes                       | WRONG — session layer exists specifically for runtime variant changes        |

---

## 3. Inherits

**Inherits** propagates opinions from a `class` prim to multiple `def` prims across the scene. It is the **I in LIVERPS** — the second strongest arc.

```
class "_PineTree"           ← template, never rendered
  height = 5.0
  displayColor = green

def "PineTree_A" (inherits = </_PineTree>)  → height=5.0, green
def "PineTree_B" (inherits = </_PineTree>)  → height=5.0, green
def "PineTree_C" (inherits = </_PineTree>)  → height=5.0, green
  height = 8.0  ← local override               (height=8.0 WINS, still green)
```

**The power of inherits:** change `_PineTree.height` to `6.0` and every tree that inherits from it updates automatically — except those with local overrides.

### Key Properties of Inherits

- Inherits uses **prim paths**, not file paths: `</_PineTree>` not `@./file.usda@`
- The class prim must exist somewhere in the **composed stage's namespace**
- Class prims use the `class` specifier — they are skipped by default traversals and renderers
- Local opinions on the inheriting prim beat inherited opinions (L before I in LIVERPS)
- Changes to the class prim propagate to all inheriting prims **live**

### USDA Syntax

```usda
# Define the class (template)
class Xform "_PineTree" {
    double height = 5.0
    color3f[] primvars:displayColor = [(0.1, 0.5, 0.1)]
}

# Inherit from the class
def Xform "Forest" {
    def Xform "PineTree_A" (
        prepend inherits = </_PineTree>
        # Uses angle brackets <> for prim paths — not @ signs for files
    ) {
        # No local overrides — gets everything from _PineTree
    }

    def Xform "PineTree_C" (
        prepend inherits = </_PineTree>
    ) {
        double height = 8.0
        # Local opinion overrides the inherited height=5.0
        # displayColor still inherited from _PineTree
    }
}
```

### Python API — `Usd.Inherits`

```python
from pxr import Usd, UsdGeom, Sdf

stage = Usd.Stage.CreateNew("forest.usda")

# Create the class prim using CreateClassPrim()
# Signature: stage.CreateClassPrim(path: str) -> Usd.Prim
class_prim = stage.CreateClassPrim("/_PineTree")
class_prim.CreateAttribute("height", Sdf.ValueTypeNames.Double).Set(5.0)

# Create a prim that inherits from the class
tree_a = UsdGeom.Xform.Define(stage, "/Forest/PineTree_A")

# Access the inherits manager and add the arc
# Signature: prim.GetInherits() -> Usd.Inherits
inherits = tree_a.GetPrim().GetInherits()
inherits.AddInherit(Sdf.Path("/_PineTree"))

# Verify the inherited value
tree_a_prim = stage.GetPrimAtPath("/Forest/PineTree_A")
print(tree_a_prim.GetAttribute("height").Get())  # 5.0 — inherited

# Add a local override (beats the inherit)
tree_a_prim.GetAttribute("height").Set(8.0)
print(tree_a_prim.GetAttribute("height").Get())  # 8.0 — local wins
```

---

## 4. Specializes

**Specializes** is the weakest composition arc in LIVERPS — the S at the end. Like Inherits, it propagates opinions from one prim to another. Unlike Inherits, the propagated opinions are **fallback defaults** that any other arc can beat.

> **The critical distinction:** Inherits opinions are strong (second in LIVERPS). Specializes opinions are weak (last in LIVERPS). A specialized value only applies when no other arc has an opinion on that property.

### The Classic Use Case — Material Libraries

```
class "_BasePlastic"
    roughness = 0.2    (smooth)
    metallic  = 0.0

def "RoughPlastic" (specializes = </_BasePlastic>)
    roughness = 0.8    ← LOCAL opinion beats specializes → 0.8 applies
    metallic is not set → falls back to specializes → 0.0 applies
```

### USDA Syntax

```usda
class "_BasePlastic" {
    float inputs:roughness = 0.2   # smooth plastic default
    float inputs:metallic  = 0.0
    color3f inputs:diffuseColor = (0.8, 0.8, 0.8)
}

def Material "RoughPlastic" (
    prepend specializes = </_BasePlastic>
) {
    float inputs:roughness = 0.8
    # Local roughness (0.8) overrides the specialized value (0.2)
    # metallic and diffuseColor fall back to _BasePlastic values
}
```

### Python API — `Usd.Specializes`

```python
from pxr import Usd, Sdf

stage = Usd.Stage.CreateNew("materials.usda")

# Create the base class
base = stage.CreateClassPrim("/_BasePlastic")
base.CreateAttribute("inputs:roughness", Sdf.ValueTypeNames.Float).Set(0.2)
base.CreateAttribute("inputs:metallic",  Sdf.ValueTypeNames.Float).Set(0.0)

# Create a specialization
rough = stage.DefinePrim("/RoughPlastic", "Material")

# Signature: prim.GetSpecializes() -> Usd.Specializes
specializes = rough.GetSpecializes()
specializes.AddSpecialize(Sdf.Path("/_BasePlastic"))

# Override roughness locally (local beats specializes)
rough.GetAttribute("inputs:roughness").Set(0.8)

stage.Save()
```

---

## 5. Inherits vs Specializes — The Critical Distinction

This distinction is one of the most commonly tested topics in the certification exam.

| Property         | Inherits                                          | Specializes                             |
| ---------------- | ------------------------------------------------- | --------------------------------------- |
| LIVERPS position | **I** — 2nd strongest                             | **S** — weakest (last)                  |
| Opinion strength | Strong — beats variant, reference, payload        | Weak — beaten by everything             |
| Purpose          | Broadcast properties across many prims            | Provide fallback defaults               |
| Typical use      | Shared properties (visibility, scale conventions) | Material base classes, default settings |
| Keyword          | `prepend inherits = <path>`                       | `prepend specializes = <path>`          |

### Mental Model

```
Inherits:     "I AM a PineTree — I should have all its properties unless I say otherwise"
              The class's opinions flow DOWN as STRONG opinions

Specializes:  "I am a SPECIALIZATION of BasePlastic — use its values as my fallback"
              The class's opinions flow DOWN as WEAK fallbacks
```

> **Exam trap:** "Specializes arcs override the entire composition of a prim, replacing all opinions from weaker arcs." — This is **WRONG**. Specializes is the **weakest** arc. It provides fallback defaults. Everything else beats it.

---

## 6. Composition Arc Best Practices

### Do

| Practice                                                               | Arc       | Why                                                                           |
| ---------------------------------------------------------------------- | --------- | ----------------------------------------------------------------------------- |
| Use **references** to bring in external assets                         | Reference | Grafts prim hierarchy without creating new composition arcs in the root layer |
| Use **payloads** for heavy assets that don't need to load immediately  | Payload   | Creates arc but defers loading — balances modularity and performance          |
| Use **variant sets** to switch between different asset configurations  | Variant   | Enables flexible scene variations within controlled composition               |
| Use **sublayers** to separate workstream concerns (anim, fx, lighting) | Sublayer  | Same namespace, different concerns — proper team collaboration pattern        |

### Don't

| Anti-pattern                                       | Why it's wrong                                                                            |
| -------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Overuse sublayers for many small unrelated changes | Makes composition unpredictable, hard to debug                                            |
| Directly edit payloaded assets in the root layer   | Breaks encapsulation, can corrupt composition arcs                                        |
| Nest references inside payloads                    | Technically possible but creates complex, unpredictable composition — avoid in production |
| Assume specializes overrides weaker arcs           | Specializes IS the weakest arc — it provides fallbacks only                               |

---

## 7. Key Takeaways

| Concept                       | What to Remember                                                                          |
| ----------------------------- | ----------------------------------------------------------------------------------------- |
| **Variant set**               | Named collection of alternatives. One active at a time. V in LIVERPS.                     |
| **Variant selection**         | Which variant is active. Can be overridden by a stronger layer.                           |
| **`GetVariantEditContext()`** | Context manager for authoring content into a specific variant                             |
| **Variant fallbacks**         | `SetGlobalVariantFallbacks()` or session layer — for when requested variant doesn't exist |
| **Inherits**                  | Propagates class opinions as STRONG opinions. I = 2nd in LIVERPS.                         |
| **`class` specifier**         | Template prim. Skipped by traversals and renderers. Used with inherits.                   |
| **Specializes**               | Propagates class opinions as WEAK fallbacks. S = last in LIVERPS.                         |
| **Inherits vs Specializes**   | Inherits = strong broadcast. Specializes = weak fallback.                                 |
| **Arc path syntax**           | Inherits/Specializes use `<prim path>`. References/Payloads use `@file path@`.            |
| **LIVERPS complete**          | Local → Inherit → Variant → rEference → Payload → Specializes                             |

---

_Previous: [Day 2 — Composition Arcs Part 1](day-02-composition-arcs-part-1.md)_  
_Next: [Day 4 — Data Modeling](day-04-data-modeling.md)_