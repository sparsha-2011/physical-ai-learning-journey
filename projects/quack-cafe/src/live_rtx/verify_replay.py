"""Compare renderer stage world centres with the approved source at mechanism handoffs."""

from pathlib import Path
import json
import numpy as np
from pxr import Usd, UsdGeom
from scipy.spatial.transform import Rotation

root = Path(__file__).resolve().parents[2]
w = root / "web/garden-bill-cafe"
meta = json.loads((w / "scene.json").read_text())
motion = json.loads((w / "motion.json").read_text())
stage = Usd.Stage.Open(str(root / "renders/garden/live-rtx/product.usda"))
poses = np.array(motion["poses"])
checked = {}
for name in ["Ladle", "Cart", "Marble", "Marble2", "Sugar", "DuckFace"]:
    path = "/World/" + name
    idx = motion["labels"].index(path)
    j, m = next(
        (i, m)
        for i, m in enumerate(meta["meshes"])
        if m.get("group") == path
        and "jaw_stl_11" not in m["name"]
        and "jaw_soft_stl_3" not in m["name"]
    )
    local = np.array(m["matrix"]).reshape(4, 4)
    errs = []
    for frame in [0, 96, 206, 400, 562, 790, 801, 835, 1150]:
        q = poses[frame, idx]
        parent = np.eye(4)
        parent[:3, :3] = Rotation.from_quat(q[3:]).as_matrix().T
        parent[3, :3] = q[:3]
        actual = np.array(
            UsdGeom.XformCache(Usd.TimeCode(frame)).GetLocalToWorldTransform(
                stage.GetPrimAtPath("/Cafe/M" + str(j))
            )
        )
        errs.append(np.max(abs(actual - local @ parent)))
    checked[name] = max(errs)
assert max(checked.values()) < 0.00002, checked
print("Maximum matrix differences", checked)
fit = json.loads((w / "thread-fit.json").read_text())
source = np.fromfile(w / "thread.bin", "<f4").reshape(fit["frames"], fit["points"], 3)
points = stage.GetPrimAtPath("/Cafe/Cotton").GetAttribute("points")
for f in [0, 25, 96, 100, 608, 803, 1200]:
    assert np.array_equal(np.array(points.Get(f)), source[f, 2:])
print("Verified thread centreline and rigid handoffs.")
