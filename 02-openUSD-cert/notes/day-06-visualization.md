# Day 6 — Visualization

> **OpenUSD NCP Certification Study Notes**  
> _UsdGeomMesh, UsdGeomCamera, UsdShadeMaterial, Lights, Primvars, Visibility_

---

## Table of Contents

1. [UsdGeomImageable — Visibility and Purpose](#1-usdgeomimageable-visibility-and-purpose)
2. [UsdGeomMesh — Polygon Geometry](#2-usdgeommesh-polygon-geometry)
3. [Primvars — Per-Element Data](#3-primvars-per-element-data)
4. [UsdShadeMaterial and UsdShadeShader](#usdshadematerial-and-usdshadeshader)
5. [UsdPreviewSurface and the Texture Chain](#5-usdpreviewsurface-and-the-texture-chain)
6. [UsdLux — Lights](#6-usdlux-lights)
7. [UsdGeomCamera — Complete Reference](#7-usdgeomcamera-complete-reference)
8. [Key Takeaways](#8-key-takeaways)

---

## 1. UsdGeomImageable — Visibility and Purpose

`UsdGeomImageable` is the base class for **all renderable prims** in USD. It provides exactly two things — nothing more:

1. `visibility` — whether the prim is rendered
2. `purpose` — which rendering context the prim appears in

### Visibility

```python
from pxr import UsdGeom

imageable = UsdGeom.Imageable(prim)

# Make invisible
imageable.MakeInvisible()
# Sets visibility = "invisible" on this prim

# Make visible
imageable.MakeVisible()
# Sets visibility = "inherited" on this prim

# Compute resolved visibility (walks up hierarchy)
computed = imageable.ComputeVisibility()
# Returns "inherited" or "invisible"
# A parent set to invisible makes ALL children invisible
# regardless of their own visibility setting
```

> **Visibility inherits down the hierarchy.** If a parent prim is invisible, all its children are invisible even if they have `visibility = "inherited"`. `ComputeVisibility()` resolves this by walking up the prim hierarchy.

### Why Purpose Exists — The Real-World Problem

Imagine a hero robot character with 2 million polygons. Every time an animator scrubs the timeline, the viewport has to render 2 million polygons just to move the character slightly. It grinds to a halt.

The solution: the same character exists **three times** in the USD file, each version tagged with a different purpose:

```
/World/Robot
  ├── /World/Robot/HeroGeo      purpose = "render"   ← 2M polygons, full detail
  ├── /World/Robot/ProxyGeo     purpose = "proxy"    ← 500 polygon box
  └── /World/Robot/RigControls  purpose = "guide"    ← circles and arrows for animators
```

Each tool only loads what it needs:

```
usdview (viewport):        shows → proxy      fast lightweight stand-in
                           hides → render     too heavy for interactive use
                           hides → guide      rig controls not needed here

Final renderer:            shows → render     the real 2M polygon geometry
                           hides → proxy      don't render the low-res box
                           hides → guide      NEVER appears in a render

Rigging / animation tool:  shows → guide      the circles animators grab to pose
                           shows → proxy      so animators can see roughly where the robot is
                           hides → render     too heavy for the rig context
```

**One USD file. Three audiences. Zero duplication. No manual hiding.**

### What Is a Rigging Tool?

A **rigging tool** (Maya, Houdini, Blender) is the software used to build the control system that makes a character move. A raw mesh is just a static bag of polygons — rigging adds:

- A **skeleton** (joints/bones) inside the mesh
- **Control curves** (circles and arrows) that animators grab
- **Rules** connecting controls → joints → mesh deformation

The control curves are what get tagged `guide` purpose in USD. They exist purely so animators can pose the character — they have no visual meaning in a final rendered image and must **never** appear in a beauty render.

```
Animator grabs the circle (guide prim) → joint rotates → mesh deforms → arm lifts
         ↑ visible in rig tool                          ↑ visible in final render
         ↑ NEVER in final render                        ↑ NEVER in rig tool
```

### Purpose Tokens

| Purpose     | Who sees it                                    | Real-world example                                |
| ----------- | ---------------------------------------------- | ------------------------------------------------- |
| `"render"`  | Final render passes only                       | 2M polygon hero geometry                          |
| `"proxy"`   | Viewport / interactive tools                   | 500 polygon bounding box stand-in                 |
| `"guide"`   | Rigging / animation tools — **NEVER rendered** | IK control curves, joint display, helper geometry |
| `"default"` | All contexts (fallback)                        | Simple props with no heavy/light split needed     |

> **`guide` is the hardest to understand** — it is not about being "hidden" like visibility. It is about being in a completely separate rendering context that is never a final render. A prim can be `guide` purpose AND `visibility = inherited` — it is still never rendered. These are independent axes.

```python
imageable.GetPurposeAttr().Set(UsdGeom.Tokens.render)
imageable.GetPurposeAttr().Set(UsdGeom.Tokens.proxy)
imageable.GetPurposeAttr().Set(UsdGeom.Tokens.guide)
imageable.GetPurposeAttr().Set(UsdGeom.Tokens.default_)

# Compute resolved purpose (inherits from parents)
purpose = imageable.ComputePurpose()
```

### In usdview

usdview has **Purposes** toggle buttons in the toolbar — icons for render, proxy, and guide. Click the render button off and the 2M polygon geometry disappears, leaving only the proxy box. That is purpose working live. This is also why the `viz_visibility_and_purpose.py` exercise exports all four purpose tokens — open it in usdview and toggle each purpose button to see exactly which prims appear and disappear.

---

## 2. UsdGeomMesh — Polygon Geometry

`UsdGeomMesh` is the schema for polygonal geometry. Every 3D mesh in a USD scene is represented by three required attributes working together.

### The Three Required Attributes

**`points`** — the 3D positions of every vertex, in the prim's local coordinate space:

```usda
point3f[] points = [(0,0,0), (1,0,0), (1,1,0), (0,1,0)]
#                   corner 0  corner 1  corner 2  corner 3
```

**`faceVertexCounts`** — how many vertices each face has:

```usda
int[] faceVertexCounts = [4, 4, 3]
#                          ↑    ↑   ↑
#                         quad quad triangle  (3 faces)
```

**`faceVertexIndices`** — which vertices (by index into `points`) form each face, all faces concatenated:

```usda
int[] faceVertexIndices = [0,1,2,3,  4,5,6,7,  0,1,5]
#                          face 0    face 1     face 2
```

> **Critical:** `faceVertexIndices.length` = **SUM of faceVertexCounts**. Not the number of points. Not the number of faces.
>
> For the above: `4 + 4 + 3 = 11` — the indices array has 11 elements.

### Additional Mesh Attributes

| Attribute           | Type        | Description                                                          |
| ------------------- | ----------- | -------------------------------------------------------------------- |
| `subdivisionScheme` | `token`     | `"none"` (flat), `"catmullClark"` (smooth), `"loop"`, `"bilinear"`   |
| `holeIndices`       | `int[]`     | Face indices to treat as holes — geometry exists but is NOT rendered |
| `doubleSided`       | `bool`      | Whether to render back faces                                         |
| `extent`            | `float3[2]` | Axis-aligned bounding box — required for correct viewport display    |

### Python API

```python
from pxr import UsdGeom, Vt, Gf

stage = Usd.Stage.CreateInMemory()
mesh  = UsdGeom.Mesh.Define(stage, "/World/Chair")

# Set geometry
mesh.GetPointsAttr().Set(Vt.Vec3fArray([
    Gf.Vec3f(-1, 0, -1), Gf.Vec3f(1, 0, -1),
    Gf.Vec3f(1, 0, 1),   Gf.Vec3f(-1, 0, 1),
]))

mesh.GetFaceVertexCountsAttr().Set(Vt.IntArray([4]))
mesh.GetFaceVertexIndicesAttr().Set(Vt.IntArray([0, 1, 2, 3]))

# Subdivision
mesh.GetSubdivisionSchemeAttr().Set(UsdGeom.Tokens.catmullClark)

# Holes — face index 2 is a hole (exists in topology, not rendered)
mesh.GetHoleIndicesAttr().Set(Vt.IntArray([2]))

# Extent — required for viewport correctness
mesh.GetExtentAttr().Set(Vt.Vec3fArray([
    Gf.Vec3f(-1, 0, -1), Gf.Vec3f(1, 0, 1)
]))
```

### The extent Attribute — What It Is and Why You Must Update It

`extent` is the axis-aligned bounding box of the mesh — a pair of Vec3f values representing the minimum and maximum corners of the box that contains all vertices.

```text
extent = [min_corner, max_corner]
= [(x_min, y_min, z_min), (x_max, y_max, z_max)]

Example: a unit cube sitting on the origin
extent = [(-0.5, 0.0, -0.5), (0.5, 1.0, 0.5)]
```

**Why it exists:** USD renderers and viewport systems use `extent` for frustum culling — before doing any real work they check the bounding box to decide whether this prim is even visible to the camera. If the bounding box says the prim is outside the view, the renderer skips it entirely. This is a major performance optimisation for large scenes.

**Why you must update it manually:** USD does NOT recompute `extent` automatically when you change `points`. It is a cached value that you are responsible for keeping in sync. If you modify the geometry and forget to update `extent`, the renderer is working from a stale bounding box.

Consequence of stale extent:

- Prim disappears at the wrong camera angle (renderer thinks it is outside the frustum when it is not)
- Prim does not render at all in some renderers
- Viewport bounding box display is wrong
- BBoxCache queries return incorrect results

This is not a cosmetic issue — it breaks rendering.

**The exam rule:** Any time you modify `points`, updating `extent` is the next required step. They always go together.

```python
from pxr import Usd, UsdGeom, Vt, Gf

stage = Usd.Stage.CreateInMemory()
mesh  = UsdGeom.Mesh.Define(stage, "/World/Chair")

new_points = Vt.Vec3fArray([
    Gf.Vec3f(-1, 0, -1), Gf.Vec3f(1, 0, -1),
    Gf.Vec3f(1,  2, -1), Gf.Vec3f(-1, 2, -1),
    Gf.Vec3f(-1, 0,  1), Gf.Vec3f(1, 0,  1),
    Gf.Vec3f(1,  2,  1), Gf.Vec3f(-1, 2,  1),
])

# Step 1 — set the new points
mesh.GetPointsAttr().Set(new_points)

# Step 2 — recompute and update extent
# Method A: let USD compute it from the points array
extent = UsdGeom.PointBased(mesh).ComputeExtent(new_points)
# returns Vt.Vec3fArray([min_corner, max_corner])
mesh.GetExtentAttr().Set(extent)

# Method B: set manually if you know the exact bounds
mesh.GetExtentAttr().Set(Vt.Vec3fArray([
    Gf.Vec3f(-1, 0, -1),   # minimum corner
    Gf.Vec3f( 1, 2,  1),   # maximum corner
]))

# Method C: use BBoxCache for the whole stage (more expensive)
bbox_cache = UsdGeom.BBoxCache(
    Usd.TimeCode.Default(),
    includedPurposes=["default"]
)
world_bound = bbox_cache.ComputeWorldBound(mesh.GetPrim())
bbox_range  = world_bound.GetRange()
mesh.GetExtentAttr().Set(Vt.Vec3fArray([
    Gf.Vec3f(bbox_range.GetMin()),
    Gf.Vec3f(bbox_range.GetMax())
]))
```

**Method signatures:**

```python
# UsdGeom.PointBased.ComputeExtent(points) -> Vt.Vec3fArray
UsdGeom.PointBased(mesh).ComputeExtent(points_array)
# points_array: Vt.Vec3fArray
# returns:      Vt.Vec3fArray with two elements [min, max]

# UsdGeomMesh.GetExtentAttr() -> UsdAttribute
mesh.GetExtentAttr().Set(Vt.Vec3fArray([min_vec, max_vec]))
# value type: float3[2] — exactly two Vec3f values

# UsdGeom.BBoxCache(timeCode, includedPurposes)
bbox_cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ["default"])
# ComputeWorldBound(prim) -> UsdGeom.BBox3d
# .GetRange() -> Gf.Range3d
# .GetMin()   -> Gf.Vec3d
# .GetMax()   -> Gf.Vec3d
```

> **Do not confuse extent with normals.** Normals describe surface orientation for lighting. Extent describes the bounding box for culling. Both are additional mesh attributes but serve completely different purposes.

> **UVs are NEVER auto-generated.** UV coordinates must be explicitly authored as `primvars:st`. The exam specifically tests this.

---

## 3. Primvars — Per-Element Data

**Primvars** (Primitive Variables) are attributes in the `primvars:` namespace that carry per-element data — colours, UVs, normals — from geometry to shaders.

### Interpolation Modes

The `interpolation` metadata on a primvar determines how many values are needed and how they map to geometry:

| Interpolation | Values needed     | Maps to                                             |
| ------------- | ----------------- | --------------------------------------------------- |
| `constant`    | 1                 | Entire prim — one value for everything              |
| `uniform`     | 1 per face        | Each face has its own value                         |
| `vertex`      | 1 per point       | Each vertex has a value, interpolated across faces  |
| `faceVarying` | 1 per face-vertex | Most precise — one per entry in `faceVertexIndices` |

> **`faceVarying` is used for UVs** because the same 3D vertex can have different UV coordinates on different faces (at seams). `faceVarying` count = `faceVertexIndices.length` = sum of `faceVertexCounts`.

### Primvar Key Facts

- Primvars are **NOT** always uniform interpolation — they have four distinct modes
- Primvars are authored on specific prims — they do **not** need to be on the root prim
- Primvars with `constant` interpolation inherit down the hierarchy
- Primvars **do not have a built-in fallback value mechanism**
- Primvars **can** be time-sampled (animated UVs, animated colours)
- `"indexed"` is **not** an interpolation type — primvars can be indexed but interpolation and indexing are separate concepts

### Python API — `UsdGeom.PrimvarsAPI`

```python
from pxr import UsdGeom, Sdf, Vt, Gf

primvar_api = UsdGeom.PrimvarsAPI(mesh.GetPrim())

# Create a UV primvar (faceVarying — most common for UVs)
st = primvar_api.CreatePrimvar(
    "st",
    Sdf.ValueTypeNames.TexCoord2fArray,
    UsdGeom.Tokens.faceVarying
)
st.Set(Vt.Vec2fArray([
    Gf.Vec2f(0, 0), Gf.Vec2f(1, 0),
    Gf.Vec2f(1, 1), Gf.Vec2f(0, 1),
]))

# Create a displayColor primvar (constant — whole prim is red)
color = primvar_api.CreatePrimvar(
    "displayColor",
    Sdf.ValueTypeNames.Color3fArray,
    UsdGeom.Tokens.constant
)
color.Set(Vt.Vec3fArray([Gf.Vec3f(1.0, 0.0, 0.0)]))
```

---

<a id="usdshadematerial-and-usdshadeshader"></a>

## 4. UsdShadeMaterial and UsdShadeShader

### The Material Hierarchy

```
/World/Looks/WoodMat                ← UsdShadeMaterial (the CONTAINER)
  └── /World/Looks/WoodMat/Shader   ← UsdShadeShader (the computation node)
```

The **Material** is a container that exposes outputs to the renderer. The **Shader** nodes inside it do the actual shading computation. They connect via outputs.

### `inputs:` and `outputs:`

Every `UsdShadeShader` has:

- **`inputs:`** — parameters the shader **accepts** (colour, roughness, texture coordinates, etc.)
- **`outputs:`** — data the shader **produces** (the surface result, colour values, etc.)

```
geometry.primvars:st
        ↓
PrimvarReader.inputs:varname = "st"
PrimvarReader.outputs:result (float2)
        ↓
UVTexture.inputs:st ← connected from PrimvarReader.outputs:result
UVTexture.inputs:file = "./textures/wood.png"
UVTexture.outputs:rgb (color3f)
        ↓
PreviewSurface.inputs:diffuseColor ← connected from UVTexture.outputs:rgb
PreviewSurface.inputs:roughness = 0.5
PreviewSurface.outputs:surface (token)
        ↓
Material.outputs:surface ← connected from PreviewSurface.outputs:surface
```

> **Exam traps:**
>
> - `inputs:` and `outputs:` are **NOT deprecated** — they are fundamental to UsdShade
> - `inputs:` can hold any data type — not just textures
> - A Shader does NOT contain Materials — it's the reverse: Material contains Shaders
> - Shader parameters MUST be defined using `UsdShadeInput`/`UsdShadeOutput` objects — setting arbitrary attributes on a shader without them breaks schema compliance and prevents shading network connections
> - Texture file paths cannot be directly assigned on `UsdShadeMaterial` — textures must go through shader nodes (`UsdUVTexture`)

### Material-Level Inputs — External Parameterisation

A `UsdShadeMaterial` prim can expose `UsdShadeInput` objects at the **material level** — not just on the shader nodes inside it. This allows external systems to set parameters on the material without knowing its internal shader network.

```python
# Expose a parameter at the material level
mat = UsdShade.Material.Define(stage, "/Looks/WoodMat")

# UsdShadeInput on the MATERIAL PRIM — accepts external parameters
mat_color_input = mat.CreateInput(
    "baseColor", Sdf.ValueTypeNames.Color3f)
mat_color_input.Set(Gf.Vec3f(0.6, 0.4, 0.2))

# Connect material input → shader input
shader = UsdShade.Shader.Define(stage, "/Looks/WoodMat/Shader")
shader.CreateIdAttr("UsdPreviewSurface")
shader_diff = shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f)
shader_diff.ConnectToSource(mat_color_input)
# Now the material's baseColor drives the shader's diffuseColor
# External tools can set mat.GetInput("baseColor") without touching the shader
```

### Displacement Output

`UsdShadeMaterial` has **two surface-related outputs** — not just one:

```python
# Surface output — connects the main shading network
mat.CreateSurfaceOutput().ConnectToSource(surface_shader_out)

# Displacement output — connects displacement shaders
# Displacement shaders modify the geometry's surface POSITIONS during rendering
# (pushes vertices in/out based on a texture — creates real geometric detail)
mat.CreateDisplacementOutput().ConnectToSource(displacement_shader_out)
```

| Output                 | Purpose                                                           |
| ---------------------- | ----------------------------------------------------------------- |
| `outputs:surface`      | Main shading — colour, roughness, metallic, reflections           |
| `outputs:displacement` | Geometry modification — pushes surface positions during rendering |

> Displacement is distinct from normal maps — normal maps fake lighting, displacement actually moves geometry.

### Python API

```python
from pxr import UsdShade, Sdf

stage = Usd.Stage.CreateInMemory()

# Create the Material container
mat    = UsdShade.Material.Define(stage, "/World/Looks/WoodMat")

# Create the Shader node inside it
shader = UsdShade.Shader.Define(stage, "/World/Looks/WoodMat/Shader")
shader.CreateIdAttr("UsdPreviewSurface")

# Author inputs (parameters going IN)
shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f
).Set(Gf.Vec3f(0.6, 0.4, 0.2))
shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.5)

# Create the surface output (data coming OUT)
surf_out = shader.CreateOutput("surface", Sdf.ValueTypeNames.Token)

# Connect Material output → Shader output
mat.CreateSurfaceOutput().ConnectToSource(surf_out)

# Bind the material to a mesh
# MaterialBindingAPI must be Applied BEFORE Bind() is called
binding_api = UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim())
binding_api.Bind(mat)
```

### UsdGeomSubset — Per-Face Material Binding

**What it is:** `UsdGeomSubset` defines a named group of face indices on a mesh. It is a child prim of the mesh that holds a list of face indices and a material binding. The mesh itself remains one prim — the subsets are just views into subsets of its faces.

**Why it is needed:** Direct `MaterialBindingAPI.Bind()` applies one material to the entire mesh. In production, a single mesh often has multiple material zones — a car body has painted metal, rubber tyres, glass windows, chrome trim. Without GeomSubsets you would need to split every mesh into separate prims for each material zone, which is expensive and breaks artist workflows.

```text
Without GeomSubset:
/Car/Body     -> one material (wrong — body has paint, rubber, glass)
OR
/Car/Body/Paint   -> split into 4 separate prims
/Car/Body/Rubber
/Car/Body/Glass
/Car/Body/Chrome  <- more complex hierarchy, harder to rig/animate

With GeomSubset:
/Car/Body           -> one mesh, full topology intact
/Car/Body/Paint   -> subset, faces [0-120]   -> paint_mat
/Car/Body/Rubber  -> subset, faces [121-160] -> rubber_mat
/Car/Body/Glass   -> subset, faces [161-200] -> glass_mat
/Car/Body/Chrome  -> subset, faces [201-240] -> chrome_mat
```

**Method signatures:**

```python
# UsdGeom.Subset.Define(stage, path) -> UsdGeom.Subset
subset = UsdGeom.Subset.Define(stage, "/World/Mesh/ZoneName")

# CreateElementTypeAttr(value) -> UsdAttribute
# value must be UsdGeom.Tokens.face for material binding
subset.CreateElementTypeAttr(UsdGeom.Tokens.face)

# CreateIndicesAttr(value) -> UsdAttribute
# value: Vt.IntArray of face indices from the parent mesh
subset.CreateIndicesAttr(Vt.IntArray([0, 1, 2, 3]))

# UsdShade.MaterialBindingAPI.Apply(prim) -> MaterialBindingAPI
# Apply on the SUBSET prim, not the mesh
binding = UsdShade.MaterialBindingAPI.Apply(subset.GetPrim())
binding.Bind(material)
```

**Full example:**

```python
from pxr import Usd, UsdGeom, UsdShade, Vt, Gf, Sdf

stage = Usd.Stage.CreateInMemory()

# Define the mesh — 12 faces total
mesh = UsdGeom.Mesh.Define(stage, "/World/Chair/Body")
mesh.GetPointsAttr().Set(Vt.Vec3fArray([...]))
mesh.GetFaceVertexCountsAttr().Set(Vt.IntArray([4]*12))
mesh.GetFaceVertexIndicesAttr().Set(Vt.IntArray([...]))

# Define materials
fabric_mat = UsdShade.Material.Define(stage, "/Looks/Fabric")
metal_mat  = UsdShade.Material.Define(stage, "/Looks/Metal")
# ... (set up shader networks on each material)

# Subset 1 — seat cushion faces
fabric_subset = UsdGeom.Subset.Define(
    stage, "/World/Chair/Body/FabricZone"
)
fabric_subset.CreateElementTypeAttr(UsdGeom.Tokens.face)
fabric_subset.CreateIndicesAttr(Vt.IntArray([0,1,2,3,4,5,6,7]))
UsdShade.MaterialBindingAPI.Apply(
    fabric_subset.GetPrim()
).Bind(fabric_mat)

# Subset 2 — metal frame faces
metal_subset = UsdGeom.Subset.Define(
    stage, "/World/Chair/Body/MetalZone"
)
metal_subset.CreateElementTypeAttr(UsdGeom.Tokens.face)
metal_subset.CreateIndicesAttr(Vt.IntArray([8,9,10,11]))
UsdShade.MaterialBindingAPI.Apply(
    metal_subset.GetPrim()
).Bind(metal_mat)
```

**Key rules:**

- `elementType` must be `UsdGeom.Tokens.face` — material binding only works on face subsets
- The subset prim must be a **direct child** of the mesh prim
- Face indices refer to the order of faces in `faceVertexCounts` — face 0 is the first entry, face 1 is the second, and so on
- A face can only belong to one material subset — overlapping indices cause undefined behaviour
- `MaterialBindingAPI` is applied on the **subset prim** not the mesh prim

### Collection-Based Material Binding

**What it is:** Collection-based binding uses `Usd.CollectionAPI` to define a named set of prims from anywhere in the scene hierarchy and then binds a material to that collection in one operation. The collection is defined on a single root prim but can include targets from any path in the stage.

**Why it is needed:** Direct binding and GeomSubset binding only affect one prim at a time. In a large scene, dozens of prims may need the same material — every metal bolt, every glass panel, every rubber seal scattered across hundreds of assets. Updating them one by one is expensive and error-prone. Collection binding lets you declare the group once and bind once.

```text
Direct binding:                      Collection binding:
/Building/Floor/Tile_001.Bind()      collection "marble_surfaces" includes:
/Building/Floor/Tile_002.Bind()        /Building/Floor/Tile_001
/Building/Floor/Tile_003.Bind()        /Building/Floor/Tile_002
... 500 more calls                     /Building/Floor/Tile_003
... 500 more entries
root.Bind(marble_mat, "marble_surfaces")
<- one bind call covers all 500
```

**When to use it:**

- Many prims scattered across the hierarchy share one material
- You want to manage material assignments at the scene level rather than per-asset
- Assets are instanced — you cannot bind on each instance directly

**Method signatures:**

```python
# Usd.CollectionAPI.Apply(prim, collectionName) -> CollectionAPI
# Apply to any prim that will own the collection definition
collection = Usd.CollectionAPI.Apply(root_prim, "collection_name")

# CreateIncludesRel() -> UsdRelationship
# Add target paths to include in the collection
collection.CreateIncludesRel().AddTarget(Sdf.Path("/World/Chair/Legs"))

# CreateExcludesRel() -> UsdRelationship
# Optionally exclude specific paths from an include-all collection
collection.CreateExcludesRel().AddTarget(Sdf.Path("/World/Chair/Legs/LeftFront"))

# UsdShade.MaterialBindingAPI.Bind(material, strength, collectionName)
# strength: UsdShade.Tokens.strongerThanDescendants
#           UsdShade.Tokens.weakerThanDescendants
binding_api.Bind(
    material,
    UsdShade.Tokens.strongerThanDescendants,
    "collection_name"
)
```

**Full example:**

```python
from pxr import Usd, UsdShade, Sdf

stage = Usd.Stage.Open("building.usda")

root      = stage.GetPrimAtPath("/Building")
metal_mat = UsdShade.Material.Get(stage, "/Looks/Metal")

# Define a collection called "structural_metal"
# that includes all metal structural prims
collection = Usd.CollectionAPI.Apply(root, "structural_metal")
includes   = collection.CreateIncludesRel()
includes.AddTarget(Sdf.Path("/Building/Floor_01/Beams"))
includes.AddTarget(Sdf.Path("/Building/Floor_02/Beams"))
includes.AddTarget(Sdf.Path("/Building/Facade/Frame"))
includes.AddTarget(Sdf.Path("/Building/Roof/Trusses"))

# Bind the material to the whole collection in one call
binding_api = UsdShade.MaterialBindingAPI.Apply(root)
binding_api.Bind(
    metal_mat,
    UsdShade.Tokens.strongerThanDescendants,
    "structural_metal"
)
# All four paths now use metal_mat
# If new paths are added to the collection later,
# they automatically inherit the binding
```

**The three-tier binding summary:**

| Tier       | Mechanism                                     | Scope                             | Best for                                        |
| ---------- | --------------------------------------------- | --------------------------------- | ----------------------------------------------- |
| Direct     | `MaterialBindingAPI.Bind(mat)`                | One prim                          | Simple single-material assets                   |
| GeomSubset | `MaterialBindingAPI.Bind(mat)` on subset      | Face group within one mesh        | Multi-material single mesh                      |
| Collection | `CollectionAPI` + `Bind(mat, strength, name)` | Any set of prims across hierarchy | Large scenes, scattered prims, instanced assets |

---

## 5. UsdPreviewSurface and the Texture Chain

`UsdPreviewSurface` is the standard physically-based shader built into USD. It works in all USD-compliant renderers.

### Key Inputs

| Input           | Type       | Description                             |
| --------------- | ---------- | --------------------------------------- |
| `diffuseColor`  | `color3f`  | Base surface colour                     |
| `roughness`     | `float`    | 0 = mirror smooth, 1 = completely rough |
| `metallic`      | `float`    | 0 = dielectric, 1 = full metal          |
| `opacity`       | `float`    | 1 = opaque, 0 = transparent             |
| `normal`        | `normal3f` | Normal map (tangent space)              |
| `emissiveColor` | `color3f`  | Self-illumination colour                |

### Reading a Texture — Three-Node Chain

```python
# Node 1 — UsdPrimvarReader_float2
# Reads the UV primvar (primvars:st) from the mesh geometry
reader = UsdShade.Shader.Define(stage, "/Looks/Mat/Reader")
reader.CreateIdAttr("UsdPrimvarReader_float2")
reader.CreateInput("varname", Sdf.ValueTypeNames.Token).Set("st")
# "st" — NOT "primvars:st" — the primvars: prefix is OMITTED in varname
reader_out = reader.CreateOutput("result", Sdf.ValueTypeNames.Float2)

# Node 2 — UsdUVTexture
# Samples an image texture using the UV coordinates
tex = UsdShade.Shader.Define(stage, "/Looks/Mat/Texture")
tex.CreateIdAttr("UsdUVTexture")
tex.CreateInput("file", Sdf.ValueTypeNames.Asset).Set("./wood.png")
tex_st = tex.CreateInput("st", Sdf.ValueTypeNames.Float2)
tex_st.ConnectToSource(reader_out)     # connect UV from reader
tex_rgb = tex.CreateOutput("rgb", Sdf.ValueTypeNames.Float3)

# Node 3 — UsdPreviewSurface
# Uses the texture colour as diffuseColor
surface = UsdShade.Shader.Define(stage, "/Looks/Mat/Surface")
surface.CreateIdAttr("UsdPreviewSurface")
diff_in = surface.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f)
diff_in.ConnectToSource(tex_rgb)       # connect texture to diffuseColor
surf_out = surface.CreateOutput("surface", Sdf.ValueTypeNames.Token)

# Wire Material
mat.CreateSurfaceOutput().ConnectToSource(surf_out)
```

---

## 6. UsdLux — Lights

All UsdLux lights inherit from `UsdGeomXformable` — they are **transformable and animatable** like any other prim.

### Common Attributes Across All Lights

| Attribute          | Type      | Description                                                                                                               |
| ------------------ | --------- | ------------------------------------------------------------------------------------------------------------------------- |
| `intensity`        | `float`   | Brightness — measured in **candela (cd)** or **watts per steradian** depending on light type. **NOT lumens.**             |
| `exposure`         | `float`   | Exponential brightness scaling in photographic stops: `final = intensity × 2^exposure`. Each unit **doubles** brightness. |
| `color`            | `color3f` | Spectral colour tint of emitted light — directly affects hue in rendered scene                                            |
| `colorTemperature` | `float`   | Colour temperature in Kelvin (e.g. 6500K = daylight, 3200K = tungsten)                                                    |
| `falloffRadius`    | `float`   | Maximum distance the light affects — geometry beyond this radius receives no contribution                                 |
| `enableShadows`    | `bool`    | **Explicitly toggles shadow casting on/off** — False by default on some renderers                                         |

> **`intensity` units — common exam trap:** The notes previously said "lumens" — this is WRONG.  
> `intensity` = **candela (cd)** or **watts per steradian** (radiant intensity), not lumens (luminous flux).  
> Lumens measure total light output in all directions. Candela measures intensity in a specific direction.

> **`falloffRadius` limits the light's effective range** — geometry beyond this radius receives no contribution. Used to optimise rendering by culling distant light calculations.

### Shadows Are NOT Automatic

Shadow casting requires **explicit configuration**. Use `enableShadows = true` to enable shadows on a specific light:

```python
# Shadows are NOT on by default — must explicitly enable
light = UsdLux.SphereLight.Define(stage, "/World/Key")
light.CreateIntensityAttr(500.0)

# Enable shadows via the shadow API
shadow_api = UsdLux.ShadowAPI.Apply(light.GetPrim())
shadow_api.CreateShadowEnableAttr(True)
# OR set directly:
light.GetPrim().CreateAttribute(
    "inputs:enableShadows", Sdf.ValueTypeNames.Bool
).Set(True)
```

### Volumetric Scattering is NOT Inherent

UsdLux lights do **not** automatically produce volumetric scattering (fog, god rays, participating media). This requires additional volumetric shaders or render-specific settings. This appears as a distractor on the exam — eliminate any option claiming UsdLux lights "inherently support" or "automatically simulate" volumetric effects.

### Light Types

| Schema               | Analogy               | Key attribute                                 |
| -------------------- | --------------------- | --------------------------------------------- |
| `UsdLuxDistantLight` | Directional sun       | `angle` (angular size of sun disk)            |
| `UsdLuxSphereLight`  | Point light with size | `radius` — controls shadow softness           |
| `UsdLuxRectLight`    | Studio softbox        | `width`, `height`                             |
| `UsdLuxDomeLight`    | HDRI environment      | `textureFile` (path to .exr/.hdr)             |
| `UsdLuxConeLight`    | Spotlight             | `shaping:cone:angle`, `shaping:cone:softness` |

### SphereLight Radius — Critical Exam Topic

`radius` on `UsdLuxSphereLight` controls the **angular spread and shadow softness** — NOT brightness.

```
Small radius → small light source → hard sharp shadows
Large radius → large light source → soft diffuse shadows

intensity  = brightness (lumens)
exposure   = brightness adjustment in photographic stops
radius     = shadow softness and light spread (SphereLight only)
color      = colour tint of emitted light
```

---

## 7. UsdGeomCamera — Complete Reference

`UsdGeomCamera` represents a camera in USD. It is **Xformable** — positioned, rotated, and animated using xformOp transforms. Animation requires **explicit time samples** — no auto-update.

### Projection Types — ONLY Two

```python
camera.GetProjectionAttr().Set(UsdGeom.Tokens.perspective)
camera.GetProjectionAttr().Set(UsdGeom.Tokens.orthographic)
# No fisheye, cylindrical, or spherical — only these two exist
```

| Projection     | Behaviour                             | Use case                           |
| -------------- | ------------------------------------- | ---------------------------------- |
| `perspective`  | Objects farther away appear smaller   | Film, games, visualisation         |
| `orthographic` | All objects same size at any distance | CAD, technical drawings, isometric |

### Complete Attribute Reference

| Attribute                  | Type     | Default         | Description                                     |
| -------------------------- | -------- | --------------- | ----------------------------------------------- |
| `projection`               | `token`  | `"perspective"` | Only `perspective` or `orthographic`            |
| `focalLength`              | `float`  | `50.0 mm`       | Lens-to-image-plane distance. Controls FOV.     |
| `horizontalAperture`       | `float`  | `20.955 mm`     | Sensor width **in millimetres** (NOT inches)    |
| `verticalAperture`         | `float`  | `15.291 mm`     | Sensor height in millimetres                    |
| `horizontalApertureOffset` | `float`  | `0.0`           | Horizontal lens shift (tilt-shift effect)       |
| `verticalApertureOffset`   | `float`  | `0.0`           | Vertical lens shift                             |
| `clippingRange`            | `float2` | `(1, 1000000)`  | Near and far clip planes **— IS in the schema** |
| `fStop`                    | `float`  | `0.0`           | Aperture f-number — controls depth of field     |
| `focusDistance`            | `float`  | `0.0`           | Distance to in-focus plane                      |

### Focal Length and Field of View

Focal length and aperture work **together** to determine field of view:

```
FOV = 2 × atan(horizontalAperture / (2 × focalLength))

18mm focal length + 24mm sensor → wide angle ~67° FOV
85mm focal length + 24mm sensor → telephoto ~16° FOV
```

### Python API

```python
from pxr import UsdGeom, Gf

camera = UsdGeom.Camera.Define(stage, "/World/MainCamera")

# Position using xformOp (camera is Xformable)
UsdGeom.XformCommonAPI(camera).SetTranslate(Gf.Vec3d(0, 5, 20))
UsdGeom.XformCommonAPI(camera).SetRotate(Gf.Vec3f(-15, 0, 0))

# Lens properties
camera.GetProjectionAttr().Set(UsdGeom.Tokens.perspective)
camera.GetFocalLengthAttr().Set(35.0)
camera.GetHorizontalApertureAttr().Set(24.0)    # mm, not inches
camera.GetVerticalApertureAttr().Set(13.5)      # 16:9 aspect ratio

# Clipping (IS in the schema — not handled externally)
camera.GetClippingRangeAttr().Set(Gf.Vec2f(0.1, 10000))

# Depth of field
camera.GetFocusDistanceAttr().Set(8.0)   # focus at 8 units
camera.GetFStopAttr().Set(2.8)           # shallow DOF

# Animate the camera — EXPLICIT time samples required
UsdGeom.XformCommonAPI(camera).SetTranslate(Gf.Vec3d(0, 5, 20), time=1)
UsdGeom.XformCommonAPI(camera).SetTranslate(Gf.Vec3d(10, 5, 15), time=48)
```

### Exam Traps

| Wrong statement                                       | Correct fact                                |
| ----------------------------------------------------- | ------------------------------------------- |
| "Sensor size is in inches"                            | Sensor size is in **millimetres**           |
| "clippingRange is handled externally by the renderer" | `clippingRange` IS in the schema            |
| "fStop controls exposure time"                        | `fStop` controls **depth of field** only    |
| "Camera auto-updates from animation clips"            | Requires **explicit time samples**          |
| "Only perspective is supported"                       | Both **perspective and orthographic** exist |

---

## 8. Key Takeaways

| Concept                          | What to Remember                                                                                |
| -------------------------------- | ----------------------------------------------------------------------------------------------- |
| **UsdGeomImageable**             | Base class for all renderable prims. Provides visibility and purpose ONLY.                      |
| **Purpose tokens**               | render, proxy, guide, default. Guide = NEVER rendered.                                          |
| **Visibility inheritance**       | Parent invisible → all children invisible, regardless of their own setting                      |
| **faceVertexIndices length**     | = SUM of faceVertexCounts. Not point count. Not face count.                                     |
| **holeIndices**                  | Marks faces as holes — exist in topology, NOT rendered                                          |
| **UVs not auto-generated**       | Must author `primvars:st` explicitly                                                            |
| **Primvar interpolation**        | constant, uniform, vertex, faceVarying. NOT "indexed".                                          |
| **inputs: and outputs:**         | NOT deprecated. inputs = data IN. outputs = data OUT. Any type.                                 |
| **MaterialBindingAPI**           | Must `Apply()` before `Bind()` — both steps required                                            |
| **`outputs:displacement`**       | Second material output — connects displacement shaders that move geometry positions             |
| **Material-level inputs**        | `UsdShadeInput` on the Material prim exposes external parameters — not just on shaders          |
| **Arbitrary attrs on shader**    | ❌ Wrong — shader params MUST use `UsdShadeInput`/`UsdShadeOutput` objects                      |
| **Texture on Material directly** | ❌ Wrong — textures go through shader nodes (`UsdUVTexture`), not on Material prim              |
| **`intensity` units**            | **Candela (cd) or watts per steradian** — NOT lumens. This is a direct exam trap.               |
| **`exposure`**                   | Exponential scaling — each unit **doubles** brightness. `final = intensity × 2^exposure`        |
| **`enableShadows`**              | Boolean attribute to explicitly toggle shadow casting. NOT automatic.                           |
| **`colorTemperature`**           | Kelvin colour temperature attribute on lights                                                   |
| **falloffRadius**                | Controls max light range. NOT brightness.                                                       |
| **SphereLight radius**           | Controls shadow softness and spread. NOT brightness.                                            |
| **Shadows not automatic**        | Requires `enableShadows = true` — not on by default                                             |
| **Volumetric scattering**        | NOT inherent to UsdLux — requires additional volumetric shaders. Always a wrong answer on exam. |
| **Camera projections**           | Only `perspective` and `orthographic`. No others.                                               |
| **Sensor size**                  | Always in millimetres. Never inches.                                                            |
| **clippingRange**                | IS in UsdGeomCamera schema. NOT handled externally.                                             |
| **fStop**                        | Controls depth of field only. NOT exposure time.                                                |

---

_Previous: [Day 5 — Schemas and Data Modeling](day-05-schemas-and-data-modeling.md)_  
_Next: [Day 7 — Pipeline Development and Data Exchange](day-07-pipeline-and-data-exchange.md)_
