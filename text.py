import omni.usd
import omni.replicator.core as rep
import carb.settings
import asyncio
import os
import numpy as np
from pxr import UsdGeom, Usd, Gf

# New stage
omni.usd.get_context().new_stage()
rep.orchestrator.set_capture_on_play(False)
carb.settings.get_settings().set("rtx/post/dlss/execMode", 2)

stage = omni.usd.get_context().get_stage()
UsdGeom.Xform.Define(stage, "/World")

ASSET_PATH = "/root/Documents/physical-ai-learning-journey/projects/omniglam-sdg/assets/lipstick.usd"
OUT_DIR = "/root/Documents/physical-ai-learning-journey/projects/omniglam-sdg/outputs"
os.makedirs(OUT_DIR, exist_ok=True)

# ---- BACKDROP ----
display_surface = rep.functional.create.plane(
    scale=(30, 30, 1), position=(0, 0, 0), parent="/World", name="DisplaySurface"
)
rep.functional.create.material(
    mdl="OmniPBR.mdl", bind_prims=[display_surface],
    diffuse_color_constant=(0.95, 0.95, 0.95),
    reflection_roughness_constant=0.15,
    metallic_constant=0.0
)

# Ambient light
rep.create.light(
    light_type="Distant", intensity=500,
    color=(1.0, 1.0, 1.0),
    parent="/World", name="AmbientLight"
)

# Three point lighting
rep.create.light(
    light_type="Sphere", position=(-4, -3, 6),
    intensity=8000, color=(1.0, 0.97, 0.92),
    parent="/World", name="KeyLight"
)
rep.create.light(
    light_type="Sphere", position=(4, -3, 4),
    intensity=3000, color=(0.92, 0.95, 1.0),
    parent="/World", name="FillLight"
)
rep.create.light(
    light_type="Sphere", position=(0, 4, 5),
    intensity=2000, color=(1.0, 1.0, 1.0),
    parent="/World", name="RimLight"
)

# ---- SHADES ----
shades = [
    ("deep_learning_red",  (-4.5,  2.5, 0.8), (0.35, 0.02, 0.02), (90, 0, 0)),
    ("render_rose",        (-1.5,  2.5, 0.8), (0.41, 0.19, 0.25), (90, 0, 0)),
    ("null_mauve",         ( 1.5,  2.5, 0.8), (0.92, 0.41, 0.72), (90, 0, 0)),
    ("softmax",            ( 4.5,  2.5, 0.8), (0.86, 0.32, 0.35), (90, 0, 0)),
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
}

base_positions = [
    (-4.5,  2.5, 0.8), (-1.5,  2.5, 0.8),
    ( 1.5,  2.5, 0.8), ( 4.5,  2.5, 0.8),
    (-3.0, -1.5, 0.5), ( 0.0, -1.5, 0.5),
    ( 3.0, -1.5, 0.5),
]

# Lighting presets
lighting_presets = [
    {"intensity": 8000,  "color": (1.0, 0.97, 0.92)},  # warm golden
    {"intensity": 10000, "color": (0.92, 0.95, 1.0)},  # cool blue
    {"intensity": 12000, "color": (1.0, 1.0, 1.0)},    # bright white
    {"intensity": 10000, "color": (1.0, 0.90, 0.85)},  # soft warm
    {"intensity": 15000, "color": (1.0, 1.0, 1.0)},    # very bright white
]

# Backdrop presets — white 75%, black 25%
backdrop_presets = [
    {"surface": (0.95, 0.95, 0.95)},  # clean white
    {"surface": (0.95, 0.95, 0.95)},  # clean white
    {"surface": (0.95, 0.95, 0.95)},  # clean white
    {"surface": (0.05, 0.05, 0.05)},  # dramatic black
]

lipsticks = []
lipstick_prims = []
for name, position, colour, rotation in shades:
    tube = rep.functional.create.reference(
        usd_path=ASSET_PATH, parent="/World",
        name=name, position=position, rotation=rotation
    )
    rep.functional.modify.semantics(tube, {"class": name}, mode="add")

    for prim in Usd.PrimRange(stage.GetPrimAtPath(f"/World/{name}")):
        if prim.GetTypeName() == "Mesh":
            mesh_name = prim.GetPath().name
            if mesh_name in part_materials:
                mat = part_materials[mesh_name]
                rep.functional.create.material(
                    mdl="OmniPBR.mdl", bind_prims=[prim],
                    diffuse_color_constant=mat["colour"],
                    metallic_constant=mat["metallic"],
                    reflection_roughness_constant=mat["roughness"]
                )

    bullet_tip = stage.GetPrimAtPath(f"/World/{name}/body_top/Cylinder_004")
    rep.functional.create.material(
        mdl="OmniPBR.mdl", bind_prims=[bullet_tip],
        diffuse_color_constant=colour,
        metallic_constant=0.0,
        reflection_roughness_constant=0.4,
        enable_emission=False
    )

    cap = stage.GetPrimAtPath(f"/World/{name}/top_cap")
    if cap.IsValid():
        cap.GetAttribute("visibility").Set("invisible")

    lipstick_prim = stage.GetPrimAtPath(f"/World/{name}")
    lipsticks.append(tube)
    lipstick_prims.append(lipstick_prim)
    print(f"Added {name}")

# ---- CAMERA — wider focal length ----
cam = rep.functional.create.camera(
    position=(0, -18, 8),
    look_at=(0, 0, 2.5),
    focal_length=18.0,
    parent="/World",
    name="OmniGlamCam"
)
rp = rep.create.render_product(cam, (1024, 1024), name="OmniGlamRender")

# ---- WRITER ----
backend = rep.backends.get("DiskBackend")
backend.initialize(output_dir=OUT_DIR)
writer = rep.writers.get("BasicWriter")
writer.initialize(
    backend=backend,
    rgb=True,
    bounding_box_2d_tight=True,
    semantic_segmentation=True,
    colorize_semantic_segmentation=True
)
writer.attach(rp)

print("Scene ready!")

# ---- CAPTURE LOOP ----
async def run_pipeline():
    num_frames = 500
    rng = np.random.default_rng(99)
    print(f"Starting OmniGlam SDG — {num_frames} frames...")

    camera_presets = [
        ((0, -18, 8),   (0, 0, 2.5)),   # front angled
        ((0, -15, 6),   (0, 0, 2.5)),   # front closer
        ((10, -14, 7),  (0, 0, 2.5)),   # side right
        ((-10, -14, 7), (0, 0, 2.5)),   # side left
        ((0, -12, 5),   (0, 0, 2.5)),   # close up front
    ]

    close_up_presets = [
        ((0, -8, 3),    (0, 0, 2.5)),   # tight front
        ((3, -7, 3),    (0, 0, 2.5)),   # tight side right
        ((-3, -7, 3),   (0, 0, 2.5)),   # tight side left
    ]

    key_light  = stage.GetPrimAtPath("/World/KeyLight")
    fill_light = stage.GetPrimAtPath("/World/FillLight")
    surf_prim  = stage.GetPrimAtPath("/World/DisplaySurface")

    for i in range(num_frames):
        print(f"Frame {i+1}/{num_frames}")

        # Switch backdrop and lighting
        bd = backdrop_presets[int(rng.integers(0, len(backdrop_presets)))]
        lp = lighting_presets[int(rng.integers(0, len(lighting_presets)))]

        rep.functional.create.material(
            mdl="OmniPBR.mdl", bind_prims=[surf_prim],
            diffuse_color_constant=bd["surface"],
            reflection_roughness_constant=0.15
        )
        if key_light.IsValid():
            key_light.GetAttribute("inputs:intensity").Set(float(lp["intensity"]))
            key_light.GetAttribute("inputs:color").Set(Gf.Vec3f(*lp["color"]))
        if fill_light.IsValid():
            fill_light.GetAttribute("inputs:intensity").Set(
                float(lp["intensity"] * 0.4)
            )

        # Every 5th frame — single tube close up
        if i % 5 == 0:
            num_visible = 1
            visible_indices = rng.choice(len(lipstick_prims), 1, replace=False)
            preset_cam = close_up_presets[int(rng.integers(0, len(close_up_presets)))]
        else:
            num_visible = int(rng.integers(1, 8))
            visible_indices = rng.choice(len(lipstick_prims), num_visible, replace=False)
            preset_cam = camera_presets[int(rng.integers(0, len(camera_presets)))]

        # Set tube visibility
        for j, prim in enumerate(lipstick_prims):
            prim.GetAttribute("visibility").Set(
                "inherited" if j in visible_indices else "invisible"
            )

        # Randomise tube positions
        for j, prim in enumerate(lipstick_prims):
            if j in visible_indices:
                base = base_positions[j]
                rep.functional.modify.pose(
                    prim,
                    position_value=(
                        base[0] + float(rng.uniform(-0.3, 0.3)),
                        base[1] + float(rng.uniform(-0.3, 0.3)),
                        base[2]
                    ),
                    rotation_value=(90, 0, float(rng.uniform(-10, 10)))
                )

        # Randomise camera
        rep.functional.modify.pose(
            cam,
            position_value=(
                preset_cam[0][0] + float(rng.uniform(-1, 1)),
                preset_cam[0][1] + float(rng.uniform(-1, 1)),
                preset_cam[0][2] + float(rng.uniform(-0.5, 0.5))
            ),
            look_at_value=preset_cam[1]
        )

        await rep.orchestrator.step_async(rt_subframes=8)

    await rep.orchestrator.wait_until_complete_async()
    writer.detach()
    rp.destroy()
    print("OmniGlam SDG complete!")

asyncio.ensure_future(run_pipeline())