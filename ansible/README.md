# Развёртывание Kubernetes с помощью Kubespray

## Общая информация

Kubernetes-кластер дипломного проекта развёрнут в Yandex Cloud с помощью Ansible и Kubespray.

| Компонент | Версия / реализация |
|---|---|
| Kubespray | v2.29.1 |
| Kubernetes | v1.33.7 |
| ОС узлов | Ubuntu 22.04 LTS |
| Container Runtime | containerd |
| Сетевой плагин | Calico |

## Архитектура кластера

| Узел | Роль | Внутренний IP |
|---|---|---|
| `k8s-control-1` | Control Plane, etcd | `10.10.1.12` |
| `k8s-worker-1` | Worker | `10.10.2.28` |
| `k8s-worker-2` | Worker | `10.10.2.34` |

Управляющая машина: `diplom-ansible` (Ubuntu 22.04 LTS, Vagrant/VirtualBox).

## Состав каталога

- [`inventory/diplom/hosts.yaml`](inventory/diplom/hosts.yaml) — Ansible inventory с узлами и группами.
- [`ssh_config.example`](ssh_config.example) — пример SSH-конфигурации управляющей машины.

Рабочий каталог `group_vars` совпадает с `inventory/sample/group_vars` из Kubespray v2.29.1 (проверено командой `diff -ru`). Поэтому стандартные файлы `group_vars` не дублируются в дипломном репозитории.

## Подготовка управляющей машины

Необходимо установить Git, Python, Ansible и зависимости в соответствии с требованиями Kubespray v2.29.1.

Получение исходного кода:

```bash
git clone --branch v2.29.1 https://github.com/kubernetes-sigs/kubespray.git
cd kubespray
```

Создание inventory из стандартного шаблона:

```bash
cp -a inventory/sample inventory/diplom
cp /path/to/diploma-repository/ansible/inventory/diplom/hosts.yaml inventory/diplom/hosts.yaml
```

Замените `/path/to/diploma-repository` путём к локальной копии дипломного репозитория. Настройте Python-окружение и установите зависимости по документации выбранной версии Kubespray.

## Настройка SSH

Для доступа к узлам используется пользователь `ubuntu`.

1. Скопируйте содержимое [`ssh_config.example`](ssh_config.example) в `~/.ssh/config` управляющей машины или объедините с существующими настройками.
2. Замените `<CONTROL_PLANE_PUBLIC_IP>` актуальным публичным IP узла `k8s-control-1`.
3. Настройте SSH-ключи или SSH-агент.
4. Проверьте подключение к worker-узлам через `ProxyJump k8s-control-1`.

```bash
ssh k8s-control-1 hostname
ssh k8s-worker-1 hostname
ssh k8s-worker-2 hostname
```

При смене динамического публичного IP control-plane обновите `HostName` в SSH-конфигурации. Приватные ключи и другие секреты в репозиторий не добавляются.

## Развёртывание Kubernetes

Команды выполняются из каталога Kubespray после настройки зависимостей и SSH.

Проверка доступности узлов:

```bash
ansible -i inventory/diplom/hosts.yaml all -m ping -T 10
```

Проверка синтаксиса:

```bash
ansible-playbook -i inventory/diplom/hosts.yaml cluster.yml --syntax-check
```

Установка:

```bash
ansible-playbook -i inventory/diplom/hosts.yaml -b cluster.yml
```

В зафиксированных командах установки дополнительные `--extra-vars` не использовались.

## Проверка кластера

На `k8s-control-1`:

```bash
sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf get nodes -o wide
sudo kubectl --kubeconfig=/etc/kubernetes/admin.conf get pods -n kube-system -o wide
```

В ходе проверки подтверждено:

- все три узла находятся в состоянии `Ready`;
- системные Pod, включая Calico и CoreDNS, работают;
- запрос из тестового Pod на `k8s-worker-1` к nginx Pod на `k8s-worker-2` вернул HTTP 200;
- временные тестовые Pod удалены после проверки.

## Примечания

В учебной конфигурации `k8s-control-1` используется также как SSH jump host. Для промышленной инфраструктуры предпочтителен отдельный bastion-сервер.

При пересоздании облачных ресурсов с другими внутренними IP необходимо обновить `hosts.yaml` и `ssh_config.example` (или рабочий `~/.ssh/config`).

Этот README описывает развёртывание Kubernetes. Виртуальные машины, сети и правила безопасности Yandex Cloud создаются отдельно с помощью Terraform.

## Удалённое управление Kubernetes

Для администрирования кластера используется отдельная управляющая виртуальная машина `diplom-ansible` под управлением Ubuntu 22.04 LTS. Доступ к Kubernetes API осуществляется через SSH-туннель до `k8s-control-1`, без публикации API в интернете.

### Установка kubectl

На управляющей машине установлен `kubectl` версии `v1.33.7`, соответствующей версии кластера:

```bash
curl -fL --retry 3 \
  -o /tmp/kubectl \
  https://dl.k8s.io/release/v1.33.7/bin/linux/amd64/kubectl
sudo install -o root -g root -m 0755 /tmp/kubectl /usr/local/bin/kubectl
kubectl version --client
```

### Получение kubeconfig

Файл `/etc/kubernetes/admin.conf` с control-plane скопирован на управляющую машину с помощью Ansible:

```bash
mkdir -p ~/.kube
chmod 700 ~/.kube

ansible -i inventory/diplom/hosts.yaml k8s-control-1 \
  -b -m fetch \
  -a 'src=/etc/kubernetes/admin.conf dest=/home/vagrant/.kube/config flat=yes'

chmod 600 ~/.kube/config
```

В полученном kubeconfig адрес Kubernetes API — `https://127.0.0.1:6443`. Он доступен на управляющей машине только при работающем SSH-туннеле. **Kubeconfig содержит административные учётные данные и не должен попадать в Git.**

### SSH-туннель к Kubernetes API

Скрипт [`scripts/k8s-tunnel.sh`](scripts/k8s-tunnel.sh) создаёт локальное перенаправление порта `127.0.0.1:6443` управляющей машины на `127.0.0.1:6443` узла `k8s-control-1`.

Для запуска скрипта требуется настроенный SSH-доступ по имени `k8s-control-1` (см. [`ssh_config.example`](ssh_config.example)).

На управляющей машине:

```bash
mkdir -p ~/bin
cp scripts/k8s-tunnel.sh ~/bin/k8s-tunnel.sh
chmod 700 ~/bin/k8s-tunnel.sh
~/bin/k8s-tunnel.sh
```

Команда `cp` предполагает, что репозиторий с этим файлом доступен на управляющей машине. В текущей учебной среде скрипт уже создан по пути `/home/vagrant/bin/k8s-tunnel.sh`; повторное копирование не требуется.

Туннель занимает терминал и работает, пока выполняется скрипт. Для команд `kubectl` следует открыть вторую SSH-сессию к `diplom-ansible`.

### Проверка доступа к кластеру

Во второй сессии:

```bash
ss -lntp | grep ':6443'
kubectl get nodes -o wide
kubectl get pods -n kube-system -o wide
```

При проверке все три узла (`k8s-control-1`, `k8s-worker-1`, `k8s-worker-2`) находились в состоянии `Ready`, версия Kubernetes — `v1.33.7`.

При остановке SSH-туннеля `kubectl` на управляющей машине теряет доступ к Kubernetes API. Чтобы восстановить подключение, достаточно снова запустить `~/bin/k8s-tunnel.sh`.
