"""Build the RTX presentation from the approved browser mesh and 60 Hz replay."""

from pathlib import Path
import base64
import json
import os
import numpy as np
from pxr import Usd, UsdGeom, UsdLux, UsdShade, Gf, Sdf, Vt
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web/garden-bill-cafe"
OUT = ROOT / "renders/garden/live-rtx"
OUT.mkdir(parents=True, exist_ok=True)
meta = json.loads((WEB / "scene.json").read_text())
motion = json.loads((WEB / "motion.json").read_text())
fit = json.loads((WEB / "thread-fit.json").read_text())
thread = np.memmap(
    WEB / "thread.bin", dtype="<f4", mode="r", shape=(fit["frames"], fit["points"], 3)
)
buf = np.memmap(WEB / "scene.bin", mode="r", dtype="u1")
dst = OUT / "cafe.usdc"
working = OUT / f"cafe-{os.getpid()}.building.usdc"
stage = Usd.Stage.CreateNew(str(working))
UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
UsdGeom.SetStageMetersPerUnit(stage, 1)
stage.SetTimeCodesPerSecond(1 / motion["dt"])
stage.SetStartTimeCode(0)
stage.SetEndTimeCode(len(thread) - 1)
T = Sdf.ValueTypeNames


def material(i, m):
    path = f"/Looks/M{i}"
    mat = UsdShade.Material.Define(stage, path)
    s = UsdShade.Shader.Define(stage, path + "/Surface")
    s.CreateIdAttr("UsdPreviewSurface")
    mat.CreateSurfaceOutput().ConnectToSource(s.ConnectableAPI(), "surface")
    for name, value in [
        ("roughness", m["roughness"]),
        ("metallic", m["metalness"]),
        ("opacity", m.get("opacity", 1.0)),
    ]:
        s.CreateInput(name, T.Float).Set(value)
    s.CreateInput("diffuseColor", T.Color3f).Set(Gf.Vec3f(*m["color"]))
    for key, name, channel in [
        ("map", "diffuseColor", "rgb"),
        ("roughnessMap", "roughness", "g"),
        ("metalnessMap", "metallic", "b"),
        ("normalMap", "normal", "rgb"),
    ]:
        if key not in m:
            continue
        reader = UsdShade.Shader.Define(stage, path + "/UV")
        reader.CreateIdAttr("UsdPrimvarReader_float2")
        reader.CreateInput("varname", T.Token).Set("st")
        uv = reader
        if key + "Transform" in m:
            tr = m[key + "Transform"]
            uv = UsdShade.Shader.Define(stage, path + "/" + key + "UV")
            uv.CreateIdAttr("UsdTransform2d")
            uv.CreateInput("in", T.Float2).ConnectToSource(
                reader.ConnectableAPI(), "result"
            )
            uv.CreateInput("scale", T.Float2).Set(Gf.Vec2f(*tr["repeat"]))
            uv.CreateInput("translation", T.Float2).Set(Gf.Vec2f(*tr["offset"]))
        tex = UsdShade.Shader.Define(stage, path + "/" + key)
        tex.CreateIdAttr("UsdUVTexture")
        tex.CreateInput("file", T.Asset).Set(os.path.relpath(WEB / m[key], OUT))
        tex.CreateInput("st", T.Float2).ConnectToSource(uv.ConnectableAPI(), "result")
        tex.CreateInput("sourceColorSpace", T.Token).Set(
            "sRGB" if key == "map" else "raw"
        )
        for axis in ["wrapS", "wrapT"]:
            tex.CreateInput(axis, T.Token).Set(
                "clamp" if key + "Transform" in m else "repeat"
            )
        if key == "map":
            tex.CreateInput("scale", T.Float4).Set(Gf.Vec4f(*m["color"], 1))
        if key == "normalMap":
            tex.CreateInput("scale", T.Float4).Set(Gf.Vec4f(2, 2, 2, 1))
            tex.CreateInput("bias", T.Float4).Set(Gf.Vec4f(-1, -1, -1, 0))
        typ = (
            T.Color3f if key == "map" else T.Normal3f if key == "normalMap" else T.Float
        )
        s.CreateInput(name, typ).ConnectToSource(tex.ConnectableAPI(), channel)
    return mat


mats = [material(i, m) for i, m in enumerate(meta["materials"])]


def array(g, k):
    a = g[k]
    return np.frombuffer(buf, dtype=a["type"], count=a["count"], offset=a["offset"])


def mesh(path, v, f, n, uv=None):
    obj = UsdGeom.Mesh.Define(stage, path)
    obj.CreatePointsAttr(Vt.Vec3fArray.FromNumpy(v))
    obj.CreateFaceVertexIndicesAttr(Vt.IntArray.FromNumpy(f))
    obj.CreateFaceVertexCountsAttr(Vt.IntArray.FromNumpy(np.full(len(f) // 3, 3, "i")))
    obj.CreateSubdivisionSchemeAttr("none")
    obj.CreateDoubleSidedAttr(True)
    if n is not None:
        obj.CreateNormalsAttr(Vt.Vec3fArray.FromNumpy(n))
        obj.SetNormalsInterpolation("vertex")
    if uv is not None:
        UsdGeom.PrimvarsAPI(obj).CreatePrimvar("st", T.TexCoord2fArray, "vertex").Set(
            Vt.Vec2fArray.FromNumpy(uv)
        )
    return obj


dynamic = []
names = []
for i, m in enumerate(meta["meshes"]):
    if m.get("retired"):
        continue
    g = meta["geometries"][m["geometry"]]
    if "inlinePositions" in g:
        v = np.asarray(g["inlinePositions"], "f").reshape(-1, 3)
        n = np.asarray(g["inlineNormals"], "f").reshape(-1, 3)
    else:
        v = array(g, "position").reshape(-1, 3)
        n = array(g, "normal").reshape(-1, 3) if "normal" in g else None
    uv = array(g, "uv").reshape(-1, 2).copy() if "uv" in g else None
    faces = (
        array(g, "index").astype("i") if "index" in g else np.arange(len(v), dtype="i")
    )
    obj = mesh("/Cafe/M" + str(i), v, faces, n, uv)
    mat = mats[m["material"]]
    if m["name"].endswith("/lens_stl_0"):
        mat = material(
            "Lens", dict(color=[0.048, 0.087, 0.100], roughness=0.14, metalness=0.18)
        )
    UsdShade.MaterialBindingAPI.Apply(obj.GetPrim()).Bind(mat)
    op = obj.AddTransformOp()
    op.Set(Gf.Matrix4d(np.array(m["matrix"]).reshape(4, 4).tolist()))
    if m["group"] or m["name"].startswith("/World/RopeDraw/"):
        names.append(m["name"])
        dynamic.append(op)
print("Scene surfaces prepared", flush=True)
# Read the actual displayed world transforms, including the jaw hinge and rigged cords.
with sync_playwright() as pw:
    browser = pw.chromium.launch(
        args=[
            "--no-sandbox",
            "--use-angle=vulkan",
            "--enable-features=Vulkan",
            "--use-vulkan=native",
        ]
    )
    page = browser.new_page()
    page.goto(
        "http://127.0.0.1:8765/garden-bill-cafe/explore.html",
        wait_until="domcontentloaded",
    )
    page.wait_for_function("!!window.cafe", timeout=180000)
    page.locator("#scene-play").click()
    pearl = page.evaluate("""()=>{const g=cafe.scene.getObjectByName('Pearl thread marker').geometry;
      return ['position','normal'].map(k=>Array.from(g.attributes[k].array)).concat([Array.from(g.index.array)])}""")
    obj = mesh(
        "/Cafe/Pearl",
        np.asarray(pearl[0], "f").reshape(-1, 3),
        np.asarray(pearl[2], "i"),
        np.asarray(pearl[1], "f").reshape(-1, 3),
    )
    UsdShade.MaterialBindingAPI.Apply(obj.GetPrim()).Bind(
        material("Pearl", dict(color=[1, 0.84, 0.69], roughness=0.24, metalness=0.1))
    )
    dynamic.append(obj.AddTransformOp())
    names.append("Pearl thread marker")
    page.evaluate(
        "(names)=>{window.parts=names.map(n=>cafe.scene.getObjectByName(n))}", names
    )
    print("Sampling verified poses", flush=True)
    prev = None
    for start in range(0, len(thread), 30):
        count = min(30, len(thread) - start)
        encoded = page.evaluate(
            """([start,count,dt])=>{const b=new Float64Array(count*parts.length*16);let k=0;
          for(let i=0;i<count;i++){cafe.time=(start+i)*dt;cafe.scene.updateMatrixWorld(true);for(const m of parts){b.set(m.matrixWorld.elements,k);k+=16}}
          const bytes=new Uint8Array(b.buffer);let text='';for(let i=0;i<bytes.length;i+=8192)text+=String.fromCharCode(...bytes.subarray(i,i+8192));return btoa(text)}""",
            [start, count, motion["dt"]],
        )
        frames = np.frombuffer(base64.b64decode(encoded), "<f8").reshape(
            count, len(names), 4, 4
        )
        for j, v in enumerate(frames):
            for k in (
                np.flatnonzero(np.any(v != prev, axis=(1, 2)))
                if prev is not None
                else range(len(v))
            ):
                # Author the previous value at the last held frame as well.
                if prev is not None:
                    dynamic[k].Set(Gf.Matrix4d(prev[k].tolist()), start + j - 1)
                dynamic[k].Set(Gf.Matrix4d(v[k].tolist()), start + j)
                if not start + j:
                    dynamic[k].Set(Gf.Matrix4d(v[k].tolist()))
            prev = v
    browser.close()
cord = UsdGeom.BasisCurves.Define(stage, "/Cafe/Cotton")
cord.CreateTypeAttr("linear")
cord.CreateCurveVertexCountsAttr([thread.shape[1] - 2])
cord.CreateWidthsAttr([2 * fit["radius"]])
cord.SetWidthsInterpolation("constant")
UsdShade.MaterialBindingAPI.Apply(cord.GetPrim()).Bind(
    material("Cotton", dict(color=[0.39, 0.20, 0.11], roughness=0.9, metalness=0))
)
pa = cord.CreatePointsAttr()
for i, row in enumerate(thread):
    pa.Set(Vt.Vec3fArray.FromNumpy(row[2:]), i)
pa.Set(Vt.Vec3fArray.FromNumpy(thread[0, 2:]))
cam = UsdGeom.Camera.Define(stage, "/Camera")
cam.CreateHorizontalApertureAttr(32)
cam.CreateFocalLengthAttr(27)
cam.CreateClippingRangeAttr(Gf.Vec2f(0.01, 100))
cam.AddTransformOp().Set(
    Gf.Matrix4d()
    .SetLookAt(
        Gf.Vec3d(3.25, -3.88, 4.85), Gf.Vec3d(-0.35, 1.95, 0.89), Gf.Vec3d.ZAxis()
    )
    .GetInverse()
)
sky = UsdLux.DomeLight.Define(stage, "/Lights/Fill")
sky.CreateIntensityAttr(350)
sky.CreateColorAttr(Gf.Vec3f(1, 0.94, 0.88))
sun = UsdLux.DistantLight.Define(stage, "/Lights/Key")
sun.CreateIntensityAttr(1900)
sun.CreateAngleAttr(4)
sun.AddRotateXYZOp().Set(Gf.Vec3f(26, -22, -15))
stage.GetRootLayer().Save()
working.replace(dst)
print(dst, flush=True)
