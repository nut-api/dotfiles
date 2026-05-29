# Reference Patterns

## hostAliases — mock domain resolution in pods

When a chart uses a hostname that doesn't exist in cluster DNS (test/mock clusters), inject it via `hostAliases` in the pod template. Do NOT patch CoreDNS.

**values.yaml:**
```yaml
hostAliases:
  - ip: "10.0.0.1"
    hostnames:
      - "my-service.internal"
```

**template:**
```yaml
{{- if .Values.hostAliases }}
hostAliases: {{ toYaml .Values.hostAliases | nindent 8 }}
{{- end }}
```

Applies to any pod spec, job template, or workflow template.

## Pull secret mount (private registry)

Secret must be type `kubernetes.io/dockerconfigjson`.

**values.yaml:**
```yaml
pullSecretName: "regcred"   # name of the k8s secret
```

**template volume:**
```yaml
{{- if .Values.pullSecretName }}
- name: pull-secret
  secret:
    secretName: {{ .Values.pullSecretName | quote }}
    items:
      - key: .dockerconfigjson
        path: config.json
{{- end }}
```

**script — set up docker config BEFORE any tool that pulls images:**
```sh
{{- if .Values.pullSecretName }}
if [ -f /pull-secret/config.json ]; then
  cp /pull-secret/config.json ~/.docker/config.json
else
  echo '{"auths":{}}' > ~/.docker/config.json
fi
{{- else }}
echo '{"auths":{}}' > ~/.docker/config.json
{{- end }}
```

## Event-driven retrigger pattern

After `helm upgrade`, clear old workloads and the resource that drives the event:

```bash
kubectl delete <workload> -n <workload-ns> --all
kubectl delete <trigger-resource> -n <watch-ns> --all

# Wait for the trigger resource to reappear (e.g. re-created by an operator)
until kubectl get <trigger-resource> -n <watch-ns> | grep -q "<expected-name>"; do sleep 5; done
kubectl get <workload> -n <workload-ns>
```

Adapt `<trigger-resource>` to whatever your EventSource or controller watches.
