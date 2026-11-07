# Дипломный проект: DevOps-инфраструктура в Yandex Cloud

> **Статус доказательств на 07.11.2026:** инфраструктура и Kubernetes ранее развёрнуты; приложение, мониторинг и автоматический tag-triggered CD v1.0.5 реализованы.
> Исторические проверки и скриншоты не гарантируют текущий uptime. Для сдачи остаются подтверждение адресов/доступа проверяющему и готовность продемонстрировать восстановление с нуля.
>
> **Основа проекта:** [дипломное задание Нетологии «Дипломный практикум в Yandex.Cloud»](https://github.com/netology-code/devops-diplom-yandexcloud).

## Цель проекта

Создать воспроизводимую инфраструктуру в Yandex Cloud, развернуть в ней Kubernetes, опубликовать тестовое контейнерное приложение, организовать мониторинг и настроить автоматизированные процессы сборки, доставки приложения и управления инфраструктурой.

Для Kubernetes выбран **self-hosted** вариант с установкой через Ansible и Kubespray вместо управляемого Kubernetes-сервиса.

## Состояние выполнения

| Этап задания | Состояние | Результат и дальнейшие действия |
|---|---|---|
| 1. Создание облачной инфраструктуры | Конфигурация готова, есть исторические проверки | Отдельные bootstrap/S3 backend и infrastructure. Terraform CI Apply #6 успешен без изменений managed resources; готовность демонстрации с нуля остаётся OWNER_ACTION_REQUIRED. |
| 2. Создание Kubernetes-кластера | Развёрнут и исторически проверен | Kubespray/Ansible, три VM; 3/3 Ready подтверждались ранее. Текущее состояние узлов не проверялось, worker-2 прерываемый. Точный kubeconfig path требует документирования. |
| 3. Создание тестового приложения | Реализован | Отдельный app repo, Dockerfile, Yandex Container Registry; версия1.0.5 и immutable image reference ниже. |
| 4. Мониторинг, деплой приложения и автоматизация Terraform | Реализованы, evidence датирована | Prometheus/Grafana/Alertmanager/exporters, Kubernetes dashboards; исторический HTTP80. Адреса для проверяющего и снимок Terraform pipeline ещё требуют оформления. |
| 5. CI/CD приложения | Tag-triggered CD подтверждён OWNER_UI | v1.0.5 / Diploma CI/CD #33: test/build-and-push/deploy SUCCESS, rollout Ready, HTTP200/exact HTML version. |

Обозначения evidence: **VERIFIED_CONFIG** — проверенная конфигурация; **OWNER_UI** — подтверждённые владельцем скриншоты; **REUSED_HISTORICAL** — прежние датированные runtime-проверки. **UNKNOWN** — текущее состояние без свежего наблюдения.

## Архитектура

### Облачная сеть

В Terraform описаны VPC `diplom-network` и три подсети в разных зонах доступности:

| Подсеть | Зона | CIDR |
|---|---|---|
| `diplom-subnet-a` | `ru-central1-a` | `10.10.1.0/24` |
| `diplom-subnet-d` | `ru-central1-d` | `10.10.2.0/24` |
| `diplom-subnet-e` | `ru-central1-e` | `10.10.3.0/24` |

В текущем развёртывании используется первая и вторая подсети; третья создана как часть сетевой инфраструктуры. Kubernetes-узлы распределены по двум зонам доступности, а не по трём.

### Виртуальные машины Kubernetes

Таблица и адреса ниже — историческое описание развёртывания, не свежий inventory.
На 07.11.2026 текущее состояние VM не перепроверялось; worker-2 preemptible ранее мог быть NotReady.

| Имя | Роль | Зона | Внутренний IP | vCPU | RAM | Диск |
|---|---|---|---|---:|---:|---:|
| `k8s-control-1` | Control Plane / etcd | `ru-central1-a` | `10.10.1.12` | 2 | 4 ГБ | 30 ГБ |
| `k8s-worker-1` | Worker | `ru-central1-d` | `10.10.2.28` | 2 | 6 ГБ | 50 ГБ |
| `k8s-worker-2` | Worker | `ru-central1-d` | `10.10.2.34` | 2 | 6 ГБ | 50 ГБ |

ОС узлов — Ubuntu 22.04 LTS. Для `k8s-worker-1` закреплён публичный IP `158.160.190.231` после устранения проблем с исходящими соединениями. Публичные IP других узлов, выделяемые динамически, не фиксируются в этом документе.

В учебной конфигурации управляющая машина подключается к worker-узлам по SSH через control-plane (`ProxyJump`). Выделенного bastion-хоста нет.

## Этап 1. Подготовка инфраструктуры Terraform

Terraform-конфигурации разделены на два независимых каталога:

- [`terraform/bootstrap/`](terraform/bootstrap/) — сервисная учётная запись, IAM-права, статический ключ доступа и бакет Object Storage для Terraform state.
- [`terraform/infrastructure/`](terraform/infrastructure/) — S3 backend, VPC, подсети, security group и три Compute Cloud ВМ.

Основная конфигурация использует удалённое состояние в бакете `netology-diplom-tfstate-myachmen`, ключ `infrastructure/terraform.tfstate`. Ключи для S3 backend получаются через outputs bootstrap-конфигурации и **не публикуются** в Git.

Для развёртывания использовались Terraform и Yandex Cloud CLI. При ранней исторической проверке после изменения публичного IP `k8s-worker-1` конфигурация и состояние Terraform были синхронизированы: контрольный `terraform plan` завершился сообщением `No changes`.

**Что ещё требуется проверить по заданию:** воспроизводимый полный цикл уничтожения и создания инфраструктуры без дополнительных ручных изменений, а также минимально необходимые права сервисной учётной записи. Известное ограничение SSH-доступа: в опубликованной конфигурации [`security.tf`](terraform/infrastructure/security.tf) порт 22 открыт для `0.0.0.0/0`.

## Этап 2. Установка и проверка Kubernetes

Кластер установлен через **Kubespray v2.29.1** (commit `0c6a29553f90c55cba5e0e359470321dc7cf7d29`) с управляющей виртуальной машины Ubuntu 22.04 LTS.

| Компонент | Версия / реализация |
|---|---|
| Kubernetes | `v1.33.7` |
| Kubespray | `v2.29.1` |
| Container Runtime | `containerd 2.1.5` |
| CNI | Calico (VXLAN) |
| ОС Kubernetes-узлов | Ubuntu 22.04 LTS |

Использован project profile поверх Kubespray v2.29.1: [group_vars](ansible/kubespray/group_vars/k8s_cluster.yml) содержит overrides containerd/Calico/IPVS и metrics. Это не неизменённый upstream sample. [Project launcher/profile](ansible/kubespray/) и [защищённый inventory profile](ansible/kubespray-current/) описывают подготовку; локальные credentials/inventory artifacts в Git не публикуются.

Конфигурация и подробная инструкция:

- **[Развёртывание Kubernetes с помощью Kubespray](ansible/README.md)**;
- [Ansible inventory](ansible/inventory/diplom/hosts.yaml);
- [Пример SSH-конфигурации](ansible/ssh_config.example).

### Проверки Kubernetes

Исторически после установки и повторного запуска виртуальных машин выполнены проверки ниже. Более поздний postcheck04.11.2026 также подтверждал работоспособность; current health не заявляется:

1. Ansible `ping` завершился успешно на всех трёх узлах.
2. `kubectl get nodes -o wide` показал три узла в состоянии `Ready`.
3. Системные Pod в `kube-system`, включая Calico, CoreDNS, `kube-proxy` и компоненты control-plane, работали (`Running`, `1/1`).
4. Тестовый HTTP-запрос из Pod на `k8s-worker-1` в nginx Pod на `k8s-worker-2` завершился с `HTTP_CODE=200`, что подтвердило межузловую связность через Calico. Временные тестовые Pod после проверки удалены.

Команды просмотра состояния (на control-plane):

```bash
sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf get nodes -o wide
sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf get pods --all-namespaces -o wide
```

**Примечание:** команды выше — исторический control-plane пример. В последующих работах использовался отдельный защищённый project kubeconfig с проверкой TLS. **OWNER_ACTION_REQUIRED:** подтвердить и документировать точный безопасный путь, включая соответствие ожидаемому в задании `~/.kube/config`; содержимое kubeconfig и admin credentials не публиковать.

Опубликованные материалы: [узлы](img/22-kubernetes-nodes.png), [Deployment/Pods](img/23-kubernetes-deployment-pods.png), [Service/Ingress](img/24-kubernetes-service-ingress.png). Подписи нейтральны: файлы не являются текущей live проверкой.

## Этап 3. Тестовое приложение

Nginx отдаёт статическую HTML-страницу. [Репозиторий приложения](https://github.com/myachmen/netology-diploma-app/tree/4cbd4ce0c69a6660d40692c22ede1cca217f515a),
[Dockerfile](https://github.com/myachmen/netology-diploma-app/blob/4cbd4ce0c69a6660d40692c22ede1cca217f515a/Dockerfile).
Подтверждённая версия — **1.0.5**, source commit `4cbd4ce0c69a6660d40692c22ede1cca217f515a`.

Immutable OCI image reference успешного tag release (без registry credentials):

```text
cr.yandex/crpb1oihnpa2uai8m3mp/netology-diploma-app@sha256:0b99b6410f06de1e7aa10c196deb1115eae86b30f0a8a012d839f939b693a775
```

OWNER_UI: tag workflow #33 подтвердил rollout Ready, public HTTP200 и exact HTML version1.0.5 на момент запуска. **OWNER_ACTION_REQUIRED:** подтвердить HTTP80 URL приложения для проверяющего; адрес здесь не выдумывается.

## Этап 4. Мониторинг, приложение и управление Terraform

**VERIFIED_CONFIG:** kube-prometheus-stack92.17.0, Prometheus/Grafana/Alertmanager,
node-exporter и метрики Kubernetes. [Canonical values](ansible/helm/monitoring-values.yaml),
[deployment profile](ansible/helm/monitoring.md). Старые `kubernetes/monitoring/values.yaml`
и disabled Grafana ingress не являются дополнительным overlay/вторым release.

**REUSED_HISTORICAL:** postcheck04.11.2026 — monitoring revision2,28UP/0DOWN,
включая kube-proxy/etcd, Grafana health/login и Alertmanager readiness HTTP200.
Этим результатом заменены старые scrape gaps из раздела130 в deployment profile;
это не текущая проверка. Prometheus targets screenshot показывает несколько UP,
но сам по себе не доказывает total28/28. **OWNER_UI:** заполненные Kubernetes/Node Exporter panels подтверждены на опубликованных09/10.

![Опубликованный Kubernetes dashboard](img/09-grafana-kubernetes-cluster.png)
![Опубликованный Node Exporter dashboard](img/10-grafana-nodes.png)

[Prometheus targets](img/12-prometheus-targets.png) ·
[Alertmanager: Watchdog](img/15-alertmanager-alerts.png) ·
[Alertmanager status](img/16-alertmanager-status.png).
Это снимки, не гарантия uptime. Alertmanager принимает Watchdog; receiver null,
внешняя доставка уведомлений не подтверждена. Cluster disabled у единственного
экземпляра не объявляется дефектом. Prometheus emptyDir/Grafana persistence=false
означают ephemeral storage.

Конфигурационная схема HTTP: ALB80 → worker NodePort30080 → Traefik → Service → Pods.
[ALB HCL](terraform/infrastructure/alb.tf), [Traefik values](ansible/helm/traefik-values.yaml),
[app manifests](kubernetes/app/). Runtime этого пути подтверждался исторически;
`traefik-migration.md` — prepared-only план, не свидетельство выполненной миграции.
**OWNER_ACTION_REQUIRED:** подтвердить Grafana HTTP80 URL/существующий Host-resolution
и безопасный способ передачи логина проверяющему. Localhost port-forward не является публичным URL.

Выбран CI/CD-вариант автоматизации Terraform. Workflow находится **в другой ветке main**:
[terraform-automation.yml](https://github.com/myachmen/netology-devops-from-zero-homeworks/blob/7661c1b7535716f211e27be67c542d19d6ebbe8a/.github/workflows/terraform-automation.yml).
**OWNER_UI:** Terraform automation #6 — saved-plan Apply SUCCESS,14 managed no-op,
1 output change. Это подтверждает pipeline, не создание всех ресурсов с нуля.
**OWNER_ACTION_REQUIRED:** добавить проверенную ссылку на уже сохранённый снимок
именно Terraform pipeline и подтвердить готовность from-scratch демонстрации,
не выполняя новый Apply/Destroy ради документации.

## Этап 5. CI/CD приложения

[App workflow](https://github.com/myachmen/netology-diploma-app/blob/4cbd4ce0c69a6660d40692c22ede1cca217f515a/.github/workflows/docker-publish.yml):
main commit → tests/build/push; feature/PR → offline tests;
новый tag attempt1 → tests → exact-source image build/push → same-run digest deploy
→ guarded rollout → публичный HTTP/HTML version smoke. Не обещается registry push
для каждого feature commit; branch scope описан по фактическим guards.

**OWNER_UI,07.11.2026:** `v1.0.5`, commit `4cbd4ce0c69a6660d40692c22ede1cca217f515a`,
`Diploma CI/CD #33`: **test/build-and-push/deploy SUCCESS**, rollout Ready,
public HTTP200 и exact HTML version1.0.5. Это успешный автоматический tag-triggered CD,
отдельный от исторической manual recovery v1.0.4. Старые failures/recovery не выдаются за current failure.

![Опубликованный снимок tag workflow](img/31-github-actions-tag-release.png)
[Снимок шага deploy](img/32-github-actions-tag-deploy-success.png) ·
[Снимок summary](img/33-github-actions-deploy-summary.png).

Сохранены immutable digest, exact source/tag/version, single-attempt policy,
restricted SSH API tunnel, TLS/SNI/RBAC, baseline/atomic patch guards, rollout/smoke,
production concurrency и cleanup. Повторный запуск, новый tag/release или rollback
требуют отдельного разрешения и проверки фактического состояния.

## Материалы для сдачи диплома

| Материал | Проверенная ссылка / оставшееся действие |
|---|---|
| Terraform/configs и backend | [bootstrap](terraform/bootstrap/), [infrastructure](terraform/infrastructure/); **OWNER_ACTION_REQUIRED:** from-scratch демонстрация и подтверждение достаточности/минимальности IAM прав, без нового запуска ради README |
| Terraform automation | [Workflow main](https://github.com/myachmen/netology-devops-from-zero-homeworks/blob/7661c1b7535716f211e27be67c542d19d6ebbe8a/.github/workflows/terraform-automation.yml), owner evidence #6; **OWNER_ACTION_REQUIRED:** ссылка на сохранённый Terraform pipeline screenshot |
| Ansible/Kubernetes | [Ansible](ansible/), [Kubespray profile](ansible/kubespray/), [Kubernetes manifests](kubernetes/); **OWNER_ACTION_REQUIRED:** точный путь защищённого kubeconfig |
| App/Dockerfile/image | [App repo](https://github.com/myachmen/netology-diploma-app/tree/4cbd4ce0c69a6660d40692c22ede1cca217f515a), [Dockerfile](https://github.com/myachmen/netology-diploma-app/blob/4cbd4ce0c69a6660d40692c22ede1cca217f515a/Dockerfile), immutable OCI reference в разделе3 |
| Monitoring evidence | [Canonical values](ansible/helm/monitoring-values.yaml), dashboards09/10 и targets12 выше; historical health не равен current uptime |
| App HTTP80 | **OWNER_ACTION_REQUIRED:** подтверждённая ссылка для проверяющего |
| Grafana HTTP80 и вход | **OWNER_ACTION_REQUIRED:** подтверждённый URL/Host-resolution и безопасный канал логина; не помещать credentials в README/PNG |
| Tag CD | Материалы31–33 выше, owner-confirmed #33/v1.0.5 SUCCESS; точный Actions run URL добавлять только после его проверки |

Материалы архитектуры: [VM](img/01-yandex-cloud-vms.png), [VPC](img/02-yandex-cloud-vpc.png),
[ALB](img/03-yandex-cloud-alb.png), [ALB health](img/05-yandex-cloud-alb-health.png).
Снимки17–21 относятся к историческим CI-попыткам/ошибкам и не являются основной
витриной финального успеха. Секреты, ключи, kubeconfig и Terraform state не публикуются.

---

*Рабочая ветка: `diplom-yandexcloud`. Отчёт относится только к дипломному проекту и не изменяет оглавление домашних работ в ветке `main`.*
