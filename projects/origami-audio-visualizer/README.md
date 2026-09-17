# Audio-Reactive Origami Visualizer

A GPU portfolio project for a large hexagonal origami tessellation that folds
in coherent waves. The project generates an OpenUSD stage, applies drive
targets through `ovphysx`, and is structured for rendering through `ovrtx`.

## Project layout

```text
assets/origami_tessellation.usda  Generated USD seed asset (5 x 5)
origami_visualizer/               Mesh, waves, USD authoring, OV adapters
scripts/setup_brev.sh             GPU/Brev environment setup
scripts/run_brev_demo.sh          Test + USD generation + runtime entrypoint
tests/                            Runtime-independent tests
```

## Build and verify locally

```bash
python -m unittest discover -s tests -v
python run_demo.py --width 20 --height 20 --seconds 6
python -m origami_visualizer.usd_asset --width 20 --height 20 --output assets/origami_20x20.usda
```

The generated USD stage contains one Xform/mesh child per rigid hex panel and
custom `origami:*` metadata identifying the shared hinges. The OV runtime uses
that deterministic topology to author `ovphysx` rigid bodies and revolute
joints once its exact early-access API is available in the target environment.

## Brev setup

No paid instance was created automatically: that needs your Brev login and
can incur GPU charges. In WSL/Ubuntu (the supported Brev path for Windows):

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/brevdev/brev-cli/main/bin/install-latest.sh)"
brev login
brev create origami-visualizer --gpu-name L4 --min-vram 20 --min-disk 100
brev shell origami-visualizer
```

On the Brev machine, use persistent storage and bootstrap the project:

```bash
cd /home/ubuntu/workspace
git clone YOUR_REPOSITORY_URL physical-ai
cd physical-ai/projects/origami-audio-visualizer
bash scripts/setup_brev.sh
bash scripts/run_brev_demo.sh
```

Use an L4/A10-class GPU for the 20 x 20 physics check; target 24 GB+ VRAM for
large RTX renders. Brev includes CUDA, Python, Docker, Jupyter, and SSH. Its
workspace persists across a stopped instance but is deleted with the instance,
so push work to Git first. See the [Brev CLI guide](https://docs.nvidia.com/brev/latest/cli/getting-started)
and [instance lifecycle guide](https://docs.nvidia.com/brev/concepts/gpu-instances).

## OV package boundary

`requirements-ov.txt` pins the same OV package versions used by this
repository's existing RTX Studio project. You need NVIDIA entitlement to
install these proprietary early-access wheels. Once installed,
`server/ovphysx_bridge.py` opens the generated stage, binds all
revolute drives, and steps the fold commands; `server/ovrtx_render.py` opens
the same stage and writes `outputs/origami_beauty.png`. This keeps the calls
aligned with the OV APIs already used by the repository's RTX Studio project.
