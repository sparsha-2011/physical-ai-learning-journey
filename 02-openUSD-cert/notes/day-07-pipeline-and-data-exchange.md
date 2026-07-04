# Day 7 — Pipeline Development and Data Exchange

> **OpenUSD NCP Certification Study Notes**  
> _File Formats, Exporters, Importers, Validators, Data Exchange, Pipeline Tools_

---

## Table of Contents

1. [USD File Format Trade-offs](#1-usd-file-format-trade-offs)
2. [Command-Line Tools](#2-command-line-tools)
3. [Stage Traversal](#3-stage-traversal)
4. [Writing a USD Exporter](#4-writing-a-usd-exporter)
5. [Asset Validators — usdchecker](#5-asset-validators--usdchecker)
6. [Exporter Hooks — Pre/Post Export](#6-exporter-hooks--prepost-export)
7. [Removing Proprietary Dependencies](#7-removing-proprietary-dependencies)
8. [Pipeline Documentation Standards](#8-pipeline-documentation-standards)
9. [UI/UX Principles for USD Pipelines](#9-uiux-principles-for-usd-pipelines)
10. [Build Configuration Management](#10-build-configuration-management)
11. [Conceptual Data Mapping Documents](#11-conceptual-data-mapping-documents)
12. [Custom Exporter and Importers](#12-custom-exporters-and-importers)
13. [Data Interchange Script Best Practices](#13-data-interchange-script-best-practices)
14. [Key Takeaways](#14-key-takeaways)

---

## 1. USD File Format Trade-offs

| Extension | Format        | Readable | Speed     | Self-contained | Best for                                       |
| --------- | ------------- | -------- | --------- | -------------- | ---------------------------------------------- |
| `.usda`   | ASCII text    | ✅ Yes   | Slow      | ❌ No          | Authoring, debugging, version control          |
| `.usdc`   | Binary crate  | ❌ No    | Very fast | ❌ No          | Production pipelines, large data               |
| `.usd`    | Auto-detected | Depends  | Depends   | ❌ No          | Generic — USD reads header to determine format |
| `.usdz`   | Zip archive   | ❌ No    | Fast      | ✅ Yes         | External delivery, AR/VR distribution          |

### Renaming Rules

Renaming `.usda` → `.usd` is **valid** — USD detects ASCII content from the file header.  
Renaming `.usda` → `.usdc` is **invalid** — these have completely different internal binary formats.

---

## 2. Command-Line Tools

### `usdcat` — Format Conversion and Inspection

```bash
# Convert ASCII to binary
usdcat scene.usda -o scene.usdc

# Flatten ALL composition into a single file
usdcat --flatten scene.usda -o flat.usda

# Print composition arc graph for all prims
usdcat --print-composition scene.usda
```

### `usdzip` — Package .usdz Archives

```bash
# Package a USD file and ALL its dependencies into .usdz
usdzip -r delivery.usdz scene.usda

# List contents without extracting
usdzip -l delivery.usdz
```

> `usdcat` handles format conversion and flattening. `usdzip` handles `.usdz` packaging. These are separate tools for separate purposes.

### `usdchecker` — Asset Validation

```bash
# Validate a USD file against best practices
usdchecker scene.usda

# Validate a .usdz package
usdchecker delivery.usdz
```

`usdchecker` **validates** — it does NOT automatically fix issues.

### `usddiff` — Compare Two USD Files

```bash
usddiff scene_v1.usda scene_v2.usda
```

---

## 3. Stage Traversal

`stage.Traverse()` visits all prims in the scene graph in depth-first order. Predicates filter the traversal.

```python
from pxr import Usd, UsdGeom

stage = Usd.Stage.Open("scene.usda")

# Traverse ALL active, defined prims
for prim in stage.Traverse():
    print(prim.GetPath(), prim.GetTypeName())

# Traverse only loaded prims (excludes unloaded payloads)
predicate = Usd.TraverseInstanceProxies(
    Usd.PrimIsActive & Usd.PrimIsDefined & Usd.PrimIsLoaded
)
for prim in stage.TraverseAll():
    if predicate(prim):
        print(prim.GetPath())

# Find all meshes
for prim in stage.Traverse():
    if prim.IsA(UsdGeom.Mesh):
        mesh = UsdGeom.Mesh(prim)
        print(f"Mesh found: {prim.GetPath()}")
```

---

## 4. Writing a USD Exporter

A USD exporter translates data from a proprietary format into USD scene description. The correct approach uses the USD API — never hand-writes ASCII.

### Exporter Pattern

```python
from pxr import Usd, UsdGeom, UsdShade, Sdf, Vt, Gf

def export_scene(source_data: dict, output_path: str):
    # 1. Create the stage
    stage = Usd.Stage.CreateNew(output_path)

    # 2. Set stage metadata — always set these
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 0.01)
    stage.SetMetadata("timeCodesPerSecond", 24)

    # 3. Create root prim and set as defaultPrim
    root = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(root.GetPrim())

    # 4. Export geometry using USD API (not hand-written ASCII)
    for mesh_data in source_data["meshes"]:
        mesh = UsdGeom.Mesh.Define(stage, f"/World/{mesh_data['name']}")
        mesh.GetPointsAttr().Set(Vt.Vec3fArray(mesh_data["points"]))
        mesh.GetFaceVertexCountsAttr().Set(Vt.IntArray(mesh_data["face_counts"]))
        mesh.GetFaceVertexIndicesAttr().Set(Vt.IntArray(mesh_data["indices"]))

    # 5. Export animation using time samples
    for frame, transform in source_data["animation"].items():
        prim.GetAttribute("xformOp:translate").Set(
            Gf.Vec3d(*transform), time=frame
        )

    # 6. Save
    stage.Save()
```

### Key Exporter Rules

| ✅ Do                                                   | ❌ Don't                              |
| ------------------------------------------------------- | ------------------------------------- |
| Use USD Python API to create UsdPrims with schemas      | Write raw USD ASCII by hand           |
| Use relative paths for all references                   | Use absolute paths                    |
| Set `defaultPrim` on the root prim                      | Leave `defaultPrim` unset             |
| Use time samples for animated data                      | Use only default values for animation |
| Use registered schemas or metadata for proprietary data | Embed unregistered string blobs       |
| Use USD's layering model                                | Flatten everything into one file      |

---

## 5. Asset Validators — usdchecker

`usdchecker` validates a USD file or package against a defined set of rules designed to ensure the asset is **interoperable and renderable** by downstream tools.

Common things `usdchecker` validates:

- `defaultPrim` is set
- All meshes have an `extent` attribute
- All material bindings resolve to valid prims
- Referenced files exist and are accessible
- Schema version compatibility
- `.usdz` package completeness

```python
# Programmatic validation using UsdUtils
from pxr import UsdUtils

errors = UsdUtils.ComplianceChecker.GetErrors(stage)
for error in errors:
    print(error)
```

> `usdchecker` validates but does NOT auto-fix. It is used as a pre-delivery QA tool, not a repair tool.

---

## 6. Exporter Hooks — Pre/Post Export

### The Problem

Your studio has a Maya-to-USD exporter built and maintained by the pipeline team. It handles geometry, materials, lights, and cameras. Every department depends on it.

Your department needs to add custom behaviour on top — tagging exported meshes with a `pipeline:assetId`, running `usdchecker` automatically, registering the exported file in an asset database. You have two options:

```
Option A — Modify the core exporter directly
  Open the pipeline team's exporter source code
  Add your custom logic inside it
  → Your version now diverges from the maintained version
  → Pipeline team releases a bug fix → you have to merge manually
  → Your change runs for every department's export → risk of breaking FX, lighting etc.
  → Hard to roll back if something breaks in production

Option B — Use hooks
  The exporter provides designated extension points
  You register your function into those points
  → Core exporter is never touched
  → Pipeline team updates their exporter → your hooks still work automatically
  → Your hook only runs when you register it → other departments unaffected
  → Remove your hook in one line if something breaks
```

Hooks exist so you can always do Option B.

### What a Hook Actually Is

A hook is a **variable that holds a function**. By default it holds an empty do-nothing function — a lambda that takes arguments and immediately returns nothing. The exporter calls whatever is stored in that variable at a designated moment in the workflow.

In Python, functions are first-class objects — they can be assigned to variables just like any other value:

```python
# Assign a function to a variable — no () because you are not calling it
# you are pointing the variable at the function object
def my_function(x):
    print(x)

hook = my_function   # hook now holds the function
hook("hello")        # calls my_function("hello") → prints "hello"

# Reassign it to a different function
hook = lambda x: None   # now hook does nothing
hook("hello")            # nothing happens
```

This is the entire mechanism. No inheritance. No class system. Just a variable holding a callable.

### Inside the Core Exporter

This is what the core exporter looks like internally — you never see or modify this:

```python
# Core exporter — owned by pipeline team, never touched by you

# Default hooks — empty lambdas that do nothing
pre_export_hook  = lambda stage, options: None
post_export_hook = lambda stage, path:    None

def run_export(maya_scene, output_path, options):
    stage = create_usd_stage()

    pre_export_hook(stage, options)    # calls whatever is in this variable
                                       # default = does nothing

    export_geometry(maya_scene, stage)
    export_materials(maya_scene, stage)
    export_lights(maya_scene, stage)
    stage.Export(output_path)

    post_export_hook(stage, output_path)  # calls whatever is in this variable
                                           # default = does nothing
```

When nobody has registered a hook, the exporter calls the empty lambda — the export runs exactly as if the hook call was not there at all.

### How You Use It

You define your own functions and reassign the hook variables. Your code lives entirely in your department's repo — completely separate from the core exporter:

```python
# YOUR code — your department's repo, not the core exporter

# Pre-export hook — runs BEFORE the core export starts
def my_pre_hook(stage, options):
    # Set pipeline metadata on the stage before export
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    stage.GetRootLayer().customLayerData = {
        "pipeline:schemaVersion": "2.0",
        "pipeline:studio":        "AcmeStudios",
        "pipeline:assetId":       options["assetId"],
    }
    # Validate required data is present before export runs
    if not options.get("assetId"):
        raise ValueError("assetId must be set before exporting")

# Post-export hook — runs AFTER the core export completes
def my_post_hook(stage, output_path):
    # Add pipeline attributes to every exported mesh
    for prim in stage.Traverse():
        if prim.IsA(UsdGeom.Mesh):
            prim.CreateAttribute(
                "pipeline:exportVersion",
                Sdf.ValueTypeNames.String
            ).Set("2.0")
    # Run usdchecker automatically
    errors = UsdUtils.ComplianceChecker.GetErrors(stage)
    if errors:
        raise RuntimeError(f"Export validation failed: {errors}")
    # Register in asset database
    asset_db.register(output_path, {"department": "modeling"})

# Reassign the hook variables — your function replaces the empty lambda
exporter.pre_export_hook  = my_pre_hook
exporter.post_export_hook = my_post_hook

# Run the export — your hooks fire automatically at the right moments
exporter.run_export(maya_scene, "/output/chair_v003.usda", options)
```

### Pre-Export Hook — runs BEFORE the core export starts

- Set stage metadata (`upAxis`, `metersPerUnit`, pipeline version)
- Validate that required data is present — fail early before any work is done
- Configure export settings based on the environment (render farm vs artist machine)
- Set the edit target to the correct layer before authoring begins
- Tag the root layer with `customLayerData` (studio name, schema version, export tool)

### Post-Export Hook — runs AFTER the core export completes

- Add pipeline-specific attributes to exported prims (asset IDs, department tags)
- Run `usdchecker` automatically — catch problems before delivery
- Register the exported file path in an asset management database
- Send a notification to downstream departments that a new version is available
- Write export logs or audit trails for pipeline tracking
- Validate that the output matches what was expected (prim count, file size checks)

> **Rule of thumb:** pre-export = set up and validate inputs. Post-export = verify and record outputs.

### What Happens Step by Step

```
1. exporter.pre_export_hook  = my_pre_hook
   → variable now holds your function instead of the empty lambda

2. exporter.run_export() is called

3. Core exporter calls pre_export_hook(stage, options)
   → your my_pre_hook runs
   → metadata written, validation passes

4. Core export logic runs unchanged
   → geometry, materials, lights exported normally

5. Core exporter calls post_export_hook(stage, output_path)
   → your my_post_hook runs
   → pipeline attributes added, usdchecker runs, asset registered

6. Export complete
```

The core exporter code did not change at all. Only the values stored in those two variables changed.

### Multiple Departments — List of Hooks

Real exporters store a **list** of functions so multiple departments can each register their own hook without overwriting each other:

```python
# Inside the core exporter
pre_export_hooks = []   # empty list by default

def run_export(maya_scene, output_path, options):
    stage = create_usd_stage()

    for hook in pre_export_hooks:   # calls every registered hook in order
        hook(stage, options)

    # core export...

# Modeling department registers their hook
pre_export_hooks.append(modeling_pre_hook)

# FX department registers their hook independently
pre_export_hooks.append(fx_pre_hook)

# Both run in order — neither overwrites the other
```

### How Hooks Solve Each Problem

| Problem without hooks                 | How hooks solve it                                                                |
| ------------------------------------- | --------------------------------------------------------------------------------- |
| Change affects every department       | Hook only runs when you register it — other departments unaffected                |
| Fork diverges from maintained version | Core exporter updates automatically — your hook file is untouched                 |
| Hard to roll back if something breaks | Unregister your hook in one line — export runs as before                          |
| Unclear ownership                     | One exporter owned by pipeline team — your additions are your responsibility only |

### Wrong Approaches

| Wrong                                               | Why                                                        |
| --------------------------------------------------- | ---------------------------------------------------------- |
| Override the main export function                   | You now own all the core logic — must maintain it forever  |
| Modify USD files on disk after export               | Bypasses pipeline control, error-prone, risk of corruption |
| Create a separate generator for custom requirements | Duplicates effort, breaks pipeline consistency             |

### When to Use Hooks

```
Use hooks when:
  Adding pipeline metadata to every exported asset
  Running usdchecker automatically after every export
  Registering assets in a pipeline database
  Applying custom schema attributes post-export
  Setting environment-specific stage configuration pre-export

Not needed for:
  One-off manual exports with no pipeline integration
  Simple test exports where the core exporter handles everything
```

---

## 7. Removing Proprietary Dependencies

Proprietary shaders, file formats, SDKs, and APIs in USD assets create **vendor lock-in** — assets can only be used in tools that support that specific proprietary technology. Removing these dependencies makes pipelines portable, maintainable, and future-proof.

### The Five Correct Strategies

**1. Replace proprietary shaders with USD-native shaders**

Refactor proprietary renderer-specific shaders into UsdPreviewSurface or MaterialX — both are open standards readable by any USD-compliant renderer.

```
Before (proprietary — Arnold only):           After (USD native — any renderer):
def Shader "Mat" {                            def Shader "Mat" {
    token info:id = "ArnoldStandardSurface"       token info:id = "UsdPreviewSurface"
    float inputs:base = 0.8                       color3f inputs:diffuseColor = (0.8,0.8,0.8)
}                                                 float inputs:roughness = 0.3
                                              }
```

**2. Replace proprietary file formats with USD-native formats**

Convert `.abc`, `.fbx`, `.obj` and other proprietary interchange formats to `.usda`, `.usdc`, or `.usdz`. Native USD formats have no external format dependency — any USD tool reads them directly.

**3. Use open-source plugins instead of proprietary SDKs**

Replace vendor-specific SDKs (e.g., a proprietary mesh processing library) with open-source USD plugins or standard USD APIs. Open-source plugins are auditable, portable, and community-maintained.

```
Proprietary SDK:   import VendorMeshSDK        # vendor lock-in
USD native:        from pxr import UsdGeom     # open standard
```

**4. Implement custom USD schemas instead of proprietary extensions**

When your pipeline needs new data types, build custom schemas adhering to the **USD specification** (via `usdGenSchema`) instead of creating proprietary extensions. Custom USD schemas are portable to any tool that loads the schema plugin — proprietary extensions are not.

```
Proprietary extension:  custom:vendor:property = ...  # only works with vendor tool
Custom USD schema:      sensor:temperature = 20.0     # works anywhere with schema plugin
```

**5. Convert proprietary animation data into USD animation schemas**

Animation stored in proprietary rigs, custom joint formats, or vendor-specific motion formats should be converted to USD's open animation schemas — `UsdSkel` for skeletal animation, time-sampled `xformOp` attributes for transform animation. This removes dependency on the source DCC tool for playback.

```python
# Convert proprietary animation → USD time samples
for frame, transform in proprietary_animation.items():
    prim.GetAttribute("xformOp:translate").Set(
        Gf.Vec3d(*transform), time=frame
    )
# Now any USD tool can play back the animation with no proprietary dependency
```

### Wrong Approaches

| Wrong approach                                     | Why it's wrong                                                    |
| -------------------------------------------------- | ----------------------------------------------------------------- |
| Embed proprietary shaders directly into USD files  | Increases lock-in — assets now require that renderer specifically |
| Reference proprietary files without converting     | The dependency still exists — just deferred to load time          |
| Use vendor-specific APIs for USD stage composition | Introduces proprietary dependency at the processing level         |
| Encapsulate without converting                     | Long-term maintenance problem — dependency still present inside   |
| Replace USD with proprietary formats               | Increases dependency, defeats the purpose of using USD            |

### What This Looks Like in a Real Pipeline

```
PROPRIETARY (before):               USD-NATIVE (after):
─────────────────────               ────────────────────────────
ArnoldStandardSurface  →            UsdPreviewSurface / MaterialX
.fbx geometry files    →            .usdc geometry
VendorRig format       →            UsdSkel + xformOp time samples
ProprietaryShadowAPI   →            UsdLux shadow attributes
VendorMeshSDK          →            pxr.UsdGeom Python API
Proprietary extensions →            Custom USD schemas (usdGenSchema)
```

The goal: any tool in the ecosystem that supports OpenUSD should be able to open, read, and render the asset **without installing any vendor-specific software**.

---

## 8. Pipeline Documentation Standards

Good USD pipeline documentation must include enough technical detail for developers to implement and maintain the pipeline.

### Required Contents

- USD **schema types** at each pipeline node
- **Stage layering structure** — which layers compose how
- **Data flow** between nodes — what enters and exits each stage
- **Composition arc annotations** — which arcs connect which assets
- **Dependency mapping** — explicit list of what each stage depends on

### What's Insufficient

- Generic block diagrams without USD-specific detail
- Code snippets only without visual diagrams
- High-level business flowcharts for technical work

---

## 9. UI/UX Principles for USD Pipelines

USD's composition model is a graph — layers reference layers, assets reference assets, variants branch and merge. The UI for a USD pipeline tool should reflect this underlying structure, not impose a linear or modal workflow on top of it.

### Core Principles

**1. Node-based visual editor**

USD composition is a directed graph. The UI should represent it as one — nodes for layers and assets, connections for arcs (references, sublayers, payloads). A linear list or sequential step wizard misrepresents how USD actually composes.

```
shot.usda ──────────────────────────────── [Shot Node]
               ↑             ↑                  ↑
          [Anim Node]  [Layout Node]      [Asset Node]
          anim.usda    layout.usda        chair_asset.usda

Each arrow = a composition arc
Each node  = a layer or asset
```

**2. Real-time feedback**

USD's change notification system fires immediately on every edit. The UI should surface composition errors, validation warnings, and loading state the moment they occur — not after a modal "apply" or "submit" button is clicked.

**3. Context-sensitive help and tooltips**

Every node and connection should have inline documentation explaining what arc it represents, what schema type a prim uses, and what attributes are available. Schema definitions from `plugInfo.json` and `schema.usda` contain this documentation — surface it in the UI.

**4. Support branching and merging**

USD sublayers and references branch and merge non-linearly. A pipeline tool that forces a single linear flow misrepresents the composition model. The UI must support multiple inputs and outputs per node — just like USD composition itself.

**5. No modal dialogs for configuration**

USD edits are live — `attr.Set()` takes effect immediately. Configuration changes in the UI should be non-blocking. Modal dialogs that require "apply" or "OK" before changes take effect are architecturally wrong for a USD pipeline tool.

**6. Scalability — lazy representation**

Large scenes have thousands of prims and dozens of layers. The UI should reflect USD's payload deferred loading model — show nodes without loading their full contents until explicitly expanded, mirroring `Usd.Stage.LoadNone` + explicit `Load()`.

### Wrong Patterns

| Anti-pattern                                 | Why it is wrong                                                 |
| -------------------------------------------- | --------------------------------------------------------------- |
| Modal dialogs for every configuration change | Blocks workflow, misrepresents USD's live editing model         |
| Linear-only pipeline flows                   | USD branches and merges — a linear flow is structurally wrong   |
| No customisation options                     | USD pipelines are studio-specific — one size does not fit all   |
| Flatten before editing                       | Defeats the composition benefits USD was designed to provide    |
| No error feedback until final submission     | USD surfaces composition errors immediately — the UI should too |
| Loading all nodes fully at startup           | Ignores USD's payload deferred loading design                   |

### Why Node-Based Is the Right Mental Model

```
USD asks:   "what layers compose this prim?"
Node UI answers visually:
  [chair_asset.usda] ──reference──> [ChairA in shot.usda]
                                         ↑
                               [anim.usda override]

Linear UI fails to represent:
  - which layer is strongest
  - where overrides come from
  - how arcs stack and resolve
```

> **The rule:** if the underlying USD data structure is a graph, the UI must be a graph. Any tool that flattens this into a sequential list is hiding information the artist needs to understand and debug composition.

---

## 10. Build Configuration Management

USD pipelines depend on environment variables, plugin versions, and schema deployments being **identical across every environment** — artist workstations, render farms, CI/CD pipelines, and client deliveries. Build configuration management is the practice of ensuring this consistency.

### Why It Is Needed

Without it, the same `.usda` file behaves differently on different machines:

```
Artist machine:   USD 23.08  acmeSensors.so v1.2  Python 3.10
Render farm:      USD 22.11  acmeSensors.so v1.0  Python 3.9

Same file. Different results.
Renders differ from viewport.
Schema attributes resolve incorrectly.
No crash — silent wrong output.
```

USD plugin mismatches cause **silent data corruption**, not errors. A renamed attribute between plugin versions means `attr.Get()` returns `None` instead of raising an exception — the pipeline appears to work but produces wrong results.

### Core Principles

**1. Explicit build variants in version-controlled config files**

Every environment's exact dependency versions are declared in a config file committed to the repository — not assumed or set manually per machine:

```yaml
# build_config.yaml — committed to source control
usd_version: "23.08"
python_version: "3.10"
plugins:
  acmeSensors: "1.2.0"
pxr_plugin_path: "/studio/plugins/23.08/v1.2/"
```

**2. Centralised config — single source of truth**

One config file drives all environments. Updating a plugin version means updating one file and committing — every environment that pulls the repo gets the same versions automatically.

**3. Conditional logic for different platforms**

```yaml
platforms:
  linux: { library_ext: ".so", plugin_path: "/studio/plugins/" }
  windows: { library_ext: ".dll", plugin_path: "C:/studio/plugins/" }
```

**4. Never ignore the build cache**

Build caches (cmake, ninja) only recompile what changed. Ignoring the cache forces full rebuilds — wasteful on large USD schema libraries that can take tens of minutes to compile.

```bash
cmake --build .              # correct — uses cache
cmake --build . --clean-first  # wrong — discards cache, full rebuild
```

**5. Document all environment variables**

Every variable that affects build or runtime must be explicitly documented and set by the config system — not left to individual artists to configure manually:

```
PXR_PLUGINPATH_NAME   path to custom schema plugins
USD_INSTALL_ROOT      path to USD installation
PYTHONPATH            path to USD Python bindings
TF_DEBUG              debug symbol flags
```

### Wrong Approaches

| Anti-pattern                       | Why                                                                      |
| ---------------------------------- | ------------------------------------------------------------------------ |
| Undocumented environment variables | Artists configure manually → inconsistent environments                   |
| Hardcoded paths in build scripts   | Breaks on different machines, operating systems, or directory structures |
| Ignoring build cache               | Unnecessary full rebuilds — wastes time on large plugin libraries        |
| No version pinning                 | Plugin updates silently change behaviour across environments             |
| Manual per-machine setup           | Not reproducible — "works on my machine" is not a pipeline               |

> **The core rule:** if any two machines in your pipeline have different values for `PXR_PLUGINPATH_NAME`, `USD_INSTALL_ROOT`, or plugin versions — your pipeline is not under configuration management and silent errors will occur.

---

## 11. Conceptual Data Mapping Documents

A conceptual data mapping document is the **logical blueprint** that specifies how source schema attributes map to target USD schema attributes before writing any code.

### Required Contents

- **Schema correspondences** — explicit mapping between source prim types and target USD prim types (e.g. `FBXMesh` → `UsdGeomMesh`)
- **Attribute correspondences** — source attribute name → target attribute name, data type, units (e.g. `diffuseColor` maps to `inputs:diffuseColor` as `color3f`)
- **Transformation rules** — how complex conversions work: unit scaling, axis flipping, coordinate system conversion
- **Mandatory vs optional fields** — which attributes must be present for a valid exchange, which may be omitted
- **Metadata inheritance mapping** — how source metadata maps to USD layer/prim metadata, and which metadata propagates through the hierarchy
- **Variant set mapping strategies** — how source asset variations (LOD levels, material swaps, configuration options) map to USD variant sets

### NOT in Mapping Documents

The following belong in OTHER documents — not in conceptual mapping docs:

| What                                        | Where it belongs instead            |
| ------------------------------------------- | ----------------------------------- |
| Runtime performance optimisation techniques | Implementation or optimisation docs |
| USD API usage examples and code snippets    | Technical implementation docs       |
| Error handling and validation procedures    | Technical or operational docs       |
| Version histories of source/target schemas  | Schema management docs              |
| Physical storage format details             | Implementation docs                 |
| Example payloads with actual data           | Testing documentation               |

> **Exam pattern:** If an option mentions "API examples", "error handling", "runtime performance", or "storage format" in the context of a mapping document question — it is wrong. Mapping documents are about _data relationships_, not _implementation details_.

---

## 12. Custom Exporters and Importers

### What They Are

A **custom exporter** translates proprietary or DCC data INTO USD.
A **custom importer** translates USD INTO another format.

```
Exporter:   Maya / Houdini / proprietary tool  →  USD stage
Importer:   USD stage  →  game engine / renderer / legacy tool
```

They are needed because USD does not automatically understand
proprietary formats. Every format that needs to exchange data
with USD requires a translation layer.

### Custom Exporter — Correct Practices

**Inherit from UsdGeom classes for built-in schema validation**

```python
# Inheriting from UsdGeom gives type safety and validation for free
mesh  = UsdGeom.Mesh.Define(stage, "/World/Chair")
light = UsdLux.SphereLight.Define(stage, "/World/Key")
# Wrong type for an attribute → error at authoring time not render time
```

**Use `stage.Export()` to serialise — not `stage.Save()`**

```python
# stage.Export() — writes flat resolved copy to any path
stage.Export("output.usda")   # correct for delivery

# stage.Save() — writes only to the root layer's own backing file
# does not produce a standalone deliverable
```

**Extend via pre/post hooks — never override the main function**

```python
def pre_export_hook(stage):
    # runs BEFORE core export
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    stage.GetRootLayer().customLayerData = {
        "pipeline:version": "2.0"
    }

def post_export_hook(stage):
    # runs AFTER core export
    for prim in stage.Traverse():
        if prim.IsA(UsdGeom.Mesh):
            prim.CreateAttribute(
                "pipeline:exported",
                Sdf.ValueTypeNames.Bool
            ).Set(True)
```

**Register custom schemas with TfType before exporting**

Custom attributes must be schema-validated before export.
If the schema plugin is not registered, custom attributes
are written as raw unvalidated data.

### Custom Importer — The Two-Pass Pattern

Decouple parsing from USD authoring. Never mix file I/O
with USD API calls.

```python
# WRONG — interleaved parsing and USD authoring
open_file()
create_usd_prim()       # USD authoring mixed with I/O
read_next_object()
set_usd_attribute()     # fragile, hard to debug

# CORRECT — two separate passes
# Pass 1: parse to intermediate — all validation and conversion here
intermediate = {
    "meshes":    parse_geometry(source_file),     # convert units
    "materials": parse_materials(source_file),    # validate types
    "animation": parse_animation(source_file),    # handle errors
}

# Pass 2: populate USD from clean validated data
stage = Usd.Stage.CreateNew("output.usda")
with Sdf.ChangeBlock():                           # batch notifications
    for mesh_data in intermediate["meshes"]:
        mesh = UsdGeom.Mesh.Define(stage, mesh_data["path"])
        mesh.GetPointsAttr().Set(mesh_data["points"])
        mesh.GetFaceVertexCountsAttr().Set(mesh_data["face_counts"])
stage.Save()
```

**Why two passes:**

- Pass 1 catches all errors before any USD state is created
- Pass 2 can be wrapped in `Sdf.ChangeBlock()` for performance
- Each pass can be tested independently
- USD API calls are never mixed with file I/O concerns

### Wrong Approaches

| Wrong                                  | Why                                                                 |
| -------------------------------------- | ------------------------------------------------------------------- |
| Write raw binary directly to USD files | Bypasses USD serialisation — corrupts the file                      |
| Hand-write USD ASCII                   | Bypasses schema validation and type checking                        |
| Embed external references as raw data  | Breaks modularity — use references or payloads                      |
| Override the main export function      | Use pre/post hooks instead — override loses built-in functionality  |
| Ignore variant sets during export      | Variant sets represent configurations — ignoring them loses data    |
| Skip schema validation for speed       | Silent corruption — validation catches type mismatches early        |
| Interleave parsing and USD authoring   | Hard to debug, cannot test independently, fragile                   |
| Use absolute file paths                | Breaks on any other machine — use relative paths or asset resolvers |

### Exam Pattern

| Question asks                                  | Correct answer signals                                    |
| ---------------------------------------------- | --------------------------------------------------------- |
| How to ensure schema compliance in an exporter | Inherit from UsdGeom classes                              |
| How to serialise the full scene                | `stage.Export(path)`                                      |
| How to extend an exporter                      | Pre/post hooks — never override main function             |
| How to structure an importer                   | Two-pass: intermediate representation then USD population |
| What tool validates export output              | `usdchecker` — validates, does not auto-fix               |

---

## 13. Data Interchange Script Best Practices

### `UsdUtils.CopyLayer` — Duplicating Layers for Merging

When merging data from multiple USD sources, `UsdUtils.CopyLayer` is the recommended utility for duplicating an entire layer accurately before merging.

```python
from pxr import UsdUtils, Sdf

# CopyLayer duplicates an entire SdfLayer cleanly
# Signature: UsdUtils.CopyLayer(source: SdfLayer, dest: SdfLayer) -> bool
source_layer = Sdf.Layer.FindOrOpen("department_anim.usda")
dest_layer   = Sdf.Layer.CreateAnonymous("merged.usda")

success = UsdUtils.CopyLayer(source_layer, dest_layer)
# dest_layer now contains all specs from source_layer
# source_layer is unchanged

# Use when: merging department layers, combining asset versions,
#           duplicating a layer before modifying it (preserve original)
```

> **Why CopyLayer and not manual copying:** Manual layer copying with Python loops over specs is error-prone and can miss nested specs, metadata, relationships, and composition arc data. `UsdUtils.CopyLayer` handles the full layer spec graph correctly.

### Complete Best Practices

| ✅ Always do                                             | ❌ Never do                             |
| -------------------------------------------------------- | --------------------------------------- |
| Use `Usd.Stage` API with proper error handling           | Directly edit USD files as plain text   |
| Use `UsdUtils.CopyLayer` to duplicate layers for merging | Manually loop over specs to copy layers |
| Use USD's layering and composition to combine sources    | Manually merge data in scripts          |
| Use USD Python API to create UsdPrims with schemas       | Write USD ASCII by hand                 |
| Use relative paths or asset resolvers                    | Use absolute file paths                 |
| Use proper schemas for proprietary metadata              | Embed unregistered string blobs         |
| Use time samples for animated data                       | Use static defaults for animation       |
| Maintain schema validation throughout                    | Skip validation to speed up script      |

---

## 14. Key Takeaways

| Concept                                  | What to Remember                                                                                                                                                         |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `.usd` extension                         | Generic — USD auto-detects ASCII vs binary from file header                                                                                                              |
| Rename `.usda` → `.usdc`                 | Invalid — different binary formats                                                                                                                                       |
| `usdcat`                                 | Format conversion and flattening. `usdzip` for `.usdz` packaging                                                                                                         |
| `usdchecker`                             | Validates. Does NOT auto-fix.                                                                                                                                            |
| Exporter hooks                           | Pre/post hooks extend export. Never override the main export function                                                                                                    |
| Proprietary dependencies                 | 5 strategies: replace shaders, file formats, SDKs, proprietary extensions, animation formats                                                                             |
| Open-source plugins                      | Use instead of proprietary SDKs — portable, maintainable, no vendor lock-in                                                                                              |
| Custom schemas vs proprietary extensions | Custom USD schemas (usdGenSchema) are portable. Proprietary extensions require vendor tools.                                                                             |
| Proprietary animation → USD              | Convert to `UsdSkel` or `xformOp` time samples — removes DCC dependency                                                                                                  |
| Vendor-specific APIs for composition     | ❌ Wrong — introduces proprietary dependency at the processing level                                                                                                     |
| Embed proprietary shaders in USD         | ❌ Wrong — increases lock-in, not removes it                                                                                                                             |
| Mapping docs contain                     | Schema correspondences, attribute correspondences, transformation rules, mandatory/optional fields, **metadata inheritance mapping**, **variant set mapping strategies** |
| Mapping docs exclude                     | API usage examples, error handling, runtime performance, storage format details, example payloads — these belong in implementation/technical docs                        |
| Importer pattern                         | Parse to intermediate first, then populate USD                                                                                                                           |
| Custom schema for import                 | NOT required for importing — only needed when extending USD data types                                                                                                   |
| Custom exporter — inherit from UsdGeom   | Gets built-in schema validation automatically — correct approach                                                                                                         |
| `stage.Export(path)`                     | Standard serialisation method — writes full resolved scene to any path                                                                                                   |
| Raw binary to USD files                  | ❌ Wrong — corrupts file, bypasses USD serialisation                                                                                                                     |
| Embed external refs as raw data          | ❌ Wrong — breaks modularity, increases file size                                                                                                                        |
| `UsdUtils.CopyLayer(src, dest)`          | Correct tool for duplicating layers when merging data — handles full spec graph                                                                                          |
| Manual spec copying                      | ❌ Wrong — error-prone, misses nested specs and metadata                                                                                                                 |
| Stage caching                            | `UsdStageCache` — avoids redundant recomposition                                                                                                                         |
| `SdfChangeBlock`                         | Batches change notifications — critical for bulk authoring performance                                                                                                   |
| Flatten preserves                        | Time samples (animation), geometry types                                                                                                                                 |
| Flatten discards                         | Variant sets (collapsed), composition arcs                                                                                                                               |

---

_Previous: [Day 6 — Visualization](day-06-visualization.md)_  
_Next: [Day 8 — Content Aggregation](day-08-content-aggregation.md)_
