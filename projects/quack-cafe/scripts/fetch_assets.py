"""Restore the verified café exports from the release described by asset-manifest.json."""
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import tarfile
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
BLOCK = 1 << 20


def valid(path, spec):
    if not path.is_file() or path.stat().st_size != spec["bytes"]:
        return False
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest() == spec["sha256"]


def destination(name):
    path = (ROOT / name).resolve()
    if not path.is_relative_to(ROOT / "web/garden-bill-cafe"):
        raise ValueError(f"Unexpected asset path: {name}")
    return path


def restore(stream, path, spec):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as f:
        tmp = Path(f.name)
    try:
        count = 0
        digest = hashlib.sha256()
        with tmp.open("wb") as f:
            while block := stream.read(BLOCK):
                count += len(block)
                if count > spec["bytes"]:
                    raise ValueError(f"Oversized asset: {path.name}")
                digest.update(block)
                f.write(block)
        if count != spec["bytes"] or digest.hexdigest() != spec["sha256"]:
            raise ValueError(f"Checksum mismatch: {path.name}")
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)


def fetch(pack, base, cache):
    members = pack["members"]
    if all(valid(destination(name), spec) for name, spec in members.items()):
        print("Cached", pack["file"], flush=True)
        return
    url = base.rstrip("/") + "/" + pack["file"]
    with tempfile.TemporaryDirectory(dir=cache) as tmp:
        archive = Path(tmp) / "download"
        for attempt in range(3):
            try:
                request = urllib.request.Request(url, headers={"User-Agent":"Quack-Cafe/1"})
                with urllib.request.urlopen(request, timeout=90) as source:
                    restore(source, archive, pack)
                break
            except (OSError, ValueError):
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)
        if pack["file"].endswith(".tar.gz"):
            seen = set()
            with tarfile.open(archive, "r|gz") as bundle:
                for entry in bundle:
                    if not entry.isfile() or entry.name not in members or entry.name in seen:
                        raise ValueError(f"Unexpected archive member: {entry.name}")
                    seen.add(entry.name)
                    with bundle.extractfile(entry) as source:
                        restore(source, destination(entry.name), members[entry.name])
            if seen != set(members):
                raise ValueError("Incomplete image archive")
        else:
            name, = members
            with gzip.open(archive, "rb") as source:
                restore(source, destination(name), members[name])
    print("Restored", pack["file"], flush=True)


def main():
    manifest = json.loads((ROOT / "asset-manifest.json").read_text())
    base = os.environ.get("CAFE_ASSET_BASE_URL") or manifest["base_url"]
    cache = ROOT / ".cache"
    cache.mkdir(exist_ok=True)
    with (cache / "assets.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        for pack in manifest["assets"]:
            fetch(pack, base, cache)


if __name__ == "__main__":
    main()
