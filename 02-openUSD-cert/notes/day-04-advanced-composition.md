# Day 4 — Advanced Composition Concepts

> **OpenUSD NCP Certification Study Notes**  
> _Edit Targets, Session Layer, Sparse Overrides, Flattening, and Asset Structure_

---

## Table of Contents

1. [Edit Target](#1-edit-target)
2. [The Session Layer](#2-the-session-layer)
3. [Sparse Overrides](#3-sparse-overrides)
4. [Flattening — Baking Composition](#4-flattening--baking-composition)
5. [Encapsulation — Asset Structure Principles](#5-encapsulation--asset-structure-principles)
6. [Change Processing and SdfChangeBlock](#6-change-processing-and-sdfchangeblock)
7. [Working Directly with Layers](#7-working-directly-with-layers)
8. [Full Composition Mental Model](#7-full-composition-mental-model)
9. [Key Takeaways](#8-key-takeaways)

---

## 1. Edit Target

The **edit target** controls which layer receives all authoring operations. When you call `Set()`, `DefinePrim()`, or any other authoring API, the resulting spec is written to exactly one layer — the current edit target.

By default, the edit target is the **root layer** of the stage. It can be switched to any layer in the layer stack at any time.

```
Stage (shot.usda)
├── root_layer.usda   ← edit target (default)
├── anim.usda
└── lighting.usda

prim.GetAttribute("translate").Set((5,0,0))
→ writes ONLY to root_layer.usda
→ anim.usda and lighting.usda are untouched
```

> **Most common USD pipeline bug:** authoring to the wrong edit target. The operation succeeds silently — no error is raised — but the opinion goes to the wrong layer. Always check `stage.GetEditTarget()` before authoring in multi-layer pipelines.

### Python API

```python
from pxr import Usd, Sdf

stage = Usd.Stage.Open("shot.usda")

# Check the current edit target
current = stage.GetEditTarget()
print(current.GetLayer().identifier)  # current layer receiving edits

# Switch edit target to a specific layer
anim_layer = Sdf.Layer.FindOrOpen("./anim.usda")
stage.SetEditTarget(anim_layer)
# Now ALL edits go to anim.usda

# Safe pattern — save and restore
previous = stage.GetEditTarget()
try:
    stage.SetEditTarget(anim_layer)
    prim.GetAttribute("xformOp:translate").Set((5, 0, 0))
finally:
    stage.SetEditTarget(previous)  # always restore
```

---

## 2. The Session Layer

The **session layer** is a special in-memory layer that is always the **strongest** layer in the stage. It is never saved to disk by `stage.Save()`.

```
Strength order when session layer is involved:
[0] session layer     ← STRONGEST (in-memory, never saved)
[1] root_layer.usda   ← default edit target
[2] anim.usda
[3] model.usda        ← weakest
```

### What the Session Layer Is For

- Storing ephemeral interactive overrides (e.g. usdview edits)
- Per-session customisation without affecting shared files
- Temporary overrides that should not persist after the session ends

### What It Is NOT

The session layer is **not** the same as a sublayer you create and name `"session.usda"`. It is USD's built-in in-memory layer, accessible via `stage.GetSessionLayer()`.

```python
# Access the session layer
session = stage.GetSessionLayer()

# Author into the session layer
stage.SetEditTarget(session)
prim.GetAttribute("visibility").Set("invisible")
# This override exists only in this session — not saved to disk

# Clear all session layer opinions
stage.GetSessionLayer().Clear()
# Removes ALL interactive edits made this session
```

> **Important:** `stage.Save()` never touches the session layer. If you need an override to persist, author it to a real file-backed layer instead.

---

## 3. Sparse Overrides

A **sparse override** uses an `over` spec to change only specific properties on a prim that is owned by another layer. The overriding layer only contains the properties it needs to change — all other properties flow through from the original layer unmodified.

```
model.usda (weaker — owns the prim):          anim.usda (stronger — sparse override):
def Xform "Chair" {                           over "Chair" {
    double3 xformOp:translate = (0,0,0)           double3 xformOp:translate = (5,0,0)
    double3 xformOp:scale = (1,1,1)               # scale NOT mentioned — flows from model
    token visibility = "inherited"                # visibility NOT mentioned — flows through
}                                             }

Composed result:
    translate = (5,0,0)  ← from anim (stronger)
    scale     = (1,1,1)  ← from model (anim has no opinion)
    visibility = "inherited" ← from model (anim has no opinion)
```

This is USD's **non-destructive override** system. The stronger layer is minimal — it only contains what it changes.

```python
from pxr import Usd, Sdf

stage      = Usd.Stage.Open("shot.usda")
anim_layer = Sdf.Layer.FindOrOpen("./anim.usda")

# Switch to the override layer
stage.SetEditTarget(anim_layer)

# Override ONLY translate — nothing else is touched
prim = stage.GetPrimAtPath("/World/Chair")
prim.GetAttribute("xformOp:translate").Set((5, 0, 0))
# anim.usda now contains an 'over "Chair"' with only translate
# model.usda is completely unchanged
```

---

## 4. Removing and Clearing Properties

### Why This Exists

Sparse overrides let you ADD or CHANGE opinions. But sometimes you need to go the other direction — **remove** an opinion entirely, or **block** a property from flowing through from a weaker layer. This is a distinct authoring operation that the exam tests specifically, and it behaves differently depending on whether you want to remove a value, remove a time sample, or block the property from appearing at all.

### The Three Scenarios

```
Scenario 1 — Remove an authored value
  A layer Set() a value on an attribute.
  You want to undo that — go back to schema fallback.
  Use: attr.Clear()

Scenario 2 — Remove a specific time sample
  An animated attribute has a keyframe you want to delete.
  Use: attr.ClearAtTime(frame)

Scenario 3 — Remove the property entirely from the layer
  The property spec itself should not exist in this layer at all.
  Use: prim.RemoveProperty("name")
```

### Scenario 1 — Clear an authored value

`Clear()` removes the authored opinion from the current edit target layer. The attribute still exists — it falls back to the schema default if one exists, or becomes unauthored.

```python
from pxr import Usd, UsdGeom

stage = Usd.Stage.Open("scene.usda")
prim  = stage.GetPrimAtPath("/World/Chair")
attr  = prim.GetAttribute("xformOp:translate")

# Before clear
attr.Get()              # (5, 0, 0) — authored value
attr.HasAuthoredValue() # True

# Clear the authored opinion from the current edit target
attr.Clear()

# After clear
attr.Get()              # (0, 0, 0) — schema fallback, or None if no fallback
attr.HasAuthoredValue() # False
```

> **Clear() does NOT delete the property.** It removes the authored value opinion from the current edit target layer. The property spec may still exist in weaker layers — their values will now flow through.

### Scenario 2 — Clear a specific time sample

When you only want to remove one keyframe from an animated attribute without touching the rest of the animation:

```python
attr = prim.GetAttribute("xformOp:translate")

# Before — time samples at frames 1, 12, 24, 48
attr.GetTimeSamples()   # [1.0, 12.0, 24.0, 48.0]

# Remove only frame 12
attr.ClearAtTime(12)

# After
attr.GetTimeSamples()   # [1.0, 24.0, 48.0] — frame 12 gone
attr.Get(time=12)       # interpolated between 1 and 24
```

### Scenario 3 — Remove the property entirely

`RemoveProperty()` deletes the property spec from the prim in the current edit target layer. Use this when the property should not exist in the layer at all — not just have no value, but not be present as a spec.

```python
# Remove a primvar that should not be on this prim
prim.RemoveProperty("primvars:displayColor")

# Remove a relationship
prim.RemoveProperty("material:binding")

# The property is gone from this layer
# If a weaker layer has it, that opinion now flows through
```

### When is this used in production?

**Removing from instanced component prims in assembly stages**

The most common exam scenario. An asset is referenced into a scene, and the assembly-level layer needs to strip a property from the composed prim — for example removing a debug primvar before delivery, or removing a material binding so a shot-level binding takes over cleanly.

```python
# Asset has a default red displayColor
# Shot layer wants to remove it so the shot material controls colour

stage      = Usd.Stage.Open("shot.usda")
shot_layer = stage.GetRootLayer()

# Switch to shot layer as edit target
stage.SetEditTarget(shot_layer)

chair = stage.GetPrimAtPath("/World/Chair")

# Remove the colour primvar from the shot layer's opinion
# This blocks the asset's red from showing through
chair.RemoveProperty("primvars:displayColor")
```

**Clearing time samples during pipeline processing**

When a downstream pipeline step needs to bake or strip animation from an asset before delivery:

```python
# Remove all time samples from an attribute
attr = prim.GetAttribute("xformOp:translate")
attr.Clear()   # removes all time samples AND default value

# Or selectively remove frames in a range
for frame in range(1, 25):
    attr.ClearAtTime(frame)
```

### Clear vs RemoveProperty — side by side

| Operation                     | What it does                            | Property still exists?         | Weaker layer flows through? |
| ----------------------------- | --------------------------------------- | ------------------------------ | --------------------------- |
| `attr.Clear()`                | Removes authored value from edit target | Yes — spec remains             | Yes                         |
| `attr.ClearAtTime(n)`         | Removes one time sample                 | Yes — spec remains             | Yes for that time           |
| `prim.RemoveProperty("name")` | Deletes property spec from edit target  | No — spec gone from this layer | Yes                         |

> **Key insight:** all three operations only affect the current edit target layer. They do not touch other layers. If a weaker layer has an opinion on that property, it will now flow through after the removal — which may or may not be what you want. Use `over` specs with `Block` to explicitly prevent weaker opinions from flowing through.

### Blocking a property from weaker layers

If you want to prevent a weaker layer's opinion from flowing through at all — not just remove your own opinion — use `Block()`:

```python
# Block() sets the value to the type's "blocked" sentinel
# telling composition to stop resolving this property
attr.Block()

# After Block():
attr.Get()              # None — blocked, not the weaker layer's value
attr.HasAuthoredValue() # True — the block IS an authored opinion
```

---

## 4. Flattening — Baking Composition

**Flattening** resolves all composition arcs and produces a single layer containing only the winning values. It is a one-way operation — the original source files are untouched but the composition structure (references, variants, sublayers) is permanently discarded in the output.

```
Before flatten:                    After flatten:
shot.usda                          flat_delivery.usda
├── anim.usda                      (one layer, no arcs)
├── layout.usda                    /World/Chair.translate = (5,0,0)
└── model.usda                     /World/Chair.size = (1,2,1)
    └── ref → chair_asset.usda     ...all winning values baked in
```

### What Flattening Preserves vs Discards

| Preserved                      | Discarded                                   |
| ------------------------------ | ------------------------------------------- |
| ✅ All winning property values | ❌ Composition arcs (references, sublayers) |
| ✅ Animation time samples      | ❌ Variant sets (collapsed to selected)     |
| ✅ All prim hierarchy          | ❌ Layer stack structure                    |
| ✅ Geometry types              | ❌ Payload lazy-loading                     |

> **Time samples are PRESERVED.** Flattening does NOT bake animation to static values. That is a separate, deliberate operation.

### `stage.Flatten()` vs `UsdUtils.FlattenLayerStack()`

Both methods return a new `SdfLayer` in memory. The original stage and all its source files are **never modified**. Think of both as taking a photograph of the stage at that moment — the scene itself is untouched.

### What each one resolves

| Method                         | Sublayers | References  | Payloads    | Variants              | Time samples |
| ------------------------------ | --------- | ----------- | ----------- | --------------------- | ------------ |
| `UsdUtils.FlattenLayerStack()` | Merged    | Kept intact | Kept intact | Kept intact           | Preserved    |
| `stage.Flatten()`              | Merged    | Resolved    | Resolved    | Collapsed to selected | Preserved    |
| `usdcat --flatten`             | Merged    | Resolved    | Resolved    | Collapsed to selected | Preserved    |

> Time samples are **always preserved** by both methods. Neither flattens animation to a static value.

---

### The true difference — what the output SdfLayer looks like

Say you have this stage:

```
shot.usda
  ├── anim.usda          (sublayer — translate keyframes)
  └── layout.usda        (sublayer — base positions)
      /World/Chair       (has reference → chair_asset.usda)
      /World/Chair       (has variantSet "color", selection = "red")
```

**After `UsdUtils.FlattenLayerStack(stage)`:**

```usda
#usda 1.0
(
    # sublayers are GONE — merged into one layer
    # but arcs are PRESERVED exactly as authored
)

def Xform "Chair" (
    prepend references = @./chair_asset.usda@   ← reference STILL HERE
    variants = { string color = "red" }          ← variant set STILL HERE
    prepend variantSets = "color"
) {
    double3 xformOp:translate.timeSamples = {    ← anim + layout merged
        1:  (0, 0, 0),
        24: (5, 0, 0),
    }
}
```

The reference to `chair_asset.usda` is still there. The variant set still exists and can still be switched. The sublayer opinions from `anim.usda` and `layout.usda` are merged into one layer but the composition structure is preserved.

**After `stage.Flatten()`:**

```usda
#usda 1.0
(
    # everything resolved — no arcs, no sublayers
)

def Xform "Chair" {
    # reference is GONE — geometry inlined from chair_asset.usda
    def Mesh "seat_geo" {
        point3f[] points = [(-1,0,-1), (1,0,-1), ...]  ← geometry inlined
        int[] faceVertexCounts = [4, 4, 4, ...]
    }
    def Mesh "legs_geo" { ... }

    # variant set is GONE — only the selected variant's data remains
    color3f[] primvars:displayColor = [(0.8, 0.2, 0.2)]  ← "red" baked in
    # cannot switch to "blue" anymore — that data is gone

    double3 xformOp:translate.timeSamples = {    ← time samples preserved
        1:  (0, 0, 0),
        24: (5, 0, 0),
    }
}
```

The reference is gone — the geometry from `chair_asset.usda` is inlined directly. The variant set is gone — only the currently selected variant's data remains. You cannot switch variants on a fully flattened file.

### When to use each

**Use `UsdUtils.FlattenLayerStack()` when:**

- You want to debug sublayer conflicts — see what the merged layer looks like without the noise of multiple files
- You need to deliver a file but want to keep references and variants intact for the recipient
- You are merging department layers (anim + layout + fx) into one file while preserving asset modularity

**Use `stage.Flatten()` when:**

- You are delivering a fully self-contained file to an external party with no dependencies
- You need to bake a snapshot of the exact current state for archiving
- You are handing off to a renderer or tool that does not support USD composition

### Code

```python
from pxr import Usd, UsdUtils

stage = Usd.Stage.Open("shot.usda")

# Sublayer-only flatten — references and variants preserved
flat_sublayers = UsdUtils.FlattenLayerStack(stage)
flat_stage     = Usd.Stage.Open(flat_sublayers)

# Confirm reference still exists
chair = flat_stage.GetPrimAtPath("/World/Chair")
print(chair.GetMetadata("references"))   # still has reference arc

# Confirm variant set still exists
print(chair.GetVariantSets().GetNames()) # ["color"] — still switchable

# Full flatten — resolves everything
flat_full = stage.Flatten()
flat_stage_b = Usd.Stage.Open(flat_full)

chair_b = flat_stage_b.GetPrimAtPath("/World/Chair")
print(chair_b.GetMetadata("references"))     # None — reference gone
print(chair_b.GetVariantSets().GetNames())   # [] — variant set gone
print(chair_b.GetChildren())                 # [seat_geo, legs_geo] — inlined

# Save flat result to disk for delivery
flat_full.Export("delivery.usda")
# Original shot.usda completely untouched
```

### The key mental model

```
UsdUtils.FlattenLayerStack()
  "Merge the filing cabinet drawers into one drawer
   but keep all the folder tabs and references intact"

stage.Flatten()
  "Photocopy every single document in the cabinet
   into one pile — no folders, no tabs, just the final content"
```

> **Flatten is safe to call for debugging** — `stage.Flatten()` returns a **new** `SdfLayer` object. It never modifies the original stage. Inspect the flat layer and discard it when done. For delivery, call `.Export()` on the result.

---

## 5. Encapsulation — Asset Structure Principles

**Encapsulation** means an asset contains all the prims it needs within its own hierarchy. Nothing reaches outside its root prim to access data from the referencing scene.

### Why It Matters

When an asset is referenced into a scene, only the hierarchy under the referenced prim is brought in. If the asset has prims outside that hierarchy — like a material at `/Looks/WoodMat` while the geometry is at `/Chair` — the material is not brought in with the reference.

```
❌ Unencapsulated asset (broken):
/Chair                    ← referenced in
  /seat_geo  (Mesh)       ✅ brought in
/Looks                    ← NOT brought in (outside /Chair)
  /WoodMat   (Material)   ← geometry can't find its material!

✅ Encapsulated asset (correct):
/Chair                    ← referenced in
  /seat_geo  (Mesh)       ✅ brought in
  /Looks                  ✅ brought in (inside /Chair)
    /WoodMat (Material)   ✅ found correctly
```

### Asset Structure Rules

1. **Set `defaultPrim`** — every published asset must have a `defaultPrim` set to its root prim
2. **Keep materials inside the asset root** — `/Asset/Looks/` not `/Looks/` at the root
3. **Use relative paths** — `./textures/wood.png` not `C:/studio/textures/wood.png`
4. **One root prim** — the `defaultPrim` is the single entry point for references

---

## 6. Change Processing and SdfChangeBlock

Every time you modify anything on a USD stage — set an attribute value, add a prim, change a variant selection — USD immediately broadcasts a **change notification** to every system listening to the stage.

**Who listens to these notifications:**

- **Hydra** — the renderer. Every notification triggers a viewport redraw.
- **Scenegraph panels** — usdview updates its prim tree.
- **Asset management systems** — marks layers as dirty, needing save.
- **Custom callbacks** — anything registered with `stage.GetObjectsChangedNotice()`.

This is fine for a handful of interactive edits. One translate change → one redraw → instant. The problem arises with bulk authoring:

```python
# Importing a 500-frame animation cache WITHOUT SdfChangeBlock
for frame in range(500):
    attr.Set(positions[frame], time=frame)
    # notification fires here — Hydra tries to redraw
    # notification fires here — Hydra tries to redraw
    # ... 500 times
    # UI freezes, import takes 10x longer than it should
```

Each `Set()` call fires a notification. Hydra receives 500 separate redraw requests. The viewport stutters, the import grinds, and all 499 intermediate redraws are completely wasted work.

### `Sdf.ChangeBlock` — batch everything into one notification

`Sdf.ChangeBlock` holds all notifications in a queue until the block exits, then sends **one consolidated notification** covering everything that changed inside the block.

```python
from pxr import Sdf

# WITH SdfChangeBlock — one notification, one redraw
with Sdf.ChangeBlock():
    for frame in range(500):
        attr.Set(positions[frame], time=frame)
# ONE notification sent here — Hydra redraws once
# Import completes instantly
```

The data is still written to the layer in real time inside the block — only the notifications are deferred. There is no risk of inconsistent state.

### Production example — importing a point cache

```python
# Loading 240 frames of simulation data
with Sdf.ChangeBlock():
    for frame, frame_points in cache_data.items():
        points.Set(Vt.Vec3fArray(frame_points), time=frame)
# 240 frames written, 1 notification sent, viewport updates once
```

### When to use it

| Situation                                               | Use SdfChangeBlock?           |
| ------------------------------------------------------- | ----------------------------- |
| Single attribute edit in a UI interaction               | No — one notification is fine |
| Writing time samples in a loop                          | Yes — wrap the entire loop    |
| Importing a simulation cache                            | Yes                           |
| Populating a PointInstancer with thousands of positions | Yes                           |
| Building a large prim hierarchy programmatically        | Yes                           |

> **Rule of thumb:** any time you are authoring inside a `for` loop, wrap it in `Sdf.ChangeBlock()`.

### Stage Caching (`UsdStageCache`) — Avoiding Redundant Composition

Opening a USD stage is expensive — reading all layers from disk and running composition across hundreds of references and sublayers can take several seconds. `UsdStageCache` stores already-opened stage objects in memory so that opening the same file a second time returns the cached stage instantly instead of re-running composition.

```python
from pxr import Usd

cache = Usd.StageCache()

with Usd.StageCacheContext(cache):
    # First open — reads from disk, runs composition, stored in cache
    stage = Usd.Stage.Open("scene.usda")

    # Second open of the same file — returns cached stage instantly
    stage2 = Usd.Stage.Open("scene.usda")

    print(stage is stage2)   # True — exact same object
```

### Will you see old/stale output?

No — the cache stores a reference to the **live Stage object**, not a frozen snapshot. Any edits made to the stage after caching are immediately visible when you retrieve it from the cache. You always see the current state.

The only scenario where you see stale data is if the **files on disk change externally** after the stage was cached:

```python
stage = Usd.Stage.Open("scene.usda")   # reads disk at this moment
# someone edits scene.usda externally on disk
stage2 = Usd.Stage.Open("scene.usda")  # returns cached stage — disk changes NOT picked up

# To pick up external changes:
stage.Reload()   # re-reads all layers from disk
```

### What the cache does and does not do

|                                | Behaviour                                                   |
| ------------------------------ | ----------------------------------------------------------- |
| Stores                         | A reference to the live Stage object — not a copy           |
| Returns                        | The same Stage object — edits visible everywhere            |
| Persists across processes      | No — lives in RAM, gone when process ends                   |
| Picks up external disk changes | No — call `stage.Reload()` to re-read from disk             |
| Caches different path strings  | No — `"scene.usda"` and `"./scene.usda"` are different keys |

### When it matters in production

```python
# Render manager opens the same shot for 10 render passes
# Without cache: 10 composition runs x 3 seconds = 30 seconds
# With cache:    1 composition run + 9 instant lookups = 3 seconds
```

> **Rule of thumb:** use `UsdStageCache` any time the same stage file is opened more than once in a single process — render managers, pipeline tools with multiple panels, batch processors.

---

## 7. Working Directly with Layers

Most USD authoring goes through the high-level `Usd` API — `stage.DefinePrim()`, `attr.Set()`, `UsdGeom.Mesh.Define()`. These are schema-aware and handle composition, type validation, and fallback values automatically.

Sometimes you need to bypass this and work directly on the raw layer data. This is the **Sdf level** — you are constructing layer specs manually with no schema safety net.

### The two levels side by side

```python
# HIGH-LEVEL — schema-aware, goes through Usd API
# USD handles type validation, composition, and fallbacks
stage = Usd.Stage.CreateNew("model.usda")
mesh  = UsdGeom.Mesh.Define(stage, "/World/Chair")
mesh.GetPointsAttr().Set(Vt.Vec3fArray([...]))

# LOW-LEVEL — raw layer data, goes through Sdf directly
# No schema awareness — you describe the structure manually
layer     = Sdf.Layer.CreateNew("model.usda")
prim_spec = Sdf.CreatePrimInLayer(layer, "/World/Chair")
prim_spec.specifier = Sdf.SpecifierDef
prim_spec.typeName  = "Mesh"

attr_spec = Sdf.AttributeSpec(
    prim_spec,
    "points",
    Sdf.ValueTypeNames.Point3fArray
)
attr_spec.default       = Vt.Vec3fArray([...])
attr_spec.documentation = "Mesh vertex positions."
```

Both produce the same USDA output. The high-level route is safer and faster to write. The Sdf route gives you direct control over exactly what goes into the layer.

### SdfPrimSpec — defining a prim in a layer

```python
from pxr import Sdf

layer = Sdf.Layer.CreateNew("scene.usda")

# Define a prim directly in the layer
prim_spec = Sdf.CreatePrimInLayer(layer, "/World/Chair")
prim_spec.specifier = Sdf.SpecifierDef    # def / over / class
prim_spec.typeName  = "Xform"             # the schema type

# Read what was authored
print(prim_spec.specifier)   # Sdf.SpecifierDef
print(prim_spec.typeName)    # "Xform"
print(prim_spec.path)        # Sdf.Path("/World/Chair")
```

### SdfAttributeSpec (subclass of SdfPropertySpec) — defining an attribute in a layer

```python
# Define an attribute on the prim spec
attr_spec = Sdf.AttributeSpec(
    prim_spec,                          # parent prim spec
    "sensor:temperature",               # attribute name
    Sdf.ValueTypeNames.Float            # value type
)

# Set schema-level properties on the attribute
attr_spec.default       = 20.0                    # fallback value
attr_spec.variability   = Sdf.VariabilityVarying  # animated or static
attr_spec.documentation = "Temperature in Celsius."

# Read back what was authored in this layer
print(attr_spec.default)        # 20.0
print(attr_spec.typeName)       # Sdf.ValueTypeNames.Float
print(attr_spec.documentation)  # "Temperature in Celsius."
```

### When you actually use this

| Scenario                                 | Why Sdf level                                                                                                                           |
| ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| Writing a pipeline validator             | Need to inspect raw layer contents, not composed result                                                                                 |
| Building a layer without opening a stage | Procedural generation, test fixtures                                                                                                    |
| Inside usdGenSchema-generated code       | The generated C++ uses SdfPropertySpec internally to register schema attributes                                                         |
| PropertyStack and PrimStack debugging    | `GetPropertyStack()` and `GetPrimStack()` return `SdfPropertySpec` and `SdfPrimSpec` objects — understanding them helps read the output |

> **Key distinction:** The high-level API (`attr.Set()`, `UsdGeom.Mesh.Define()`) is schema-aware — it knows about types, fallbacks, and composition. The Sdf level is raw layer data — you are writing directly into one file's spec list with no schema validation. Both produce the same on-disk result.

---

## 8. Full Composition Mental Model

When USD composes a prim, it collects all **PrimSpecs** from every layer that has an opinion on that prim, orders them by LIVERPS strength, and merges the winning values:

```
1. Collect all PrimSpecs for /World/Chair across all layers
   (from sublayers, references, inherits, variants, specializes)

2. Order by LIVERPS strength:
   [Local opinions in root layer]           strength 1
   [Inherited from class prim]              strength 2
   [Active variant content]                 strength 3
   [Referenced asset opinions]              strength 4
   [Payload opinions]                       strength 5
   [Specialized class opinions]             strength 6 (weakest)

3. For each property: take the value from the strongest spec that has an opinion
   If no spec has an opinion → use schema fallback value

4. Result: the composed prim with its final resolved values
```

---

## 9. Key Takeaways

| Concept                    | What to Remember                                                             |
| -------------------------- | ---------------------------------------------------------------------------- |
| **Edit target**            | Controls which layer receives all authoring operations                       |
| **Default edit target**    | Root layer — always check before authoring in multi-layer stages             |
| **Session layer**          | Always strongest. In-memory. Never saved. `stage.GetSessionLayer()`          |
| **Sparse override**        | `over` spec changes only specific properties. Non-destructive.               |
| **`stage.Flatten()`**      | Returns new `SdfLayer` with all composition resolved. Never modifies source. |
| **`FlattenLayerStack()`**  | Merges sublayers only. References and variants kept intact.                  |
| **Time samples preserved** | Flattening does NOT bake animation to static values                          |
| **Variants collapsed**     | Flattening collapses variant sets to the currently selected variant          |
| **Encapsulation**          | Materials and all prims inside the asset root prim. Relative paths.          |
| **defaultPrim**            | Must be set on every published asset                                         |
| **SdfChangeBlock**         | Batch many edits into one notification — critical for performance            |
| **UsdStageCache**          | Cache open stages to avoid redundant recomposition                           |

---

_Previous: [Day 3 — Composition Arcs Part 2](day-03-composition-arcs-part-2.md)_  
_Next: [Day 5 — Schemas and Data Modeling](day-05-schemas-and-data-modeling.md)_
