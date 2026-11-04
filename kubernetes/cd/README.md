# CD RBAC draft — №139, не применять автоматически

Только tracked specification. Effective cluster grants, наличие SA/Binding,
дополнительные права и token lifetime **UNKNOWN**. В №139 Kubernetes не вызывался,
Role/Binding/SA не применялись и credentials не выдавались.

`rbac.yaml`: namespace default; ServiceAccount/Role/RoleBinding
github-actions-deployer. Единственное rule: apps/deployments, resourceNames
только diploma-app, verbs get/patch/list/watch. Нет update, namespace-wide
deployments list/watch, replicasets/pods, Secrets, exec/proxy, nodes, RBAC writes
или ClusterRoleBinding. SA automount=false не мешает отдельно разрешённому
TokenRequest; права выдачи токена самому deployer не предоставляются.

## Почему нужен list

В закреплённом kubectl1.33.7
[rollout_status.go L186–202](https://github.com/kubernetes/kubernetes/blob/a7245cdf3f69e11356c7e8f92b3e78ca4ee4e757/staging/src/k8s.io/kubectl/pkg/cmd/rollout/rollout_status.go#L186)
ListWatch выполняет list и watch с metadata.name=diploma-app.
[RBAC1.33](https://v1-33.docs.kubernetes.io/docs/reference/access-authn-authz/rbac/)
требует такой field selector для ограниченных resourceNames list/watch.
`get/patch/watch` из первоначального плана137 недостаточно. Отказ исправлять
молчаливым namespace-wide list/watch запрещён: сначала отдельно разрешённый test.

## Будущая positive/negative matrix — сейчас не выполнять

| Под scoped identity | Ожидание |
|---|---|
| get named deployment diploma-app в default | allow |
| list deployments.apps с field-selector metadata.name=diploma-app | allow, только этот объект |
| bounded watch того же selector | allow; отсутствие событий/timeout ≠ Forbidden |
| SelfSubjectAccessReview patch named deployment | allow, без пробной мутации |
| unfiltered deployments list/watch, selector другого имени | deny |
| get/patch другого Deployment или другого namespace | deny |
| Secret get/list, pods/exec/attach/portforward, replicasets/pods, nodes, proxy | SelfSubjectAccessReview deny, не извлекать реальный Secret |
| role/binding/SA/token creation, impersonation | deny |

Проверить effective identity/дополнительные bindings и discovery/SelfSubjectAccessReview
доступ. can-i дополняет actual filtered list/watch, а не заменяет его. Не выдавать
CI admin/impersonation для проверки. Все тесты требуют отдельного разрешения.

## Остаточный blast radius и activation gate

Patch named Deployment может менять Pod template, serviceAccountName, mounts,
commands/securityContext, не только image. RBAC не ограничивает JSON fields.
Нужны явное принятие этого риска для учебного приложения либо отдельная admission
policy; её установка не разрешена №139. CLI JSON patch с UID/resourceVersion/
generation/image tests защищает от случайного drift, но не уменьшает права
украденного token на сервере.

До активации: независимый host-key/TLS identity gate, restricted SSH account,
действительные branch/tag protections и environment reviewers, scoped short-lived
token с подтверждёнными TTL/audience, один approved ref/SHA/run и запрет иных app
writes. Ни synthetic fixture, ни boolean в CI не доказывает эти условия.
По умолчанию deployment disabled; automatic retry/rollback/repair отсутствуют.
