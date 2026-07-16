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
OUT_DIR = "/root/Documents/physical-ai-learning-journey/projects/omniglam-sdg/outputs_v2"
os.makedirs(OUT_DIR, exist_ok=True)

# ---- HELPER ----
def make_box(name, position, scale, colour, roughness=0.9):
    box = UsdGeom.Cube.Define(stage, f"/World/{name}")
    xform = UsdGeom.Xformable(box)
    xform.AddTranslateOp().Set(Gf.Vec3d(*position))
    xform.AddScaleOp().Set(Gf.Vec3f(*scale))
    prim = stage.GetPrimAtPath(f"/World/{name}")
    rep.functional.create.material(
        mdl="OmniPBR.mdl", bind_prims=[prim],
        diffuse_color_constant=colour,
        reflection_roughness_constant=roughness
    )
    return prim

# ---- FLOORS ----
white_floor  = make_box("WhiteFloor",  (0,0,-0.5), (40,40,0.5), (0.95,0.95,0.95), 0.15)
black_floor  = make_box("BlackFloor",  (0,0,-0.5), (40,40,0.5), (0.05,0.05,0.05), 0.15)
wood_floor   = make_box("WoodFloor",   (0,0,-0.5), (40,40,0.5), (0.45,0.28,0.15), 0.7)
marble_floor = make_box("MarbleFloor", (0,0,-0.5), (40,40,0.5), (0.88,0.87,0.86), 0.2)
warm_floor   = make_box("WarmFloor",   (0,0,-0.5), (40,40,0.5), (0.85,0.78,0.68), 0.95)
pink_floor   = make_box("PinkFloor",   (0,0,-0.5), (40,40,0.5), (0.96,0.82,0.85), 0.6)

# ---- WALLS ----
make_box("BackWall",  (0,  25, 15), (40, 1, 30), (0.95,0.95,0.95))
make_box("LeftWall",  (-25, 0, 15), (1, 40, 30), (0.95,0.95,0.95))
make_box("RightWall", (25,  0, 15), (1, 40, 30), (0.95,0.95,0.95))

# Hide all floors initially
for f in [white_floor, black_floor, wood_floor, marble_floor, warm_floor, pink_floor]:
    f.GetAttribute("visibility").Set("invisible")

# Background config
backgrounds = [
    {"floor": white_floor,  "wall": (0.95,0.95,0.95), "weight": 3},
    {"floor": black_floor,  "wall": (0.05,0.05,0.05), "weight": 1},
    {"floor": wood_floor,   "wall": (0.92,0.88,0.82), "weight": 2},
    {"floor": marble_floor, "wall": (0.95,0.95,0.95), "weight": 1},
    {"floor": warm_floor,   "wall": (0.88,0.84,0.78), "weight": 1},
    {"floor": pink_floor,   "wall": (0.96,0.90,0.92), "weight": 1},
]

weighted_backgrounds = []
for bg in backgrounds:
    weighted_backgrounds.extend([bg] * bg["weight"])

# ---- LIGHTING ----
rep.create.light(light_type="Distant", intensity=500, color=(1.0,1.0,1.0), parent="/World", name="AmbientLight")
rep.create.light(light_type="Sphere", position=(-4,-3,6), intensity=8000, color=(1.0,0.97,0.92), parent="/World", name="KeyLight")
rep.create.light(light_type="Sphere", position=(4,-3,4), intensity=3000, color=(0.92,0.95,1.0), parent="/World", name="FillLight")
rep.create.light(light_type="Sphere", position=(0,4,5), intensity=2000, color=(1.0,1.0,1.0), parent="/World", name="RimLight")

lighting_presets = [
    {"intensity": 8000,  "color": (1.0, 0.97, 0.92)},
    {"intensity": 10000, "color": (0.92, 0.95, 1.0)},
    {"intensity": 12000, "color": (1.0, 1.0, 1.0)},
    {"intensity": 6000,  "color": (1.0, 0.88, 0.75)},
    {"intensity": 15000, "color": (1.0, 1.0, 1.0)},
    {"intensity": 4000,  "color": (0.85, 0.90, 1.0)},
]

# ---- CASE VARIANTS ----
case_variants = [
    {"body": (0.83,0.68,0.21), "metallic": 1.0, "roughness": 0.1,  "base": (0.05,0.05,0.05), "base_metallic": 0.0},
    {"body": (0.80,0.80,0.82), "metallic": 1.0, "roughness": 0.05, "base": (0.05,0.05,0.05), "base_metallic": 0.0},
    {"body": (0.08,0.08,0.08), "metallic": 0.0, "roughness": 0.8,  "base": (0.08,0.08,0.08), "base_metallic": 0.0},
    {"body": (0.85,0.60,0.55), "metallic": 1.0, "roughness": 0.1,  "base": (0.65,0.42,0.38), "base_metallic": 1.0},
    {"body": (0.95,0.95,0.95), "metallic": 0.0, "roughness": 0.6,  "base": (0.75,0.75,0.78), "base_metallic": 1.0},
    {"body": (0.08,0.10,0.25), "metallic": 0.0, "roughness": 0.5,  "base": (0.83,0.68,0.21), "base_metallic": 1.0},
    {"body": (0.55,0.08,0.08), "metallic": 0.0, "roughness": 0.3,  "base": (0.05,0.05,0.05), "base_metallic": 0.0},
]

# ---- SHADES ----
# Z offset to place tubes on floor
Z = 0

shades = [
    ("deep_learning_red", (-4.5,  2.5, Z), (0.35, 0.02, 0.02), (90,0,0)),
    ("render_rose",       (-1.5,  2.5, Z), (0.41, 0.19, 0.25), (90,0,0)),
    ("null_mauve",        ( 1.5,  2.5, Z), (0.92, 0.41, 0.72), (90,0,0)),
    ("softmax",           ( 4.5,  2.5, Z), (0.86, 0.32, 0.35), (90,0,0)),
    ("runtime_berry",     (-3.0, -1.5, Z), (0.15, 0.00, 0.09), (90,0,0)),
    ("pixar_pink",        ( 0.0, -1.5, Z), (0.64, 0.05, 0.15), (90,0,0)),
    ("cudiva",            ( 3.0, -1.5, Z), (0.78, 0.21, 0.14), (90,0,0)),
]

base_positions = [
    (-4.5,2.5,Z), (-1.5,2.5,Z), (1.5,2.5,Z), (4.5,2.5,Z),
    (-3.0,-1.5,Z), (0.0,-1.5,Z), (3.0,-1.5,Z),
]

# ---- BUILD LIPSTICK TUBES ----
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
            if mesh_name in ["Cylinder_003", "Cylinder_002", "Cylinder_001"]:
                rep.functional.create.material(
                    mdl="OmniPBR.mdl", bind_prims=[prim],
                    diffuse_color_constant=(0.83,0.68,0.21),
                    metallic_constant=1.0, reflection_roughness_constant=0.1
                )
            elif mesh_name in ["Cylinder_006", "Cylinder"]:
                rep.functional.create.material(
                    mdl="OmniPBR.mdl", bind_prims=[prim],
                    diffuse_color_constant=(0.05,0.05,0.05),
                    metallic_constant=0.0, reflection_roughness_constant=0.5
                )

    bullet_tip = stage.GetPrimAtPath(f"/World/{name}/body_top/Cylinder_004")
    rep.functional.create.material(
        mdl="OmniPBR.mdl", bind_prims=[bullet_tip],
        diffuse_color_constant=colour,
        metallic_constant=0.0, reflection_roughness_constant=0.4,
        enable_emission=False
    )

    cap = stage.GetPrimAtPath(f"/World/{name}/top_cap")
    if cap.IsValid():
        cap.GetAttribute("visibility").Set("invisible")

    lipstick_prims.append(stage.GetPrimAtPath(f"/World/{name}"))
    print(f"Added {name}")

# ---- CAMERA ----
cam = rep.functional.create.camera(
    position=(0,-12,6), look_at=(0,0,2.5),
    focal_length=18.0, parent="/World", name="OmniGlamCam"
)
rp = rep.create.render_product(cam, (1024,1024), name="OmniGlamRender")

# ---- WRITER ----
backend = rep.backends.get("DiskBackend")
backend.initialize(output_dir=OUT_DIR)
writer = rep.writers.get("BasicWriter")
writer.initialize(
    backend=backend, rgb=True,
    bounding_box_2d_tight=True,
    semantic_segmentation=True,
    colorize_semantic_segmentation=True
)
writer.attach(rp)

print("Scene ready — OmniGlam SDG v2!")

# ---- CAPTURE LOOP ----
async def run_pipeline():
    num_frames = 1000
    rng = np.random.default_rng(7)
    print(f"Starting OmniGlam SDG v2 — {num_frames} frames...")

    # Tighter camera presets — always facing tubes
    camera_presets = [
        ((0,  -12, 6),  (0, 0, 2.8)),
        ((0,  -10, 5),  (0, 0, 2.8)),
        ((7,  -10, 6),  (0, 0, 2.8)),
        ((-7, -10, 6),  (0, 0, 2.8)),
        ((0,   -8, 4),  (0, 0, 2.8)),
    ]
    close_up_presets = [
        ((0,  -8, 5),   (0, 0, 2.8)),
        ((2,  -7, 5),   (0, 0, 2.8)),
        ((-2, -7, 5),   (0, 0, 2.8)),
    ]

    key_light  = stage.GetPrimAtPath("/World/KeyLight")
    fill_light = stage.GetPrimAtPath("/World/FillLight")
    back_wall  = stage.GetPrimAtPath("/World/BackWall")
    left_wall  = stage.GetPrimAtPath("/World/LeftWall")
    right_wall = stage.GetPrimAtPath("/World/RightWall")

    for i in range(num_frames):
        print(f"Frame {i+1}/{num_frames}")

        # Switch floor + wall tint
        active = weighted_backgrounds[int(rng.integers(0, len(weighted_backgrounds)))]
        for bg in backgrounds:
            bg["floor"].GetAttribute("visibility").Set(
                "inherited" if bg["floor"].GetPath() == active["floor"].GetPath() else "invisible"
            )
        for wall in [back_wall, left_wall, right_wall]:
            if wall.IsValid():
                rep.functional.create.material(
                    mdl="OmniPBR.mdl", bind_prims=[wall],
                    diffuse_color_constant=active["wall"],
                    reflection_roughness_constant=0.9
                )

        # Switch lighting
        lp = lighting_presets[int(rng.integers(0, len(lighting_presets)))]
        if key_light.IsValid():
            key_light.GetAttribute("inputs:intensity").Set(float(lp["intensity"]))
            key_light.GetAttribute("inputs:color").Set(Gf.Vec3f(*lp["color"]))
        if fill_light.IsValid():
            fill_light.GetAttribute("inputs:intensity").Set(float(lp["intensity"] * 0.4))

        # Pick case variant
        case_variant = case_variants[int(rng.integers(0, len(case_variants)))]

        # Tube visibility
        if i % 8 == 0:
            num_visible = 1
            visible_indices = rng.choice(len(lipstick_prims), 1, replace=False)
            preset_cam = close_up_presets[int(rng.integers(0, len(close_up_presets)))]
        else:
            num_visible = int(rng.integers(1, 8))
            visible_indices = rng.choice(len(lipstick_prims), num_visible, replace=False)
            preset_cam = camera_presets[int(rng.integers(0, len(camera_presets)))]

        for j, prim in enumerate(lipstick_prims):
            prim.GetAttribute("visibility").Set(
                "inherited" if j in visible_indices else "invisible"
            )

            if j in visible_indices:
                for mesh_prim in Usd.PrimRange(prim):
                    if mesh_prim.GetTypeName() == "Mesh":
                        mesh_name = mesh_prim.GetPath().name
                        if mesh_name in ["Cylinder_003", "Cylinder_002", "Cylinder_001"]:
                            rep.functional.create.material(
                                mdl="OmniPBR.mdl", bind_prims=[mesh_prim],
                                diffuse_color_constant=case_variant["body"],
                                metallic_constant=case_variant["metallic"],
                                reflection_roughness_constant=case_variant["roughness"]
                            )
                        elif mesh_name == "Cylinder":
                            rep.functional.create.material(
                                mdl="OmniPBR.mdl", bind_prims=[mesh_prim],
                                diffuse_color_constant=case_variant["base"],
                                metallic_constant=case_variant["base_metallic"],
                                reflection_roughness_constant=0.3
                            )

                base = base_positions[j]
                rep.functional.modify.pose(
                    prim,
                    position_value=(
                        base[0] + float(rng.uniform(-0.3,0.3)),
                        base[1] + float(rng.uniform(-0.3,0.3)),
                        base[2]
                    ),
                    rotation_value=(90+float(rng.uniform(-8,8)), 0, float(rng.uniform(-15,15)))
                )

        # Camera — tighter variation
        rep.functional.modify.pose(
            cam,
            position_value=(
                preset_cam[0][0] + float(rng.uniform(-0.5,0.5)),
                preset_cam[0][1] + float(rng.uniform(-0.5,0.5)),
                preset_cam[0][2] + float(rng.uniform(-0.3,0.3))
            ),
            look_at_value=preset_cam[1]
        )

        await rep.orchestrator.step_async(rt_subframes=8)

    await rep.orchestrator.wait_until_complete_async()
    writer.detach()
    rp.destroy()
    print("OmniGlam SDG v2 complete!")

asyncio.ensure_future(run_pipeline())

