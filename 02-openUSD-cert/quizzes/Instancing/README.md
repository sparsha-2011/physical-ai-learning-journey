# Instancing: Scenegraph and Point Instancing

One stop reference combining native (scenegraph) instancing and point instancing:
when to use each, editability rules, refinement techniques, and the full
prototype, instance, PointInstancer transform and primvar resolution order.

## Contents

- [PART 1: The Two Instancing Systems, Which One and When](#part-1-the-two-instancing-systems-which-one-and-when)
- [PART 2: Scenegraph (Native) Instancing](#part-2-scenegraph-native-instancing)
  - [2.0 Definition](#20-definition)
  - [2.1 Key Terms and Quick Snippet](#21-key-terms-and-quick-snippet)
  - [2.2 The Golden Rule of Instance Editability](#22-the-golden-rule-of-instance-editability)
  - [2.3 The Full Resolution Order](#23-the-full-resolution-order)
  - [2.4 The Golden Rule in Practice, With Worked Examples](#24-the-golden-rule-in-practice-with-worked-examples)
  - [2.5 Refinement Techniques, Detailed](#25-refinement-techniques-detailed)
  - [2.6 Refinement Techniques, Full Comparison Table](#26-refinement-techniques-full-comparison-table)
- [PART 3: Point Instancing](#part-3-point-instancing)
  - [3.0 Quick Snippet](#30-quick-snippet)
  - [3.1 The Three Levels](#31-the-three-levels)
  - [3.2 Mandatory vs. Optional Properties](#32-mandatory-vs-optional-properties)
  - [3.3 The Transform Order](#33-the-transform-order)
  - [3.4 Each Level's Independence](#34-each-levels-independence)
  - [3.5 Position, Orientation, Scale](#35-position-orientation-scale)
  - [3.6 Array and List Mutation, Per Attribute](#36-array-and-list-mutation-per-attribute-unique-to-pointinstancer)
  - [3.7 Point Instancing Refinement Techniques](#37-point-instancing-refinement-techniques)
  - [3.8 List and Array Update Behavior](#38-list-and-array-update-behavior)
  - [3.9 Promotion, the Full Recipe](#39-promotion-the-full-recipe)
  - [3.10 Full Combined Scenario Walkthrough](#310-full-combined-scenario-walkthrough)

---

# PART 1: The Two Instancing Systems, Which One and When

| | Scenegraph (Native) Instancing | Point Instancing |
|---|---|---|
| Mechanism | `instanceable = true` on a prim with composition arcs | A `PointInstancer` schema prim using array attributes |
| Prototypes | Implicit. USD figures them out from composition arcs | Explicit. You manually define, relate, and index them |
| Each copy is | A real, addressable prim, for example `/RobotArm_047` | An index into arrays. No prim, no path |
| Best for | Moderate counts, tens to low thousands, when individual addressability matters | Massive counts, thousands to millions, simple repeated items |
| Per copy editing | Only on the instanceable prim's own root | Only through array indexing, or full "promotion" to a real prim |
| Mantra | Explicit instances, implicit prototypes | Explicit prototypes. You build the relationship yourself |
| Classic example | A warehouse of 50 unique robot arms | 100,000 leaves on a tree, packing peanuts in a box |

---

# PART 2: Scenegraph (Native) Instancing

## 2.0 Definition

Scenegraph instancing is `instanceable = true` combined with at least one composition arc, authored on the same prim.

Neither piece alone is enough.

- `instanceable = true` alone does nothing. No prototype is generated.
- A composition arc alone gives normal composition and reuse, but no sharing benefit.
- Both together turn on scenegraph instancing. A prototype is generated and shared.

The arc can be any of these. All are confirmed to count.

- `references`. Yes.
- `payload`. Yes.
- `inherits`. Yes.
- `specializes`. Yes.
- A variant set selection. Yes.
- Nothing at all, just a bare local opinion with no arc. No. This is the trick question case. Zero prototypes.

```usda
def "RobotArm_01" (
    references = @./RobotArm.usd@   # the composition arc
    instanceable = true               # the flag
)
{
}
```

Only when both the flag and an arc are present on the same prim does scenegraph instancing actually happen.

## 2.1 Key Terms and Quick Snippet

```usda
def Xform "Warehouse"
{
    def "RobotArm_01" (                    # instance, also called the instanceable prim
        references = @./RobotArm.usd@      # a real, addressable prim. this IS the mutable root
        instanceable = true
    )
    {
        double3 xformOp:translate = (10, 20, 0)   # editable here, and only here
    }
    def "RobotArm_02" (                    # another instance
        references = @./RobotArm.usd@      # shares the same prototype as RobotArm_01
        instanceable = true
    )
    {
        double3 xformOp:translate = (10, 30, 0)
    }
}

# Not shown in your file at all. USD builds this automatically, implicitly,
# by composing RobotArm.usd's own content:
# /__Prototype_1                          the runtime prototype name for the composed result
#     Base, Arm, Gripper                  content that came from RobotArm.usd itself.
#                                          viewed through /RobotArm_01/... or /RobotArm_02/...
#                                          these become instance proxies
```

`RobotArm.usd` is the prototype itself, the source file, sitting on disk, edited normally.

```usda
#usda 1.0
(
    defaultPrim = "RobotArm"
)
def Xform "RobotArm"                       # this file IS the prototype
{
    def Xform "Base"
    {
        double3 xformOp:translate = (0, 0, 0)
    }
    def Xform "Arm"
    {
        double3 xformOp:rotateY = 0
    }
    def Xform "Gripper"
    {
        color3f primvars:displayColor = [(0.5, 0.5, 0.5)]   # baked in default gray
    }
}
```

Edit this file, and every instance that references it (`RobotArm_01`, `RobotArm_02`, and any future ones) picks up the change automatically. This is a completely ordinary, editable USD file.

Terms used in these notes:

- Prototype. `RobotArm.usd`, the actual source file and its content. Editable, just like any normal asset.
- Runtime Prototype. `/__Prototype_1`, the internal name USD assigns to the composed result. Not editable. Not a stable authoring target.
- Instance. A repetition of a prototype within a scene. A general, conceptual term.
- Instanceable Prim, also called Instance Prim. The concrete, real prim in the scene that represents one instance. The mutable root.
- Instance Proxy. A read only, addressable stand in for a prototype's internal prims, viewed through an instance's path.

A note on official terminology. In OpenUSD's own documentation, and in most interview contexts, the word prototype by itself usually means the runtime composed result, what these notes call the Runtime Prototype, not the source file. The two term split used here is a clarity choice for study purposes, not the industry standard usage. If an interviewer says "the prototype," assume they mean the runtime composed result unless the context says otherwise.

## 2.2 The Golden Rule of Instance Editability

- The prototype's runtime name, `/__Prototype_1`, authored directly from a different layer. Never editable. The name is runtime assigned and can change between compositions.
- The prototype's source content, editing `RobotArm.usd` itself. Always editable. This is a completely normal file, and editing it updates every instance that shares it.
- An instance proxy, for example `/Box_01/Decal`. Never editable. Local opinions are discarded, and authoring one raises an error.
- The instanceable prim itself, for example `/Box_01`. Always editable. This is the only editable point from within the consuming scene.

The trick question: `instanceable = true` with no composition arcs generates zero prototypes. See section 2.0 for the full breakdown of which arcs count.

## 2.3 The Full Resolution Order

Two different orderings apply here, and they are easy to mix up. Keep them separate.

### Ordering A: within one prim's own transform

A single prim's `xformOpOrder` can technically list operations in any order you author. The standard convention, the one `XformCommonAPI` and `Gf.Matrix4d.SetTransform` build for you, applies them in this order, applied to a point:

- **Scale** first: closest to the raw geometry.
- **Rotate** or **orient** second.
- **Translate** last: moves the already scaled and rotated result.

A simple way to remember this: *scale it, spin it, then slide it*.

**Worked example**: `Box_01` has `scale = 2`, `rotate = 90°` around Z, `translate = (5,0,0)`. Take a point on its geometry, `p = (1,0,0)`.

- Scale by 2: `(1,0,0)` becomes `(2,0,0)`.
- Rotate 90° around Z: a 90° rotation around Z maps `(x,y,z)` to `(-y,x,z)`, so `(2,0,0)` becomes `(0,2,0)`.
- Translate by `(5,0,0)`: `(0,2,0)` becomes `(5,2,0)`.

Final result: `p = (5, 2, 0)`.

This is the same S then R then T convention already covered for PointInstancer's per instance array data, where `scales[i]` is applied, then `orientations[i]`, then `positions[i]`. It is not a PointInstancer specific rule. It is the general USD and graphics convention for building one transform matrix.

### Ordering B: across the hierarchy of prims and levels

This is a separate axis from Ordering A. Each level in the hierarchy computes its own complete transform using its own internal Ordering A, and those per level results are then combined, most local first.

For scenegraph instancing:

- The **source file's** own internal content: most local. For example `CubeBox.usd`'s `Geometry` transform.
- The **instanceable prim's** own transform: for example `Box_01`'s translate, rotate, and scale.
- **World**, or any ancestor above the instance: least local, applied last, wrapping around everything else.

For point instancing, shown for direct comparison, same shape, different names:

- The **prototype's** own transform: most local.
- **Instance array data**: scale then orient then position.
- The **PointInstancer's** own transform: least local.

**Worked example, full calculation**: take a point on `Geometry`, `p = (1,0,0)`.

*Prototype* (`Geometry`'s own transform): `scale = 2`, `rotate = 0°` (identity), `translate = (0,0,1)`.
- Scale by 2: `(1,0,0)` becomes `(2,0,0)`.
- Rotate by 0°: unchanged, `(2,0,0)`.
- Translate by `(0,0,1)`: `(2,0,0)` becomes `(2,0,1)`.
- Result after the Prototype level: `(2, 0, 1)`.

*Instanceable Prim* (`Box_01`'s own transform): `scale = 1`, `rotate = 90°` around Z, `translate = (5,0,0)`.
- Scale by 1: unchanged, `(2,0,1)`.
- Rotate 90° around Z: `(x,y,z)` maps to `(-y,x,z)`, so `(2,0,1)` becomes `(0,2,1)`.
- Translate by `(5,0,0)`: `(0,2,1)` becomes `(5,2,1)`.
- Result after the Instanceable Prim level: `(5, 2, 1)`.

*World* (ancestor transform): `scale = 1`, `rotate = 0°` (identity), `translate = (10,0,0)`.
- Scale by 1: unchanged, `(5,2,1)`.
- Rotate by 0°: unchanged, `(5,2,1)`.
- Translate by `(10,0,0)`: `(5,2,1)` becomes `(15,2,1)`.
- Result after the World level: `(15, 2, 1)`.

**Final world position: `(15, 2, 1)`.**

*Note: rotation composition is not commutative, and this example shows exactly why.* If you naively tried to just add up the three translate values, `(0,0,1) + (5,0,0) + (10,0,0)`, you would get `(15, 0, 1)`, which is wrong. The correct answer has a `y` of `2`, not `0`, because `Box_01`'s 90° rotation rotated the Prototype's own translate contribution before it got combined with anything else. Simple sums of translate and scale alone only work when every level's rotation is identity. The moment a real rotation shows up anywhere, the full transform has to be built level by level and multiplied together in the fixed order, Prototype first, then Instanceable Prim, then World, not computed as separate sums or products pulled out across levels.

### Where primvars fit

Primvars are not part of this transform stack at all. This is the part most likely to cause confusion. Primvars do not combine or stack the way transforms do. They resolve through a different mechanism: inheritance, not multiplication.

- There is no summing and no matrix math. It is a single lookup. Does this prim have its own opinion? If yes, use it and stop looking. If no, check the next ancestor up, and repeat.
- Primvars never interact with the S, R, T ordering at all. A `displayColor` primvar authored on `World` has nothing to do with `World`'s own translate, rotate, or scale. They are two unrelated attributes, resolved by two unrelated mechanisms, that simply happen to live on the same prim.

The contrast, stated directly:

- Transforms: every level contributes, always, even when a level is identity. Order matters, both within a prim, scale before rotate before translate, and across levels, most local before least local. The mechanism is multiplication.
- Primvars: only the winning level's value is used. Every other level is ignored entirely. Order only matters in the sense of which opinion is nearest. There is no summing or blending.

## 2.4 The Golden Rule in Practice, With Worked Examples

Setup shared by every example below:
```usda
def Xform "World"                          # parent, sits above the instance
{
    def "Box_01" (
        references = @./CubeBox.usd@
        instanceable = true
    )
    {
    }
}
```
`CubeBox.usd` internally has `def Mesh "Geometry" { def Mesh "Decal" {...} }`, plus its own authored `displayColor = red` and `xformOp:scale = (1,1,1)`.

Every table below uses the same row order: World, Prototype (the source file's own content), Instanceable Prim, Instance Proxy, Runtime Prototype.

### Transforms

| Level | Authored value | Allowed? |
|---|---|---|
| World | `translate = (10,0,0)` | ✓ |
| Prototype (`CubeBox.usd`'s Geometry) | not authored in this example | ✓ |
| Instanceable Prim (`Box_01`) | `translate = (5,0,0)` | ✓ |
| Instance Proxy (`Box_01/Geometry`) | `translate = (1,0,0)` | ✗ |
| Runtime Prototype (`/__Prototype_1`) | `translate = (99,0,0)` | ✗ |

Default if nothing is authored anywhere: `(0,0,0)`, identity.

Result, computed most local first: the Prototype contributes `(0,0,0)`, since nothing was authored on it here. The Instanceable Prim (`Box_01`) contributes `(5,0,0)`. World contributes `(10,0,0)`, applied last. Adding these in that order gives `(0,0,0) + (5,0,0) + (10,0,0) = (15, 0, 0)`. The two ✗ rows contribute nothing at all, since neither is allowed to author in the first place.

### Visibility

| Level | Authored value | Allowed? |
|---|---|---|
| World | `visibility = "invisible"` | ✓ |
| Prototype (`CubeBox.usd`'s Geometry) | not authored in this example | ✓ |
| Instanceable Prim (`Box_01`) | not authored in this example | ✓ |
| Instance Proxy (`Box_01/Decal`) | `visibility = "invisible"` | ✗ |
| Runtime Prototype (`/__Prototype_1`) | not applicable | ✗ |

Default if nothing is authored anywhere: `"inherited"`, meaning visible, unless an ancestor says otherwise.

Result: World's `"invisible"` is a poison pill. It propagates down and cannot be undone by anything beneath it, so `Box_01` is invisible regardless of what the Prototype or the Instanceable Prim itself says. The attempted edit on `Box_01/Decal` is rejected outright, since it targets an instance proxy.

### Primvars, for example `displayColor`

| Level | Authored value | Allowed? |
|---|---|---|
| World | `displayColor = blue` | ✓ |
| Prototype (`CubeBox.usd`'s Geometry) | `displayColor = red` | ✓ |
| Instanceable Prim (`Box_01`) | `displayColor = green` | ✓ |
| Instance Proxy (`Box_01/Geometry`) | `displayColor = yellow` | ✗ |
| Runtime Prototype (`/__Prototype_1`) | not applicable | ✗ |

Default if nothing is authored anywhere: no fallback value. Primvars have no schema default the way an attribute like radius does.

Result: green. The Instanceable Prim's own opinion is the nearest authored value from the perspective of anything reading this primvar inside the prototype's subgraph, so it wins over both World's blue and the Prototype's own red. If `Box_01` had nothing authored, the result would fall back to whatever the Prototype itself authored, red, since the Prototype's own opinion sits closer than World's. The attempted edit on `Box_01/Geometry` is rejected outright.

A subtlety worth noting: authoring `displayColor` on the Instanceable Prim does not simply win a tie. It works because primvars inherit down into the Prototype's own subgraph, and the Instanceable Prim sits above everything in the Prototype from the instance's perspective. This is the same primvar inheritance mechanism covered in the Hierarchy Behavior cheat sheet, Type A, applied specifically at the instance root boundary.

### Material binding

| Level | Authored value | Allowed? |
|---|---|---|
| World | not applicable in this example | ✓ |
| Prototype (`CubeBox.usd`'s Geometry) | not authored in this example | ✓ |
| Instanceable Prim (`Box_01`) | `rel material:binding = </Looks/RedPaint>` | ✓ |
| Instance Proxy (`Box_01/Geometry`) | a new binding | ✗ |
| Runtime Prototype (`/__Prototype_1`) | not applicable | ✗ |

Default if nothing is authored anywhere: unbound, no material.

Result: `Box_01` renders with RedPaint, since that is the nearest authored binding. Other instances sharing the same Prototype are unaffected. The attempted new binding on `Box_01/Geometry` is rejected outright. A separate mechanism, Broadcasted Refinement through a `specializes` target such as `_PalletBox`, can also deliver a binding to every instance connected to that target, without touching any Instanceable Prim directly.

Summary across all four attribute types. The same boundary applies to transforms, visibility, primvars, and relationships alike. Author it on the Instanceable Prim, or on an ancestor above it, and it works. Try to reach into any descendant of the Instanceable Prim, or into the Runtime Prototype directly, and it fails. The behavior once authored still follows the ordinary rules already covered: additive for transforms, poison pill for visibility, inheritance based for primvars. Instancing does not introduce new value resolution rules. It adds one extra hard boundary. Never past the Instanceable Prim.

## 2.5 Refinement Techniques, Detailed

### Deinstancing

- The simplest tool available. Set `instanceable = false` on one specific instance, in a stronger layer, to pull it out of the shared prototype system entirely.
  ```usda
  over "Box_01" ( instanceable = false ) {}
  ```
  `Box_01` shared a prototype with 999 other boxes. This one line pulls it out on its own.

- Once deinstanced, the prim's descendants become editable again. Overrides on any internal prim now succeed instead of erroring.
  ```usda
  over "Box_01/Decal" { token visibility = "invisible" }
  ```
  Before deinstancing, this line raised an error. After deinstancing, it works, and only this one box's decal disappears.

- The deinstanced prim keeps its `references` or `payload` arc, so it retains asset reuse and centralized editing benefits. It only loses the prototype sharing memory benefit.
  > `Box_01` still says `references = @./CubeBox.usd@`. If someone later fixes a bug in `CubeBox.usd`'s geometry, `Box_01` still picks up that fix, exactly like every other box.

- Best suited to one, or a small handful, of truly unique one off cases. For example, a single sample box for a marketing shot.
  > One box out of 1,000 needs a "sample product" sticker for one photo. Deinstancing that one box is the simplest fix.

- Does not scale well. Deinstancing many copies to introduce the same kind of variety means paying the full memory cost of a separate composed copy for each one. At that point, a technique that creates one shared new prototype is more efficient.
  > If 300 boxes all need the same kind of unique decal, deinstancing all 300 individually means 300 fully separate composed copies in memory, instead of one shared new prototype.

### Variant Sets

- Selecting a different variant on an instanceable prim is a valid form of refinement. It triggers the creation of a new prototype, one shared by every instance that picks the same combination.
  ```usda
  def "Box_01" ( references = @./CubeBox.usd@, instanceable = true, variants = { string boxType = "allocated" } ) {}
  def "Box_02" ( references = @./CubeBox.usd@, instanceable = true, variants = { string boxType = "allocated" } ) {}
  ```
  Both boxes share one new "allocated" prototype, distinct from the plain-box prototype used by everyone else.

- Requires foresight. The variant set must already be authored on the source asset. You cannot select a variant that does not exist.
  > If `CubeBox.usd` was never built with a `boxType` variant set at all, there is nothing to select.

- Scales cleanly. Switching more instances to an already existing variant adds no additional prototypes. They all share the one prototype for that variant.
  > Whether 2 boxes or 200 boxes pick `"allocated"`, it is still just one shared prototype for that variant.

- A real comparison from the exercise: two de-instanced boxes cost 1771 total prims. Two boxes switched to an "allocated" variant cost only 1737 prims, for the same visual outcome. Variant sets are the cheaper path when the variation was planned for in advance.
  | Scenario | Prims | Prototypes |
  |---|---|---|
  | Instancing, before the change | 1711 | 3 |
  | 2 de-instanced boxes | 1771 | 3 |
  | 2 boxes on the "allocated" variant | 1737 | 4 |

### Hierarchical Refinement

- Refines instances by authoring inherited properties on an ancestor, or on the instance root itself. Most commonly transforms, visibility, and primvars.
  ```usda
  over "World" { double3 xformOp:translate = (0, 5, 0) }
  ```
  Every box beneath `World` shifts up by 5 units at once, without touching any box individually.

- Creates no new prototypes, ever. The underlying subgraphs among instances stay identical. Only the ancestor or root gains a new opinion.
  > Moving `World` does not change what any box's internal geometry or material data looks like. Only `World`'s own transform gained an opinion.

- Transforms compose additively or multiplicatively down the hierarchy regardless of instancing, so instances can be spatially varied at no extra cost.
  > `World`'s translate `(10,0,0)` combines with `Box_01`'s own translate `(5,0,0)` for a total world position of `(15,0,0)`.

- Visibility on an ancestor always propagates down and cannot be undone by a descendant. An instance beneath an invisible ancestor is never rendered, no matter what the prototype itself says.
  ```usda
  over "World" { token visibility = "invisible" }
  ```
  Every box beneath `World` is hidden. No individual box can override its way back to visible.

- Primvars set on the instance root are inherited into the prototype's own subgraph, letting materials read a per instance value without needing a new prototype. This is the cheapest way to introduce visual variety at scale.
  ```usda
  over "Box_01" { color3f primvars:displayColor = [(0, 1, 0)] }
  ```
  This tints just `Box_01` green, since materials inside the shared prototype read the inherited value. No new prototype is created.

### Ad Hoc Arcs Refinement

- Adds a brand new composition arc directly onto specific instanceable prims, retroactively, on the local layer stack. No foresight or pre existing asset design is required.
  ```python
  box1.GetReferences().AddReference(decals_path, "/_MixinOverrides/DamagedStamp")
  ```
  Bolts a new reference onto an already-existing box, with zero changes needed in `CubeBox.usd` itself.

- The added arc introduces new opinions and triggers a new prototype, shared by every instance that received that identical arc.
  ```python
  box1.GetReferences().AddReference(decals_path, "/_MixinOverrides/DamagedStamp")
  box3.GetReferences().AddReference(decals_path, "/_MixinOverrides/DamagedStamp")
  ```
  `Box_01` and `Box_03` now share one new "box plus damage" prototype, separate from the plain-box prototype still used by `Box_02` and `Box_04`.

- A real example: adding the same "Damaged" stamp reference to two out of many boxes created exactly one new shared prototype, going from three to four total. The prim count grew only by the decal's own prim footprint, about thirty prims, not by duplicating the boxes.
  | Scenario | Prims | Prototypes |
  |---|---|---|
  | Instancing, before the change | 1711 | 3 |
  | After adding the ad hoc arc to 2 boxes | 1741 | 4 |

- The more instances share the identical new arc, the more this technique pays off. A dozen or so instances is usually the point where it clearly makes sense.
  > Applying the same arc to a dozen boxes still only costs one new shared prototype. The per-box cost shrinks the more boxes adopt the same change.

- If only one or two instances need the change, deinstancing is simpler and more direct. There is no obligation to preserve instancing at all costs.
  > If only a single box ever needs the damage stamp, building a whole new shared prototype for a group of one is not worth it. Plain deinstancing is more direct.

### Broadcasted Refinement

- Uses the broadcasting behavior of `inherits` and `specializes` arcs. Author one new opinion on the shared target namespace, and every prim already connected to that target through the arc receives it automatically, resolved according to LIVERPS.
  ```python
  pallet_box = stage.OverridePrim(".../_PalletBox")
  pallet_box.GetReferences().AddReference(decals_path, "/_MixinOverrides/DamagedStamp")
  ```
  One line, and every box that specializes from `_PalletBox` picks it up.

- Requires a pre existing group connection. The instances must already specialize from, or inherit from, a shared target before the change is needed. This technique cannot be retrofitted onto assets with no such connection already in place.
  > If none of the 500 boxes were ever wired up with `specializes = </_PalletBox>` in the first place, this technique is not available. Ad Hoc Arcs would be needed instead.

- Delivers the change in exactly one authored edit, regardless of whether the group has three members or three thousand. This is the most efficient of the five techniques in terms of edit count.
  > Whether the pallet has 3 boxes or 3,000, the exact same single line of code applies the damage stamp to all of them.

- A real example: authoring one reference addition on a shared `_PalletBox` class prim stamped every box on that pallet with a damage decal. The result was 1747 total prims, one new shared prototype, and zero edits made to any individual box's own file.
  | Scenario | Prims | Prototypes |
  |---|---|---|
  | Instancing, before the change | 1711 | 3 |
  | After the broadcasted edit on `_PalletBox` | 1747 | 4 |

- Works on instances too. The target's opinion reaches instanceable prims the same way it reaches any other prim.
  > Every box in the pallet is `instanceable = true`, yet the broadcasted opinion from `_PalletBox` still reaches all of them.

Choosing between `inherits` and `specializes` for the group connection. This decision comes down to whether the broadcasted change should be allowed to override something more specific already on the instance.

- LIVERPS strength. `inherits` sits near the strongest position, right after Local. `specializes` sits at the weakest position of all seven arcs.
  > On the same LIVERPS ladder, `inherits` beats `references` and `payload`. `specializes` loses to everything.

- Can it override a payload or reference already on the instance? `inherits` can. `specializes` never can.
  > If `Box_03` has a payload-sourced physics rotation of 87 degrees, connecting the group via `specializes` can never override that. Connecting via `inherits` could force it back to a mandatory default.

- When to use it. Use `inherits` when the change must be mandatory and override everything, for example a safety recall. Use `specializes` when the change should act as a default, safe to be overridden by anything more specific, for example a shared paint style.
  > A mandatory recall belongs on `inherits`. A shared default paint style, meant to be overridable, belongs on `specializes`.

- The guarantee. With `inherits`, the broadcasted change always wins. With `specializes`, individual instance customizations, for example from a payload simulation or a reference, always survive.
  > With `specializes`, a box's own payload-driven simulation data always survives the broadcast. With `inherits`, the broadcasted change wins even over that same payload data.

**Full example: `specializes`, preserving a physics simulation.**

```usda
class "_PalletBox" {}

def "Box_03" (
    references = @./CubeBox.usd@
    specializes = </_PalletBox>
    payload = @./SimCache.usd@         # SimCache.usd sets rotateX = 87, from a physics drop test
)
{}
```

Later, someone adds a "default upright" opinion to the shared template:

```usda
over "_PalletBox" { double3 xformOp:rotateX = 0 }
```

Because `specializes` is the weakest arc, `Payload` still outranks it. `Box_03` stays tipped over at `rotateX = 87`, exactly as the simulation computed. Any other box in the pallet with no payload of its own falls back to the template's `rotateX = 0` correctly.

**Full example: `inherits`, applying a rule to everything, even overriding the simulation.**

```usda
class "_MandatoryRecall" {}

def "Box_03" (
    references = @./CubeBox.usd@
    inherits = </_MandatoryRecall>
    payload = @./SimCache.usd@         # same simulation data, rotateX = 87
)
{}
```

A mandatory safety change is issued on the shared target:

```usda
over "_MandatoryRecall" { double3 xformOp:rotateX = 0 }
```

Because `inherits` outranks `Payload`, `Box_03` now snaps upright to `rotateX = 0`, even though it has simulated physics data. This is the correct behavior for a genuinely mandatory, no-exceptions change, but it would be the wrong choice if the simulation data was meant to be preserved.

## 2.6 Refinement Techniques, Full Comparison Table

| Technique | Creates new prototype? | Edits needed for N instances | Requires pre-planning? | Best for |
|---|---|---|---|---|
| Deinstancing (`instanceable = false`) | No, leaves the shared system entirely | N, but simplest per edit | No | One, or very few, truly unique one-offs |
| Variant Sets | Yes, one per unique combination | N, one selection per instance | Yes, the variant set must pre-exist on the asset | Pre-planned, discrete option menus, for example paint color |
| Hierarchical Refinement (xformOps, visibility, primvars on an ancestor or root) | No new prototype, ever | One, on the ancestor or per instance root | No | Cheapest possible variety: position, visibility, simple color |
| Ad Hoc Arcs (new composition arc added to specific instances) | Yes, one per unique combination of arcs | N, one arc addition per instance | No, works retroactively on any asset | Many instances need identical new content, but no pre-existing group |
| Broadcasted Refinement (`inherits` or `specializes` to a shared target) | Yes, one shared by the whole group | One, regardless of group size | Yes, the group connection must already exist | Many instances already belong to a defined group; one edit updates all |

---

# PART 3: Point Instancing

## 3.0 Quick Snippet

```usda
def PointInstancer "Scatter"              # <-- THE POINTINSTANCER (the whole scatter group)
{
    rel prototypes = [</Scatter/Prototypes/Peanut>]
    int[] protoIndices = [0, 0, 0]
 
    point3f[] positions = [(0,0,0), (5,0,0), (10,0,0)]        # <-- INSTANCE data (per-index, no prim!)
    quath[] orientations = [(1,0,0,0), (1,0,0,0), (1,0,0,0)]  # <-- INSTANCE data
    float3[] scales = [(1,1,1), (1,1,1), (1,1,1)]             # <-- INSTANCE data
 
    double3 xformOp:translate = (100, 0, 0)   # <-- the POINTINSTANCER's OWN transform
    uniform token[] xformOpOrder = ["xformOp:translate"]
 
    over Scope "Prototypes"                    # container — NOT one of the 3 levels itself
    {
        def "Peanut" (                          # <-- THE PROTOTYPE (shared template)
            references = @./Peanut.usd@
        )
        {
            double3 xformOp:translate = (0, 0, 0.1)   # <-- the PROTOTYPE's OWN transform
            uniform token[] xformOpOrder = ["xformOp:translate"]
        }
    }
}
 
# NOTE: "Instance" is NOT a real prim anywhere in this file — it's just
# whatever sits at index 0, 1, 2 across the positions/orientations/scales arrays.
```
 
**Why `over Scope "Prototypes"` and not `def Scope "Prototypes"`**: a pure `over` (no `def` for that path anywhere) is skipped by default traversal, along with everything nested inside it.
 
```python
for prim in Usd.PrimRange(stage.GetPseudoRoot()):
    print(prim.GetPath())
```
 
With `over Scope "Prototypes"`:
```
/Scatter
```
`Prototypes` and `Peanut` never appear — invisible to any generic tool.
 
With `def Scope "Prototypes"`:
```
/Scatter
/Scatter/Prototypes
/Scatter/Prototypes/Peanut
```
Both show up, and a non-PointInstancer-aware tool could try to process or render `Peanut` directly.
 
This is defense in depth, not a strict requirement. A tool that IS PointInstancer-aware already knows to skip anything targeted by the `prototypes` relationship, regardless of `def` or `over`. `over` protects you specifically when the consuming tool is NOT PointInstancer-aware.

## 3.1 The Three Levels

| Level | What it is | Authored as |
|---|---|---|
| **Prototype** | The shared template shape (e.g. one peanut asset) | A real, `def`-ed prim with its OWN `xformOp:translate/orient/scale` |
| **Instance** | NOT a prim — just one index/row across parallel arrays | `positions[i]`, `orientations[i]`, `scales[i]` |
| **PointInstancer** | The whole scattering group | The PointInstancer prim's OWN `xformOp:translate/orient/scale` |

### Worked example, all four levels including World

A `PointInstancer` is just a prim, so it can sit beneath an ordinary ancestor like `World`, exactly like any other prim. That makes a fourth level available above the three in the table.

```usda
def Xform "World"                              # ancestor above the PointInstancer
{
    double3 xformOp:translate = (100, 0, 0)

    def PointInstancer "Scatter"
    {
        double3 xformOp:translate = (10, 0, 0)   # the PointInstancer's OWN transform

        int[] protoIndices = [0]
        point3f[] positions = [(1, 0, 0)]        # instance array data
        float3[] scales = [(2, 2, 2)]

        over Scope "Prototypes"
        {
            def "Peanut" ( references = @./Peanut.usd@ )
            {
                double3 xformOp:translate = (0, 0, 0.1)   # the Prototype's OWN transform
            }
        }
    }
}
```
`over Scope "Prototypes"` is used here for the same reason as the earlier snippet: a "pure over" is skipped by default traversal, protecting `Peanut` from generic tools that don't understand `PointInstancer`.

Applied most local to least local:
1. **Prototype**: `Peanut`'s own translate, `(0, 0, 0.1)`.
2. **Instance**: `positions[0] = (1, 0, 0)`, `scales[0] = 2`.
3. **PointInstancer**: its own translate, `(10, 0, 0)`.
4. **World**: its own translate, `(100, 0, 0)`.


Translate combines additively, most local first, assuming no rotation is involved: `(0,0,0.1) + (1,0,0) + (10,0,0) + (100,0,0) = (111, 0, 0.1)`. Scale combines multiplicatively: the Prototype and PointInstancer both leave scale unauthored, defaulting to `1`, so the only real contribution is the instance's own `2`, giving a final scale of `2`.

**The point worth taking from this**: `World` is not one of the three official PointInstancer levels, but it behaves exactly like any other ancestor in ordinary USD hierarchy. It simply adds one more level on top of the three, using the same hierarchical transform rules covered in Part 2's Ordering B, not a PointInstancer-specific rule.

### 3.1.1 Golden Rule in Practice for Point Instancing, With Worked Examples

Same format as Part 2's tables. Every table below uses the same row order: Prototype, Instance (the array data), PointInstancer, World.

Setup shared by every example below: `Peanut` is the prototype, referenced from `Peanut.usd`, with its own baked-in `translate = (0, 0, 0.1)` and `displayColor = gray`. `Scatter` is the PointInstancer, with one instance at index `0`. `World` sits above `Scatter`.

#### Translate / Position

| Level | Authored value | Allowed? |
|---|---|---|
| Prototype (`Peanut`'s own translate) | `(0, 0, 0.1)` | ✓ |
| Instance (`positions[0]`) | `(1, 0, 0)` | ✓ |
| PointInstancer (`Scatter`'s own translate) | `(10, 0, 0)` | ✓ |
| World | `(100, 0, 0)` | ✓ |

Default if nothing is authored anywhere: `(0,0,0)`, identity.

Result, most local first: `(0,0,0.1) + (1,0,0) + (10,0,0) + (100,0,0) = (111, 0, 0.1)`. All four levels contribute, since none of them is disallowed the way an instance proxy is in scenegraph instancing.

#### Scale

| Level | Authored value | Allowed? |
|---|---|---|
| World | not authored | ✓ |
| PointInstancer (`Scatter`'s own scale) | not authored | ✓ |
| Instance (`scales[0]`) | `2` | ✓ |
| Prototype (`Peanut`'s own scale) | not authored | ✓ |

Default if nothing is authored anywhere: `1`, identity.

Result: `1 x 1 x 2 x 1 = 2`. The instance's own value is the only real contribution here, since the other three default to `1` and do not change the product.

#### Orientation
 
| Level | Authored value | Allowed? |
|---|---|---|
| World | not authored | ✓ |
| PointInstancer (`Scatter`'s own orient) | not authored | ✓ |
| Instance (`orientations[0]`) | `90°` around Y | ✓ |
| Prototype (`Peanut`'s own orient) | not authored | ✓ |
 
Default if nothing is authored anywhere: `(1,0,0,0)`, identity, no rotation.
 
Result: only the instance's own `90°` around Y contributes. The other three are identity and do not change the composed result. Order still matters for any level that does author a rotation, applied Prototype first, then Instance, then PointInstancer, then World, same as translate and scale.
 
#### Primvars, for example `displayColor`
 
| Level | Authored value | Allowed? |
|---|---|---|
| World | not authored in this example | ✓ |
| PointInstancer (authored directly on `Scatter`, not as a per-instance array) | not authored in this example | ✓ |
| Instance (a per-instance `primvars` array on the PointInstancer, `vertex` interpolation) | `blue` | ✓ |
| Prototype (`Peanut`'s own `displayColor`) | `gray` | ✓ |
 
Default if nothing is authored anywhere: no fallback value, same as scenegraph instancing.
 
Result: gray, not blue. This is the primvar-blocking gotcha. The Prototype's own opinion is a descendant's opinion relative to the PointInstancer's per-instance array, so it wins and shadows the array data, even though the array was clearly meant to give each instance its own color. Fix: `.Block()` the Prototype's own `displayColor` opinion, which removes the shadowing entirely and lets each instance's own array value take over.
 
#### Visibility
 
| Level | Authored value | Allowed? |
|---|---|---|
| World | `visibility = "invisible"` | ✓ |
| PointInstancer (via `inactiveIds`, listing this instance's id) | listed as inactive | ✓ |
| Instance (via `invisibleIds`, listing this instance's id) | listed as invisible | ✓ |
| Prototype | not authored in this example | ✓ |
 
Default if nothing is authored anywhere: visible.
 
Result: invisible, for two independent reasons at once. World's `"invisible"` is a poison pill affecting the whole PointInstancer and everything it scatters, exactly like ordinary hierarchy. Separately, this specific instance is also individually pruned by `inactiveIds` and individually hidden by `invisibleIds`, which operate per-instance rather than through ordinary hierarchical visibility at all.
 

## 3.2 Mandatory vs. Optional Properties

| Property | Required? | Type | Meaning |
|---|---|---|---|
| `prototypes` | ✅ Mandatory | relationship | Points at the prim hierarchies used as templates |
| `protoIndices` | ✅ Mandatory | int array | Maps each point to which prototype it uses |
| `positions` | ✅ Mandatory | point3f array | Where each instance sits, in the PointInstancer's local space |
| `orientations` | Optional | quath array | Rotation per instance (defaults to identity if absent) |
| `scales` | Optional | float3 array | Scale per instance (defaults to (1,1,1) if absent) |
| `ids` | Optional | int64 array | Explicit instance IDs (defaults to array index if absent) |

## 3.3 The Transform Order

```
1. Prototype's OWN transform      (most local — applied FIRST)
                                   this is itself Scale, then Rotate, then Translate,
                                   the same internal sub-order as any other prim's transform
2. Instance array data, in THIS sub-order:
   a. scales[i]
   b. orientations[i]
   c. positions[i]
3. PointInstancer's OWN transform  (least local — applied LAST)
                                   also Scale, then Rotate, then Translate internally
```

**Memory trick**: *"Proto starts it, Instance steers it (Scale→Orient→Position), Group moves it all."*

## 3.4 Each Level's Independence

**Each of the 3 levels is completely independent. None of them "borrow" from each other. If a level is unauthored, it defaults to identity — it does NOT inherit a value from either of the other two levels.**

| Level unauthored | What happens |
|---|---|
| Prototype has no transform | Contributes identity — nothing added |
| Instance array entry missing/absent | Contributes identity for that component |
| PointInstancer has no transform | Contributes identity — nothing added |
| **ALL THREE absent** | Instance sits exactly where the prototype's raw geometry was authored, no rotation, no scale, no offset |

## 3.5 Position, Orientation, Scale

### Position (`point3f`, additive across levels)
```
World position = Prototype's translate + Instance's positions[i] + PointInstancer's translate
```
Example: Prototype `(0,0,0.1)` + Instance `(5,0,0)` + PointInstancer `(100,0,0)` = **`(105, 0, 0.1)`**

### Scale (`float3`, multiplicative across levels)
```
World scale = Prototype's scale × Instance's scales[i] × PointInstancer's scale
```
Example: Prototype `1×` + Instance `2×` + PointInstancer `1×` = **`2×` total**

### Orientation (`quath`, composed via quaternion or matrix multiplication)
```
World rotation = combine(Prototype's rotation, Instance's orientations[i], PointInstancer's rotation)
                 applied in that literal order: Prototype first, then Instance, then PointInstancer
```
- Same-axis rotations → can add directly, then `% 360°`.
- Different-axis rotations → must use quaternion/matrix composition; order matters (non-commutative).
- Multiplication notation is written **right-to-left for application order**: `PointInstancer_rot × Instance_rot × Prototype_rot` (Prototype, being rightmost, is applied first).

## 3.6 Array and List Mutation, Per Attribute (unique to PointInstancer)

See section 3.8 for the full comparison, merged with `inactiveIds`, `invisibleIds`, `DeactivateId`, and `.Block()`.

## 3.7 Point Instancing Refinement Techniques

| Technique | What it does | Key mechanism |
|---|---|---|
| **Primvars (vertex interpolation)** | Per-instance shading variety (color, dirtiness, etc.) | Author an array on the PointInstancer; prototype's material must be wired to read it |
| **Introducing new prototypes** | Add more variety of shape | Manual 3-step process: (1) define new prim hierarchy, (2) add to `prototypes` rel, (3) update `protoIndices` |
| **`inactiveIds`** | Permanently prune instances | Metadata; **list-editable** (can sparsely add/remove ids across layers) |
| **`invisibleIds`** | Temporarily hide instances (can animate on/off) | Attribute; use when visibility needs to change over time |
| **Promotion** | Turn ONE point instance into a real, fully-editable prim | Prune via `inactiveIds`, reference a real asset at the same computed world transform, and use `.Block()` to clear any conflicting inherited opinion on the new prim |

## 3.8 List and Array Update Behavior

Easy to conflate. There is no single, named handle for an individual point instance the way `stage.GetPrimAtPath(...)` gives you a real prim. If you want "instance 47" specifically, the correct way to reach it, and what happens when you try to change it, is different for each attribute below:

### 1. `positions`, `orientations`, `scales`, `protoIndices`

Ordinary per-instance array data. Not a visibility or lifecycle control at all, just placement, rotation, and scale.

- **Addressed by**: array index only, e.g. `positions[47]`.
- **Mechanism**: these are ordinary attributes, so they are all-or-nothing per authored value. There is no sparse per-element editing across layers, and no sparse editing across time samples either.
- **Mutation**: changing even one entry means reading the current array, editing that one index, and setting the entire array back.

```
positions = [(0,0,0), (1,0,0), (2,0,0)]
```
To move just index `1`, read all three values, change only the middle one, and set `[(0,0,0), (9,0,0), (2,0,0)]` back as one full array.

Because each time sample also needs a full copy of the array, animated scatters with many instances get expensive fast. Use USDC (Crate), not USDA, for large animated scatters.

### 2. `inactiveIds`

Permanently prunes an instance from the PointInstancer entirely.

- **Addressed by**: id, not index.
- **Mechanism**: this is composition **metadata**, the same category as `references` or `variantSets`, so it inherits ordinary list-editing behavior: `prepend`, `append`, `delete`, across layers. This is the one exception in this whole section that supports sparse editing.
- **Mutation**: no full restatement needed. You can sparsely add or remove ids across layers.

```usda
# weaker layer
inactiveIds = [12]
```
```usda
# stronger layer
prepend inactiveIds = [47]
```
Composed result: `[47, 12]`, both pruned, without either layer needing to know about the other's id.

Right tool for: peanuts that fell out and are gone forever.

### 3. `invisibleIds`

Hides an instance from rendering without removing it. It still exists and is still tracked.

`DeactivateId(N)` is simply the Python API for authoring `inactiveIds`.

```python
pi.DeactivateId(1228)
```

- **Addressed by**: id, not index, same as `inactiveIds`.
- **Mechanism**: this is an ordinary **attribute**, not list-editable metadata, despite being id-based like `inactiveIds`. Ordinary attributes are all-or-nothing per authored value.
- **Mutation**: each authored time sample needs the complete set of currently-invisible ids, not just the ones changing.

```
invisibleIds.timeSamples = { 1: [], 50: [12, 47], 100: [] }
```
At frame 50, both ids must be listed together. You cannot add `47` at frame 50 without also restating `12`.

Right tool for: flickering something on or off across an animation.

## 3.9 Promotion, the Full Recipe

```
1. pi.DeactivateId(N)                          → prune the point instance
2. stage.DefinePrim(new_path)                  → create a real prim
3. new_prim.GetReferences().AddReference(...)   → give it real content
4. xforms = pi.ComputeInstanceTransformsAtTime(
       Usd.TimeCode.Default(), Usd.TimeCode.Default(),
       applyMask=UsdGeom.PointInstancer.IgnoreMask)   → get the FULL resolved world transform
                                                          (IgnoreMask needed since it's now deactivated)
5. Extract translation/rotation/scale from xforms[N], apply to the new prim
```

```python
box_proto.GetAttribute("primvars:cleanness").Block()
```

## 3.10 Full Combined Scenario Walkthrough

**Setup:**
```usda
def PointInstancer "Scatter"
{
    rel prototypes = [</Scatter/Prototypes/Peanut>]
    int[] protoIndices = [0, 0]
    point3f[] positions = [(5,0,0), (10,0,0)]
    quath[] orientations = [(0.707,0,0.707,0), (1,0,0,0)]
    float3[] scales = [(2,2,2), (1,1,1)]
    double3 xformOp:translate = (100,0,0)     # PointInstancer's own

    def Scope "Prototypes"
    {
        def "Peanut" { double3 xformOp:translate = (0,0,0.1) }   # Prototype's own
    }
}
```

| | Instance 0 | Instance 1 |
|---|---|---|
| Prototype contributes | `(0,0,0.1)` | `(0,0,0.1)` (same — shared prototype) |
| Instance scale | `2×` | `1×` (identity) |
| Instance orientation | 90° around Y | identity |
| Instance position | `(5,0,0)` | `(10,0,0)` |
| PointInstancer contributes | `(100,0,0)` | `(100,0,0)` (same — shared group transform) |
| **Final world position (approx.)** | `(105, 0, 0.1)`, scaled 2×, rotated 90°Y | `(110, 0, 0.1)`, no scale/rotation change |

**Key takeaway from this table**: the Prototype's and PointInstancer's contributions are **identical for every instance sharing that prototype/group** — only the middle row (instance array data) varies per instance.
