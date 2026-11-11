import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("release", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    release = args.release.resolve()
    manifest = json.loads((release / "manifest.json").read_text())
    files = ["graph.sqlite", "schema_config.yaml", "provenance.json", "run.json"]
    for filename in files:
        content = (release / filename).read_bytes()
        if hashlib.sha256(content).hexdigest() != manifest["files"][filename]["sha256"] or len(content) != manifest["files"][filename]["size"]:
            raise ValueError(f"Release checksum mismatch: {filename}")
    output = Path(tempfile.mkdtemp(prefix="atlas-serving-"))
    ignore = shutil.ignore_patterns(".venv", "node_modules", "dist", "__pycache__", ".pytest_cache", ".env", "*.pyc")
    for directory in ("server", "dashboard"):
        shutil.copytree(root / directory, output / directory, ignore=ignore)
    for filename in ("Dockerfile",):
        shutil.copy2(root / filename, output / filename)
    (output / "release").mkdir()
    for filename in ["manifest.json", *files]:
        shutil.copy2(release / filename, output / "release" / filename)
    print(output)


if __name__ == "__main__":
    main()
