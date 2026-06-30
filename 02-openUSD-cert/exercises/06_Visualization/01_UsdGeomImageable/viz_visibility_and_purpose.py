"""
Visualization Exercise — Visibility and Purpose
=================================================
Understand how visibility and purpose control what renders
and what appears in different rendering contexts.

TOPICS:
  UsdGeomImageable — base class for all renderable prims
  visibility — inherited, shows/hides in all render contexts
  purpose — render, proxy, guide, default
  ComputeVisibility() — resolves inherited visibility
  ComputePurpose() — resolves inherited purpose

Run: python viz_visibility_and_purpose.py
"""

from pxr import Usd, UsdGeom, Sdf, Vt, Gf
import os

SEP = "=" * 65
stage = Usd.Stage.CreateInMemory()
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
UsdGeom.Xform.Define(stage, "/World")

# ── STEP 1: VISIBILITY ────────────────────────────────────────────────
print(SEP)
print("  STEP 1 — Visibility")
print(SEP)
print("""
  visibility = "inherited"  (default) — visible unless parent is invisible
  visibility = "invisible"            — hidden, not rendered

  Visibility INHERITS DOWN the hierarchy.
  If a parent is invisible, ALL children are invisible
  regardless of their own visibility setting.
""")

# Root group — visible
group = UsdGeom.Xform.Define(stage, "/World/VisGroup")

# Sphere A — explicitly visible
sphere_a = UsdGeom.Sphere.Define(stage, "/World/VisGroup/SphereA")
UsdGeom.XformCommonAPI(sphere_a).SetTranslate(Gf.Vec3d(-4, 1, 0))
UsdGeom.Imageable(sphere_a).MakeVisible()

# Sphere B — explicitly invisible
sphere_b = UsdGeom.Sphere.Define(stage, "/World/VisGroup/SphereB")
UsdGeom.XformCommonAPI(sphere_b).SetTranslate(Gf.Vec3d(0, 1, 0))
UsdGeom.Imageable(sphere_b).MakeInvisible()

# Sphere C — inherits from parent (visible because parent is visible)
sphere_c = UsdGeom.Sphere.Define(stage, "/World/VisGroup/SphereC")
UsdGeom.XformCommonAPI(sphere_c).SetTranslate(Gf.Vec3d(4, 1, 0))
# No visibility set — inherits parent's "inherited" = visible

print(f"  {'Prim':<35} {'visibility attr':<20} {'ComputeVisibility()'}")
print("  " + "-" * 75)
for prim, label in [
    (sphere_a.GetPrim(), "SphereA (explicit visible)"),
    (sphere_b.GetPrim(), "SphereB (explicit invisible)"),
    (sphere_c.GetPrim(), "SphereC (inherits)"),
]:
    imageable   = UsdGeom.Imageable(prim)
    vis_attr    = imageable.GetVisibilityAttr().Get()
    computed    = imageable.ComputeVisibility()
    print(f"  {label:<35} {str(vis_attr):<20} {computed}")

print()

# Now make the GROUP invisible — affects ALL children
UsdGeom.Imageable(group).MakeInvisible()
print(f"  After making VisGroup INVISIBLE:")
for prim, label in [
    (sphere_a.GetPrim(), "SphereA"),
    (sphere_b.GetPrim(), "SphereB"),
    (sphere_c.GetPrim(), "SphereC"),
]:
    computed = UsdGeom.Imageable(prim).ComputeVisibility()
    print(f"    {label:<35} ComputeVisibility() = {computed}")

print(f"""
  Even though SphereA has visibility="inherited" (visible),
  the PARENT VisGroup is invisible → ALL children inherit invisible.
  ComputeVisibility() walks up the hierarchy to resolve this.
""")

# Restore group visibility
UsdGeom.Imageable(group).MakeVisible()

# ── STEP 2: PURPOSE ───────────────────────────────────────────────────
print(SEP)
print("  STEP 2 — Purpose tokens")
print(SEP)
print("""
  purpose controls WHICH RENDERING CONTEXT a prim appears in:

  "render"   → full quality render only (heavy geometry)
  "proxy"    → viewport stand-in (low-res representation)
  "guide"    → rig controls, helper geometry — NEVER rendered
  "default"  → appears in all contexts (fallback)
""")

UsdGeom.Xform.Define(stage, "/World/PurposeGroup")

# Render prim — full quality geometry
render_prim = UsdGeom.Sphere.Define(
    stage, "/World/PurposeGroup/FullResModel")
UsdGeom.XformCommonAPI(render_prim).SetTranslate(Gf.Vec3d(-6, 1, -4))
UsdGeom.Imageable(render_prim).GetPurposeAttr().Set(
    UsdGeom.Tokens.render)
render_prim.GetRadiusAttr().Set(1.5)  # bigger = "more detailed"

# Proxy prim — low-res stand-in at same location
proxy_prim = UsdGeom.Cube.Define(
    stage, "/World/PurposeGroup/LowResProxy")
UsdGeom.XformCommonAPI(proxy_prim).SetTranslate(Gf.Vec3d(-6, 1, -4))
UsdGeom.Imageable(proxy_prim).GetPurposeAttr().Set(
    UsdGeom.Tokens.proxy)

# Guide prim — rig control, never renders
guide_prim = UsdGeom.Sphere.Define(
    stage, "/World/PurposeGroup/RigControl")
UsdGeom.XformCommonAPI(guide_prim).SetTranslate(Gf.Vec3d(0, 3, -4))
UsdGeom.Imageable(guide_prim).GetPurposeAttr().Set(
    UsdGeom.Tokens.guide)
guide_prim.GetRadiusAttr().Set(0.3)

# Default prim — appears everywhere
default_prim = UsdGeom.Sphere.Define(
    stage, "/World/PurposeGroup/DefaultObject")
UsdGeom.XformCommonAPI(default_prim).SetTranslate(Gf.Vec3d(6, 1, -4))
UsdGeom.Imageable(default_prim).GetPurposeAttr().Set(
    UsdGeom.Tokens.default_)

print(f"  {'Prim':<35} {'purpose':<12} {'ComputePurpose()'}")
print("  " + "-" * 65)
for prim, label in [
    (render_prim.GetPrim(), "FullResModel"),
    (proxy_prim.GetPrim(),  "LowResProxy"),
    (guide_prim.GetPrim(),  "RigControl"),
    (default_prim.GetPrim(),"DefaultObject"),
]:
    imageable = UsdGeom.Imageable(prim)
    purpose   = imageable.GetPurposeAttr().Get()
    computed  = imageable.ComputePurpose()
    print(f"  {label:<35} {str(purpose):<12} {computed}")

print(f"""
  In usdview:
    FullResModel (render) — only in final render passes
    LowResProxy  (proxy)  — visible in viewport as stand-in
    RigControl   (guide)  — visible in rigging context only
    DefaultObject(default)— visible everywhere

  The purpose system lets artists work with proxy geometry
  in the viewport while renderers use the full-quality mesh.
""")

# ── STEP 3: UsdGeomImageable ──────────────────────────────────────────
print(SEP)
print("  STEP 3 — UsdGeomImageable is NOT about shape or materials")
print(SEP)
print("""
  UsdGeomImageable is the BASE CLASS for all renderable prims.
  It provides exactly TWO things:
    1. visibility attribute
    2. purpose attribute

  That is ALL it does. It is NOT:
  ❌ a geometry shape schema
  ❌ a material management API
  ❌ related to lighting or textures

  Every renderable prim (Mesh, Sphere, Camera, Light) inherits from
  UsdGeomImageable which is why they ALL have visibility and purpose.

  UsdGeomXformable inherits from UsdGeomImageable and adds transforms.
  UsdGeomGprim inherits from UsdGeomXformable and adds geometry.
""")

# ── EXPORT ───────────────────────────────────────────────────────────
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(SCRIPT_DIR, "viz_visibility_and_purpose.usda")
if os.path.exists(output_path): os.remove(output_path)
stage.Export(output_path)
print(f"  Saved → {output_path}")
print(f"  Open in usdview:")
print(f"    .\\scripts\\usdview.bat {output_path}")
print(f"""
  In usdview:
    /World/VisGroup — click each sphere:
      Properties panel → visibility attribute
      SphereA = "inherited", SphereB = "invisible", SphereC = "inherited"
      SphereB is hidden in viewport (invisible)

    /World/PurposeGroup:
      LowResProxy (cube) → visible in viewport (proxy purpose)
      FullResModel (sphere) → may be hidden (render purpose = final render)
      RigControl → hidden (guide purpose)
""")
