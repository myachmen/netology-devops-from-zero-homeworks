# Monitoring profile: kube-prometheus-stack

Installed and checked in task130 on 2026-11-04 UTC in the existing three-node
Kubespray cluster: Helm deployed revision1, eight monitoring Pods Ready, actual
Kubernetes metrics collected. App HTTP and ALB health remained healthy. These
are timestamped observations, not a guarantee of current availability. Use the
published task130 report for detailed evidence. Do not repeat the install.

- Release/namespace: `monitoring` / `monitoring`.
- Official chart: `kube-prometheus-stack` **92.17.0**, appVersion **v0.94.2**
  (Prometheus Operator version, not the Prometheus server version).
- Source: https://prometheus-community.github.io/helm-charts
- Package SHA256: `f267989be8318f12b37273a075504d4986a2a744383daf7cca0732a8d35d400d`.
- Chart kubeVersion `>=1.25.0-0` includes the existing Kubernetes1.33.7.
- Canonical values for this deployment: `ansible/helm/monitoring-values.yaml`.
  The older `kubernetes/monitoring/values.yaml` is a historical duplicate, not a
  second release or an additional values overlay to apply automatically.

## Storage and resources

Prometheus retention7d, emptyDir5Gi; Grafana persistence disabled. Alertmanager
uses its chart's ephemeral default. No PVC, dynamic disk or LoadBalancer Service
is requested. Metrics, silences and unsaved Grafana settings can be lost when
Pods/VMs are recreated. Limits/requests are retained from the existing profile;
capacity must be rechecked before future changes. Request headroom is not a
measurement of actual RAM/CPU usage. Sidecars/node-exporter have chart defaults.

## Expected Kubernetes scope

The reviewed rendering includes10 monitoring.coreos.com CRDs, Prometheus and
Alertmanager CRs, ServiceMonitors/PrometheusRules, the operator, Grafana,
kube-state-metrics, node-exporter DaemonSet, Services, ConfigMaps, generated
Secrets, chart RBAC and admission webhooks/certificate hooks. The chart has
Grafana test hooks which are not executed by install; `helm test` is a separate
action. No cluster-admin binding is used. The operator has standard broad
cluster monitoring permissions; do not add manual RBAC or change existing
application/Traefik resources. Node-exporter uses hostNetwork/hostPID and host
read-only mounts, without privileged container mode. These are reviewed chart
features, not Yandex Cloud network/VM configuration writes.

## Grafana routing and authentication

Grafana ingress is owned by this Helm release and uses class `traefik`, explicit
provider opt-in label `diploma-ingress=enabled`, web entrypoint and priority10.
It uses the existing separate Grafana Host from the staged monitoring manifest;
the application's hostless `/` route is unchanged. Do not apply the older
`kubernetes/monitoring/grafana-ingress.yaml` as a second route: it is disabled
and superseded for this deployment by the chart-managed ingress.

Grafana anonymous access is explicitly disabled. The chart generates an
unpredictable admin password; no static password is committed and the executor
does not print/read Secret contents to log in. Login page/API health can be
checked without reading admin credentials; `/api/user` must reject unauthenticated
requests. Existing public ALB HTTP80 can be tested with the Grafana Host header.
This does not configure public DNS or TLS, and HTTP is not a safe transport for
sending an admin password over an untrusted network. Credential retrieval/login
or future TLS/DNS changes need their own approved scope.

## Validation and future operation

Use only the protected project kubeconfig explicitly. A temporary strict SSH
forwarding must have PID ownership, bounded lifecycle and finally cleanup. Do
not copy/recreate credentials or leave a permanent tunnel. Before a future
approved operation check release ownership, nodes/system health, capacity,
StorageClass/PVC implications, chart digest and offline lint/template. Inspect
rendered RBAC/CRDs/webhooks and reject unexpected changes. Rendering may contain
generated Secrets: keep it private and never commit or print it.

A new-cluster install (only with separate explicit approval) uses the pinned
package, these values, `--create-namespace --wait --wait-for-jobs --timeout 10m`.
No `--atomic`, automatic retry, upgrade, rollback or uninstall. If an install
fails/times out, preserve its state, collect bounded read-only evidence and stop.
Do not change the working application, Traefik or ALB to make checks pass.

Postchecks must include actual Prometheus targets and Kubernetes metrics, not
only Running Pods; Grafana database/login health and unauthenticated rejection;
Alertmanager readiness; and the existing app HTML/ALB target health before/after.
Control-plane metrics may be unreachable with the existing secure bindings or
certificates: report down target categories honestly, without exposing endpoints
or disabling monitors merely to claim green. No certificate extraction or
control-plane reconfiguration is authorized by this profile.

## Task130 check results / known limitations

Prometheus readiness200,24 targets UP/3 DOWN; the three DOWN targets are
kube-proxy with connection refused. Do not call this all-green scraping and do
not change kube-proxy, ports, TLS or cloud rules automatically. Etcd scraping
was not established by the observed target list and remains unverified.
Queries confirmed kube_node_info count3, kube_pod_info30, container CPU series95,
node_uname_info3 and two ready app Pod metrics;35 rule groups loaded.
Grafana13.3.0 health database=ok, login200, unauthenticated /api/user401;
Alertmanager readiness200. External Grafana HTTP200 was checked with explicit
Grafana Host header through the existing ALB. DNS resolution and TLS were not
configured. App expected HTML remained200 and all four ALB health records
HEALTHY. Dashboard configuration is provisioned by the chart; an authenticated
UI/dashboard review was not performed because credentials were not read.

The installer had one failed local capacity-parser session before any mutation;
a second forwarding was separately approved after offline parser tests. There
was still exactly one Helm install and both temporary SSH sessions were closed.
No automatic upgrade, rollback, repair or cloud changes were performed.
