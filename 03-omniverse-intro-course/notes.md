# Intro to Developing with NVIDIA Omniverse — Course Notes

**Course:** [An Introduction to Developing with NVIDIA Omniverse](https://learn.nvidia.com/courses/course-detail?course_id=course-v1:DLI+S-OV-11+V1)  
**Kit App Template:** [NVIDIA-Omniverse/kit-app-template](https://github.com/NVIDIA-Omniverse/kit-app-template)  
**Completed:** Jul 8, 2026  
**Environment:** NVIDIA Brev cloud · Isaac Sim 6.0.0 · L40S GPU · Browser VS Code + noVNC

---

## What I learned

### 1. What is a `.kit` file

An Omniverse application is defined entirely by a `.kit` file — a config file that references all the extensions and settings the app needs. Think of it like a `package.json` for an Omniverse app. It tells Kit which extensions to load, in what order, and with what settings.

### 2. How extensions work

Omniverse apps are built entirely from extensions — every feature, every UI panel, every tool is an extension. The `.kit` file is just a list of extensions to assemble. Adding functionality to your app means adding an extension reference to the `.kit` file.

### 3. Kit App Template

The `kit-app-template` repo is NVIDIA's starting point for building custom Omniverse applications. It provides:

- A `repo.sh` build and launch script
- A `repo.toml` config that defines which apps to build
- A `source/apps/` folder where your `.kit` files live
- A `source/extensions/` folder for custom extensions

### 4. How to build and launch

```bash
# Build the app
./repo.sh build

# Launch the app
./repo.sh launch -n my_company.my_editor
```

### 5. Extensions window

The Extensions window (Window → Extensions) shows all loaded extensions and lets you browse, enable, and disable them at runtime. This is how you explore what's available in the Omniverse ecosystem.

---

## Friction points — what other developers should know

### ❗ repo.toml had a stale app reference

The `repo.toml` file had a hardcoded reference to `my_company.my_usd_composer.kit` which didn't exist after running `./repo.sh template new`. The build failed until I removed that entry and kept only `my_company.my_editor.kit`.

**Fix:**

```toml
# Change this
apps = ["${root}/source/apps/my_company.my_usd_composer.kit", "${root}/source/apps/my_company.my_editor.kit"]

# To this
apps = ["${root}/source/apps/my_company.my_editor.kit"]
```

### ❗ `-d` developer mode flag doesn't work

The course docs say to run `./repo.sh launch -d` to enable developer mode and get the Extensions menu. This flag doesn't exist in the current version of kit-app-template. The available flags are `-h`, `--container`, `-p`, and `-n`.

**Fix:** The Extensions window is already available under Window → Extensions without any special flag. Just launch normally with `-n appname`.

### ❗ noVNC required for UI rendering

Running `./repo.sh launch` from VS Code terminal starts the app but the UI window only renders in noVNC. You need both open simultaneously — VS Code for terminal commands and file editing, noVNC for the actual Omniverse UI.

### ❗ RTX loading takes 10-15 mins on first launch

First launch triggers shader compilation which takes 10-15 minutes. The progress shows as `RTX Loading 0.00%` for a long time before jumping. This is normal — subsequent launches are much faster because the cache is built.

---

## Hands-on — Two apps, two use cases

### My USD Editor — `my_company.my_editor.kit`

A minimal custom editor built from the kit-app-template. Used for basic USD scene manipulation — creating primitives, moving objects, editing properties directly. This is the app you build and customise as a developer.

- Created a cube primitive
- Moved it around the viewport
- Demonstrates the core USD scene editing workflow

### My USD Explorer — `my_company.my_usd_explorer.kit`

A more fully featured viewer app template. Better suited for loading and exploring existing USD assets — browsing the scene hierarchy, inspecting prims and properties, loading NVIDIA assets from the asset library.

- Loaded a NVIDIA USD asset from the asset library
- Explored the scene hierarchy
- Enabled the variant section in the UI — variants allow different versions of an asset to be swapped non-destructively, a core USD composition concept seen in the cert curriculum and now observed in a live app
- Demonstrates how Omniverse connects to NVIDIA's asset ecosystem

### Key difference

**Editor = you build scenes from scratch. Explorer = you load and inspect existing assets.**
In a real Physical AI pipeline, you'd use an editor-style app to assemble robot environments and an explorer-style app to inspect and validate USD assets before simulation.

Omniverse apps are just collections of extensions assembled by a `.kit` file. Understanding this makes the entire platform make sense — every capability is an extension, every app is a configuration. This is why the ecosystem is so composable and why OpenUSD sits underneath all of it as the shared data format.
