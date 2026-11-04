# Traefik migration preparation — task 118

Prepared configuration only. No installation has been performed. Historical
`ingress-nginx-values.yaml` is superseded and must not be deployed. Kubespray's
Ingress addon stays disabled. Do not run both controllers.

## Pinned artifacts and compatibility

- Official chart: https://traefik.github.io/charts/traefik/traefik-42.3.0.tgz
- Chart 42.3.0, appVersion v3.7.17; image `docker.io/traefik:v3.7.17`.
- SHA256 chart: `d5a3180d93a96f3edbf82246037f65c4c8deec6f2b8a12c5cf1e55631c981d78`,
  matched official https://traefik.github.io/charts/index.yaml.
- Official chart Chart.yaml kubeVersion `>=1.30.0-0` includes Kubernetes 1.33.7;
  bundled README prerequisites and values document NodePort support.
- https://doc.traefik.io/traefik/deprecation/releases/ lists 3.7 as actively and
  security supported at review time (2026-11-04). Recheck before installation.
- Chart repository: https://github.com/traefik/traefik-helm-chart/tree/v42.3.0
- Image digest/signature and chart cryptographic provenance were NOT verified;
  SHA256 against the same official HTTPS index is integrity, not independent signing.
  Revalidate provenance/image identity before deployment; do not claim a verified image digest.
- Chart compatibility is not a live integration test or a guarantee of continued
  Kubernetes 1.33 upstream security maintenance.

## Contract and effects

ALB HTTP80 → current two worker targets:30080 → NodePort Service80 → Traefik
web8000 → application Ingress `/` → ClusterIP Service80 → application Pod80.
No cloud LoadBalancer, hostPort or hostNetwork. HTTPS30443 deliberately omitted:
ALB has no TLS listener; no DNS/TLS promise. Internal websecure8443 default exists
but is not exposed by Service; only web is a default routing entryPoint.

Two replicas, required worker hostname affinity and required hostname pod
anti-affinity match the worker labels recorded in task117. No control-plane
fallback. With two workers, a missing/preempted worker leaves one replica Pending.
Rolling updates use maxSurge0/maxUnavailable1 to avoid third-Pod scheduling
 deadlock; temporary single-replica availability is an accepted limitation to review.

Class `traefik`, controller `traefik.io/ingress-controller`, not default.
Only native Kubernetes Ingress provider is enabled; selector
`diploma-ingress=enabled` controls explicit opt-in. CRD/Gateway/NGINX compatibility
providers are disabled. Always use `--skip-crds`: chart ships CRDs even with CRD
provider disabled. No Gateway CRDs required. Rendered scope is one Deployment,
Service, ServiceAccount, ClusterRole, ClusterRoleBinding and IngressClass. No
admission webhook, Helm hook, Job, Secret or CRD in the selected rendering.
ClusterRole grants cluster reads including Secrets and update on Ingress status;
this is chart default RBAC scope, not permission for an executor to inspect secrets.
`publishedService` is disabled: do not copy worker addresses or pretend NodePort
Service has a public LB status. Ingress status may remain empty.

Non-root65532, RuntimeDefault seccomp, no privilege escalation, drop ALL,
read-only root filesystem; writable emptyDir data/tmp. Dashboard is disabled;
internal `/ping`8080 is used for readiness/liveness, not exposed via NodePort.
It does NOT replace the existing ALB health check `/` on30080. Without the app
route/backend, ALB may see404/503; controller-only installation does not prove
ALB healthy. Metrics port9100 remains internal with chart default Prometheus
annotations; no monitoring stack or metrics Service is installed here.

App retains hostless Prefix `/`, service80 and no TLS/redirect. Explicit priority1
keeps it below the separately staged Grafana Host route priority10. Nginx-specific
ssl-redirect annotation removed; Traefik web HTTP behavior replaces it.
Grafana retains its existing hostname and service80 but label `disabled` excludes
it from this provider. Host matching is NOT authorization. Do not change that label
or apply Grafana before separately approving authentication/access, DNS and monitoring.
Do not bulk-apply `kubernetes/`: private-registry credentials and workloads are separate.

## Offline validation (safe commands, from repository root)

Obtain the pinned public chart into a temporary directory, compare SHA256 above.
Commands below read only local files and never contact Kubernetes:

```sh
helm lint /tmp/traefik-42.3.0.tgz --kube-version 1.33.7 -f ansible/helm/traefik-values.yaml
helm template traefik /tmp/traefik-42.3.0.tgz --namespace traefik --kube-version 1.33.7 --skip-crds -f ansible/helm/traefik-values.yaml > /tmp/traefik-rendered.yaml
git diff --check
```

Inspect rendered NodePort30080, replicas2, affinity, class, image, provider selector,
RBAC and probes; no LoadBalancer, webhook, hooks or CRDs. YAML parse all changed
YAML and both Ingress manifests. Local schema/render checks cannot prove runtime,
image pull, network dataplane, actual target health or public DNS.

## Future installation — separate approval required; NOT executed

1. Review exact implementation commit and values; reconfirm chart support,
   provenance/image identity and approved Kubernetes compatibility risk.
2. Fresh bounded read-only gate: VM identity/trust and current worker target
   associations, both workers Ready/schedulable and expected labels/taints,
   system health, no controller/class/release/NodePort collision. Confirm current
   secure kubeconfig/context via established access; do not invent tunnels or credentials.
3. Offline render again and review six-object scope plus namespace. Separately
   approve one release `traefik`, namespace `traefik`, pinned chart42.3.0:

```sh
# FUTURE MUTATION, prohibited in task118; requires separate approval
helm install traefik /tmp/traefik-42.3.0.tgz --namespace traefik --create-namespace --skip-crds -f ansible/helm/traefik-values.yaml --wait --timeout 10m
```

   Do not add `--atomic`: that would perform an unapproved automatic uninstall.
   Do not retry install/upgrade automatically if command fails or times out.
4. Approved bounded read-only postchecks: Deployment2/2 and Pods Ready on different
   workers; Service only30080/HTTP; expected class/provider/RBAC; no cloud LB,
   no CRDs/admission; system health stable. Controller404 before app is expected,
   not justification to change ALB. Do not expose dashboard or health endpoint.
5. Separate app deployment approval: review registry credential handling without
   printing secrets; deploy only app scope after credential readiness. Then verify
   app endpoints and content, both worker NodePorts, actual ALB target health,
   public HTTP80 and expected response through ALB. ALB config stays unchanged.
6. Monitoring/Grafana authentication and DNS/TLS are separate decisions/stages.

STOP on identity/port/class/diff mismatch, unsupported/provenance uncertainty,
unexpected CRD/cloud objects, Pending/CrashLoop/image pull failures, system
regression, timeout or uncertain outcome. Preserve sanitized evidence; no repair,
whole operation retry or automatic rollback. For this first release there is no
previous Helm revision to roll back to: separately approve uninstall of only its
owned resources (and shared IngressClass/RBAC review). Existing namespace, app,
ALB, VM, Terraform/backend must not be deleted. Future upgrades require explicit
revision-specific rollback approval; rollout strategy briefly reduces redundancy.
