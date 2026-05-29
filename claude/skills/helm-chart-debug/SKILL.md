---
name: helm-chart-debug
description: Debug newly implemented Helm charts by cycling through deploy → observe → diagnose → fix → upgrade → retrigger until the feature works as designed. Use when debugging a Helm chart that deploys Kubernetes resources (pods, workflows, jobs, CRDs) and something isn't working as expected after install or upgrade.
---

# Helm Chart Debug

## The Loop

```
establish problem + retrigger → observe → diagnose → fix → upgrade → retrigger → verify
```

Never stack multiple unverified fixes. One hypothesis per cycle.

## Step 0 — Establish before touching anything

Answer both questions before starting the loop. If either is unclear, ask the user or diagnose together — don't guess.

**1. What failed?**
- Which resource? (workflow, pod, job, CronJob)
- Which stage? (init container, sidecar, main container, specific step)
- What is the exact error message or exit code?

**2. How to retrigger?**
- Know the exact commands to reproduce the failure from scratch after a fix
- If the trigger is event-driven, know which resource to delete and how to confirm the new one appeared
- If retrigger is unclear — stop and ask the user before proceeding

If you cannot answer both, say so explicitly and ask:
> "I can see X failed but I'm not sure how to retrigger it. Can you tell me how the pipeline gets kicked off, or walk through it together?"

## Tooling principle

Use `kubectl`, `grep`, `jsonpath`, and `jq` — not Python or custom scripts. The data is already in the resource; you just need to read it. If you find yourself writing a script to extract info, use a simpler kubectl flag instead.

```bash
# Good
kubectl get workflow <name> -n <ns> -o jsonpath='{.status.message}'
kubectl logs <pod> -n <ns> -c main | tail -20
kubectl get <resource> -o json | grep -A3 '"env"'

# Avoid
kubectl get workflow -o json | python3 -c "import json,sys; ..."
```

## Step 1 — Observe

Find the failing resource, closest to the failure:

```bash
kubectl get pods -n <ns> --sort-by=.metadata.creationTimestamp

# Pod exists — check logs (main container first)
kubectl logs <pod> -n <ns> -c main | tail -30

# Pod not found — check parent resource
kubectl get workflow <name> -n <ns> -o jsonpath='{.status.message}'
```

## Step 2 — Diagnose

Read the error signal precisely. Common exit codes:

| Code | Meaning | Fix direction |
|------|---------|---------------|
| curl exit 6 | DNS failure | hostname not resolving in pod |
| curl exit 28 | Timeout | wrong port or host unreachable |
| exit 1 | Script logic / auth | read output above the exit line |

**DNS rule**: node `/etc/hosts` does NOT affect pods. Pods use CoreDNS.  
→ For mock/test domains: add `hostAliases` to the pod/workflow template.

**Protocol rule**: `https://` to a port-80 service = timeout. Match scheme to port.

**Script order rule**: if step B needs credentials or files set up by step A, A must run first. Read the script top-to-bottom and check what each step assumes already exists.

**Verify flags before using them**: Before adding a CLI flag, confirm it exists:
```bash
kubectl run tool-help --restart=Never -n <ns> --image=<image> --command -- <tool> <subcmd> --help
until kubectl get pod/tool-help -n <ns> -o jsonpath='{.status.phase}' | grep -qE "Succeeded|Failed"; do sleep 2; done
kubectl logs tool-help -n <ns>; kubectl delete pod tool-help -n <ns> --ignore-not-found
```

## When to search before guessing

**Same error after 2 fix attempts → stop and search before trying again.**

Pattern: you changed something, error persisted unchanged → your mental model of root cause is wrong. Read docs.

1. Run `--help` on the failing tool to verify flags exist
2. Search tool's GitHub issues for the exact error string
3. Find a working Kubernetes example in docs or issues

Failing to do this leads to stacking unverified guesses that each cost a full deploy+retrigger cycle.

## Step 3 — Fix

Minimal chart change. Touch only what the error points to.

```bash
helm lint .
helm template <release> . -f values.yaml | grep -A5 "<changed-field>"
```

## Step 4 — Upgrade + Retrigger

```bash
helm upgrade --install <release> . --namespace <ns> -f values.yaml
```

Clear old state so the pipeline triggers fresh:

```bash
kubectl delete <workload-resource> -n <ns> --all
kubectl delete <trigger-resource> -n <target-ns> --all

# Wait for retrigger
until kubectl get <trigger-resource> -n <target-ns> | grep -q "<name>"; do sleep 5; done
kubectl get <workload-resource> -n <ns>
```

## Step 5 — Verify

Watch pod logs directly — faster signal than polling workflow/job phase.

```bash
# Find the pod as soon as it appears
until kubectl get pods -n <ns> | grep -q "<pod-name-pattern>"; do sleep 3; done
kubectl get pods -n <ns> | grep "<pod-name-pattern>"

# Watch the relevant container directly
kubectl logs <pod> -n <ns> -c <container> 2>&1 | tail -30

# For multi-container pods, check the failing container first
kubectl logs <pod> -n <ns> -c <sidecar-name> 2>&1 | tail -10
kubectl logs <pod> -n <ns> -c main 2>&1 | tail -20

# Only poll phase if you need final pass/fail status
until kubectl get pods -n <ns> | grep "<pod>" | grep -qE "Error|Completed|CrashLoop"; do sleep 5; done
```

If still failing — go back to Step 1. Read the NEW error before forming next hypothesis.

## Reference

See [REFERENCE.md](REFERENCE.md) for hostAliases snippet and pull-secret mount pattern.
