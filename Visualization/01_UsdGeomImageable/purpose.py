"""
UsdGeomImageable — PURPOSE DEMO (usdview compatible)
======================================================
This script creates TWO separate scenes so you can compare them
side by side in usdview WITHOUT needing View -> Show By Purpose.

  purpose_demo_ALL.usda    → everything visible (all purposes shown)
  purpose_demo_RENDER.usda → only render purpose prim shown
  purpose_demo_PROXY.usda  → only proxy purpose prim shown

The character has three representations:
  HeroMesh    purpose="render"  big orange sphere (3 units radius)
  ProxyMesh   purpose="proxy"   small grey sphere (1 unit radius)
  RigControl  purpose="guide"   tiny cyan sphere above head

HOW TO SEE THE DIFFERENCE:
  Open all three files in separate usdview windows and compare.
  Each file forces a different representation to be "default"
  so usdview shows it without any special filter settings.

Run: python purpose_demo.py
Then open each .usda file in usdview and press F to frame.
"""

import os
from pxr import Usd, UsdGeom, Gf

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def add_ground(stage):
    """Add a grey ground plane so there is always something to frame."""
    ground = UsdGeom.Cube.Define(stage, "/World/Ground")
    ground.GetSizeAttr().Set(1.0)                                    # unit cube
    UsdGeom.XformCommonAPI(ground).SetScale(Gf.Vec3f(40, 0.1, 40))  # flat slab
    UsdGeom.XformCommonAPI(ground).SetTranslate(Gf.Vec3d(0, -4, 0)) # well below spheres
    ground.GetDisplayColorAttr().Set([(0.2, 0.2, 0.2)])

# ─────────────────────────────────────────────────────────────────────
# SCENE 1 — ALL THREE REPRESENTATIONS VISIBLE
# We set purpose="default" on all three so usdview shows everything
# This is the "see the full picture" file
# ─────────────────────────────────────────────────────────────────────
s1 = Usd.Stage.CreateInMemory()
UsdGeom.SetStageUpAxis(s1, UsdGeom.Tokens.y)
UsdGeom.SetStageMetersPerUnit(s1, 0.01)

char1 = UsdGeom.Xform.Define(s1, "/World/Character")

# Hero — big orange sphere
hero1 = UsdGeom.Sphere.Define(s1, "/World/Character/HeroMesh")
hero1.GetRadiusAttr().Set(3.0)
hero1.GetDisplayColorAttr().Set([(0.9, 0.5, 0.1)])  # orange
# NOTE: purpose = "default" here so usdview shows it without filtering

# Proxy — small grey sphere, offset to the right so you can see both
proxy1 = UsdGeom.Sphere.Define(s1, "/World/Character/ProxyMesh")
proxy1.GetRadiusAttr().Set(1.0)
proxy1.GetDisplayColorAttr().Set([(0.6, 0.6, 0.6)])  # grey
UsdGeom.XformCommonAPI(proxy1).SetTranslate(Gf.Vec3d(7, 0, 0))

# Guide — tiny cyan sphere above hero
guide1 = UsdGeom.Sphere.Define(s1, "/World/Character/RigControl")
guide1.GetRadiusAttr().Set(0.4)
guide1.GetDisplayColorAttr().Set([(0.0, 1.0, 1.0)])  # cyan
UsdGeom.XformCommonAPI(guide1).SetTranslate(Gf.Vec3d(0, 5, 0))

# Labels via display colour make it easy to identify:
# Orange = what the renderer would use
# Grey   = what the artist sees in viewport
# Cyan   = what the rigger sees

add_ground(s1)
path1 = os.path.join(SCRIPT_DIR, "purpose_ALL.usda")
s1.Export(path1)
print(f"Scene 1 saved → {path1}")
print("  Shows: all three — big orange + small grey + tiny cyan")


# ─────────────────────────────────────────────────────────────────────
# SCENE 2 — ONLY THE HERO (what a renderer sees)
# Hide proxy and guide by making them invisible
# This simulates what the renderer would show
# ─────────────────────────────────────────────────────────────────────
s2 = Usd.Stage.CreateInMemory()
UsdGeom.SetStageUpAxis(s2, UsdGeom.Tokens.y)
UsdGeom.SetStageMetersPerUnit(s2, 0.01)

char2 = UsdGeom.Xform.Define(s2, "/World/Character")

hero2 = UsdGeom.Sphere.Define(s2, "/World/Character/HeroMesh")
hero2.GetRadiusAttr().Set(3.0)
hero2.GetDisplayColorAttr().Set([(0.9, 0.5, 0.1)])  # orange

proxy2 = UsdGeom.Sphere.Define(s2, "/World/Character/ProxyMesh")
proxy2.GetRadiusAttr().Set(1.0)
proxy2.GetDisplayColorAttr().Set([(0.6, 0.6, 0.6)])
UsdGeom.XformCommonAPI(proxy2).SetTranslate(Gf.Vec3d(7, 0, 0))
UsdGeom.Imageable(proxy2.GetPrim()).MakeInvisible()   # ← hidden

guide2 = UsdGeom.Sphere.Define(s2, "/World/Character/RigControl")
guide2.GetRadiusAttr().Set(0.4)
guide2.GetDisplayColorAttr().Set([(0.0, 1.0, 1.0)])
UsdGeom.XformCommonAPI(guide2).SetTranslate(Gf.Vec3d(0, 5, 0))
UsdGeom.Imageable(guide2.GetPrim()).MakeInvisible()   # ← hidden

add_ground(s2)
path2 = os.path.join(SCRIPT_DIR, "purpose_RENDER_ONLY.usda")
s2.Export(path2)
print(f"Scene 2 saved → {path2}")
print("  Shows: ONLY the big orange sphere (render quality)")


# ─────────────────────────────────────────────────────────────────────
# SCENE 3 — ONLY THE PROXY (what an artist's viewport sees)
# Hide hero and guide, show only the proxy
# This simulates what the layout artist would see
# ─────────────────────────────────────────────────────────────────────
s3 = Usd.Stage.CreateInMemory()
UsdGeom.SetStageUpAxis(s3, UsdGeom.Tokens.y)
UsdGeom.SetStageMetersPerUnit(s3, 0.01)

char3 = UsdGeom.Xform.Define(s3, "/World/Character")

hero3 = UsdGeom.Sphere.Define(s3, "/World/Character/HeroMesh")
hero3.GetRadiusAttr().Set(3.0)
hero3.GetDisplayColorAttr().Set([(0.9, 0.5, 0.1)])
UsdGeom.Imageable(hero3.GetPrim()).MakeInvisible()    # ← hidden

proxy3 = UsdGeom.Sphere.Define(s3, "/World/Character/ProxyMesh")
proxy3.GetRadiusAttr().Set(1.0)
proxy3.GetDisplayColorAttr().Set([(0.6, 0.6, 0.6)])

guide3 = UsdGeom.Sphere.Define(s3, "/World/Character/RigControl")
guide3.GetRadiusAttr().Set(0.4)
guide3.GetDisplayColorAttr().Set([(0.0, 1.0, 1.0)])
UsdGeom.XformCommonAPI(guide3).SetTranslate(Gf.Vec3d(0, 3, 0))
UsdGeom.Imageable(guide3.GetPrim()).MakeInvisible()   # ← hidden

add_ground(s3)
path3 = os.path.join(SCRIPT_DIR, "purpose_PROXY_ONLY.usda")
s3.Export(path3)
print(f"Scene 3 saved → {path3}")
print("  Shows: ONLY the small grey sphere (viewport stand-in)")


# ─────────────────────────────────────────────────────────────────────
# SCENE 4 — ONLY THE GUIDE (what a rigger sees)
# ─────────────────────────────────────────────────────────────────────
s4 = Usd.Stage.CreateInMemory()
UsdGeom.SetStageUpAxis(s4, UsdGeom.Tokens.y)
UsdGeom.SetStageMetersPerUnit(s4, 0.01)

char4 = UsdGeom.Xform.Define(s4, "/World/Character")

hero4 = UsdGeom.Sphere.Define(s4, "/World/Character/HeroMesh")
hero4.GetRadiusAttr().Set(3.0)
hero4.GetDisplayColorAttr().Set([(0.9, 0.5, 0.1)])
UsdGeom.Imageable(hero4.GetPrim()).MakeInvisible()    # ← hidden

proxy4 = UsdGeom.Sphere.Define(s4, "/World/Character/ProxyMesh")
proxy4.GetRadiusAttr().Set(1.0)
proxy4.GetDisplayColorAttr().Set([(0.6, 0.6, 0.6)])
UsdGeom.Imageable(proxy4.GetPrim()).MakeInvisible()   # ← hidden

guide4 = UsdGeom.Sphere.Define(s4, "/World/Character/RigControl")
guide4.GetRadiusAttr().Set(0.4)
guide4.GetDisplayColorAttr().Set([(0.0, 1.0, 1.0)])
UsdGeom.XformCommonAPI(guide4).SetTranslate(Gf.Vec3d(0, 3, 0))
# guide is NOT hidden — this is what the rigger sees

add_ground(s4)
path4 = os.path.join(SCRIPT_DIR, "purpose_GUIDE_ONLY.usda")
s4.Export(path4)
print(f"Scene 4 saved → {path4}")
print("  Shows: ONLY the tiny cyan sphere (rig control)")


# ─────────────────────────────────────────────────────────────────────
# PRINT USDA OF SCENE 1 SO YOU CAN SEE THE STRUCTURE
# ─────────────────────────────────────────────────────────────────────
print()
print("=== USDA of purpose_ALL.usda ===")
print(s1.ExportToString(addSourceFileComment=False))

print("=" * 60)
print("OPEN EACH FILE IN USDVIEW AND PRESS F:")
print()
print(f"  ALL visible:    .\\scripts\\usdview.bat {path1}")
print(f"  Render only:    .\\scripts\\usdview.bat {path2}")
print(f"  Proxy only:     .\\scripts\\usdview.bat {path3}")
print(f"  Guide only:     .\\scripts\\usdview.bat {path4}")
print()
print("In real production:")
print("  The renderer opens the scene and filters for purpose='render'")
print("  so it only sees the big orange sphere.")
print("  The layout artist's viewport shows purpose='proxy'")
print("  so they only see the small grey sphere (fast to load).")
print("  The rigger's tool shows purpose='guide'")
print("  so they see the rig controls.")
print("  Same USD file. Same prims. Different consumers see different things.")
print("=" * 60)