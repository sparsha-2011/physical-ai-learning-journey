"""
Visualization Exercise — UsdLux Lights
========================================
Explore all major UsdLux light types and their key attributes.

TOPICS:
  UsdLuxDistantLight — directional (sun)
  UsdLuxSphereLight  — point light (radius controls softness)
  UsdLuxRectLight    — area light
  UsdLuxDomeLight    — environment / HDRI
  falloffRadius, exposure, intensity, color
  Lights are Xformable — can be positioned and animated

Run: python viz_lights.py
"""

from pxr import Usd, UsdGeom, UsdLux, Sdf, Vt, Gf
import os

SEP = "=" * 65
stage = Usd.Stage.CreateInMemory()
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
UsdGeom.Xform.Define(stage, "/World")
UsdGeom.Xform.Define(stage, "/World/Lights")
UsdGeom.Xform.Define(stage, "/World/Geometry")

# Ground plane to show light falloff
ground = UsdGeom.Mesh.Define(stage, "/World/Geometry/Ground")
ground.GetPointsAttr().Set(Vt.Vec3fArray([
    Gf.Vec3f(-10, 0, -10), Gf.Vec3f(10, 0, -10),
    Gf.Vec3f(10, 0, 10),   Gf.Vec3f(-10, 0, 10),
]))
ground.GetFaceVertexCountsAttr().Set(Vt.IntArray([4]))
ground.GetFaceVertexIndicesAttr().Set(Vt.IntArray([0, 1, 2, 3]))
ground.GetSubdivisionSchemeAttr().Set(UsdGeom.Tokens.none)
ground.GetExtentAttr().Set(Vt.Vec3fArray([
    Gf.Vec3f(-10, 0, -10), Gf.Vec3f(10, 0, 10)
]))

# A few spheres to receive light
for i, (tx, name) in enumerate([
    (-6, "SphereA"), (0, "SphereB"), (6, "SphereC")
]):
    s = UsdGeom.Sphere.Define(stage, f"/World/Geometry/{name}")
    UsdGeom.XformCommonAPI(s).SetTranslate(Gf.Vec3d(tx, 1, 0))
    s.GetRadiusAttr().Set(1.0)

# ── LIGHT 1: DistantLight ─────────────────────────────────────────────
print(SEP)
print("  LIGHT 1 — DistantLight (directional / sun)")
print(SEP)

distant = UsdLux.DistantLight.Define(stage, "/World/Lights/Sun")
UsdGeom.XformCommonAPI(distant).SetRotate(Gf.Vec3f(-45, 30, 0))
distant.CreateIntensityAttr(1.0)
distant.CreateColorAttr(Gf.Vec3f(1.0, 0.95, 0.8))  # warm sunlight

print(f"""
  DistantLight simulates a light source infinitely far away (the sun).
  ALL light rays are parallel — no falloff with distance.
  Position doesn't matter — only ROTATION matters.
  Rotating -45° on X = light coming from above at 45°.

  Key attributes:
    intensity  = {distant.GetIntensityAttr().Get()}  (brightness)
    color      = warm white (sunlight)
    angle      = angular size of the sun disk (softens shadows)
""")

# ── LIGHT 2: SphereLight ─────────────────────────────────────────────
print(SEP)
print("  LIGHT 2 — SphereLight (point light)")
print(SEP)

sphere_light = UsdLux.SphereLight.Define(
    stage, "/World/Lights/PointLight")
UsdGeom.XformCommonAPI(sphere_light).SetTranslate(Gf.Vec3d(0, 5, 0))
sphere_light.CreateIntensityAttr(500.0)
sphere_light.CreateColorAttr(Gf.Vec3f(1.0, 0.9, 0.7))
sphere_light.CreateRadiusAttr(0.5)

print(f"""
  SphereLight = physically sized spherical light source.

  RADIUS controls angular spread and shadow SOFTNESS:
    Small radius (0.1) → small light source → hard sharp shadows
    Large radius (2.0)  → large light source → soft diffuse shadows
    Current radius = {sphere_light.GetRadiusAttr().Get()}

  EXAM POINT: radius controls shadow softness, NOT brightness.
  intensity controls brightness. exposure adjusts in stops.

  falloffRadius — maximum distance light affects:
    (not set here — light affects everything in scene)
""")

# Add a second sphere light with large radius to compare
sphere_light2 = UsdLux.SphereLight.Define(
    stage, "/World/Lights/SoftLight")
UsdGeom.XformCommonAPI(sphere_light2).SetTranslate(Gf.Vec3d(6, 5, 0))
sphere_light2.CreateIntensityAttr(500.0)
sphere_light2.CreateColorAttr(Gf.Vec3f(0.7, 0.8, 1.0))  # cool blue
sphere_light2.CreateRadiusAttr(3.0)   # large radius = soft shadows

print(f"  Added SoftLight with radius=3.0 — compare shadow softness")

# ── LIGHT 3: RectLight (area light) ──────────────────────────────────
print()
print(SEP)
print("  LIGHT 3 — RectLight (rectangular area light)")
print(SEP)

rect_light = UsdLux.RectLight.Define(stage, "/World/Lights/AreaLight")
UsdGeom.XformCommonAPI(rect_light).SetTranslate(Gf.Vec3d(-6, 4, 2))
UsdGeom.XformCommonAPI(rect_light).SetRotate(Gf.Vec3f(-60, 0, 0))
rect_light.CreateIntensityAttr(200.0)
rect_light.CreateColorAttr(Gf.Vec3f(0.9, 0.95, 1.0))
rect_light.CreateWidthAttr(4.0)
rect_light.CreateHeightAttr(2.0)

print(f"""
  RectLight = a rectangular panel of light (studio softbox).
  The physical size (width/height) determines shadow softness.
  Larger panel = softer shadows.

  Like all UsdLux lights it is XFORMABLE — positioned and rotated
  like any other prim using xformOp transforms.

  Key attributes:
    width  = {rect_light.GetWidthAttr().Get()}
    height = {rect_light.GetHeightAttr().Get()}
    intensity = {rect_light.GetIntensityAttr().Get()}
""")

# ── LIGHT 4: DomeLight ───────────────────────────────────────────────
print(SEP)
print("  LIGHT 4 — DomeLight (environment / HDRI)")
print(SEP)

dome = UsdLux.DomeLight.Define(stage, "/World/Lights/Environment")
dome.CreateIntensityAttr(0.5)
dome.CreateColorAttr(Gf.Vec3f(0.5, 0.6, 0.8))   # sky blue
# In production you'd set a real HDRI texture:
# dome.CreateTextureFileAttr("./textures/studio_hdri.exr")

print(f"""
  DomeLight = infinite environment sphere surrounding the scene.
  Provides image-based lighting (IBL) from an HDRI texture.
  No position — it wraps the entire scene.

  inputs:textureFile = path to an .exr or .hdr HDRI image
  Without a texture it uses a solid colour (set above to sky blue).

  Most production renders use DomeLight as the primary light source
  combined with a DistantLight or key SphereLight.
""")

# ── ATTRIBUTE COMPARISON ─────────────────────────────────────────────
print(SEP)
print("  ATTRIBUTE COMPARISON — intensity vs exposure vs radius")
print(SEP)
print("""
  intensity   Controls raw brightness in lumens/nits
              intensity=1000 → twice as bright as intensity=500

  exposure    Adjusts brightness in PHOTOGRAPHIC STOPS
              exposure=1  → 2× brighter (one stop up)
              exposure=-1 → 0.5× dimmer (one stop down)
              exposure=0  → no change (default)
              Final brightness = intensity × 2^exposure

  radius      On SphereLight ONLY — controls ANGULAR SIZE
              Larger radius = physically larger light source
              → softer shadows, broader spread
              Does NOT affect brightness

  color       RGB tint of the emitted light
              (1,1,1) = white, (1,0.9,0.7) = warm, (0.7,0.8,1) = cool

  EXAM TRAPS:
  ❌ "fStop controls exposure time" → fStop is a CAMERA attr, not a light
  ❌ "radius controls brightness"  → radius controls SOFTNESS
  ❌ "lights are immutable"        → lights ARE Xformable
  ❌ "shadows are automatic"       → shadows need explicit configuration
""")

# ── EXPORT ───────────────────────────────────────────────────────────
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(SCRIPT_DIR, "viz_lights.usda")
if os.path.exists(output_path): os.remove(output_path)
stage.Export(output_path)
print(f"  Saved → {output_path}")
print(f"  Open in usdview:")
print(f"    .\\scripts\\usdview.bat {output_path}")
print(f"""
  In usdview — what to look for:
    Enable Hydra Storm renderer for physically based shading.

    /World/Lights/PointLight  (radius=0.5) vs
    /World/Lights/SoftLight   (radius=3.0)
    → Compare the shadow sharpness on the spheres

    Click any light in Scenegraph:
      Properties panel → see all light attributes
      intensity, color, radius etc.

    Rotate the DistantLight (/World/Lights/Sun):
      Change xformOp:rotateXYZ → watch the whole scene lighting shift
      Position has NO effect on DistantLight — only rotation matters
""")
