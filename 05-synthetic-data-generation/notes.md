# Synthetic Data Generation with Isaac Sim — Notes

**Course:** [Synthetic Data Recorder — Isaac Sim Docs](https://docs.isaacsim.omniverse.nvidia.com/latest/replicator_tutorials/tutorial_replicator_recorder.html)
**Date:** Jul 10, 2026
**Environment:** NVIDIA Brev cloud · Isaac Sim 5.1.0 · L40S GPU · Browser VS Code + noVNC

---

## What is Synthetic Data Generation?

Robots need to learn from data — lots of it. Getting that data in the real world is slow, expensive, and sometimes dangerous. Synthetic Data Generation (SDG) solves this by creating training data inside a simulation instead.

**A concrete example:**
To train a robot to pick up a red cup you'd normally need thousands of real photos — different lighting, angles, backgrounds — all manually labelled. With Isaac Sim and Replicator you can generate 10,000 perfectly labelled images in an hour by randomising the scene automatically.

**Why Isaac Sim's SDG is powerful:**
NVIDIA's RTX renderer makes synthetic scenes photorealistic, which closes the sim-to-real gap — the problem where robots trained on fake-looking data don't behave well in the real world.

---

## What I did

### 1. Loaded the warehouse scene

Loaded a pre-built semantically labelled warehouse scene from NVIDIA's asset library:

```
Isaac Sim > Samples > Replicator > Stage > full_warehouse_worker_and_anim_cameras.usd
```

The scene comes pre-loaded with:

- Semantic annotations on all objects (labels for AI training)
- Multiple cameras including animated ones that move around the scene

### 2. Created the MyCustomWriter

Created `/root/Documents/synthetic-data-generation/MyCustomWriter.py` — a custom writer that captures RGB images and surface normal maps and saves them as PNGs.

### 3. Created my_params.json

Created `/root/Documents/synthetic-data-generation/my_params.json` to configure what the writer captures:

```json
{
  "rgb": true,
  "normals": true
}
```

### 4. Registered the writer in Isaac Sim

Opened **Window → Script Editor** in Isaac Sim and ran:

```python
import importlib.util

spec = importlib.util.spec_from_file_location("MyCustomWriter", "/root/Documents/synthetic-data-generation/MyCustomWriter.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
```

This loads the custom writer into the current Isaac Sim session and makes it available in the Synthetic Data Recorder dropdown.

### 5. Configured the Synthetic Data Recorder

Opened **Tools → Replicator → Synthetic Data Recorder** and configured:

- Writer: Custom Writer → MyCustomWriter
- Parameters Path: `/root/Documents/synthetic-data-generation/my_params.json`
- Output: `/root/Documents/synthetic-data-generation/output`
- Number of Frames: 50

### 6. Hit Start and generated the dataset

The recorder captured 50 frames from the warehouse scene cameras and saved them to two folders:

- `output/rgb/` — colour images of the warehouse scene
- `output/normals/` — surface normal maps of the same frames

---

## Output — what was generated

| Folder     | Contents                                | Purpose                |
| ---------- | --------------------------------------- | ---------------------- |
| `rgb/`     | `rgb_0000.png` → `rgb_0049.png`         | Colour training images |
| `normals/` | `normals_0000.png` → `normals_0049.png` | Surface geometry maps  |

Every frame has a matching RGB and normals image — paired data that tells an AI model both what things look like AND their 3D geometry.

---

## Code breakdown — MyCustomWriter.py

### Imports

```python
import numpy as np
import omni.replicator.core as rep
from omni.replicator.core import AnnotatorRegistry, BackendDispatch, Writer
from omni.replicator.core import functional as F
from omni.replicator.core.scripts.backends import BaseBackend
```

- `numpy` — for transforming normals data mathematically
- `omni.replicator.core` — NVIDIA's synthetic data framework
- `Writer` — base class your writer inherits from
- `AnnotatorRegistry` — registry of available data types (rgb, depth, normals etc)
- `BackendDispatch` — handles writing files to disk
- `F` — utility functions like `write_image`

---

### Class definition

```python
class MyCustomWriter(Writer):
```

Extends NVIDIA's base `Writer` class. Same pattern as extending any base class in OOP — you inherit all base behaviour and override what you need.

---

### Constructor `__init__`

```python
def __init__(self, rgb=True, normals=False, output_dir=None, backend=None, **kwargs):
    self.version = "0.0.1"
    self.data_structure = "renderProduct"
```

Sets up the writer when it's created. `version` and `data_structure` are metadata NVIDIA's framework expects.

```python
    if backend is not None:
        self.backend = backend
    elif output_dir:
        self.backend = BackendDispatch(output_dir=output_dir)
    else:
        raise ValueError("Provide backend or output_dir")
```

Figures out where to save files:

- When called from the GUI recorder → `backend` is passed directly
- When called from a Python script → you pass `output_dir`
- If neither → throws an error

```python
    self.annotators = []
    if rgb:
        self.annotators.append(AnnotatorRegistry.get_annotator("rgb"))
    if normals:
        self.annotators.append(AnnotatorRegistry.get_annotator("normals"))
    self._frame_id = 0
```

Registers which data types to capture based on `my_params.json`. `_frame_id` is the counter that numbers output files — starts at 0.

---

### The `write` method — heart of the writer

```python
def write(self, data: dict):
```

Isaac Sim calls this **once per frame**, passing all captured data as a dictionary.

```python
    if "renderProducts" in data:
        for rp_name, annotators_data in data["renderProducts"].items():
```

Handles the newer Isaac Sim data format where data is grouped by render product (camera). Loops through each camera's data.

```python
            if "rgb" in annotators_data:
                self.backend.schedule(F.write_image,
                    path=f"{rp_prefix}rgb/rgb_{self._frame_id}.png",
                    data=rgb_arr)
```

If RGB data exists, schedule it to be written as a PNG. The path creates the `rgb/` folder structure.

```python
            if "normals" in annotators_data:
                colored = ((n_arr * 0.5 + 0.5) * 255).astype(np.uint8)
                self.backend.schedule(F.write_image,
                    path=f"{rp_prefix}normals/normals_{self._frame_id}.png",
                    data=colored)
```

**The key transformation for normals:**
Raw normals are float values from -1 to 1. PNG files need integers from 0 to 255. The formula converts between them:

- `* 0.5 + 0.5` → shifts range from (-1 to 1) to (0 to 1)
- `* 255` → scales to (0 to 255)
- `.astype(np.uint8)` → converts to integer pixel format

Without this transformation the normals data can't be saved as an image at all.

```python
        self._frame_id += 1
        return
```

Increments frame counter after processing all cameras, then returns early.

---

### Legacy format handling

```python
    for annotator in list(data.keys()):
        annotator_split = annotator.split("-")
```

Handles the older Isaac Sim data format where annotators are named like `rgb-Camera_01`. The split separates the annotator type from the camera name. Same logic as above, just for the old format.

---

### Reset

```python
def on_final_frame(self):
    self._frame_id = 0
```

Called when recording stops. Resets the frame counter to 0 so the next recording starts numbering from scratch.

---

### Registration

```python
rep.writers.register_writer(MyCustomWriter)
```

The most important line for GUI integration. Tells NVIDIA's Replicator framework this writer exists and makes it available in the Synthetic Data Recorder dropdown. Without this line the writer never shows up as an option.

---

## The full flow in plain English

```
1. Configure what to capture → my_params.json (rgb + normals)
2. Hit Start in the recorder
3. Isaac Sim renders each frame
4. write() is called once per frame with all the data
5. Writer transforms data and schedules it to be saved
6. Files appear in output folder numbered by frame
7. Recording stops → on_final_frame() resets the counter
```

---

## Friction points — what other developers should know

### ❗ Custom writer must be registered every session

The `rep.writers.register_writer()` call only persists for the current Isaac Sim session. Every time you restart Isaac Sim you need to re-run the Script Editor registration step. There's no persistent auto-registration.

### ❗ The normals transformation is not optional

Raw normals data cannot be saved as PNG without the `((n_arr * 0.5 + 0.5) * 255).astype(np.uint8)` conversion. If you skip it the backend will throw a type error. This isn't documented clearly in the tutorial.

### ❗ Scene must have semantic labels

The Synthetic Data Recorder requires assets to be semantically labelled for annotators to work correctly. The sample warehouse scene comes pre-labelled. If you use your own scene you need to add semantic labels manually to every object.

---

## Key takeaway

Synthetic data generation is not just about capturing images — it's about generating precisely labelled, structured training data at scale that a real AI model can learn from. The custom writer is what gives you control over the format so the data fits directly into whatever training pipeline you're building for.
