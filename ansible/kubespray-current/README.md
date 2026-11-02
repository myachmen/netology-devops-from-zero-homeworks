# Текущий локальный Kubespray inventory

Рабочая точка входа: `inventory.py` и `ansible.cfg` этого каталога.
Исторические `hosts.yaml` и Kubespray `ansible.cfg` не используются автоматически.
Исходники Kubespray: закреплённый tag `v2.29.1`, commit
`0c6a29553f90c55cba5e0e359470321dc7cf7d29`, Kubernetes baseline `1.33.7`.
Это подготовка конфигурации, а не разрешение установки.

`inventory.py` — локальный executable inventory reader стандартной библиотеки Python.
Он только читает `.local/nodes.json`: не обращается к облаку, SSH или Ansible.
Файл создаётся отдельно из свежих Compute metadata, directory mode 0700,
file mode 0600; `.local/` исключён из Git. Рядом с файлами допускается только
согласованный локальный refresh metadata: автоматического обновления нет.

Формат локальных настроек (placeholders, не значения для запуска):

```json
{
  "known_hosts_file": "<EXISTING_VERIFIED_PROJECT_TRUST_FILE>",
  "ssh_private_key_file": "<EXISTING_DEDICATED_KEY_FILE>",
  "hosts": {
    "k8s-control-1": {"public_endpoint": "<CURRENT_PUBLIC>", "private_endpoint": "<CURRENT_PRIVATE>"},
    "k8s-worker-1": {"public_endpoint": "<CURRENT_PUBLIC>", "private_endpoint": "<CURRENT_PRIVATE>"},
    "k8s-worker-2": {"public_endpoint": "<CURRENT_PUBLIC>", "private_endpoint": "<CURRENT_PRIVATE>"}
  }
}
```

Private key contents, passwords, tokens и credentials сюда не копируются.
Пути существующих key/trust файлов и реальные адреса остаются только локально.
Не добавлять `.local/` с force и не публиковать вывод inventory `--list`/`--host`.
При изменении identity/endpoint/host key остановиться: отдельное подтверждение
trust обязательно, этот reader не выполняет enrollment.

Роли: control-plane и etcd на control-1; kube_node только два workers.
`ansible_host` — текущий public endpoint для ранее проверенного прямого SSH,
`ip`/`access_ip` — private address. Become явно sudo/root, без пароля.
Клиентский SSH использует отдельный project trust file и `ssh_config` этого
каталога: strict ED25519, без forwarding, автопринятия или повторов.
GlobalKnownHostsFile направлен в тот же проверенный project trust file,
системные/default trust файлы не изменяются.

Локальные проверки (из корня основного репозитория, в существующем venv):

```bash
export ANSIBLE_CONFIG="$PWD/ansible/kubespray-current/ansible.cfg"
ansible-inventory --graph
```

Это только локальный разбор. Не заменять его `ansible ping`, become или playbook.
При запуске из каталога Kubespray надо явно оставить этот ANSIBLE_CONFIG и
этот inventory; не полагаться на небезопасный upstream config. Убедиться в
соответствующем CONFIG_FILE и host-key checking до отдельно разрешённых запусков.

Приватный `.local/nodes.json` не появится после clone: перед использованием
его нужно отдельно подготовить по свежим metadata и проверить все host keys.
Отсутствие файла приводит к отказу reader. В config разрешён только script
plugin, unparsed_is_failed=True: нет fallback на другие форматы/исторические файлы.
Group_vars, metrics exposure, runtime preparation и реальный become требуют
отдельного согласования. Содержимое старого ignored inventory/group_vars
не копировалось. Текущие статические проверки не доказывают readiness deployment.
