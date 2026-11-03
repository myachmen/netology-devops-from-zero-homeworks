# Проектный профиль Kubespray v2.29.1

Это локальная подготовка для будущего развёртывания, а не доказательство работающего кластера. Старые hosts.yaml, ssh-config.example и k8s-cluster-custom.yml — исторические материалы; этот профиль их не загружает. Глобальные настройки и upstream checkout не меняются.

`profile.py` требует `KUBESPRAY_CHECKOUT`, указывающий на чистый checkout v2.29.1, commit `0c6a29553f90c55cba5e0e359470321dc7cf7d29`. Запускайте Python из существующего окружения зависимостей Kubespray. Пути вычисляются, пользовательские абсолютные пути в Git не сохраняются.

Launcher сохраняет `kubespray-current/ansible.cfg`, явно задаёт roles и custom modules закреплённого checkout. `inventory.py` делегирует существующему защищённому dynamic inventory без копирования JSON, ключей или trust. Adjacent `group_vars/k8s_cluster.yml` загружается Ansible для всех трёх узлов. SSH остаётся строгим: существующий project trust, ED25519, без обновления ключей и forwarding. Upstream ansible.cfg использовать нельзя.

## Только локальные проверки

Из этого каталога, после задания переменной KUBESPRAY_CHECKOUT:

```bash
python profile.py verify
python profile.py inventory-graph
python profile.py config
```

`inventory-list` также локален, но вывод содержит private hostvars: не публиковать и не включать в общие логи. Launcher намеренно не предоставляет команд deployment, SSH, playbook или автоматического исправления. Проверка verify использует только локальные Ansible role/module loaders, не загружает playbooks и не исполняет modules.

## Выбранная конфигурация

Kubernetes 1.33.7, containerd 2.1.5/systemd cgroups, Calico VXLAN без IPIP, kube-proxy IPVS, CoreDNS/NodeLocalDNS, запрет swap, host etcd. Группы защищённого inventory определяют один control-plane/etcd и две workers; это не HA. Service/Pod сети наследуются из pinned defaults; статическая проверка №104 не выявила пересечений с Terraform сетями. Числовые диапазоны и адреса здесь не дублируются. При изменении topology проверять пересечения заново.

API использует private addressing и штатный localhost proxy Kubespray; cloud ALB предназначен для HTTP приложения, не для API. Существующее архитектурное решение — административный доступ через отдельно согласуемый SSH tunnel. Окончательная проверка endpoint/TLS SAN и защищённого kubeconfig обязательна до использования; доступ CI/CD остаётся UNKNOWN. Автоматическое получение локальных kubeconfig/kubectl отключено.

Для будущего, отдельно разрешённого deployment следует импортировать `environment()` из profile.py и передать возвращённый env процессу Ansible с абсолютным cluster.yml закреплённого checkout. Это сохраняет тот же ANSIBLE_CONFIG, inventory, roles/modules и adjacent group_vars независимо от cwd. До отдельного задания не запускать playbook, даже --check/--syntax-check. Новый запуск требует свежей identity/trust проверки и разрешения guest mutations.

## Единственный ingress — существующий Helm механизм

Сохранённый `ansible/helm/ingress-nginx-values.yaml` предназначен для исторически выбранного chart ingress-nginx 4.14.5 / controller 1.14.5. Kubespray ingress addon явно выключен. Установка Helm выполняется только после базового Kubernetes и отдельного разрешения; в этом задании ничего не установлено и chart не скачивался/не рендерился.

Service NodePort: HTTP 30080, HTTPS 30443. Две controller replicas закреплены affinity на двух worker hostname; обязательная pod anti-affinity распределяет их по разным workers. При потере одного worker одна replica останется Pending — осознанное ограничение доступности, особенно для preemptible worker. externalTrafficPolicy=Cluster позволяет обоим ALB targets направлять запросы к доступным endpoints. Runtime hostname labels и chart rendering ещё требуют проверки.

Terraform ALB использует HTTP backend 30080 на обеих workers, health path `/`; отдельный health port не задан, используется backend port. Существующий kubernetes/app/ingress.yaml имеет hostless Prefix `/`, class nginx и backend Service HTTP 80. После отдельно разрешённой установки приложения этот маршрут соответствует ALB health path. До готовности приложения ingress может вернуть 404/503: это не controller /healthz на порту 10254, и не доказательство исправного ALB. Не подменять health check искусственным 200 и не менять Terraform без разрешения. HTTPS NodePort 30443 сохранён, но ALB HTTPS listener/TLS не настроен.

Последовательность после нового разрешения: базовый Kubernetes → проверка nodes/CNI/DNS → единственный Helm ingress-nginx с этим values → проверка placement/Service → приложение и hostless `/` → отдельная проверка ALB health и внешнего HTTP. До появления здорового маршрута `/` runtime HTTP readiness остаётся UNKNOWN. Никакие команды этой последовательности заданием №105 не разрешены.

## Оставшиеся gates

Single etcd/control-plane, preemptible worker, Calico loose RPF/MTU и kernel modules, registry/package access, capacity, API TLS/доступ и chart compatibility требуют дальнейшей проверки. Значения RPF и Security Groups не меняются автоматически. Исторические успехи не доказывают текущую доступность. При ошибках — STOP без повторного deployment, repair/reset/destroy.
