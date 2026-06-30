"""
Visualization Exercise — UsdGeomCamera
========================================
Understand every camera attribute and how they affect the view.

TOPICS:
  projection — perspective vs orthographic
  focalLength — controls field of view
  horizontalAperture / verticalAperture — sensor size in mm
  clippingRange — near and far clip planes (IS in the schema)
  fStop + focusDistance — depth of field
  aperture offsets — lens shift
  Camera is Xformable — must explicitly animate with timeSamples

Run: python viz_camera.py
"""

from pxr import Usd, UsdGeom, Sdf, Vt, Gf
import os

SEP = "=" * 65
stage = Usd.Stage.CreateInMemory()
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
UsdGeom.Xform.Define(stage, "/World")
UsdGeom.Xform.Define(stage, "/World/Cameras")
UsdGeom.Xform.Define(stage, "/World/Geometry")

# Some reference geometry to look at
for i, (x, name) in enumerate([(-4,"Left"),(0,"Centre"),(4,"Right")]):
    s = UsdGeom.Sphere.Define(stage, f"/World/Geometry/{name}")
    UsdGeom.XformCommonAPI(s).SetTranslate(Gf.Vec3d(x, 1, 0))
    s.GetRadiusAttr().Set(1.0)
    box = UsdGeom.Cube.Define(stage, f"/World/Geometry/{name}Box")
    UsdGeom.XformCommonAPI(box).SetTranslate(Gf.Vec3d(x, 0.5, -4))

# ── CAMERA 1: Standard perspective ───────────────────────────────────
print(SEP)
print("  CAMERA 1 — Standard perspective (35mm)")
print(SEP)

cam1 = UsdGeom.Camera.Define(stage, "/World/Cameras/StandardPerspective")
UsdGeom.XformCommonAPI(cam1).SetTranslate(Gf.Vec3d(0, 3, 12))
UsdGeom.XformCommonAPI(cam1).SetRotate(Gf.Vec3f(-15, 0, 0))

cam1.GetProjectionAttr().Set(UsdGeom.Tokens.perspective)
cam1.GetFocalLengthAttr().Set(35.0)                    # standard 35mm lens
cam1.GetHorizontalApertureAttr().Set(24.0)             # sensor width in mm
cam1.GetVerticalApertureAttr().Set(13.5)               # sensor height in mm
# 24 / 13.5 = 1.777 = 16:9 aspect ratio
cam1.GetClippingRangeAttr().Set(Gf.Vec2f(0.1, 1000))  # near/far clip

print(f"""
  projection:          perspective
  focalLength:         35.0 mm
  horizontalAperture:  24.0 mm   ← sensor width — in MILLIMETRES not inches
  verticalAperture:    13.5 mm   ← sensor height
  aspectRatio:         {24/13.5:.3f}  (= 16:9)
  clippingRange:       (0.1, 1000)  ← IS in the schema, NOT renderer-only

  EXAM TRAP: "UsdGeomCamera does not support clipping planes" → WRONG
  clippingRange IS a schema attribute defined in UsdGeomCamera.
""")

# ── CAMERA 2: Wide angle vs telephoto ────────────────────────────────
print(SEP)
print("  CAMERA 2 — Wide angle (18mm) vs Telephoto (85mm)")
print(SEP)

cam_wide = UsdGeom.Camera.Define(stage, "/World/Cameras/WideAngle")
UsdGeom.XformCommonAPI(cam_wide).SetTranslate(Gf.Vec3d(-8, 3, 12))
UsdGeom.XformCommonAPI(cam_wide).SetRotate(Gf.Vec3f(-10, 10, 0))
cam_wide.GetProjectionAttr().Set(UsdGeom.Tokens.perspective)
cam_wide.GetFocalLengthAttr().Set(18.0)   # wide — sees a lot
cam_wide.GetHorizontalApertureAttr().Set(24.0)
cam_wide.GetVerticalApertureAttr().Set(13.5)
cam_wide.GetClippingRangeAttr().Set(Gf.Vec2f(0.1, 1000))

cam_tele = UsdGeom.Camera.Define(stage, "/World/Cameras/Telephoto")
UsdGeom.XformCommonAPI(cam_tele).SetTranslate(Gf.Vec3d(8, 3, 12))
UsdGeom.XformCommonAPI(cam_tele).SetRotate(Gf.Vec3f(-10, -10, 0))
cam_tele.GetProjectionAttr().Set(UsdGeom.Tokens.perspective)
cam_tele.GetFocalLengthAttr().Set(85.0)   # telephoto — zoomed in
cam_tele.GetHorizontalApertureAttr().Set(24.0)
cam_tele.GetVerticalApertureAttr().Set(13.5)
cam_tele.GetClippingRangeAttr().Set(Gf.Vec2f(0.1, 1000))

print(f"""
  WideAngle:  focalLength=18mm  → sees much more of the scene
  Telephoto:  focalLength=85mm  → zoomed in, narrow field of view

  FOV formula: 2 × atan(horizontalAperture / (2 × focalLength))
  WideAngle FOV:  2 × atan(24 / (2×18))  = ~67°  (wide)
  Telephoto FOV:  2 × atan(24 / (2×85))  = ~16°  (narrow)

  Shorter focalLength = wider field of view
  Longer focalLength  = narrower field of view (zoom)
""")

# ── CAMERA 3: Orthographic ────────────────────────────────────────────
print(SEP)
print("  CAMERA 3 — Orthographic (no perspective distortion)")
print(SEP)

cam_ortho = UsdGeom.Camera.Define(stage, "/World/Cameras/Orthographic")
UsdGeom.XformCommonAPI(cam_ortho).SetTranslate(Gf.Vec3d(0, 10, 0))
UsdGeom.XformCommonAPI(cam_ortho).SetRotate(Gf.Vec3f(-90, 0, 0))
cam_ortho.GetProjectionAttr().Set(UsdGeom.Tokens.orthographic)
# In orthographic, aperture directly sets the view dimensions (in mm/scene units)
cam_ortho.GetHorizontalApertureAttr().Set(20.0)
cam_ortho.GetVerticalApertureAttr().Set(20.0)
cam_ortho.GetClippingRangeAttr().Set(Gf.Vec2f(0.1, 1000))

print(f"""
  projection: orthographic
  → Objects at any distance appear the SAME SIZE
  → Parallel lines stay parallel — no vanishing point
  → Used for technical drawings, CAD, top-down views
  → focalLength has no effect in orthographic mode
  → horizontalAperture directly sets the view WIDTH in scene units

  EXAM POINT: Only 'perspective' and 'orthographic' exist.
  No fisheye, cylindrical, or spherical projections in UsdGeomCamera.
""")

# ── CAMERA 4: Depth of field ──────────────────────────────────────────
print(SEP)
print("  CAMERA 4 — Depth of field (fStop + focusDistance)")
print(SEP)

cam_dof = UsdGeom.Camera.Define(stage, "/World/Cameras/DepthOfField")
UsdGeom.XformCommonAPI(cam_dof).SetTranslate(Gf.Vec3d(0, 2, 8))
UsdGeom.XformCommonAPI(cam_dof).SetRotate(Gf.Vec3f(-10, 0, 0))
cam_dof.GetProjectionAttr().Set(UsdGeom.Tokens.perspective)
cam_dof.GetFocalLengthAttr().Set(50.0)
cam_dof.GetHorizontalApertureAttr().Set(24.0)
cam_dof.GetVerticalApertureAttr().Set(13.5)
cam_dof.GetClippingRangeAttr().Set(Gf.Vec2f(0.1, 1000))

cam_dof.GetFocusDistanceAttr().Set(8.0)   # focus on the centre sphere
cam_dof.GetFStopAttr().Set(1.4)            # wide open — shallow DOF

print(f"""
  focusDistance = {cam_dof.GetFocusDistanceAttr().Get()} units
    Objects at this distance are perfectly sharp.
    Objects closer or farther will blur.

  fStop = {cam_dof.GetFStopAttr().Get()}  (wide open aperture)
    Low fStop (1.4, 2.8) = shallow depth of field → lots of blur
    High fStop (11, 16)  = deep depth of field → everything sharp
    fStop = 0 = no depth of field (default)

  EXAM TRAP: "fStop controls exposure time" → WRONG
  fStop only controls DEPTH OF FIELD — how much blur.
  Exposure time is shutter speed — a separate concept.
""")

# ── CAMERA 5: Animated camera ─────────────────────────────────────────
print()
print(SEP)
print("  CAMERA 5 — Animated camera (explicit time samples required)")
print(SEP)

stage.SetMetadata("timeCodesPerSecond", 24)
stage.SetMetadata("startTimeCode", 1)
stage.SetMetadata("endTimeCode", 48)

cam_anim = UsdGeom.Camera.Define(stage, "/World/Cameras/AnimatedCam")
cam_anim.GetProjectionAttr().Set(UsdGeom.Tokens.perspective)
cam_anim.GetFocalLengthAttr().Set(35.0)
cam_anim.GetHorizontalApertureAttr().Set(24.0)
cam_anim.GetVerticalApertureAttr().Set(13.5)
cam_anim.GetClippingRangeAttr().Set(Gf.Vec2f(0.1, 1000))

# Animate the camera position — MUST use explicit time samples
# Camera does NOT auto-update. No time samples = no animation.
UsdGeom.XformCommonAPI(cam_anim).SetTranslate(
    Gf.Vec3d(-8, 3, 10), time=1)   # frame 1 — left position
UsdGeom.XformCommonAPI(cam_anim).SetTranslate(
    Gf.Vec3d( 0, 3, 12), time=24)  # frame 24 — centre
UsdGeom.XformCommonAPI(cam_anim).SetTranslate(
    Gf.Vec3d( 8, 3, 10), time=48)  # frame 48 — right position

UsdGeom.XformCommonAPI(cam_anim).SetRotate(
    Gf.Vec3f(-15, 20, 0), time=1)
UsdGeom.XformCommonAPI(cam_anim).SetRotate(
    Gf.Vec3f(-15, 0, 0),  time=24)
UsdGeom.XformCommonAPI(cam_anim).SetRotate(
    Gf.Vec3f(-15,-20, 0), time=48)

print(f"""
  Camera has 3 position keyframes at frames 1, 24, 48.
  USD interpolates between them automatically.

  EXAM TRAP: "UsdGeomCamera auto-updates from animation clips" → WRONG
  The camera does NOT auto-update without timeSamples.
  You must explicitly Set() the transform at each keyframe.
  Without timeSamples the camera is frozen at its default position.
""")

# ── SUMMARY ──────────────────────────────────────────────────────────
print(SEP)
print("  COMPLETE ATTRIBUTE REFERENCE")
print(SEP)
print(f"""
  {'Attribute':<30} {'Type':<12} {'Default':<15} What it does
  {'─'*80}
  {'projection':<30} {'token':<12} {'perspective':<15} perspective or orthographic ONLY
  {'focalLength':<30} {'float':<12} {'50.0 mm':<15} lens-to-image-plane distance
  {'horizontalAperture':<30} {'float':<12} {'20.955 mm':<15} sensor width in MILLIMETRES
  {'verticalAperture':<30} {'float':<12} {'15.291 mm':<15} sensor height in MILLIMETRES
  {'horizontalApertureOffset':<30} {'float':<12} {'0.0':<15} horizontal lens shift
  {'verticalApertureOffset':<30} {'float':<12} {'0.0':<15} vertical lens shift (tilt-shift)
  {'clippingRange':<30} {'float2':<12} {'(1, 1000000)':<15} near/far clip — IS in schema
  {'fStop':<30} {'float':<12} {'0.0 (no DOF)':<15} depth of field aperture
  {'focusDistance':<30} {'float':<12} {'0.0':<15} in-focus plane distance
""")

# ── EXPORT ───────────────────────────────────────────────────────────
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(SCRIPT_DIR, "viz_camera.usda")
if os.path.exists(output_path): os.remove(output_path)
stage.Export(output_path)
print(f"  Saved → {output_path}")
print(f"  Open in usdview:")
print(f"    .\\scripts\\usdview.bat {output_path}")
print(f"""
  In usdview:
    Click any camera in Scenegraph → Properties panel
    → See all attributes: focalLength, clippingRange, fStop etc.

    Click /World/Cameras/AnimatedCam:
      Properties panel → xformOp:translate
      → Click the attribute → see timeSamples listed
      → Scrub the timeline to see the camera move

    Compare WideAngle vs Telephoto cameras:
      Click each → focalLength 18.0 vs 85.0
      → In viewport switch to each camera to see the FOV difference

    Click /World/Cameras/Orthographic:
      Properties panel → projection = "orthographic"
      → Switch viewport to this camera to see parallel projection
""")
