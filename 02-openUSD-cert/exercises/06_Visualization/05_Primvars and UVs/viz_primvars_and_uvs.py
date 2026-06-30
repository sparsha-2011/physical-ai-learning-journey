"""
Visualization Exercise — Primvars and UVs
==========================================
Understand primvar interpolation modes and how UVs connect
geometry to textures through the shading network.

TOPICS:
  primvars — per-element data on geometry
  interpolation modes — constant, uniform, vertex, faceVarying
  primvars:st — the UV coordinate primvar
  UsdPrimvarReader — reads primvars into the shader network
  UsdUVTexture — samples a texture using UV coordinates

Run: python viz_primvars_and_uvs.py
"""

from pxr import Usd, UsdGeom, UsdShade, UsdLux, Sdf, Vt, Gf
import os

SEP = "=" * 65
stage = Usd.Stage.CreateInMemory()
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
UsdGeom.Xform.Define(stage, "/World")
UsdGeom.Xform.Define(stage, "/World/Geometry")
UsdGeom.Xform.Define(stage, "/World/Looks")

# Dome light — needed for smooth shaded mode to show colour
dome = UsdLux.DomeLight.Define(stage, "/World/Light")
dome.CreateIntensityAttr(1.0)

# ── HELPER: 2×2 grid of 4 quads, 9 points, upright facing camera ─────
# Using a multi-face grid instead of a single quad so that
# vertex vs faceVarying interpolation is actually visually different.
# A single quad looks identical for both — difference only shows at
# shared edges between multiple faces.
def make_grid(path, tx=0.0):
    mesh = UsdGeom.Mesh.Define(stage, path)
    UsdGeom.XformCommonAPI(mesh).SetTranslate(Gf.Vec3d(tx, 1.5, 0))

    # 9 points — 3×3 grid standing upright (in XY plane)
    #  6─7─8
    #  3─4─5
    #  0─1─2
    mesh.GetPointsAttr().Set(Vt.Vec3fArray([
        Gf.Vec3f(-1, -1, 0),  # 0 bottom-left
        Gf.Vec3f( 0, -1, 0),  # 1 bottom-mid
        Gf.Vec3f( 1, -1, 0),  # 2 bottom-right
        Gf.Vec3f(-1,  0, 0),  # 3 mid-left
        Gf.Vec3f( 0,  0, 0),  # 4 centre  ← SHARED by all 4 faces
        Gf.Vec3f( 1,  0, 0),  # 5 mid-right
        Gf.Vec3f(-1,  1, 0),  # 6 top-left
        Gf.Vec3f( 0,  1, 0),  # 7 top-mid
        Gf.Vec3f( 1,  1, 0),  # 8 top-right
    ]))

    # 4 faces — each is a quad
    mesh.GetFaceVertexCountsAttr().Set(Vt.IntArray([4, 4, 4, 4]))

    # face 0: bottom-left  face 1: bottom-right
    # face 2: top-left     face 3: top-right
    # Point 4 (centre) is SHARED by all 4 faces
    mesh.GetFaceVertexIndicesAttr().Set(Vt.IntArray([
        0, 1, 4, 3,   # face 0 — bottom-left quad
        1, 2, 5, 4,   # face 1 — bottom-right quad
        3, 4, 7, 6,   # face 2 — top-left quad
        4, 5, 8, 7,   # face 3 — top-right quad
    ]))
    mesh.GetSubdivisionSchemeAttr().Set(UsdGeom.Tokens.none)
    mesh.GetDoubleSidedAttr().Set(True)
    mesh.GetExtentAttr().Set(Vt.Vec3fArray([
        Gf.Vec3f(-1, -1, 0), Gf.Vec3f(1, 1, 0)
    ]))
    return mesh

# ── STEP 1: INTERPOLATION MODES ──────────────────────────────────────
print(SEP)
print("  STEP 1 — The four primvar interpolation modes")
print(SEP)
print("""
  constant    — one value for the entire prim
  uniform     — one value per FACE
  vertex      — one value per POINT (smoothly interpolated across shared edges)
  faceVarying — one value per FACE-VERTEX (hard colour breaks at every face edge)

  KEY DISTINCTION — vertex vs faceVarying:
  On a SINGLE quad they look identical — both give 4 values for 4 corners.
  The difference only shows on MULTI-FACE meshes at SHARED edges:

    vertex:      point 4 (centre) = ONE colour shared by all 4 faces
                 → smooth gradient flowing across the whole mesh

    faceVarying: point 4 appears 4 times (once per face that uses it)
                 → each face gets its OWN colour at the centre
                 → hard colour break at every face boundary

  This is why UVs always use faceVarying — at a seam, the same 3D vertex
  needs DIFFERENT UV coordinates on different faces.
""")

# ── MESH A: constant ─────────────────────────────────────────────────
print(SEP)
print("  MESH A — constant (1 value → entire mesh)")
print(SEP)

mesh_const = make_grid("/World/Geometry/Constant", tx=-8)
UsdGeom.PrimvarsAPI(mesh_const).CreatePrimvar(
    "displayColor",
    Sdf.ValueTypeNames.Color3fArray,
    UsdGeom.Tokens.constant
).Set(Vt.Vec3fArray([Gf.Vec3f(0.8, 0.2, 0.2)]))   # solid red
print("  1 red value → whole mesh is one flat colour")

# ── MESH B: uniform ──────────────────────────────────────────────────
print()
print(SEP)
print("  MESH B — uniform (1 value per FACE = 4 values)")
print(SEP)

mesh_uniform = make_grid("/World/Geometry/Uniform", tx=-3)
UsdGeom.PrimvarsAPI(mesh_uniform).CreatePrimvar(
    "displayColor",
    Sdf.ValueTypeNames.Color3fArray,
    UsdGeom.Tokens.uniform
).Set(Vt.Vec3fArray([
    Gf.Vec3f(1.0, 0.2, 0.2),   # face 0 — red
    Gf.Vec3f(0.2, 0.7, 0.2),   # face 1 — green
    Gf.Vec3f(0.2, 0.4, 1.0),   # face 2 — blue
    Gf.Vec3f(1.0, 0.8, 0.1),   # face 3 — yellow
]))
print("  4 values (one per face) → each quad is a flat solid colour")
print("  Hard boundary between faces — no interpolation across edges")

# ── MESH C: vertex ───────────────────────────────────────────────────
print()
print(SEP)
print("  MESH C — vertex (1 value per POINT = 9 values)")
print(SEP)

mesh_vert = make_grid("/World/Geometry/Vertex", tx=3)

# 9 values — one per point in the 3×3 grid
# The centre point (index 4) is SHARED by all 4 faces
# It gets ONE colour which smoothly blends across all face boundaries
UsdGeom.PrimvarsAPI(mesh_vert).CreatePrimvar(
    "displayColor",
    Sdf.ValueTypeNames.Color3fArray,
    UsdGeom.Tokens.vertex
).Set(Vt.Vec3fArray([
    Gf.Vec3f(1.0, 0.2, 0.2),   # 0 bottom-left  — red
    Gf.Vec3f(1.0, 0.5, 0.0),   # 1 bottom-mid   — orange
    Gf.Vec3f(0.2, 0.7, 0.2),   # 2 bottom-right — green
    Gf.Vec3f(1.0, 0.0, 0.8),   # 3 mid-left     — purple
    Gf.Vec3f(1.0, 1.0, 1.0),   # 4 centre       — WHITE (shared by all 4 faces)
    Gf.Vec3f(0.2, 0.8, 0.8),   # 5 mid-right    — cyan
    Gf.Vec3f(0.2, 0.2, 1.0),   # 6 top-left     — blue
    Gf.Vec3f(0.8, 0.2, 1.0),   # 7 top-mid      — violet
    Gf.Vec3f(0.2, 0.9, 0.4),   # 8 top-right    — lime
]))
print("  9 values (one per point)")
print("  Centre point (index 4) = WHITE — shared by all 4 faces")
print("  → smooth gradient flowing outward from white centre")
print("  → NO hard breaks — colours blend smoothly across face boundaries")

# ── MESH D: faceVarying ──────────────────────────────────────────────
print()
print(SEP)
print("  MESH D — faceVarying (1 value per face-vertex = 16 values)")
print(SEP)

mesh_fv = make_grid("/World/Geometry/FaceVarying", tx=8)

# faceVarying: one value per entry in faceVertexIndices
# faceVertexIndices has 16 entries (4 faces × 4 corners)
# The centre point (index 4) appears 4 times — once per face
# Each time it appears it gets its own independent colour
# → creates hard breaks at face boundaries

# Each face gets its own corner colours
# Face 0 (bottom-left):  corners = points 0,1,4,3
# Face 1 (bottom-right): corners = points 1,2,5,4
# Face 2 (top-left):     corners = points 3,4,7,6
# Face 3 (top-right):    corners = points 4,5,8,7

UsdGeom.PrimvarsAPI(mesh_fv).CreatePrimvar(
    "displayColor",
    Sdf.ValueTypeNames.Color3fArray,
    UsdGeom.Tokens.faceVarying
).Set(Vt.Vec3fArray([
    # face 0 — red gradient
    Gf.Vec3f(1.0, 0.0, 0.0),   # point 0
    Gf.Vec3f(1.0, 0.3, 0.3),   # point 1
    Gf.Vec3f(1.0, 0.0, 0.0),   # point 4 AS SEEN BY FACE 0 → deep red
    Gf.Vec3f(1.0, 0.3, 0.3),   # point 3
    # face 1 — green gradient
    Gf.Vec3f(0.3, 1.0, 0.3),   # point 1
    Gf.Vec3f(0.0, 1.0, 0.0),   # point 2
    Gf.Vec3f(0.0, 1.0, 0.0),   # point 5
    Gf.Vec3f(0.0, 1.0, 0.0),   # point 4 AS SEEN BY FACE 1 → deep green
    # face 2 — blue gradient
    Gf.Vec3f(0.3, 0.3, 1.0),   # point 3
    Gf.Vec3f(0.0, 0.0, 1.0),   # point 4 AS SEEN BY FACE 2 → deep blue
    Gf.Vec3f(0.3, 0.3, 1.0),   # point 7
    Gf.Vec3f(0.0, 0.0, 1.0),   # point 6
    # face 3 — yellow gradient
    Gf.Vec3f(1.0, 1.0, 0.0),   # point 4 AS SEEN BY FACE 3 → yellow
    Gf.Vec3f(1.0, 0.8, 0.0),   # point 5
    Gf.Vec3f(1.0, 0.8, 0.0),   # point 8
    Gf.Vec3f(1.0, 1.0, 0.0),   # point 7
]))
print("  16 values (4 faces × 4 corners = sum of faceVertexCounts)")
print("  Centre point (index 4) appears 4 times:")
print("    → deep red   for face 0")
print("    → deep green for face 1")
print("    → deep blue  for face 2")
print("    → yellow     for face 3")
print("  → HARD colour breaks at every face boundary")
print()
print("  COMPARE MESH C vs MESH D:")
print("  Mesh C (vertex):      centre = white, smooth blend outward")
print("  Mesh D (faceVarying): centre = 4 different colours, hard breaks")
print("  Same geometry. Different interpolation. Very different result.")

# ── STEP 2: UV COORDINATES ────────────────────────────────────────────
print()
print(SEP)
print("  STEP 2 — UV coordinates (primvars:st)")
print(SEP)
print("""
  UVs use faceVarying so that the same 3D vertex can have
  different UV positions on different faces at UV seams.
  primvars:st is ALWAYS authored manually — never auto-generated.
""")

primvar_st = UsdGeom.PrimvarsAPI(mesh_fv).CreatePrimvar(
    "st",
    Sdf.ValueTypeNames.TexCoord2fArray,
    UsdGeom.Tokens.faceVarying
)
# Each face maps to its own 0→1 UV square
primvar_st.Set(Vt.Vec2fArray([
    # face 0
    Gf.Vec2f(0,0), Gf.Vec2f(0.5,0), Gf.Vec2f(0.5,0.5), Gf.Vec2f(0,0.5),
    # face 1
    Gf.Vec2f(0.5,0), Gf.Vec2f(1,0), Gf.Vec2f(1,0.5), Gf.Vec2f(0.5,0.5),
    # face 2
    Gf.Vec2f(0,0.5), Gf.Vec2f(0.5,0.5), Gf.Vec2f(0.5,1), Gf.Vec2f(0,1),
    # face 3
    Gf.Vec2f(0.5,0.5), Gf.Vec2f(1,0.5), Gf.Vec2f(1,1), Gf.Vec2f(0.5,1),
]))
print("  primvars:st added to FaceVarying mesh — maps 4 faces across UV space")

# ── SUMMARY ──────────────────────────────────────────────────────────
print()
print(SEP)
print("  SUMMARY — the four modes side by side")
print(SEP)
print(f"""
  {'Mode':<14} {'Values needed':<20} {'What each value maps to':<30} Visual result
  {'─'*85}
  {'constant':<14} {'1':<20} {'Entire prim':<30} Solid flat colour
  {'uniform':<14} {'1 per face':<20} {'Each face':<30} Flat per-face colour, hard boundaries
  {'vertex':<14} {'1 per point':<20} {'Each point (shared)':<30} Smooth gradient across whole mesh
  {'faceVarying':<14} {'1 per face-vertex':<20} {'Each face-vertex independently':<30} Hard breaks at every face edge
""")

# ── EXPORT ───────────────────────────────────────────────────────────
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(SCRIPT_DIR, "viz_primvars_and_uvs.usda")
if os.path.exists(output_path): os.remove(output_path)
stage.Export(output_path)
print(f"  Saved → {output_path}")
print(f"  Open in usdview:")
print(f"    .\\scripts\\usdview.bat {output_path}")
print(f"""
  In usdview — press F to frame, must be in Smooth Shaded mode:

  Left to right:
    /World/Geometry/Constant     → solid red (1 value, whole mesh)
    /World/Geometry/Uniform      → 4 solid colour quads (1 per face, hard edges)
    /World/Geometry/Vertex       → smooth rainbow gradient, white centre
                                   → colours blend SMOOTHLY across face boundaries
    /World/Geometry/FaceVarying  → 4 separate colour zones, hard breaks at centre
                                   → same geometry as Vertex but NO smooth blending

  THE KEY COMPARISON: click Vertex then FaceVarying
    Both are 2×2 grids of 4 faces.
    Vertex:      centre point = ONE white value shared by all 4 faces → smooth
    FaceVarying: centre point = 4 independent values (one per face) → hard break

  This is why UVs always use faceVarying — at a UV seam, the same 3D
  vertex needs completely different UV coordinates on each side of the seam.
""")