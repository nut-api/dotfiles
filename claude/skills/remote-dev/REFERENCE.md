# Remote Dev — Reference

## Mutagen command cheat sheet

```
mutagen sync list                         # status of all sessions
mutagen sync monitor <name>                # live status until Ctrl-C
mutagen sync pause <name>
mutagen sync resume <name>
mutagen sync terminate <name>              # stop for good
mutagen sync reset <name>                  # force full rescan (after a conflict or weirdness)
mutagen daemon stop                        # kill the background daemon entirely
```

Conflicts: `two-way-resolved` auto-resolves in favor of the more-recently-modified side. If both sides edited the same file near-simultaneously, `mutagen sync list` shows a conflict entry — check it manually, don't assume it resolved the way you wanted.

## Alternative: Docker context over SSH (no full mutagen sync needed)

If the only goal is "build for the remote's arch," and you don't need live file sync, a Docker context is lighter weight:
```
docker context create remote --docker host=ssh://user@host
docker --context remote build -t myimg:latest .
```
For true multi-arch (need both arm64 and amd64 images from one pipeline), use buildx with multiple contexts as nodes:
```
docker buildx create --name multiarch --platform linux/amd64 remote-amd64
docker buildx create --name multiarch --append --platform linux/arm64 remote-arm64
docker buildx build --builder multiarch --platform linux/amd64,linux/arm64 -t myimg:latest --push .
```
This still requires files to already be on whichever host is building — pair it with mutagen sync, or just build from a fresh `git clone` on the remote if you don't need uncommitted local changes reflected.

## Cross-arch native build gotchas

- **musl vs glibc**: a Rust/Go/C binary built against glibc on one host and run on a runtime image with a different (often older) glibc can crash-loop with `GLIBC_x.xx not found`. Building against musl (`rust:1-alpine`, `FROM ... -musl` targets) produces a binary with no libc dependency — immune to this regardless of the final runtime base image.
- **npm native modules**: never sync `node_modules` across machines with different arch/OS — packages with native bindings (e.g. anything using `node-gyp`) compile a `.node` file for the build machine's arch. Run `npm install` on the remote, not synced from local.
- **QEMU emulation**: cross-arch `docker build --platform` without a matching remote builder falls back to QEMU emulation — often 5-10x slower than native. Prefer building natively on a host that matches the target arch.

## Session persistence on the remote

If you also SSH in directly (not just for one-off build commands, but interactively — e.g. tailing logs, running a debugger), use `tmux` or `mosh` so the session survives a dropped connection or laptop sleep:
```
ssh user@host
tmux new -s dev          # or: tmux attach -t dev
```
`mosh user@host` instead of `ssh` if the network is flaky — it survives IP changes/sleep that would kill a raw SSH session, and works fine alongside a backgrounded `tmux`.

## Reaching remote-only services from the laptop

A port-forward or tunnel started on the remote (`kubectl port-forward`, a dev server bound to `localhost`) isn't reachable from the laptop by default. Two options:
- Run the port-forward remotely and curl/test **from the remote's own shell** (simplest, no extra step, matches "exec is remote").
- Tunnel it back if you want to hit it from a local browser or GUI tool:
  ```
  ssh -L 8080:localhost:8080 user@host
  ```

## No registry, no shared daemon: last-resort image transfer

If a cluster's runtime doesn't share the build host's daemon and has no `image import`-style command (or you built somewhere entirely separate from the cluster), fall back to a save/load pipe over SSH:
```
docker save myimg:latest | ssh user@host 'docker load'
```
Slower than a native import for large images, but always works as long as both ends have any Docker/OCI-compatible runtime.
