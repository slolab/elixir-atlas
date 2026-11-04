"""Sync data/ with S3: immutable snapshots of input/ + extracted/, and releases. See README."""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import boto3

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"
SNAPSHOT_DIRS = ("input", "extracted")
BASE = DATA / ".snapshot.json"  # manifest of the snapshot local data was last pulled or pushed as


class Store:
    def __init__(self):
        uri = os.environ.get("DATA_S3_URI", "")
        if not uri.startswith("s3://"):
            sys.exit("Set DATA_S3_URI=s3://<bucket>/<prefix> in .env (see .env.template)")
        self.bucket, _, prefix = uri.removeprefix("s3://").partition("/")
        self.prefix = prefix.strip("/") + "/" if prefix.strip("/") else ""
        self.s3 = boto3.client("s3")

    def key(self, kind, id, path):
        return f"{self.prefix}{kind}/{id}/{path}"

    def ids(self, kind):
        pages = self.s3.get_paginator("list_objects_v2").paginate(
            Bucket=self.bucket, Prefix=f"{self.prefix}{kind}/", Delimiter="/"
        )
        return sorted(p["Prefix"].rstrip("/").rsplit("/", 1)[-1] for page in pages for p in page.get("CommonPrefixes", []))

    def manifest(self, kind, id):
        """The upload's manifest, or None while it is incomplete: manifest.json is written last."""
        try:
            return json.load(self.s3.get_object(Bucket=self.bucket, Key=self.key(kind, id, "manifest.json"))["Body"])
        except self.s3.exceptions.NoSuchKey:
            return None

    def latest(self, kind):
        return next(filter(None, (self.manifest(kind, id) for id in reversed(self.ids(kind)))), None)

    def download(self, kind, id, path, dest):
        dest.parent.mkdir(parents=True, exist_ok=True)
        self.s3.download_file(self.bucket, self.key(kind, id, path), str(dest))

    def upload(self, src, kind, id, path):
        self.s3.upload_file(str(src), self.bucket, self.key(kind, id, path))

    def copy(self, kind, src_id, dst_id, path):
        self.s3.copy({"Bucket": self.bucket, "Key": self.key(kind, src_id, path)}, self.bucket, self.key(kind, dst_id, path))

    def put_manifest(self, kind, manifest):
        body = json.dumps(manifest, indent=1).encode()
        self.s3.put_object(Bucket=self.bucket, Key=self.key(kind, manifest["id"], "manifest.json"), Body=body)


def load_env():
    env = REPO / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            key, sep, value = line.partition("=")
            if sep and value.strip() and not key.strip().startswith("#"):
                os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def scan(root, subdirs=(".",)):
    """{posix path relative to root: {sha256, size}}, skipping dotfiles such as .DS_Store."""
    files = {}
    for sub in subdirs:
        for p in sorted((root / sub).rglob("*")):
            rel = p.relative_to(root)
            if p.is_file() and not any(part.startswith(".") for part in rel.parts):
                files[rel.as_posix()] = {"sha256": sha256(p), "size": p.stat().st_size}
    return files


def git(*args):
    try:
        return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def new_manifest(files, id=None, **lineage):
    now = datetime.now(UTC)
    return {
        "id": id or now.strftime("%Y%m%dT%H%M%SZ"),
        **lineage,
        "created_at": now.isoformat(timespec="seconds"),
        "created_by": git("config", "user.name"),
        "git_commit": git("rev-parse", "HEAD"),
        "files": files,
    }


def load_base():
    return json.loads(BASE.read_text()) if BASE.exists() else None


def cmd_list(store, args):
    for kind in ("snapshots", "releases"):
        print(f"{kind}:")
        for id in store.ids(kind):
            if m := store.manifest(kind, id):
                source = f", from snapshot {m['snapshot']}" if m.get("snapshot") else ""
                print(f"  {id}  {len(m['files'])} files, by {m['created_by']}{source}")


def cmd_pull(store, args):
    remote = store.manifest("snapshots", args.id) if args.id else store.latest("snapshots")
    if not remote:
        sys.exit(f"No snapshot {args.id}" if args.id else "No snapshot on S3 yet")
    base = (load_base() or {}).get("files", {})
    local = scan(DATA, SNAPSHOT_DIRS)
    # Three-way: take S3's change unless the file changed locally since the last pull or push.
    for path in sorted(remote["files"].keys() | base.keys()):
        r, b, l = remote["files"].get(path), base.get(path), local.get(path)
        if l == r:
            continue
        if l != b:
            if r != b:
                print(f"kept your version of {path} (it also changed on S3)")
            continue
        if r is None:
            (DATA / path).unlink()
            print(f"deleted {path}")
        else:
            store.download("snapshots", remote["id"], path, DATA / path)
            print(f"got {path}")
    for d in SNAPSHOT_DIRS:
        (DATA / d).mkdir(parents=True, exist_ok=True)
    BASE.write_text(json.dumps(remote, indent=1))
    print(f"Local data is at snapshot {remote['id']}")


def cmd_push(store, args):
    parent = store.latest("snapshots")
    if parent and parent["id"] != (load_base() or {}).get("id"):
        sys.exit(f"S3 has snapshot {parent['id']}, which you haven't pulled. Run pull first.")
    local = scan(DATA, SNAPSHOT_DIRS)
    if not local:
        sys.exit("Nothing to push: data/input and data/extracted are empty")
    if parent and local == parent["files"]:
        sys.exit(f"Nothing to push: local data matches snapshot {parent['id']}")
    manifest = new_manifest(local, parent=parent and parent["id"])
    if manifest["id"] in store.ids("snapshots"):
        sys.exit(f"Snapshot {manifest['id']} already exists. Push again in a second.")
    for path, info in local.items():
        if parent and parent["files"].get(path) == info:
            store.copy("snapshots", parent["id"], manifest["id"], path)
        else:
            store.upload(DATA / path, "snapshots", manifest["id"], path)
            print(f"uploaded {path}")
    if (store.latest("snapshots") or {}).get("id") != (parent and parent["id"]):
        sys.exit("Someone pushed a snapshot meanwhile. Run pull, then push again.")
    store.put_manifest("snapshots", manifest)
    BASE.write_text(json.dumps(manifest, indent=1))
    print(f"Pushed snapshot {manifest['id']}")


def cmd_pull_release(store, args):
    remote = store.manifest("releases", args.id) if args.id else store.latest("releases")
    if not remote:
        sys.exit(f"No release {args.id}" if args.id else "No release on S3 yet")
    root = DATA / "releases" / remote["id"]
    local = scan(root)
    for path, info in remote["files"].items():
        if local.get(path) != info:
            store.download("releases", remote["id"], path, root / path)
            print(f"got {path}")
    (root / "manifest.json").write_text(json.dumps(remote, indent=1))
    print(f"Release {remote['id']} is in {root.relative_to(REPO)}")


def cmd_push_release(store, args):
    root = DATA / "releases" / args.id
    files = {path: info for path, info in scan(root).items() if path != "manifest.json"}
    if not files:
        sys.exit(f"No files in {root.relative_to(REPO)}")
    if store.manifest("releases", args.id):
        sys.exit(f"Release {args.id} is already on S3, and releases never change")
    base = load_base()
    if not base or scan(DATA, SNAPSHOT_DIRS) != base["files"]:
        sys.exit("Local input/ or extracted/ is not a snapshot on S3. Run push first, so the release records its data.")
    manifest = new_manifest(files, id=args.id, snapshot=base["id"])
    for path in files:
        store.upload(root / path, "releases", args.id, path)
        print(f"uploaded {path}")
    store.put_manifest("releases", manifest)
    (root / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(f"Pushed release {args.id}")


def main():
    load_env()
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="list snapshots and releases on S3")
    sub.add_parser("pull", help="update input/ and extracted/ to a snapshot (newest by default)").add_argument("id", nargs="?")
    sub.add_parser("push", help="upload input/ and extracted/ as a new snapshot")
    sub.add_parser("pull-release", help="download a release (newest by default)").add_argument("id", nargs="?")
    sub.add_parser("push-release", help="upload data/releases/<id>").add_argument("id")
    args = parser.parse_args()
    commands = {"list": cmd_list, "pull": cmd_pull, "push": cmd_push, "pull-release": cmd_pull_release, "push-release": cmd_push_release}
    commands[args.command](Store(), args)


if __name__ == "__main__":
    main()
