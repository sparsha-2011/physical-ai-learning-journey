"""Render a smoke-test frame from the generated USD scene through ovrtx."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import ovrtx
import ovstage
from PIL import Image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", default="assets/origami_20x20.usda")
    parser.add_argument("--output", default="outputs/origami_beauty.png")
    args = parser.parse_args()
    scene, output = Path(args.scene).resolve(), Path(args.output).resolve()
    if not scene.exists():
        raise SystemExit(f"Missing USD asset: {scene}")
    output.parent.mkdir(parents=True, exist_ok=True)
    renderer, stage = ovrtx.Renderer(), ovstage.Stage("origami-render")
    try:
        renderer.attach_ovstage(stage)
        ordinal = 1
        ovstage.population.open_usd(stage, str(scene), ordinal=ordinal)
        stage.advance_write_floor(ordinal, ovstage.Scope.ALL).wait()
        products = renderer.step(render_products={"/Render/ProductShot"}, delta_time=1 / 60, ordinal=ordinal)
        frame = next(iter(products.values())).frames[0]
        mapped = frame.render_vars["LdrColor"].map(device=ovrtx.Device.CPU)
        view = np.from_dlpack(mapped)
        pixels = view.copy()
        del view
        mapped.unmap()
        Image.fromarray(pixels.astype(np.uint8)).convert("RGB").save(output)
        print(f"ovrtx wrote {output}")
    finally:
        renderer.detach_ovstage()
        stage.destroy()
        renderer.destroy()


if __name__ == "__main__":
    main()
