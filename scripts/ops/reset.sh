#!/usr/bin/env bash
# Reset every known toggle back to baseline. Doesn't try to undo one-off
# manual patches (resource limits, ingress class, secrets) - those are
# reverted with whatever specific command was used to apply them, since a
# generic "undo" can't know the original value.
set -euo pipefail
NS=minishop

echo "Clearing imperative env overrides..."
kubectl -n "$NS" set env deployment/order EXPERIMENT_FLAG="" DB_POOL_SIZE- DB_MAX_OVERFLOW- >/dev/null
kubectl -n "$NS" set env deployment/catalog THROTTLE_MODE="" DB_POOL_SIZE- DB_MAX_OVERFLOW- >/dev/null
kubectl -n "$NS" set env deployment/notification CACHE_MODE="" DB_POOL_SIZE- DB_MAX_OVERFLOW- >/dev/null

echo "Restoring replica counts..."
for d in web-bff catalog order notification redis; do
  kubectl -n "$NS" scale deployment/"$d" --replicas=1 >/dev/null
done

echo "Uncordoning any drained nodes..."
for n in $(kubectl get nodes -o jsonpath='{.items[*].metadata.name}'); do
  kubectl uncordon "$n" >/dev/null 2>&1 || true
done

echo "Waiting for rollouts..."
for d in web-bff catalog order notification redis; do
  kubectl -n "$NS" rollout status deployment/"$d" --timeout=120s
done

echo "Done. Cluster back to baseline."
