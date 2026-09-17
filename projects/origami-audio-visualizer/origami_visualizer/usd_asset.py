"""Write a portable ASCII OpenUSD asset without requiring a local USD SDK."""
from __future__ import annotations

import argparse
from math import cos, pi, sin
from pathlib import Path

from .mesh import HexGussetMesh


def _hex_points(radius: float) -> str:
    return ", ".join(f"({radius * cos(pi / 6 + index * pi / 3):.4f}, {radius * sin(pi / 6 + index * pi / 3):.4f}, 0)" for index in range(6))


def write_stage(output: str | Path, width: int = 5, height: int = 5, radius: float = 1.0) -> Path:
    mesh = HexGussetMesh(width, height, radius)
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "#usda 1.0",
        '(',
        '    defaultPrim = "World"',
        '    metersPerUnit = 1',
        '    upAxis = "Z"',
        ')',
        '',
        'def Xform "World" (',
        '    kind = "assembly"',
        ')',
        '{',
        '    custom string origami:description = "Hexagonal origami tessellation seed asset"',
        f'    custom int origami:gridWidth = {width}',
        f'    custom int origami:gridHeight = {height}',
        '    def PhysicsScene "PhysicsScene" { vector3f physics:gravityDirection = (0, 0, -1) float physics:gravityMagnitude = 9.81 }',
        '    def Xform "Panels" ( prepend apiSchemas = ["PhysicsArticulationRootAPI"] )',
        '    {',
    ]
    points = _hex_points(radius)
    for panel in mesh.panels:
        x, y = panel.center
        lines.extend([
            f'        def Xform "{panel.id}" (',
            '            prepend apiSchemas = ["PhysicsRigidBodyAPI", "PhysicsMassAPI"]',
            f'            custom string origami:coord = "{panel.coord[0]},{panel.coord[1]}"',
            '            custom bool origami:rigidPanel = 1',
            '        )',
            '        {',
            '            float physics:mass = 0.01',
            f'            double3 xformOp:translate = ({x:.4f}, {y:.4f}, 0)',
            '            uniform token[] xformOpOrder = ["xformOp:translate"]',
            f'            def Mesh "panelMesh" {{ point3f[] points = [{points}] int[] faceVertexCounts = [6] int[] faceVertexIndices = [0, 1, 2, 3, 4, 5] uniform token subdivisionScheme = "none" }}',
            '        }',
        ])
    lines.extend(['    }', '    def Xform "Hinges"', '    {'])
    for hinge in mesh.hinges:
        lines.extend([
            f'        def PhysicsRevoluteJoint "{hinge.id}" (',
            '            prepend apiSchemas = ["PhysicsDriveAPI:angular"]',
            '        )',
            '        {',
            f'            rel physics:body0 = </World/Panels/{hinge.panel_a}>',
            f'            rel physics:body1 = </World/Panels/{hinge.panel_b}>',
            '            uniform token physics:axis = "Z"',
            '            float physics:lowerLimit = -70',
            '            float physics:upperLimit = 70',
            '            float drive:angular:physics:damping = 38',
            '            float drive:angular:physics:maxForce = 250',
            '            float drive:angular:physics:stiffness = 180',
            '            float drive:angular:physics:targetPosition = 0',
            f'            custom string origami:bodyA = "/World/Panels/{hinge.panel_a}"',
            f'            custom string origami:bodyB = "/World/Panels/{hinge.panel_b}"',
            f'            custom int origami:foldSign = {hinge.fold_sign}',
            '            custom string origami:jointType = "revolute"',
            '        }',
        ])
    lines.extend([
        '    }',
        '    def DistantLight "Key" { float intensity = 3000 float angle = 0.53 color3f color = (1, 0.82, 0.62) }',
        '    def DistantLight "Rim" { float intensity = 1800 float angle = 0.35 color3f color = (0.38, 0.55, 1) double3 xformOp:rotateXYZ = (25, 0, 150) uniform token[] xformOpOrder = ["xformOp:rotateXYZ"] }',
        '    def Camera "Camera" { float2 clippingRange = (0.1, 1000) float focalLength = 50 float horizontalAperture = 20.955 matrix4d xformOp:transform = ((1, 0, 0, 0), (0, 0.94, -0.34, 0), (0, 0.34, 0.94, 0), (0, -22, 35, 1)) uniform token[] xformOpOrder = ["xformOp:transform"] }',
        '}',
        'def "Render" { def RenderProduct "ProductShot" { rel camera = </World/Camera> rel orderedVars = [<LdrColor>] int2 resolution = (1280, 720) def RenderVar "LdrColor" { string sourceName = "LdrColor" } } }',
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the origami USD asset")
    parser.add_argument("--output", default="assets/origami_tessellation.usda")
    parser.add_argument("--width", type=int, default=5)
    parser.add_argument("--height", type=int, default=5)
    parser.add_argument("--radius", type=float, default=1.0)
    args = parser.parse_args()
    asset = write_stage(args.output, args.width, args.height, args.radius)
    print(f"Wrote {asset}")


if __name__ == "__main__":
    main()
