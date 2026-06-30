# Day 10 - Custom Schemas

> **OpenUSD NCP Certification Study Notes**  
> _Custom IsA Schemas, API Schemas, usdGenSchema, TfType, SdfFileFormat, Model Kinds, Variant Fallbacks_

---

## Table of Contents

1. [Why Custom Schemas?](#1-why-custom-schemas)
2. [The Schema Inheritance Hierarchy](#2-the-schema-inheritance-hierarchy)
3. [The Complete usdGenSchema Workflow](#3-the-complete-usdgenschema-workflow)
4. [The TfType System — What Registration Actually Means](#4-the-tftype-system--what-registration-actually-means)
5. [File Format Plugins — SdfFileFormat](#5-file-format-plugins--sdffileformat)
6. [Custom Model Kinds — UsdModelKindRegistry](#6-custom-model-kinds--usdmodelkindregistry)
7. [Variant Fallback Selections](#7-variant-fallback-selections)
8. [Exam Pattern Recognition — Elimination Guide](#8-exam-pattern-recognition--elimination-guide)
9. [Key Takeaways — The 12 Things to Know Cold](#9-key-takeaways--the-12-things-to-know-cold)

---

## 1. Why Custom Schemas?

USD ships with schemas for common 3D concepts — `Mesh`, `Sphere`, `Material`, `DistantLight`. These cover general-purpose use cases. But a factory automation company needs prims for `TemperatureSensor` and `ConveyorBelt`. A film studio needs `ShotCamera` and `CharacterRig`. These don't exist in USD out of the box.

Custom schemas let you add new prim types as **first-class USD citizens** — with the same type safety, API generation, schema fallbacks, and tool integration as built-in schemas.

### Plain Attributes vs Custom Schema

| Capability                    | Plain custom attributes           | Custom schema                        |
| ----------------------------- | --------------------------------- | ------------------------------------ |
| `prim.IsA(TemperatureSensor)` | ❌ No type checking               | ✅ Works correctly                   |
| Schema fallback values        | ❌ Returns `None` if unset        | ✅ Returns defined default           |
| Generated Python/C++ API      | ❌ Manual `GetAttribute("name")`  | ✅ `sensor.GetTemperatureAttr()`     |
| usdview introspection         | ❌ Arbitrary data, no schema info | ✅ Full attribute listing with types |
| Validation at authoring time  | ❌ Silent errors                  | ✅ Type-checked at definition        |
| Inheritance chain known       | ❌ No                             | ✅ `IsA(UsdGeomXform)` also works    |

### When to Use

| ✅ Use custom schemas when                 | ❌ Don't use for                          |
| ------------------------------------------ | ----------------------------------------- |
| Standardised types shared across teams     | Quick one-off pipeline attributes         |
| `prim.IsA()` and `prim.HasAPI()` must work | Data not shared across tools              |
| Schema fallback values are needed          | Rapid prototyping (use plain attrs first) |
| Full C++ and Python API is needed          | One-time migration scripts                |

---

## 2. The Schema Inheritance Hierarchy

Choosing the wrong base class is a common exam trap. The hierarchy determines what capabilities your schema inherits.

```
UsdSchemaBase                            ← root of ALL schemas
├── UsdTyped                             ← base for all IsA (typed) schemas
│   ├── UsdGeomImageable                 ← all renderable prims (visibility, purpose)
│   │   ├── UsdGeomXformable             ← all transformable prims
│   │   │   ├── UsdGeomGprim             ← all geometric primitives
│   │   │   │   ├── UsdGeomMesh
│   │   │   │   ├── UsdGeomSphere
│   │   │   │   └── ...
│   │   │   ├── UsdGeomCamera
│   │   │   └── UsdLuxLight
│   │   └── UsdShadeMaterial
│   └── (other UsdTyped subclasses)
└── UsdAPISchemaBase                     ← base for all API schemas
    ├── UsdGeomMotionAPI
    ├── UsdPhysicsRigidBodyAPI
    └── ...


                    YOUR CUSTOM SCHEMA
                    → Inherit from UsdTyped
                      or UsdGeomImageable
                      NOT directly from UsdSchemaBase
```

### Choosing the Right Base Class

| Base Class         | What it gives you                                                                                                                  | When to use                                                                                                                                         | Exam answer?                                                                      |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| `UsdSchemaBase`    | The absolute root of ALL schemas — provides the base interface. Technically valid but requires implementing all plumbing manually. | When the exam says "subclass `UsdSchemaBase` or a derived schema class" — this phrasing IS correct since `UsdTyped` is derived from `UsdSchemaBase` | ✅ **Correct** in exam phrasing — "subclass UsdSchemaBase **or a derived class**" |
| `UsdTyped`         | Sets `typeName` on the prim. All plumbing for `IsA()` to work. Schema fallback values. Standard base for typed IsA schemas.        | Any custom IsA schema that is a new prim type — `TemperatureSensor`, `ConveyorBelt`, `CharacterRig`                                                 | ✅ Correct — recommended standard base                                            |
| `UsdGeomImageable` | Everything from UsdTyped + `visibility` + `purpose` attributes. The base for anything that renders.                                | Custom schemas for renderable objects — custom geometry types, custom lights                                                                        | ✅ Correct for renderable objects                                                 |

> **Exam phrasing nuance:** Q22 and Q26 phrase the correct answer as "subclassing `UsdSchemaBase` or a derived schema class". This IS correct because `UsdTyped` and `UsdGeomImageable` ARE derived from `UsdSchemaBase`. The key phrase is **"or a derived class"** — it covers the full hierarchy. The wrong answer is "inheriting **directly** from `UsdSchemaBase`" when a more specific derived class should be used.

---

## 3. The Complete usdGenSchema Workflow

`usdGenSchema` is the code generation tool that transforms a `schema.usda` definition into compilable C++ source code and Python bindings. This is the required path for production-grade custom schemas.

### Step 1 — Write `schema.usda`

Define your schema class, its base class, and its attributes with types and defaults:

```usda
#usda 1.0
(
    subLayers = [
        @usd/schema.usda@           # inherit from base USD schemas
    ]
)

over "GLOBAL" (
    customData = {
        string libraryName   = "acmeSensors"    # your library name
        string libraryPrefix = "AcmeSensor"     # C++ class prefix
    }
) {}

# ── IsA Schema — defines a new prim TYPE ────────────────────────────
class Xform "TemperatureSensor" (
    customData = {
        string className = "TemperatureSensor"
    }
    doc = """A prim representing a physical temperature sensor in
             the factory automation pipeline."""
    inherits = </Xform>              # inherits from UsdGeomXform
                                     # which inherits from UsdGeomImageable
                                     # which inherits from UsdTyped
) {
    # Attribute definitions — these become GetXxxAttr() methods
    float  sensor:temperature = 20.0     (
        doc = "Current sensor reading in degrees Celsius."
    )
    float  sensor:minRange    = -40.0    (
        doc = "Minimum measurable temperature."
    )
    float  sensor:maxRange    = 125.0    (
        doc = "Maximum measurable temperature."
    )
    string sensor:serialNumber = ""      (
        doc = "Manufacturer serial number for asset tracking."
    )
}
```

### Step 2 — Run usdGenSchema

```bash
usdGenSchema schema.usda
```

This generates:

- `acmeSensors.h` — C++ header with class declaration and attribute accessors
- `acmeSensors.cpp` — C++ implementation
- `wrapAcmeSensors.cpp` — Python binding code
- `plugInfo.json` — plugin discovery and TfType registration metadata

### Step 3 — Compile C++ into a shared library

```bash
# Using CMake
cmake -DPXR_ROOT=/path/to/usd_install .
make

# Output:
# acmeSensors.so  (Linux)
# acmeSensors.dll (Windows)
```

### Step 4 — Deploy the plugin

Place the compiled library and `plugInfo.json` where USD can discover them:

```bash
# Set the plugin path environment variable
export PXR_PLUGINPATH_NAME=/path/to/acmeSensors/

# USD reads plugInfo.json at startup and registers the types
```

### Step 5 — Use like any built-in schema

```python
from pxr import Usd, AcmeSensors   # your generated module

stage = Usd.Stage.CreateInMemory()

# Define a prim using your custom IsA schema
sensor = AcmeSensors.TemperatureSensor.Define(stage, "/Factory/Sensor_001")

# Schema fallback values work — even without Set()
print(sensor.GetTemperatureAttr().Get())   # 20.0 ← schema fallback
print(sensor.GetMinRangeAttr().Get())      # -40.0
print(sensor.GetSerialNumberAttr().Get())  # ""

# Set a value
sensor.GetTemperatureAttr().Set(23.5)

# Type checking works — full inheritance chain known
prim = sensor.GetPrim()
print(prim.GetTypeName())                           # "TemperatureSensor"
print(prim.IsA(AcmeSensors.TemperatureSensor))     # True
print(prim.IsA(UsdGeom.Xform))                     # True — inheritance
print(prim.IsA(UsdGeom.Imageable))                 # True — inheritance chain
```

### Why Not Python-Only?

| Python-only schema                                 | Full C++ schema via usdGenSchema    |
| -------------------------------------------------- | ----------------------------------- |
| No C++ type registration                           | ✅ Full TfType registration         |
| `prim.IsA()` fails or returns False                | ✅ `IsA()` works correctly          |
| No schema fallback values — `Get()` returns `None` | ✅ Schema fallbacks work            |
| No generated accessor methods                      | ✅ `GetTemperatureAttr()` etc.      |
| Not found by USD's schema discovery                | ✅ Discoverable via `plugInfo.json` |
| **Correct for prototyping only**                   | **Required for production**         |

---

## 4. The TfType System — What Registration Actually Means

`TfType` is USD's runtime type identification system. Registration is what makes `prim.IsA()`, `prim.HasAPI()`, schema fallback values, and schema discovery actually function.

### What Breaks Without Registration

```python
# You have a USD file with typeName = "TemperatureSensor"
# But the schema plugin is NOT deployed:

prim.IsA(TemperatureSensor)      # ERROR or always False
prim.GetTypeName()               # "TemperatureSensor" — just a string, no meaning
sensor.GetTemperatureAttr().Get() # None — no schema fallback known
# usdview shows: "unknown schema type"
# No attribute listing from schema definition
```

### What Registration Enables

```python
# Schema plugin IS deployed with plugInfo.json:

prim.IsA(AcmeSensors.TemperatureSensor)  # True ✅
prim.IsA(UsdGeom.Xform)                 # True ✅ — inheritance chain known
prim.IsA(UsdGeom.Imageable)             # True ✅ — full hierarchy traversable
sensor.GetTemperatureAttr().Get()        # 20.0 ✅ — schema fallback works
# usdview shows all attributes with types, defaults, documentation
# Schema API methods all function correctly
```

### How Registration Happens

```
1. usdGenSchema generates plugInfo.json
   → declares library name, all schema types, their base types

2. In the generated C++ source, TF_REGISTRY_FUNCTION performs the actual registration:

   TF_REGISTRY_FUNCTION(TfType) {
       TfType::Define<AcmeTemperatureSensor,
                      TfType::Bases<UsdGeomXform>>();
   }

   This is the MACRO that hooks the type into the TfType registry.
   Registration via manifest file ALONE is not sufficient — the
   TF_REGISTRY_FUNCTION macro in the C++ code is required.

3. Plugin is deployed to PXR_PLUGINPATH_NAME

4. USD startup sequence:
   → scans all directories in PXR_PLUGINPATH_NAME
   → reads every plugInfo.json found
   → loads the shared library (.so / .dll)
   → TF_REGISTRY_FUNCTION runs, registering each type
   → TfType registry now knows the full inheritance chain

5. Now at runtime:
   → prim.IsA(TemperatureSensor) triggers TfType lookup
   → registry knows: TemperatureSensor → Xform → Imageable → Typed → SchemaBase
   → can answer IsA() queries for the entire chain
```

> **Exam trap — Q23:** "Implement the schema by subclassing `UsdGeomImageable` and registering it via a **plugin manifest file only**" is **WRONG**. The manifest file (`plugInfo.json`) enables discovery but the actual type registration requires the `TF_REGISTRY_FUNCTION` macro in the C++ source code. Both are required.

### Defining Schema Attributes — `SdfPropertySpec` and `SdfPrimSpec`

When defining schema attributes at the Sdf layer level (rather than via the generated high-level API), you use:

```python
from pxr import Sdf

# SdfPrimSpec — defines a prim and its metadata at the Sdf layer level
prim_spec = Sdf.CreatePrimInLayer(layer, "/TemperatureSensor")
prim_spec.specifier = Sdf.SpecifierDef
prim_spec.typeName  = "TemperatureSensor"

# SdfPropertySpec (via SdfAttributeSpec) — defines an attribute and its schema
# Signature: Sdf.AttributeSpec(owner, name, typeName) -> SdfAttributeSpec
attr_spec = Sdf.AttributeSpec(
    prim_spec,
    "sensor:temperature",
    Sdf.ValueTypeNames.Float
)
attr_spec.default     = 20.0      # schema fallback value
attr_spec.variability = Sdf.VariabilityVarying
attr_spec.documentation = "Current temperature reading in Celsius."
```

`SdfPropertySpec` and `SdfPrimSpec` are the Sdf-level objects used to describe schema attributes and prim metadata. `usdGenSchema` generates code that uses these objects internally. You interact with them directly when authoring at the Sdf level or when implementing custom schema validation.

> **Exam trap:** "Registering the custom model kind token in the TfType system without any schema or API linkage" is **WRONG**. Token registration alone provides a name but no inheritance chain, no fallback values, and no API. The schema definition itself must be fully linked.

---

## 5. File Format Plugins — SdfFileFormat

A **file format plugin** teaches USD to read and write a new file type. This is **completely independent** from custom schemas.

```
Custom Schema   = defines what scene data IS (prim types, attributes, meaning)
SdfFileFormat   = defines how data is READ and WRITTEN from/to files
```

These address entirely different problems. A factory might need both: a custom `TemperatureSensor` schema (defines the data type) AND a `SdfFileFormat` plugin for their proprietary `.mysim` simulation format (teaches USD to read that format).

### Implementation Steps

```
1. Create C++ class inheriting from SdfFileFormat:
   class MyFormatPlugin : public SdfFileFormat { ... }

2. Implement required interface methods:
   bool Read(SdfLayer*, const string& resolvedPath, bool metadataOnly)
   bool WriteToFile(const SdfLayer&, const string& filePath, ...)
   bool CanRead(const string& filePath) const

3. Register with TfType:
   TF_REGISTRY_FUNCTION(TfType) {
       TfType::Define<MyFormatPlugin,
                      TfType::Bases<SdfFileFormat>>();
   }

4. Declare in plugInfo.json:
   USD discovers it at startup via PXR_PLUGINPATH_NAME

5. Now USD can transparently open your format:
   stage = Usd.Stage.Open("simulation.mysim")
   → USD sees .mysim extension
   → Looks up registered SdfFileFormat plugins
   → Finds MyFormatPlugin (registered for .mysim)
   → Calls MyFormatPlugin.Read() to translate to SdfLayer
   → Stage composes normally from that point
```

### ArResolver — Handling External References During File I/O

When your file format contains **references to external assets** (textures, sub-files, referenced layers), the plugin must integrate with **`ArResolver`** — USD's asset resolution system — to correctly locate those files.

```
Without ArResolver integration:
  MyFormat file contains: texture = "textures/wood.png"
  Plugin reads raw string "textures/wood.png" — but WHERE is it?
  Relative to what? The answer depends on the resolver context.

With ArResolver integration:
  Plugin calls ArResolver to resolve "textures/wood.png"
  → Resolver applies search paths, asset remapping, version pinning
  → Returns the actual absolute path to the correct file
  → File loading works correctly in all deployment environments
```

```cpp
// Inside your SdfFileFormat::Read() implementation:
ArResolver& resolver = ArGetResolver();
ArResolverContext ctx = resolver.GetCurrentContext();

// Resolve asset paths from the file using the resolver
std::string resolved = resolver.Resolve("textures/wood.png");
// resolved = "/project/assets/textures/wood.png"
```

> **Exam trap — Q20:** "Ensure thread safety by implementing custom locking mechanisms" is **WRONG**. USD core manages concurrent access — file format plugins do not implement their own locking. This is unnecessary and handled at a higher level.

> **Exam trap:** "Embed a custom USD stage cache within the plugin" is **WRONG**. Stage caching is managed by USD core and clients, not inside file format plugins. Embedding one causes inconsistencies.

### Wrong Approaches

| Wrong approach                                 | Why it's wrong                                                                                               |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Override `UsdStage::Open()`                    | Static method, not designed for overriding. File loading happens at the `SdfLayer` level, not `Stage` level. |
| Modify USD core source code                    | USD is designed for extensibility via plugins. Modifying core breaks compatibility.                          |
| Create a `UsdSchema` for the file format       | Schemas define scene description types. They do NOT control file I/O.                                        |
| Implement custom thread locking in Read/Write  | USD core manages concurrent access — plugins don't need custom locking                                       |
| Embed a stage cache inside the plugin          | Stage caching belongs at the USD core/client level — not inside file format plugins                          |
| Use `UsdUtils` exclusively to parse the format | UsdUtils provides utilities but does NOT replace implementing `SdfFileFormat` methods                        |
| Implement a `UsdStage` subclass for the format | UsdStage is format-agnostic — file format I/O is `SdfFileFormat`'s responsibility                            |

---

## 6. Custom Model Kinds — UsdModelKindRegistry / UsdModelRegistry

> **Naming note:** The exam uses both `UsdModelKindRegistry` and `UsdModelRegistry` in different questions. Both refer to the same concept — the registry that tracks model kind identifiers and their hierarchy. Use whichever term the question uses; they are functionally equivalent in exam context.

USD has a built-in hierarchy of **model kinds** that classify prims by their role in the scene:

```
assembly       ← top-level published collection of assets (a full scene or set)
  group        ← organisational container (a city block, a character rig)
    component  ← leaf reusable asset (a chair, a tree, a sensor)
      subcomponent ← important internal node within a component
```

Custom model kinds extend this hierarchy with domain-specific classifications.

### The 5-Step Process

**Step 1 — Define a unique token for your kind**

```python
# "factory_unit" — a new kind for factory floor assets
# This is just a string token at this stage
```

**Step 2 — Register with `UsdModelKindRegistry`**

The registry must know this kind exists, where it sits in the hierarchy (its parent kind), and what prim types it allows:

```python
# Registration specifies:
# - The new kind's unique identifier token ("factory_unit")
# - Its parent in the hierarchy (e.g. "component")
# - Its fallback prim type — what type a prim of this kind defaults to
# - Its allowed root prim types — which prim types are valid for this kind
```

**Specify fallback prim type and allowed root prim types**

This is specifically tested on the exam (Q27). When registering a custom model kind, you must define:

- **Fallback prim type** — the default prim type used when a prim of this kind has no explicit type
- **Allowed root prim types** — which prim types are valid as the root prim for this kind
  These settings ensure schema validation behaves correctly for the new kind and integrate with USD's composition framework.

**Step 3 — Apply to prims using `Usd.ModelAPI`**

```python
from pxr import Usd

prim      = stage.DefinePrim("/Factory/Unit_A", "Xform")
model_api = Usd.ModelAPI(prim)
model_api.SetKind("factory_unit")

# Verify
print(model_api.GetKind())   # "factory_unit"
```

**Step 4 — Implement a schema plugin that EXTENDS (not overrides) `UsdModelAPI`**

Your plugin adds behaviours and properties specific to `factory_unit` without replacing the existing `UsdModelAPI` behaviour.

```
EXTEND UsdModelAPI   ← adds behaviour for the new kind  ✅
OVERRIDE UsdModelAPI ← replaces existing behaviour      ❌ WRONG
```

**Step 5 — Extend the `Validate()` method**

Add domain-specific structural validation:

```python
# Custom validation rules for factory_unit prims:
# "must have a sensor:serialNumber attribute"
# "must have at least one child TemperatureSensor prim"
# "must have pipeline:facilityId metadata set"
```

### Wrong Approaches

| Wrong approach                                                        | Why                                                                                                 |
| --------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| Override (not extend) `UsdModelAPI`                                   | Replaces existing `assembly`/`component`/`group` behaviour — breaks standard kinds for all users    |
| Register token in TfType without schema linkage                       | Provides a name but no behaviour, validation, or API                                                |
| Use variants within the model kind to handle different configurations | Variants serve content variation (LOD, colour). Model kinds serve classification. Separate systems. |
| Modify USD core source                                                | USD's plugin and registry system exists precisely to avoid this                                     |

---

## 7. Variant Fallback Selections

When a scene requests a variant that doesn't exist in a given asset, **variant fallback selections** define what USD should use instead.

```
Scene requests: lod = "ultra"
"ultra" variant doesn't exist in the asset.
→ Without fallbacks: composition error or wrong result
→ With fallbacks: USD tries "high", then "medium", then "low"
```

### Three Correct Approaches

**Approach 1 — `variantFallbacks` in USDA layer metadata**

```usda
#usda 1.0
(
    variantFallbacks = {
        string[] "lod"   = ["high", "medium", "low"]
        string[] "color" = ["default"]
    }
)
```

**Approach 2 — `Usd.Stage.SetGlobalVariantFallbacks()` (Python)**

```python
from pxr import Usd

# Must be called BEFORE opening the stage
fallbacks = {
    "lod":   ["high", "medium", "low"],
    "color": ["default"],
}
Usd.Stage.SetGlobalVariantFallbacks(fallbacks)

# Now all stages opened after this call use these fallbacks
stage = Usd.Stage.Open("scene.usda")
```

**Approach 3 — Session layer overrides**

Author fallback variant selections into the session layer for per-user or per-environment preferences:

```python
stage   = Usd.Stage.Open("scene.usda")
session = stage.GetSessionLayer()
stage.SetEditTarget(session)
# Author fallback selections — never saved to disk
```

### Approach 4 — Author `variantFallbacks` per referencing layer

For consistency across all layers that reference an asset, explicitly author `variantFallbacks` in **each layer** that references the prim:

```usda
# department_shot.usda — this layer references the asset
#usda 1.0
(
    variantFallbacks = {
        string[] "lod"   = ["high", "medium", "low"]
    }
)
# Now this layer AND any layer that sublayers it will use these fallbacks
# without relying on the asset's own defaults
```

> **Why per-layer matters:** If only the asset defines fallbacks, a referencing layer that requests a non-existent variant may fail if its `variantFallbacks` context differs. Explicitly authoring fallbacks in each referencing layer ensures consistent behaviour regardless of which tool opens the stage.

### Wrong Approaches

| Wrong approach                                          | Why                                                                                                                                                |
| ------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Embed fallback selections in prim metadata              | Prim metadata is not designed for fallback logic — leads to unpredictable behaviour                                                                |
| Rely only on the default variant selection              | Default selections don't cover cases where the requested variant doesn't exist                                                                     |
| Rely solely on session layer without defining fallbacks | Session layer can override but provides no fallback logic — must define fallbacks in asset or layer                                                |
| Duplicate prims with different variant sets             | Increases complexity, not scalable — `variantFallbacks` metadata is the correct mechanism                                                          |
| Assume USD auto-selects variants alphabetically         | **USD does NOT auto-select alphabetically** — fallback behaviour must be explicitly defined. No selection = no variant = potentially broken state. |

---

## 8. Exam Pattern Recognition — Elimination Guide

### Pattern 1 — "How do you create a custom schema?"

**Correct answer framework:**

1. Write `schema.usda`
2. Inherit from **`UsdTyped`** or **`UsdGeomImageable`** (NOT `UsdSchemaBase` directly)
3. Run **`usdGenSchema`** to generate C++ and Python
4. Register with **TfType system** via `plugInfo.json`
5. Deploy as plugin via `PXR_PLUGINPATH_NAME`

### Pattern 2 — "How do you add a new file format?"

**Correct answer framework:**
Implement the **`SdfFileFormat` interface** + register with **TfType system** + declare in `plugInfo.json`

### Pattern 3 — "How do you create custom model kinds?"

**Correct answer framework:**
Unique token + **`UsdModelKindRegistry`** + `kind` metadata on root prim via **`UsdModelAPI`** + schema plugin that **inherits** (EXTENDS, not overrides) `UsdModelAPI` + extended `Validate()` method

### Pattern 4 — "Extend vs Override"

> Any option saying "**override**" an existing schema, API, or core system = **WRONG**. USD is always extended, never overridden. Overriding breaks existing functionality for all users of that schema. Extending (inheriting from, adding to) maintains backward compatibility while adding new capabilities.

### Instant Elimination Phrases

Eliminate **any option** containing these phrases immediately:

| Phrase in option                                                | Reason to eliminate                                                                                 |
| --------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `"Modify the core USD source code"`                             | USD uses plugins — never modifies core                                                              |
| `"Python-only schema"` or `"subclassing Usd.Schema in Python"`  | Full schemas need C++ + usdGenSchema                                                                |
| `"Overriding"` any existing schema, API, or method              | Always EXTEND — never override                                                                      |
| `"Override UsdStage::Open()"`                                   | File formats use `SdfFileFormat`, not Stage::Open                                                   |
| `"Register token in TfType WITHOUT schema or API linkage"`      | Token alone is insufficient — needs full schema backing                                             |
| `"Define schema in a .usd file at runtime"`                     | Schemas defined in `schema.usda` + compiled offline                                                 |
| `"Create new UsdSchema to control file format I/O"`             | Schemas ≠ file I/O — use `SdfFileFormat`                                                            |
| `"Embed fallback variant selections in prim metadata"`          | Fallbacks belong at stage/layer level, not prim metadata                                            |
| `"Plugin manifest file only"` for schema registration           | `TF_REGISTRY_FUNCTION` macro in C++ source is ALSO required — manifest alone is insufficient        |
| `"Custom locking in Read/Write"` for file format plugins        | USD core manages concurrency — plugins don't implement locking                                      |
| `"Embed stage cache in file format plugin"`                     | Stage caching belongs at USD core/client level, not in plugins                                      |
| `"Implement UsdStage subclass for new file format"`             | UsdStage is format-agnostic — use `SdfFileFormat`                                                   |
| `"USD auto-selects variants alphabetically"`                    | USD does NOT auto-select variants — fallbacks must be explicitly defined                            |
| `"UsdSchemaRegistry for dynamic loading without recompilation"` | Custom schemas require plugin mechanisms or compile-time registration — not dynamic runtime loading |
| `"Using UsdUtils exclusively to parse custom format"`           | UsdUtils provides utilities but does not replace implementing `SdfFileFormat` methods               |

---

## 9. Key Takeaways — The 12 Things to Know Cold

| #   | Concept                                 | What to Remember                                                                                                                                |
| --- | --------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **Complete schema workflow**            | `schema.usda` → `usdGenSchema` → C++ compile → `TF_REGISTRY_FUNCTION` → plugin deploy                                                           |
| 2   | **Correct base class exam phrasing**    | "Subclass `UsdSchemaBase` **or a derived class**" = CORRECT. `UsdTyped` and `UsdGeomImageable` are derived from `UsdSchemaBase`.                |
| 3   | **`TF_REGISTRY_FUNCTION` macro**        | The C++ macro that performs actual type registration. `plugInfo.json` alone is insufficient.                                                    |
| 4   | **`SdfPropertySpec` and `SdfPrimSpec`** | Sdf-level objects used to define schema attributes and prim metadata — used in schema definition and authoring                                  |
| 5   | **TfType registration**                 | Makes `IsA()`, `HasAPI()`, fallback values, and schema discovery work. Token alone is insufficient.                                             |
| 6   | **SdfFileFormat**                       | For new file formats. Must implement `Read()`, `Write()`, `CanRead()`. Integrate with `ArResolver` for external refs.                           |
| 7   | **ArResolver in file format plugins**   | Integrate with `ArResolver` to correctly resolve external asset paths during file I/O                                                           |
| 8   | **File format plugin wrong patterns**   | No custom locking, no embedded stage cache, no `UsdStage` subclass, no `UsdUtils` exclusively                                                   |
| 9   | **Custom model kinds**                  | Unique token + `UsdModelKindRegistry` (also called `UsdModelRegistry`) + fallback prim type + allowed root prim types + `UsdModelAPI` extension |
| 10  | **Extend vs Override**                  | Always **EXTEND** `UsdModelAPI` — never override. Override breaks existing kinds.                                                               |
| 11  | **Variant fallbacks — no alphabetical** | USD does NOT auto-select variants alphabetically. Fallbacks must be explicitly defined.                                                         |
| 12  | **Variant fallbacks — per layer**       | Author `variantFallbacks` in each referencing layer for consistent behaviour across all tools                                                   |
| 13  | **Never modify core**                   | USD's entire extensibility architecture exists to avoid core modification                                                                       |
| 14  | **Schema vs file format**               | Schema = what data IS. `SdfFileFormat` = how data is STORED. Independent concerns.                                                              |
| 15  | **Elimination rule**                    | "override", "modify core", "manifest only", "alphabetical fallback", "dynamic loading without recompile" → eliminate                            |

---

_Related notes:_  
_[Day 5 — Schemas and Data Modeling](day-05-schemas-and-data-modeling.md) — overview of IsA vs API schemas_  
_[Day 9 — Debugging and Troubleshooting](day-09-debugging-and-troubleshooting.md) — schema version validation_

_Previous: [Day 9 — Debugging and Troubleshooting](day-09-debugging-and-troubleshooting.md)_
_Back to start: [Day 1 — USD Foundations](day-01-usd-foundations.md)_
