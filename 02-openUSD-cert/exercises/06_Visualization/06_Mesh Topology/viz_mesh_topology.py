"""
Visualization Exercise — Mesh Topology
========================================
Understand how points, faceVertexCounts, and faceVertexIndices
work together to build a 3D mesh from scratch.

TOPICS:
  UsdGeomMesh — points, faceVertexCounts, faceVertexIndices
  subdivisionScheme — none vs catmullClark
  holeIndices — marking faces as holes
  normals as primvars

Run: python viz_mesh_topology.py
"""

from pxr import Usd, UsdGeom, Sdf, Vt, Gf
import os

SEP = "=" * 65

from pxr import UsdLux

stage = Usd.Stage.CreateInMemory()
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
root  = UsdGeom.Xform.Define(stage, "/World")

# Dome light — lights the whole scene evenly
# Without any light, smooth shaded mode renders everything black
dome = UsdLux.DomeLight.Define(stage, "/World/Light")
dome.CreateIntensityAttr(1.0)

# ── MESH 1: A single flat quad ───────────────────────────────────────
print(SEP)
print("  MESH 1 — A single flat quad (4 points, 1 face)")
print(SEP)

quad = UsdGeom.Mesh.Define(stage, "/World/Quad")
# Points in XY plane (Z=0) — stands upright facing camera, no rotation needed
UsdGeom.XformCommonAPI(quad).SetTranslate(Gf.Vec3d(-6, 1, 0))

points = Vt.Vec3fArray([
    Gf.Vec3f(-1, -1, 0),   # corner 0 — bottom left
    Gf.Vec3f( 1, -1, 0),   # corner 1 — bottom right
    Gf.Vec3f( 1,  1, 0),   # corner 2 — top right
    Gf.Vec3f(-1,  1, 0),   # corner 3 — top left
])
quad.GetPointsAttr().Set(points)
quad.GetFaceVertexCountsAttr().Set(Vt.IntArray([4]))
quad.GetFaceVertexIndicesAttr().Set(Vt.IntArray([0, 1, 2, 3]))
quad.GetSubdivisionSchemeAttr().Set(UsdGeom.Tokens.none)
quad.GetDoubleSidedAttr().Set(True)   # visible from both sides
quad.GetExtentAttr().Set(Vt.Vec3fArray([
    Gf.Vec3f(-1, -1, 0), Gf.Vec3f(1, 1, 0)   # XY plane — correct
]))
# displayColor — gives usdview something to shade with
UsdGeom.PrimvarsAPI(quad).CreatePrimvar(
    "displayColor", Sdf.ValueTypeNames.Color3fArray,
    UsdGeom.Tokens.constant
).Set(Vt.Vec3fArray([Gf.Vec3f(0.8, 0.3, 0.2)]))   # red

print(f"\n  Points:             {len(points)}")
print(f"  Faces:              1  (a single quad)")
print(f"  faceVertexIndices:  4  (= sum of faceVertexCounts = 4)")
print(f"  subdivisionScheme:  none  (flat polygon)")

# ── MESH 2: A cube with shared vertices ──────────────────────────────
print()
print(SEP)
print("  MESH 2 — A cube (8 shared points, 6 faces)")
print(SEP)

cube = UsdGeom.Mesh.Define(stage, "/World/Cube")
# Lift cube above floor so it sits visibly in the scene
UsdGeom.XformCommonAPI(cube).SetTranslate(Gf.Vec3d(0, 1, 0))

cube_points = Vt.Vec3fArray([
    Gf.Vec3f(-1, -1, -1),  # 0 bottom-back-left
    Gf.Vec3f( 1, -1, -1),  # 1 bottom-back-right
    Gf.Vec3f( 1, -1,  1),  # 2 bottom-front-right
    Gf.Vec3f(-1, -1,  1),  # 3 bottom-front-left
    Gf.Vec3f(-1,  1, -1),  # 4 top-back-left
    Gf.Vec3f( 1,  1, -1),  # 5 top-back-right
    Gf.Vec3f( 1,  1,  1),  # 6 top-front-right
    Gf.Vec3f(-1,  1,  1),  # 7 top-front-left
])
cube.GetPointsAttr().Set(cube_points)
cube.GetFaceVertexCountsAttr().Set(Vt.IntArray([4, 4, 4, 4, 4, 4]))
cube.GetFaceVertexIndicesAttr().Set(Vt.IntArray([
    0, 1, 2, 3,   # face 0 — bottom
    4, 5, 6, 7,   # face 1 — top
    0, 1, 5, 4,   # face 2 — back
    2, 3, 7, 6,   # face 3 — front
    0, 3, 7, 4,   # face 4 — left
    1, 2, 6, 5,   # face 5 — right
]))
cube.GetSubdivisionSchemeAttr().Set(UsdGeom.Tokens.none)
cube.GetExtentAttr().Set(Vt.Vec3fArray([
    Gf.Vec3f(-1, -1, -1), Gf.Vec3f(1, 1, 1)
]))
UsdGeom.PrimvarsAPI(cube).CreatePrimvar(
    "displayColor", Sdf.ValueTypeNames.Color3fArray,
    UsdGeom.Tokens.constant
).Set(Vt.Vec3fArray([Gf.Vec3f(0.2, 0.5, 0.8)]))   # blue

print(f"\n  Points:             8  (corners shared between faces)")
print(f"  Faces:              6")
print(f"  faceVertexCounts:   [4,4,4,4,4,4]  (6 quads)")
print(f"  faceVertexIndices:  {6*4}  (= sum of faceVertexCounts = 6×4)")
print(f"  Key: indices length != point count (8) != face count (6)")

# ── MESH 3: Subdivision ──────────────────────────────────────────────
print()
print(SEP)
print("  MESH 3 — Subdivision (catmullClark rounds the cube)")
print(SEP)

subd = UsdGeom.Mesh.Define(stage, "/World/SubdivCube")
UsdGeom.XformCommonAPI(subd).SetTranslate(Gf.Vec3d(6, 1, 0))

# Same 8 points and 6 faces as the cube above
subd.GetPointsAttr().Set(cube_points)
subd.GetFaceVertexCountsAttr().Set(Vt.IntArray([4, 4, 4, 4, 4, 4]))
subd.GetFaceVertexIndicesAttr().Set(Vt.IntArray([
    0,1,2,3, 4,5,6,7, 0,1,5,4, 2,3,7,6, 0,3,7,4, 1,2,6,5
]))
subd.GetExtentAttr().Set(Vt.Vec3fArray([
    Gf.Vec3f(-1,-1,-1), Gf.Vec3f(1,1,1)
]))
UsdGeom.PrimvarsAPI(subd).CreatePrimvar(
    "displayColor", Sdf.ValueTypeNames.Color3fArray,
    UsdGeom.Tokens.constant
).Set(Vt.Vec3fArray([Gf.Vec3f(0.2, 0.7, 0.3)]))   # green

# ONLY difference from Mesh 2: subdivisionScheme = catmullClark
subd.GetSubdivisionSchemeAttr().Set(UsdGeom.Tokens.catmullClark)

print(f"\n  Same 8 points and 6 faces as Mesh 2")
print(f"  Only difference: subdivisionScheme = catmullClark")
print(f"  In usdview: the hard cube becomes a smooth sphere-like shape")
print(f"  Topology is identical — only the DISPLAY changes")

# ── MESH 4: Hole indices ─────────────────────────────────────────────
print()
print(SEP)
print("  MESH 4 — holeIndices (one face removed as a hole)")
print(SEP)

frame = UsdGeom.Mesh.Define(stage, "/World/Frame")
# Position left and lift above floor — geometry is in XY plane (upright)
# so it faces the camera directly without needing a rotation
UsdGeom.XformCommonAPI(frame).SetTranslate(Gf.Vec3d(-12, 2, 0))

# Points defined in XY plane (Z=0) so mesh stands upright
frame.GetPointsAttr().Set(Vt.Vec3fArray([
    Gf.Vec3f(-2, -2, 0), Gf.Vec3f(0, -2, 0), Gf.Vec3f(2, -2, 0),  # row 0
    Gf.Vec3f(-2,  0, 0), Gf.Vec3f(0,  0, 0), Gf.Vec3f(2,  0, 0),  # row 1
    Gf.Vec3f(-2,  2, 0), Gf.Vec3f(0,  2, 0), Gf.Vec3f(2,  2, 0),  # row 2
]))
frame.GetFaceVertexCountsAttr().Set(Vt.IntArray([4, 4, 4, 4]))
frame.GetFaceVertexIndicesAttr().Set(Vt.IntArray([
    0, 1, 4, 3,   # face 0 — top-left quad
    1, 2, 5, 4,   # face 1 — top-right quad
    3, 4, 7, 6,   # face 2 — bottom-left quad
    4, 5, 8, 7,   # face 3 — bottom-right quad  ← the hole
]))
frame.GetSubdivisionSchemeAttr().Set(UsdGeom.Tokens.none)
frame.GetDoubleSidedAttr().Set(True)
frame.GetExtentAttr().Set(Vt.Vec3fArray([
    Gf.Vec3f(-2, -2, 0), Gf.Vec3f(2, 2, 0)
]))
frame.GetHoleIndicesAttr().Set(Vt.IntArray([3]))
UsdGeom.PrimvarsAPI(frame).CreatePrimvar(
    "displayColor", Sdf.ValueTypeNames.Color3fArray,
    UsdGeom.Tokens.constant
).Set(Vt.Vec3fArray([Gf.Vec3f(0.8, 0.7, 0.1)]))   # yellow

print(f"\n  4 faces defined — holeIndices = [3]")
print(f"  Face 3 (bottom-right) exists in topology but is NOT rendered")
print(f"  In usdview: 3 visible quads with a gap at bottom-right")

# ── SUMMARY ──────────────────────────────────────────────────────────
print()
print(SEP)
print("  KEY FACTS TO REMEMBER")
print(SEP)
print("""
  faceVertexIndices length = SUM of faceVertexCounts
    NOT number of points    NOT number of faces

  subdivisionScheme options:
    "none"         → flat polygon mesh (hard edges)
    "catmullClark" → smooth subdivision (default)
    "loop"         → Loop subdivision
    "bilinear"     → bilinear subdivision

  holeIndices = face indices to treat as holes (not rendered)
    The face still exists in topology, just invisible

  doubleSided = True → flat quads visible from both sides
    Without this, flat meshes disappear when camera is behind them

  UVs are NEVER auto-generated — must author primvars:st explicitly
  Normals are primvars with interpolation vertex or faceVarying
""")

# ── EXPORT ───────────────────────────────────────────────────────────
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(SCRIPT_DIR, "viz_mesh_topology.usda")
if os.path.exists(output_path): os.remove(output_path)
stage.Export(output_path)
print(f"  Saved → {output_path}")
print(f"  Open in usdview:")
print(f"    .\\scripts\\usdview.bat {output_path}")
print(f"""
  In usdview — what to look for:
    Press F to frame the whole scene — you should see 4 objects in a row.

    /World/Frame      → far left  — 2×2 grid with bottom-right face missing
    /World/Quad       → left      — single upright flat quad
    /World/Cube       → centre    → hard-edged cube (subdivisionScheme=none)
    /World/SubdivCube → right     → same topology, smooth (catmullClark)

    Press W to toggle wireframe — this is the most important view.
    Wireframe shows the actual polygon edges and makes it clear how
    faceVertexIndices connects the points into faces.

    Click /World/Cube → Properties panel → faceVertexCounts = [4,4,4,4,4,4]
    Click /World/SubdivCube → same faceVertexCounts — identical topology
    The ONLY difference is subdivisionScheme = catmullClark.
""")