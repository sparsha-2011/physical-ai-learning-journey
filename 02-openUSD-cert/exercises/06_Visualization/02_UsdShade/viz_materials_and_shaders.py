"""
Visualization Exercise — Materials and Shaders
================================================
Build a complete UsdPreviewSurface material from scratch and bind
it to geometry. Understand Material → Shader → inputs/outputs chain.

TOPICS:
  UsdShadeMaterial — the container
  UsdShadeShader   — individual shading nodes
  UsdPreviewSurface — the standard PBR shader
  inputs: / outputs: — data flow between nodes
  MaterialBindingAPI — how to attach material to geometry

Run: python viz_materials_and_shaders.py
"""

from pxr import Usd, UsdGeom, UsdShade, Sdf, Vt, Gf
import os

SEP = "=" * 65
stage = Usd.Stage.CreateInMemory()
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
UsdGeom.Xform.Define(stage, "/World")
UsdGeom.Xform.Define(stage, "/World/Geometry")
UsdGeom.Xform.Define(stage, "/World/Looks")   # convention: materials live here

# ── HELPER: create a simple sphere ───────────────────────────────────
def make_sphere(path, translate, radius=1.0):
    sphere = UsdGeom.Sphere.Define(stage, path)
    UsdGeom.XformCommonAPI(sphere).SetTranslate(translate)
    sphere.GetRadiusAttr().Set(radius)
    return sphere

# ── STEP 1: BUILD A BASIC MATERIAL ───────────────────────────────────
print(SEP)
print("  STEP 1 — Build a basic UsdPreviewSurface material")
print(SEP)
print("""
  Structure:
    /World/Looks/RedMaterial          ← UsdShadeMaterial (the CONTAINER)
    /World/Looks/RedMaterial/Shader   ← UsdShadeShader (the node)

  The Material is just a container that exposes outputs.
  The Shader does the actual shading computation.
  They connect via: Material.outputs:surface → Shader.outputs:surface
""")

# Create the Material prim
red_mat = UsdShade.Material.Define(stage, "/World/Looks/RedMaterial")

# Create the Shader prim INSIDE the Material
red_shader = UsdShade.Shader.Define(
    stage, "/World/Looks/RedMaterial/Shader")

# Tell USD this shader uses the UsdPreviewSurface implementation
red_shader.CreateIdAttr("UsdPreviewSurface")

# ── inputs: data going INTO the shader ───────────────────────────────
# These are the parameters you set on the shader
red_shader.CreateInput(
    "diffuseColor", Sdf.ValueTypeNames.Color3f
).Set(Gf.Vec3f(0.8, 0.1, 0.1))   # red

red_shader.CreateInput(
    "roughness", Sdf.ValueTypeNames.Float
).Set(0.3)                         # somewhat shiny

red_shader.CreateInput(
    "metallic", Sdf.ValueTypeNames.Float
).Set(0.0)                         # not metal

# ── outputs: data coming OUT of the shader ────────────────────────────
# The shader produces a surface result that the Material exposes
shader_out = red_shader.CreateOutput(
    "surface", Sdf.ValueTypeNames.Token)

# Connect Material output → Shader output
# This is how the Material knows which shader to use for rendering
red_mat.CreateSurfaceOutput().ConnectToSource(shader_out)

print(f"  Material path:  {red_mat.GetPath()}")
print(f"  Shader path:    {red_shader.GetPath()}")
print(f"  Shader id:      {red_shader.GetIdAttr().Get()}")
print(f"\n  Shader INPUTS (data going IN):")
for inp in red_shader.GetInputs():
    print(f"    inputs:{inp.GetBaseName():<20} = {inp.Get()}")
print(f"\n  Shader OUTPUTS (data coming OUT):")
for out in red_shader.GetOutputs():
    print(f"    outputs:{out.GetBaseName()}")

# ── STEP 2: BIND THE MATERIAL TO GEOMETRY ────────────────────────────
print()
print(SEP)
print("  STEP 2 — Bind the material to a sphere")
print(SEP)
print("""
  Material binding uses a RELATIONSHIP not an attribute.
  You must Apply MaterialBindingAPI first, then call Bind().
""")

sphere1 = make_sphere("/World/Geometry/RedSphere",
                       Gf.Vec3d(-3, 1, 0))

# Step 1: Apply the API
binding_api = UsdShade.MaterialBindingAPI.Apply(sphere1.GetPrim())

# Step 2: Bind the material
binding_api.Bind(red_mat)

bound = UsdShade.MaterialBindingAPI(sphere1.GetPrim()).GetDirectBinding()
print(f"  Bound material: {bound.GetMaterialPath()}")

# ── STEP 3: THREE MATERIALS SHOWING KEY PROPERTIES ───────────────────
print()
print(SEP)
print("  STEP 3 — Three spheres showing roughness and metallic")
print(SEP)

def make_preview_surface(name, diffuse, roughness, metallic, translate):
    mat = UsdShade.Material.Define(
        stage, f"/World/Looks/{name}")
    sh  = UsdShade.Shader.Define(
        stage, f"/World/Looks/{name}/Shader")
    sh.CreateIdAttr("UsdPreviewSurface")
    sh.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(diffuse)
    sh.CreateInput("roughness",    Sdf.ValueTypeNames.Float).Set(roughness)
    sh.CreateInput("metallic",     Sdf.ValueTypeNames.Float).Set(metallic)
    mat.CreateSurfaceOutput().ConnectToSource(
        sh.CreateOutput("surface", Sdf.ValueTypeNames.Token))
    sphere = make_sphere(
        f"/World/Geometry/{name}Sphere", translate)
    UsdShade.MaterialBindingAPI.Apply(
        sphere.GetPrim()).Bind(mat)
    return mat

# Rough plastic — high roughness, no metallic
make_preview_surface(
    "RoughPlastic",
    Gf.Vec3f(0.1, 0.4, 0.8),   # blue
    roughness=0.9,
    metallic=0.0,
    translate=Gf.Vec3d(0, 1, 0)
)

# Shiny plastic — low roughness, no metallic
make_preview_surface(
    "ShinyPlastic",
    Gf.Vec3f(0.1, 0.8, 0.2),   # green
    roughness=0.1,
    metallic=0.0,
    translate=Gf.Vec3d(3, 1, 0)
)

# Metal — low roughness, full metallic
make_preview_surface(
    "Metal",
    Gf.Vec3f(0.8, 0.7, 0.3),   # gold-ish
    roughness=0.2,
    metallic=1.0,
    translate=Gf.Vec3d(6, 1, 0)
)

print(f"  {'Material':<20} {'diffuseColor':<25} {'roughness':<12} {'metallic'}")
print("  " + "-" * 70)
print(f"  {'RedMaterial':<20} {'(0.8, 0.1, 0.1)':<25} {'0.3':<12} {'0.0'}")
print(f"  {'RoughPlastic':<20} {'(0.1, 0.4, 0.8)':<25} {'0.9':<12} {'0.0'}")
print(f"  {'ShinyPlastic':<20} {'(0.1, 0.8, 0.2)':<25} {'0.1':<12} {'0.0'}")
print(f"  {'Metal':<20} {'(0.8, 0.7, 0.3)':<25} {'0.2':<12} {'1.0'}")

# ── STEP 4: UNDERSTAND inputs vs outputs ─────────────────────────────
print()
print(SEP)
print("  STEP 4 — inputs vs outputs explained")
print(SEP)
print("""
  inputs:  = parameters the shader ACCEPTS
    → diffuseColor, roughness, metallic, opacity, normal
    → These receive values (either hardcoded or from another shader output)
    → Can be ANY data type — not just textures, not just numbers

  outputs: = data the shader PRODUCES
    → surface (the shading result)
    → This connects TO the Material's outputs:surface
    → The Material exposes this to the renderer

  EXAM TRAPS:
  ❌ "inputs and outputs are deprecated" → WRONG. They are fundamental.
  ❌ "inputs are exclusively for texture data" → WRONG. Any data type.
  ❌ "Shader contains Materials" → WRONG. Material CONTAINS Shaders.
  ❌ "Shader defines geometry" → WRONG. Shaders = shading computation only.

  Connection flow:
  Texture/Value → Shader.inputs:diffuseColor
                  Shader.outputs:surface → Material.outputs:surface
                                           → Renderer
""")

# ── EXPORT ───────────────────────────────────────────────────────────
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(SCRIPT_DIR, "viz_materials_and_shaders.usda")
if os.path.exists(output_path): os.remove(output_path)
stage.Export(output_path)
print(f"  Saved → {output_path}")
print(f"  Open in usdview:")
print(f"    .\\scripts\\usdview.bat {output_path}")
print(f"""
  In usdview:
    Press F to frame all spheres. Enable Hydra renderer.
    You should see 4 coloured spheres with different material properties.

    Click any sphere → Properties panel:
      material:binding rel → shows the bound material path

    Click /World/Looks/RoughPlastic in Scenegraph:
      Properties panel → see inputs:roughness, inputs:diffuseColor etc.

    Click /World/Looks/RoughPlastic/Shader:
      Properties panel → see all shader inputs and outputs
      This is the actual UsdShadeShader node

    Compare RoughPlastic vs ShinyPlastic:
      Same blue colour, different roughness → different specular highlight
""")
