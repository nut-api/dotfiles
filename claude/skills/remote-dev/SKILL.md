---
name: remote-dev
description: Set up a local-edit, remote-build-and-run dev workflow using Mutagen two-way file sync to a remote host (VM, server, beefier box), so builds/tests/containers run there instead of on a slow or architecture-mismatched local machine. Use when the local machine is too slow/resource-constrained for a project, when local and remote OS/arch differ (e.g. macOS arm64 vs Linux x86_64), or when the user asks to develop locally but build/run/test on a remote VM, server, or cluster.
---

# Remote Dev (Mutagen sync + remote exec)

## Quick start

1. Confirm Mutagen is installed locally (`mutagen version`); if missing:
   ```
   brew install mutagen-io/mutagen/mutagen   # may prompt: brew trust mutagen-io/mutagen
   mutagen daemon start
   ```
2. Probe the remote host before committing — confirm arch, resources, reachability:
   ```
   scripts/remote-dev.sh probe <user@host>
   ```
3. Start the sync (code stays local, mirrors to remote):
   ```
   scripts/remote-dev.sh sync <user@host> <remote-path> [local-path=.]
   ```
4. From here on: **edit locally, exec remotely.** Every build/run/test/docker/kubectl command goes through `ssh <user@host>` — never local shell for those. That's the whole point: native arch, no local CPU/RAM pressure.

## Why this pattern

- Local machine underpowered, or under load from other work.
- Local and remote differ in OS/arch (e.g. Apple Silicon laptop vs x86_64 Linux server) — building containers locally for the remote's arch means slow QEMU emulation or wrong-arch binaries/native modules. Building natively on the remote sidesteps this entirely.
- Keeps git history, editor, and muscle memory local; only the compute-heavy steps (build, test, run, container/k8s work) move remote.

## What syncs, what doesn't

Mutagen two-way sync (`--sync-mode=two-way-resolved`) mirrors files both directions in ~1s. Never sync:
- `.git` (`--ignore-vcs` handles this) — git push/pull stay local; the remote copy doesn't need `.git` to build/run.
- Arch-specific build/dependency output: `node_modules`, `target` (Rust), `.venv`/`__pycache__` (Python), `vendor` (Go), `dist`/`build`/`.next`. Install/build these **on the remote only** — syncing them risks landing wrong-arch native bindings/binaries.
- Local runtime state that shouldn't cross machines: `*.sqlite*`, `.wrangler`, `.terraform`.

`scripts/remote-dev.sh sync` bakes in this default ignore list; pass extra `--ignore=<pattern>` args for project-specific additions (e.g. `--ignore=.venv` is already default, but a project might need `--ignore=coverage`).

## Containers / k8s on the remote

Build images **on the remote host itself** (`ssh <host> 'docker build ...'`), never locally — matches native arch, avoids emulation. Whether the built image needs an extra load step depends on the cluster type:
- **Colima's k3s**: shares the host Docker daemon — a local `docker build` is immediately visible to the cluster, no extra step. `imagePullPolicy: Never` in the manifest is enough.
- **k3d**: nodes run as separate containers with their own containerd, NOT sharing the host daemon — after building, explicitly load the image:
  ```
  ssh <host> 'k3d image import <image>:<tag> -c <cluster-name>'
  ```
- **Plain k3s / kubeadm**: usually also its own containerd — use `k3s ctr images import <tar>` or push to a registry the node can reach.

See [REFERENCE.md](REFERENCE.md) for the full command cheat sheet, port-forward/tunnel patterns, and troubleshooting (musl vs glibc cross builds, mosh/tmux session persistence, registry fallback).

## Verify before declaring it done

Don't tell the user the workflow works without proof: create/read something through the project's own smoke test (curl, test suite, whatever it normally uses), run on the remote, and show the actual output.
