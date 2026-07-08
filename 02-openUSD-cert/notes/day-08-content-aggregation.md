# Day 8 — Content Aggregation

> **OpenUSD NCP Certification Study Notes**  
> _Instancing, PointInstancer, Asset Management, Scenegraph Best Practices_

---

## Table of Contents

1. [Instancing — Native USD Instancing](#1-instancing--native-usd-instancing)
2. [Point Instancing — UsdGeomPointInstancer](#2-point-instancing--usdgeompointinstancer)
3. [Per-Instance Overrides](#3-per-instance-overrides)
4. [Asset Versioning and Management](#4-asset-versioning-and-management)
5. [Scenegraph Organisation Patterns](#5-scenegraph-organisation-patterns)
6. [Key Takeaways](#6-key-takeaways)

---

## 1. Instancing — Native USD Instancing

**Instancing** allows multiple prims to share the same underlying data (the **prototype**) without duplicating it in memory. All instances reference one prototype, dramatically reducing memory usage for repeated objects.

```python
from pxr import Usd, UsdGeom

stage = Usd.Stage.Open("scene.usda")

# Make a prim instanceable
tree_prim = stage.GetPrimAtPath("/World/Tree_001")
tree_prim.SetInstanceable(True)
# USD now treats this prim as an instance that shares a prototype

# Check instancing status
print(tree_prim.IsInstanceable())   # True
print(tree_prim.IsInstance())       # True — if USD has promoted to instance
print(tree_prim.IsPrototype())      # True — if this prim IS the prototype
```

### Native Instancing Rules

- A prim becomes **instanceable** when `instanceable = True` is set in its metadata
- USD automatically creates a **prototype** (the shared data)
- All instanceable prims that reference the same data become instances of that prototype
- Instances share geometry data — memory usage is for one prototype, not N copies
- **Instance proxies** — reading properties on an instance returns the prototype's value; writing directly to an instance's children requires `SetInstanceable(False)` first

```usda
def Xform "Tree_001" (
    instanceable = true
    prepend references = @./tree_asset.usda@
) { }

def Xform "Tree_002" (
    instanceable = true
    prepend references = @./tree_asset.usda@
) { }
# Both trees share one prototype — memory for one tree
```

---

## 2. Point Instancing — UsdGeomPointInstancer

`UsdGeomPointInstancer` places many instances of one or more prototype prims at positions defined by arrays. It is the highest-performance instancing mechanism in USD — designed for forests, crowds, particle systems, and any scenario with thousands to millions of repeated objects.

```
UsdGeomPointInstancer (/World/Forest)
├── prototypes (hidden):
│   └── /World/Forest/Protos/Tree (Mesh — the shared geometry)
├── protoIndices  = [0, 0, 0, 0, ...]  # which prototype each instance uses
├── positions     = [(x,y,z), ...]      # where each instance is placed
├── orientations  = [(quat), ...]       # rotation of each instance
└── scales        = [(sx,sy,sz), ...]   # scale of each instance
```

### Python API — `UsdGeom.PointInstancer`

```python
from pxr import UsdGeom, Vt, Gf, Usd

stage      = Usd.Stage.CreateInMemory()
instancer  = UsdGeom.PointInstancer.Define(stage, "/World/Forest")

# 1. Define the prototype (the shared geometry)
proto_root = stage.DefinePrim("/World/Forest/Protos")
tree_proto = UsdGeom.Sphere.Define(stage, "/World/Forest/Protos/Tree")
tree_proto.GetRadiusAttr().Set(0.5)

# 2. Point instancer to the prototypes
instancer.GetPrototypesRel().AddTarget("/World/Forest/Protos/Tree")

# 3. Define per-instance arrays
num_instances = 1000
import random

positions = Vt.Vec3fArray([
    Gf.Vec3f(random.uniform(-50, 50), 0, random.uniform(-50, 50))
    for _ in range(num_instances)
])
proto_indices = Vt.IntArray([0] * num_instances)  # all use prototype 0

instancer.GetPositionsAttr().Set(positions)
instancer.GetProtoIndicesAttr().Set(proto_indices)
```

### Per-Instance Customisation

Point instancing supports per-instance variation through the per-instance arrays:

| Array          | Type        | Controls                                             |
| -------------- | ----------- | ---------------------------------------------------- |
| `positions`    | `point3f[]` | World position of each instance                      |
| `orientations` | `quath[]`   | Rotation (quaternion) of each instance               |
| `scales`       | `float3[]`  | Scale of each instance                               |
| `protoIndices` | `int[]`     | Which prototype each instance uses (enables variety) |
| `invisibleIds` | `int64[]`   | Instance IDs to hide                                 |

### Adding New Prototypes to a PointInstancer Dynamically

**What it is:** A `UsdGeomPointInstancer` can reference multiple prototype prims simultaneously. Each instance selects which prototype it uses via the `protoIndices` array. Adding a new prototype means registering a new prim with the instancer's `prototypes` relationship and updating `protoIndices` to reference it.

**Why it is needed:** In production, scenes are built incrementally. A forest scene might start with one tree type and later need oak, pine, and birch variants. A crowd simulation might add a new character type mid-production. Adding prototypes dynamically — without rebuilding the entire instancer — is the correct production pattern.

```
Before adding:                    After adding Oak:
prototypes rel:                   prototypes rel:
[0] /Forest/Protos/Pine           [0] /Forest/Protos/Pine
                                  [1] /Forest/Protos/Oak   ← new

protoIndices = [0,0,0,0,0]        protoIndices = [0,1,0,1,0]
(all Pine)                         (alternating Pine and Oak)
```

**What breaks if you do it wrong:** The `protoIndices` array must always be valid — every index must map to an existing prototype. If you add a prototype but forget to register it in the relationship, or set an index that is out of range, the instancer silently fails to render those instances.

**Method signatures:**

```python
# UsdGeomPointInstancer.GetPrototypesRel() -> UsdRelationship
# The relationship holding all registered prototype paths
instancer.GetPrototypesRel()

# UsdRelationship.AddTarget(path) -> bool
# Register a new prototype path — appends to the list
# The index of the new prototype = len(existing_targets) before adding
instancer.GetPrototypesRel().AddTarget(Sdf.Path("/Forest/Protos/Oak"))

# UsdRelationship.GetTargets() -> list[Sdf.Path]
# Check current registered prototypes and their indices
targets = instancer.GetPrototypesRel().GetTargets()
# targets[0] = first prototype (index 0)
# targets[1] = second prototype (index 1)

# UsdGeomPointInstancer.GetProtoIndicesAttr() -> UsdAttribute
# Must update after adding prototype to use the new index
instancer.GetProtoIndicesAttr().Set(Vt.IntArray([...]))
```

**Full example:**

```python
from pxr import Usd, UsdGeom, Vt, Gf, Sdf

stage     = Usd.Stage.Open("scene.usda")
instancer = UsdGeom.PointInstancer.Get(stage, "/World/Forest")

# --- Check existing prototypes and their indices ---
targets = instancer.GetPrototypesRel().GetTargets()
# targets = [Sdf.Path("/World/Forest/Protos/Pine")]
# Pine is at index 0

# --- Step 1: Define the new prototype prim ---
oak_proto = UsdGeom.Mesh.Define(
    stage, "/World/Forest/Protos/Oak"
)
# ... set up oak geometry ...

# --- Step 2: Register with the instancer ---
# AddTarget appends — Oak will be at index 1
instancer.GetPrototypesRel().AddTarget(
    Sdf.Path("/World/Forest/Protos/Oak")
)

# Verify indices
targets = instancer.GetPrototypesRel().GetTargets()
# targets[0] = Pine   ← index 0
# targets[1] = Oak    ← index 1

# --- Step 3: Update protoIndices to use the new prototype ---
# Existing instances still use 0 (Pine)
# New instances use 1 (Oak)
current_indices = list(instancer.GetProtoIndicesAttr().Get())
# Add 200 new Oak instances
new_indices = current_indices + [1] * 200
instancer.GetProtoIndicesAttr().Set(Vt.IntArray(new_indices))

# --- Step 4: Add positions for the new instances ---
current_positions = list(instancer.GetPositionsAttr().Get())
import random
new_positions = [
    Gf.Vec3f(random.uniform(-100, 100), 0, random.uniform(-100, 100))
    for _ in range(200)
]
instancer.GetPositionsAttr().Set(
    Vt.Vec3fArray(current_positions + new_positions)
)
```

> **Index order is the prototype order in the relationship.** The first target added = index 0, second = index 1, and so on. If you need to remove a prototype, all existing `protoIndices` that reference it and everything after it in the list must be updated — this is why removing prototypes is rare and adding is the standard operation.

---

## 3. Per-Instance Overrides

Point instancing supports per-instance attribute variations. Each instance can have different colours, materials, or custom attributes driven by primvars on the PointInstancer or by connecting shader inputs to per-instance primvars.

### Correct Override Approaches

| Approach                        | How                                                         | Use case                         |
| ------------------------------- | ----------------------------------------------------------- | -------------------------------- |
| Per-instance transforms         | `positions`, `orientations`, `scales` arrays                | Different placement per instance |
| Per-instance material variation | Connect `UsdShade` inputs to primvars                       | Different colour per instance    |
| `UsdReferences` with payloads   | Reference asset at different paths with selective overrides | Targeted property overrides      |

### Variant Set Override on an Instanced Prim

To override properties on a **specific instance** without touching the source asset, apply a variant selection override on the instance's prim path:

```usda
# The asset defines two color variants in chair_asset.usda
# In the scene, ChairA gets the default "brown" variant
# ChairB gets a "blue" variant override — locally, without editing the source

def Xform "ChairA" (
    prepend references = @./chair_asset.usda@
) { }   # uses default variant from asset

def Xform "ChairB" (
    prepend references = @./chair_asset.usda@
    variants = { string color = "blue" }   # ← local override on this instance
) { }   # only this instance uses blue — asset unchanged
```

```python
# Python equivalent — override variant on one instance
chair_b = stage.GetPrimAtPath("/World/ChairB")
chair_b.GetVariantSets().GetVariantSet("color").SetVariantSelection("blue")
# ChairA is unaffected — still uses the default from the asset
```

This is the correct pattern for per-instance customisation when the asset already defines variant sets for the property you want to change.

### Wrong Approaches

| Wrong approach                                                    | Why it's wrong                                                                         |
| ----------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Modify the prototype prim directly                                | Changes ALL instances — not a per-instance override                                    |
| Duplicate the entire prototype for each instance                  | Destroys instancing efficiency — defeats the purpose                                   |
| Use `variantSets` on the **prototype** for per-instance variation | Variants on the prototype affect ALL instances globally                                |
| Use a payload override to modify instance properties              | Payloads are for deferred loading — not for property overrides                         |
| Create a new prim that "inherits" from the instanced prim         | USD prims don't derive from each other in the OOP sense — use references and overrides |

> **Point instancing DOES support per-instance material variations.** This is a common exam trap — the false statement is "point instancing disables per-instance material variations." It does not. Per-instance materials work via primvar-driven shader inputs.

### Instance Proxy — Reading and Overriding Without Breaking Instancing

**What it is:** When a prim has `instanceable = True`, USD creates a shared prototype and makes the prim an instance of it. You cannot directly author opinions on the children of an instanceable prim — doing so would break the prototype sharing because USD would need to diverge the data. An **instance proxy** is the read-only handle USD gives you to access those children for inspection. For authoring overrides, you work on the instance root itself — not the children.

**Why it is needed:** Instanced assets are common in large scenes — thousands of trees, crowds, props. You often need to customise individual instances (this particular tree is dead, this character is injured) without breaking the instancing for all the others or duplicating the entire asset. Understanding the correct override pattern prevents a common production bug: writing to an instance child and silently breaking instancing.

```
Instanceable prim:
/World/Tree_042  (instanceable = True)
← prototype is shared with all other Tree instances

What you can do:
Read:    stage.GetPrimAtPath("/World/Tree_042/Trunk")
→ returns instance proxy — readable, not writable
Override: stage.OverridePrim("/World/Tree_042")
→ override on the INSTANCE ROOT — this is valid
→ author sparse opinions here without breaking instancing

What breaks instancing:
stage.GetPrimAtPath("/World/Tree_042").SetInstanceable(False)
→ now this tree is NOT an instance — it gets its own copy
→ memory efficiency lost for this prim
```

**The three patterns — read, override, and break:**

```python
from pxr import Usd, UsdGeom, UsdShade, Sdf

stage = Usd.Stage.Open("scene.usda")

# --- Pattern 1: READ via instance proxy (always safe) ---
trunk_proxy = stage.GetPrimAtPath("/World/Tree_042/Trunk")
# trunk_proxy IS an instance proxy — you can read from it
print(trunk_proxy.IsInstanceProxy())           # True
print(trunk_proxy.GetAttribute("radius").Get()) # reads prototype value

# You CANNOT author on an instance proxy child
# trunk_proxy.GetAttribute("radius").Set(2.0)  ← WRONG — no effect or error

# --- Pattern 2: OVERRIDE on the instance root (correct) ---
# Author a sparse override on the instance root prim
# This is the correct way to customise one instance
stage.SetEditTarget(stage.GetRootLayer())
over = stage.OverridePrim("/World/Tree_042")

# Override a property at the instance root level
UsdGeom.Imageable(over).GetVisibilityAttr().Set(
    UsdGeom.Tokens.invisible
)
# Only Tree_042 becomes invisible — all other trees unchanged
# Instancing is preserved — prototype is still shared

# Override material binding on the instance root
binding = UsdShade.MaterialBindingAPI.Apply(over)
binding.Bind(dead_tree_mat)
# Only Tree_042 uses dead_tree_mat — prototype unchanged

# --- Pattern 3: BREAK instancing (use only when necessary) ---
# If you need to author on a specific child prim,
# you must turn off instanceable for that prim
tree_prim = stage.GetPrimAtPath("/World/Tree_042")
tree_prim.SetInstanceable(False)
# Now Tree_042 is NOT an instance — it gets its own copy of the prototype
# You can now author on /World/Tree_042/Trunk directly
# BUT: this tree no longer shares the prototype — memory cost increases
trunk = stage.GetPrimAtPath("/World/Tree_042/Trunk")
trunk.GetAttribute("radius").Set(2.0)   # now valid
```

**Method signatures:**

```python
# UsdPrim.IsInstanceProxy() -> bool
# True if this prim is a child accessed through an instance
prim.IsInstanceProxy()

# UsdPrim.IsInstance() -> bool
# True if this prim IS an instance (the root, not a child)
prim.IsInstance()

# UsdPrim.IsPrototype() -> bool
# True if this prim IS the prototype (the shared template)
prim.IsPrototype()

# UsdPrim.SetInstanceable(bool) -> None
# True = share prototype with matching instances
# False = this prim gets its own copy — breaks sharing for this prim only
prim.SetInstanceable(False)

# Usd.Stage.OverridePrim(path) -> UsdPrim
# Creates an over spec at path for sparse authoring
# Safe to use on instance roots — does not break instancing
stage.OverridePrim("/World/Tree_042")
```

**Key rules:**

- Instance proxy children are **read-only** — reading is always safe, authoring is not
- Override on the **instance root** (the instanceable prim itself) — not on its children
- Overriding on the instance root via `stage.OverridePrim()` is safe and does not break instancing
- `SetInstanceable(False)` breaks prototype sharing for that prim — use only when you genuinely need to diverge the geometry
- Visibility, material binding, transform overrides on the instance root all work correctly and preserve instancing

> **Exam phrasing:** "Edit properties of instanceProxy meshes without breaking instancing status" → the answer is override on the instance root using `stage.OverridePrim()`, not on the proxy child. The proxy child is read-only.

---

## 3b. Payload Pruning — Optimising Scene Aggregation

When a scene contains many payloads, loading all of them at once creates unnecessary overhead. **Payload pruning** excludes unused or irrelevant payloads during aggregation, reducing load time and memory.

```python
from pxr import Usd

# Open with LoadNone — no payloads loaded
stage = Usd.Stage.Open("scene.usda", Usd.Stage.LoadNone)

# Prune: only load payloads within a specific part of the scene
# Everything outside /World/ActiveSets is never loaded
stage.LoadAndUnload(
    loadSet   = {"/World/ActiveSets"},   # load these subtrees
    unloadSet = {}                        # unload nothing extra
)

# Check which payloads are loaded
for prim in stage.Traverse():
    if prim.HasPayload():
        print(f"{prim.GetPath()}  loaded={prim.IsLoaded()}")
```

> **Payload pruning vs increasing granularity:** More small payloads = finer edit control BUT more overhead during aggregation. Fewer, well-pruned payloads = faster aggregation. The correct optimisation strategy is pruning, not adding more granular payloads.

| Strategy                           | Effect on aggregation                                      |
| ---------------------------------- | ---------------------------------------------------------- |
| Payload pruning                    | ✅ Reduces load time — only loads what's needed            |
| More granular payloads             | ❌ Increases overhead — more file loads even when unneeded |
| Embedding all assets in root layer | ❌ Eliminates modularity, increases initial load           |
| Disabling instancing               | ❌ Duplicates data — increases memory and aggregation cost |

---

## 3c. Interface Schemas — Loose Coupling for Composable Components

**Interface schemas** define the boundary of what a component exposes to the outside world — its public "API". They allow components to be composed dynamically without tight coupling between the consumer and the internal structure of each asset.

```
Without interface schemas (tight coupling):
  Scene needs to know: "chair asset has /Chair/Seat with primvars:displayColor"
  → If asset restructures internally, the scene breaks

With interface schemas (loose coupling):
  Interface defines: "this asset exposes 'chair:color' as a public input"
  → Scene only talks to the interface — internal structure can change freely
  → Components can be swapped as long as they implement the same interface
```

```python
# Asset exposes a public interface via UsdShadeInput on the root prim
chair_root = stage.GetPrimAtPath("/Chair")

# Interface attribute — public contract with the outside world
color_input = chair_root.CreateAttribute(
    "interface:color", Sdf.ValueTypeNames.Color3f
)
color_input.Set(Gf.Vec3f(0.6, 0.4, 0.2))

# Internal shader is wired to read from interface:color
# Consumer doesn't need to know about the internal shader network
```

> **When the exam asks about loose coupling and composability:** The correct answer involves interface schemas + USD references/payloads. Wrong answers: embedding all logic in one layer, hardcoding asset paths, duplicating data.

---

## 3d. Collaborative Aggregation — Composition Arcs vs File Locking

USD's composition system is the **correct** mechanism for collaborative asset aggregation. Multiple artists contribute to separate files which are composed together non-destructively.

```
Artist A → anim.usda          ┐
Artist B → layout.usda        ├── composition arcs → shot_042.usda
Artist C → fx.usda            ┘

Each artist works in their own file.
No file locking needed.
No overwriting.
Composition resolves conflicts using LIVERPS.
```

| Mechanism                               | Correct for collaboration? | Why                                                                      |
| --------------------------------------- | -------------------------- | ------------------------------------------------------------------------ |
| Composition arcs (references, payloads) | ✅ Yes                     | Each contributor has their own file, composed non-destructively          |
| File locking                            | ❌ No                      | Not scalable, doesn't leverage USD composition, blocks other artists     |
| Single flat USD file                    | ❌ No                      | All changes serialised into one file — concurrent edits impossible       |
| Variant sets for concurrent edits       | ❌ No                      | Variant sets = asset variations, not concurrent collaboration mechanisms |

---

## 4. Asset Versioning and Management

### References — Single Source of Truth

Using references instead of duplicating data means there is one authoritative copy of each asset. Update the asset file and all scenes that reference it automatically see the update.

```python
# Instead of duplicating chair geometry into every scene:
# scene_A.usda, scene_B.usda, scene_C.usda all reference:
chair = stage.DefinePrim("/World/ChairA")
chair.GetReferences().AddReference("./assets/chair_v003.usda")
# Update chair_v003.usda → all three scenes update automatically
```

### Variant Sets for Versioning

Variant sets can represent different versions or configurations of the same asset within one file:

```usda
def Xform "Chair" (
    prepend variantSets = "version"
    variants = { string version = "v003" }
) {
    variantSet "version" = {
        "v001" { prepend references = @./chair_v001.usda@ }
        "v002" { prepend references = @./chair_v002.usda@ }
        "v003" { prepend references = @./chair_v003.usda@ }
    }
}
```

### Payloads for Performance

Reference large assets as payloads so scenes open quickly even when they contain many heavy assets:

```python
# Heavy asset referenced as payload — not loaded until explicitly requested
heavy_prim = stage.DefinePrim("/World/HighResCity")
heavy_prim.GetPayloads().AddPayload("./city_highres.usda")

# Open stage without loading any payloads — instant open
stage = Usd.Stage.Open("scene.usda", Usd.Stage.LoadNone)

# Load only the assets you need
stage.Load("/World/HighResCity")
```

### Version Control Best Practices

| ✅ Do                                               | ❌ Don't                               |
| --------------------------------------------------- | -------------------------------------- |
| Reference assets — one source of truth              | Embed all data in each stage           |
| Use variant sets for version switching              | Rely only on file naming conventions   |
| Version delivery files (`v001`, `v002`)             | Overwrite original USD files directly  |
| Keep source composition files under version control | Edit flattened delivery files directly |

---

## 5. Scenegraph Organisation Patterns

### Standard Hierarchy Convention

```
/World                              ← Xform — root of the scene
├── /World/Geometry  (Scope)        ← all renderable geometry
│   ├── /World/Geometry/Chair (Mesh)
│   └── /World/Geometry/Table (Mesh)
├── /World/Lights    (Scope)        ← all lights
│   └── /World/Lights/KeyLight
├── /World/Looks     (Scope)        ← all materials
│   └── /World/Looks/WoodMat
└── /World/Cameras   (Scope)
    └── /World/Cameras/MainCam
```

### `UsdGeomScope` vs `UsdGeomXform`

| Schema         | Transform? | Use case                                            |
| -------------- | ---------- | --------------------------------------------------- |
| `UsdGeomXform` | ✅ Yes     | Grouping prims that need to move together           |
| `UsdGeomScope` | ❌ No      | Namespace organisation only — no transform overhead |

Use `Scope` for containers like `/World/Looks/`, `/World/Lights/` where you need grouping but no transform. Use `Xform` where the group itself needs to be positioned or animated.

---

## 6. Key Takeaways

| Concept                                  | What to Remember                                                                                            |
| ---------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| **Native instancing**                    | `SetInstanceable(True)` — shares prototype data, reduces memory                                             |
| **PointInstancer**                       | Highest performance — for forests, crowds, particles. Per-instance transforms without duplicating geometry. |
| **`positions`, `protoIndices`**          | Core per-instance arrays on PointInstancer                                                                  |
| **Per-instance materials**               | Supported via primvar-driven shader inputs — not disabled                                                   |
| **Modify prototype = global change**     | Affects ALL instances — not a per-instance override                                                         |
| **Variant set override on instance**     | Override variant selection on the instance's prim path — correct per-instance override mechanism            |
| **Payload override ≠ property override** | Payloads = deferred loading. NOT for overriding instance properties.                                        |
| **Payload pruning**                      | Exclude unused payloads during aggregation — reduces load time and memory                                   |
| **More granular payloads**               | ❌ Increases overhead — pruning is the correct optimisation, not more payloads                              |
| **Interface schemas**                    | Define public API for components — enables loose coupling and swappable assets                              |
| **Collaboration = composition arcs**     | Each artist contributes their own file. File locking = wrong. Flat single file = wrong.                     |
| **Variant sets ≠ collaboration**         | Variant sets = asset variations. NOT for managing concurrent edits by multiple artists.                     |
| **References = single source of truth**  | Update asset file → all referencing scenes update                                                           |
| **Payloads for heavy assets**            | `Stage.LoadNone` + explicit `Load()` — optimal for large scenes                                             |
| **UsdGeomScope**                         | Namespace grouping, no transform. For `/Looks/`, `/Lights/`                                                 |
| **UsdGeomXform**                         | Transform container. For groups that need to move.                                                          |
| **Don't overwrite originals**            | Version deliveries (`v001`, `v002`), never overwrite source                                                 |

---

_Previous: [Day 7 — Pipeline Development and Data Exchange](day-07-pipeline-and-data-exchange.md)_  
_Next: [Day 9 — Debugging and Troubleshooting](day-09-debugging-and-troubleshooting.md)_
