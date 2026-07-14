import omni.usd
import omni.replicator.core as rep
import carb.settings
import asyncio
import os
import numpy as np
from pxr import UsdGeom, Usd

# New stage
omni.usd.get_context().new_stage()
rep.orchestrator.set_capture_on_play(False)
carb.settings.get_settings().set("rtx/post/dlss/execMode", 2)

stage = omni.usd.get_context().get_stage()
UsdGeom.Xform.Define(stage, "/World")

ASSET_PATH = "/root/Documents/physical-ai-learning-journey/projects/omniglam-sdg/assets/lipstick.usd"

# Vanity surface
surface = rep.functional.create.plane(scale=(12, 12, 1), position=(0, 0, 0), parent="/World")
rep.functional.create.material(
    mdl="OmniPBR.mdl",
    bind_prims=[surface],
    diffuse_color_constant=(0.95, 0.95, 0.95),
    reflection_roughness_constant=0.8
)

# Dome light
rep.functional.create.dome_light(intensity=3000, parent="/World")

# Two rows
shades = [
    # Back row
    ("deep_learning_red",  (-4.5,  2.5, 0.8), (0.35, 0.02, 0.02), (90, 0, 0)),
    ("render_rose",        (-1.5,  2.5, 0.8), (0.41, 0.19, 0.25), (90, 0, 0)),
    ("null_mauve",         ( 1.5,  2.5, 0.8), (0.92, 0.41, 0.72), (90, 0, 0)),
    ("softmax",            ( 4.5,  2.5, 0.8), (0.86, 0.32, 0.35), (90, 0, 0)),
    # Front row
    ("runtime_berry",      (-3.0, -1.5, 0.5), (0.15, 0.00, 0.09), (90, 0, 0)),
    ("pixar_pink",         ( 0.0, -1.5, 0.5), (0.64, 0.05, 0.15), (90, 0, 0)),
    ("cudiva",             ( 3.0, -1.5, 0.5), (0.78, 0.21, 0.14), (90, 0, 0)),
]

GOLD  = (0.83, 0.68, 0.21)
BLACK = (0.05, 0.05, 0.05)

part_materials = {
    "Cylinder_006": {"colour": BLACK, "metallic": 0.0, "roughness": 0.5},
    "Cylinder_003": {"colour": GOLD,  "metallic": 1.0, "roughness": 0.1},
    "Cylinder_002": {"colour": GOLD,  "metallic": 1.0, "roughness": 0.1},
    "Cylinder_001": {"colour": GOLD,  "metallic": 1.0, "roughness": 0.1},
    "Cylinder":     {"colour": (0.9, 0.9, 0.9), "metallic": 0.0, "roughness": 0.5},
}

lipsticks = []
for name, position, colour, rotation in shades:
    tube = rep.functional.create.reference(
        usd_path=ASSET_PATH,
        parent="/World",
        name=name,
        position=position,
        rotation=rotation
    )
    rep.functional.modify.semantics(tube, {"class": name}, mode="add")

    for prim in Usd.PrimRange(stage.GetPrimAtPath(f"/World/{name}")):
        if prim.GetTypeName() == "Mesh":
            mesh_name = prim.GetPath().name
            if mesh_name in part_materials:
                mat = part_materials[mesh_name]
                rep.functional.create.material(
                    mdl="OmniPBR.mdl",
                    bind_prims=[prim],
                    diffuse_color_constant=mat["colour"],
                    metallic_constant=mat["metallic"],
                    reflection_roughness_constant=mat["roughness"]
                )

    bullet_tip = stage.GetPrimAtPath(f"/World/{name}/body_top/Cylinder_004")
    rep.functional.create.material(
        mdl="OmniPBR.mdl",
        bind_prims=[bullet_tip],
        diffuse_color_constant=colour,
        metallic_constant=0.0,
        reflection_roughness_constant=0.4,
        enable_emission=False
    )

    cap = stage.GetPrimAtPath(f"/World/{name}/top_cap")
    if cap.IsValid():
        cap.GetAttribute("visibility").Set("invisible")

    lipsticks.append(tube)
    print(f"Added {name}")

# Camera
cam = rep.functional.create.camera(
    position=(0, -18, 10),
    look_at=(0, 0, 2),
    parent="/World",
    name="OmniGlamCam"
)
rp = rep.create.render_product(cam, (1024, 1024), name="OmniGlamRender")

# Lighting randomiser
with rep.trigger.on_custom_event(event_name="randomize_lighting"):
    rep.create.light(
        light_type="Dome",
        intensity=rep.distribution.uniform(800, 3000),
        color=rep.distribution.uniform((0.8, 0.8, 0.8), (1.0, 1.0, 1.0))
    )

# Writer
out_dir = "/root/Documents/physical-ai-learning-journey/projects/omniglam-sdg/outputs"
os.makedirs(out_dir, exist_ok=True)
backend = rep.backends.get("DiskBackend")
backend.initialize(output_dir=out_dir)
writer = rep.writers.get("BasicWriter")
writer.initialize(
    backend=backend,
    rgb=True,
    bounding_box_2d_tight=True,
    semantic_segmentation=True,
    colorize_semantic_segmentation=True
)
writer.attach(rp)

print("All 7 OmniGlam shades loaded!")

# Capture loop
async def run_pipeline():
    num_frames = 10
    rng = np.random.default_rng(42)
    print(f"Starting OmniGlam SDG — generating {num_frames} frames...")

    for i in range(num_frames):
        rep.utils.send_og_event(event_name="randomize_lighting")
        rep.functional.modify.pose(
            cam,
            position_value=(
                float(rng.uniform(-2, 2)),
                float(rng.uniform(-18, -14)),
                float(rng.uniform(8, 12))
            ),
            look_at_value=(0, 0, 2)
        )
        await rep.orchestrator.step_async(rt_subframes=8)
        print(f"Frame {i+1}/{num_frames} captured")

    await rep.orchestrator.wait_until_complete_async()
    writer.detach()
    rp.destroy()
    print("OmniGlam SDG complete!")

asyncio.ensure_future(run_pipeline())
