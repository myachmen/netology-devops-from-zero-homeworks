# Домашнее задание по теме "Работа с roles" Ячмень Марк Викторович

## Подготовка к выполнению

1. * Необязательно. Познакомьтесь с [LightHouse](https://youtu.be/ymlrNlaHzIY?t=929).
2. Создайте два пустых публичных репозитория в любом своём проекте: vector-role и lighthouse-role.
3. Добавьте публичную часть своего ключа к своему профилю на GitHub.

## Основная часть

Ваша цель — разбить ваш playbook на отдельные roles. 

Задача — сделать roles для ClickHouse, Vector и LightHouse и написать playbook для использования этих ролей. 

Ожидаемый результат — существуют три ваших репозитория: два с roles и один с playbook.

**Что нужно сделать**

1. Создайте в старой версии playbook файл `requirements.yml` и заполните его содержимым:

   ```yaml
   ---
     - src: git@github.com:AlexeySetevoi/ansible-clickhouse.git
       scm: git
       version: "1.13"
       name: clickhouse 
   ```

2. При помощи `ansible-galaxy` скачайте себе эту роль.
3. Создайте новый каталог с ролью при помощи `ansible-galaxy role init vector-role`.
4. На основе tasks из старого playbook заполните новую role. Разнесите переменные между `vars` и `default`. 
5. Перенести нужные шаблоны конфигов в `templates`.
6. Опишите в `README.md` обе роли и их параметры. Пример качественной документации ansible role [по ссылке](https://github.com/cloudalchemy/ansible-prometheus).
7. Повторите шаги 3–6 для LightHouse. Помните, что одна роль должна настраивать один продукт.
8. Выложите все roles в репозитории. Проставьте теги, используя семантическую нумерацию. Добавьте roles в `requirements.yml` в playbook.
9. Переработайте playbook на использование roles. Не забудьте про зависимости LightHouse и возможности совмещения `roles` с `tasks`.
10. Выложите playbook в репозиторий.
11. В ответе дайте ссылки на оба репозитория с roles и одну ссылку на репозиторий с playbook.

## Решение 1

Для выполнения задания выполним следующие действия.

Подготовим виртуальные машины с помощью Vagrant.
В директории с Vagrant проектом создадим Vagrant файл следующего содержания:

```
# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/jammy64"
  config.vm.box_check_update = false

  nodes = {
    "ansible-controller" => {
      ip:     "192.168.57.10",
      memory: 2048,
      cpus:   2
    },
    "clickhouse" => {
      ip:     "192.168.57.11",
      memory: 2048,
      cpus:   2
    },
    "vector" => {
      ip:     "192.168.57.12",
      memory: 1024,
      cpus:   1
    },
    "lighthouse" => {
      ip:     "192.168.57.13",
      memory: 1024,
      cpus:   1
    }
  }

  public_key = File.read(File.join(__dir__, "ansible_key.pub")).strip

  nodes.each do |name, node_config|
    config.vm.define name do |node|
      node.vm.hostname = name

      node.vm.network "private_network",
                      ip: node_config[:ip]

      node.vm.provider "virtualbox" do |vb|
        vb.name = "ansible-roles-#{name}"
        vb.memory = node_config[:memory]
        vb.cpus = node_config[:cpus]
      end

      node.vm.provision "shell", inline: <<-SHELL
        set -e

        apt-get update
        apt-get install -y python3 python3-apt curl

        install -d -m 700 -o vagrant -g vagrant /home/vagrant/.ssh

        if ! grep -qxF '#{public_key}' /home/vagrant/.ssh/authorized_keys; then
          echo '#{public_key}' >> /home/vagrant/.ssh/authorized_keys
        fi

        chown vagrant:vagrant /home/vagrant/.ssh/authorized_keys
        chmod 600 /home/vagrant/.ssh/authorized_keys
      SHELL

      if name == "ansible-controller"
        node.vm.provision "file",
                          source: "ansible_key",
                          destination: "/tmp/ansible_key"

        node.vm.provision "shell", inline: <<-SHELL
          set -e

          apt-get install -y \
            ansible \
            git \
            python3-pip \
            python3-venv \
            sshpass

          install -m 600 \
            -o vagrant \
            -g vagrant \
            /tmp/ansible_key \
            /home/vagrant/.ssh/ansible_key

          rm -f /tmp/ansible_key
        SHELL
      end
    end
  end
end
```

Данная конфигурация создаст нам четыре виртуальные машины:

| Машина               | IP              | Назначение         |
| -------------------- | --------------- | ------------------ |
| `ansible-controller` | `192.168.57.10` | запуск Ansible     |
| `clickhouse`         | `192.168.57.11` | ClickHouse         |
| `vector`             | `192.168.57.12` | Vector             |
| `lighthouse`         | `192.168.57.13` | LightHouse и nginx |

Выполним проверку синтаксиса Vagrant файла:

```
vagrant validate
```

![img](img/image3.png)

Создадим ssh-ключ:

```
ssh-keygen -t ed25519 -f .\ansible_key -N '""'
```

![img](img/image1.png)

![img](img/image2.png)

Запустим виртуальную машину ```ansible-controller```:

```
vagrant up ansible-controller
```

![img](img/image4.png)

Подключимся к созданной виртуальной машине и проверим установленные пакеты, необходимые для выполнения домашней работы:

```
vagrant ssh ansible-controller
ansible --version
git --version
python3 --version
```
![img](img/image5.png)

Запустим виртуальные машины ```clickhouse```, ```vector``` и ```lighthouse```:

```
vagrant up clickhouse
vagrant up vector
vagrant up lighthouse
```

Проверим, что все виртуальные машины запущены:

```
vagrant status
```

![img](img/image6.png)

Подключимся к виртуальной машине ```ansible-controller``` и проверим подключение с неё к остальным виртуальным машинам:

```
vagrant ssh ansible-controller

ssh -i ~/.ssh/ansible_key vagrant@192.168.57.11 hostname
ssh -i ~/.ssh/ansible_key vagrant@192.168.57.12 hostname
ssh -i ~/.ssh/ansible_key vagrant@192.168.57.13 hostname
```

![img](img/image7.png)

Создадим inventory и проверяем Ansible.
На виртуальной машине ```ansible-controller``` выполним:

```
mkdir -p ~/ansible-roles-homework/inventory
cd ~/ansible-roles-homework
```

Создадим inventory:

```
cat > inventory/prod.yml <<'EOF'
---
clickhouse:
  hosts:
    clickhouse-node:
      ansible_host: 192.168.57.11

vector:
  hosts:
    vector-node:
      ansible_host: 192.168.57.12

lighthouse:
  hosts:
    lighthouse-node:
      ansible_host: 192.168.57.13

all:
  vars:
    ansible_user: vagrant
    ansible_ssh_private_key_file: ~/.ssh/ansible_key
    ansible_python_interpreter: /usr/bin/python3
EOF
```

Проверим, как Ansible видит inventory:

```
ansible-inventory -i inventory/prod.yml --graph
```

![img](img/image8.png)

Выполним тест связи:

```
ansible all -i inventory/prod.yml -m ping
```

![img](img/image9.png)

Проверим, что become тоже работает:

```
ansible all -i inventory/prod.yml -b -m command -a "whoami"
```

![img](img/image10.png)

Создадим файл ```requirements.yml``` следующего содержания:

```
cat > requirements.yml <<'EOF'
---
- src: https://github.com/AlexeySetevoi/ansible-clickhouse.git
  scm: git
  version: "1.13"
  name: clickhouse
EOF
```

Создадим какталог для ролей:

```
mkdir -p roles
```

Установим роль:

```
ansible-galaxy role install -r requirements.yml -p roles
```

![img](img/image11.png)

Проверим результат:

```
ls -la roles
ls -la roles/clickhouse
```

Видим, что появились необходимые каталоги:

![img](img/image12.png)

Создадим файл ```site.yml``` следующего содержания:

```
cat > site.yml <<'EOF'
---
- name: Install ClickHouse
  hosts: clickhouse
  become: true
  roles:
    - clickhouse
EOF
```

Проверим синтаксис:

```
ansible-playbook -i inventory/prod.yml site.yml --syntax-check
```

![img](img/image13.png)

Создадим ```group_vars```.
Создадим директорию:

```
mkdir -p group_vars/clickhouse
```

Создадим файл ```vars.yml``` следующего содержания:

```
cat > group_vars/clickhouse/vars.yml <<'EOF'
---
clickhouse_version: "latest"

clickhouse_listen_host_custom:
  - "192.168.57.11"

clickhouse_networks_default:
  - "::1"
  - "127.0.0.1"
  - "192.168.57.0/24"
EOF
```

Проверим загрузку переменных:

```
ansible-inventory -i inventory/prod.yml --host clickhouse-node
```

![img](img/image14.png)

Запустим роль:

```
ansible-playbook -i inventory/prod.yml site.yml
```

![img](img/image15.png)

![img](img/image16.png)

Проверим, что приложение запустилось:

```
ansible clickhouse -i inventory/prod.yml -b -m command -a "systemctl is-active clickhouse-server"
```

![img](img/image17.png)

Проверим версию приложения:

```
ansible clickhouse -i inventory/prod.yml -b -m command -a "clickhouse-client --query 'SELECT version()'"
```

![img](img/image18.png)

Приступим к созданию собственной роли Vector.

Сгенерируем шаблон роли:

```
ansible-galaxy role init roles/vector
```

![img](img/image19.png)

Проверим структуру:

```
find roles/vector -maxdepth 2 -type f | sort
```

Заполним файл ```roles/vector/defaults/main.yml``` следующим содержимым:

```
cat > roles/vector/defaults/main.yml <<'EOF'
---
vector_version: "0.48.0"
vector_arch: "amd64"
vector_config_dir: "/etc/vector"
vector_config_file: "/etc/vector/vector.yaml"
EOF
```

Заполним файл ```roles/vector/tasks/main.yml``` следующим содержимым(это задачи установки):

```
cat > roles/vector/tasks/main.yml <<'EOF'
---
- name: Download Vector package
  ansible.builtin.get_url:
    url: "https://packages.timber.io/vector/{{ vector_version }}/vector_{{ vector_version }}-1_{{ vector_arch }}.deb"
    dest: "/tmp/vector_{{ vector_version }}-1_{{ vector_arch }}.deb"
    mode: "0644"

- name: Install Vector package
  ansible.builtin.apt:
    deb: "/tmp/vector_{{ vector_version }}-1_{{ vector_arch }}.deb"
    state: present

- name: Create Vector config directory
  ansible.builtin.file:
    path: "{{ vector_config_dir }}"
    state: directory
    owner: root
    group: root
    mode: "0755"

- name: Deploy Vector config
  ansible.builtin.template:
    src: vector.yaml.j2
    dest: "{{ vector_config_file }}"
    owner: root
    group: root
    mode: "0644"
  notify: Restart Vector

- name: Enable and start Vector
  ansible.builtin.service:
    name: vector
    enabled: true
    state: started
EOF
```

Заполним файл ```roles/vector/handlers/main.yml``` следующим содержимым(создадим handler):

```
cat > roles/vector/handlers/main.yml <<'EOF'
---
- name: Restart Vector
  ansible.builtin.service:
    name: vector
    state: restarted
EOF
```

Заполним файл ```roles/vector/templates/vector.yaml.j2``` следующим содержимым(создадим шаблон конфигурации):

```
cat > roles/vector/templates/vector.yaml.j2 <<'EOF'
sources:
  demo_logs:
    type: demo_logs
    format: syslog
    interval: 1

sinks:
  clickhouse:
    type: clickhouse
    inputs:
      - demo_logs
    endpoint: http://192.168.57.11:8123
    database: default
    table: logs
    skip_unknown_fields: true
EOF
```

Добавим Vector в ```site.yml```:

```
cat > site.yml <<'EOF'
---
- name: Install ClickHouse
  hosts: clickhouse
  become: true
  roles:
    - clickhouse

- name: Install Vector
  hosts: vector
  become: true
  roles:
    - vector
EOF
```

Проверим синтаксис:

```
ansible-playbook -i inventory/prod.yml site.yml --syntax-check
```

Подготовим в ClickHouse таблицу, куда Vector будет отправлять тестовые события.
Для этого в файл ```site.yml``` добавим соответствующую задачу:

```
cat > site.yml <<'EOF'
---
- name: Install and configure ClickHouse
  hosts: clickhouse
  become: true

  roles:
    - clickhouse

  tasks:
    - name: Create logs table
      ansible.builtin.command:
        argv:
          - clickhouse-client
          - --query
          - >-
            CREATE TABLE IF NOT EXISTS default.logs
            (
              timestamp String,
              message String
            )
            ENGINE = MergeTree
            ORDER BY tuple()
      changed_when: false

- name: Install and configure Vector
  hosts: vector
  become: true

  roles:
    - vector
EOF
```

Запустим playbook:

```
ansible-playbook -i inventory/prod.yml site.yml
```

После окончания процесса проверим сервис Vector:

```
ansible vector -i inventory/prod.yml -b -m command -a "systemctl is-active vector"
```

![img](img/image21.png)

Проверим конфигурацию Vector:

```
ansible vector -i inventory/prod.yml -b -m command -a "vector validate /etc/vector/vector.yaml"
```

![img](img/image22.png)

Проверим таблицу ClickHouse.
Убедимся, что таблица существует:

```
ansible clickhouse -i inventory/prod.yml -b -m command -a "clickhouse-client --query 'SHOW TABLES FROM default'"
```

![img](img/image23.png)

Проверим количество записей в таблице:

```
ansible clickhouse -i inventory/prod.yml -b -m command -a "clickhouse-client --query 'SELECT count() FROM default.logs'"
```

![img](img/image24.png)

Посмотрим несколько строк записей из таблицы:

```
ansible vector -i inventory/prod.yml -b -m command -a "journalctl -u vector -n 50 --no-pager"
```

![img](img/image25.png)

Приступим к созданию собственной роли Lighthouse.

Сгенерируем шаблон роли:

```
ansible-galaxy role init roles/lighthouse
```

![img](img/image26.png)

Проверим структуру:

```
find roles/lighthouse -maxdepth 2 -type f | sort
```

![img](img/image27.png)

Заполним файл ```roles/lighthouse/defaults/main.yml``` следующим содержимым:

```
cat > roles/lighthouse/defaults/main.yml <<'EOF'
---
lighthouse_repo: "https://github.com/VKCOM/lighthouse.git"
lighthouse_branch: "master"
lighthouse_dir: "/var/www/lighthouse"

lighthouse_nginx_port: 80
lighthouse_server_name: "_"
EOF
```

Заполним файл ```roles/lighthouse/tasks/main.yml``` следующим содержимым(это задачи установки):

```
cat > roles/lighthouse/tasks/main.yml <<'EOF'
---
- name: Install LightHouse dependencies
  ansible.builtin.apt:
    name:
      - git
      - nginx
    state: present
    update_cache: true
    cache_valid_time: 3600

- name: Clone LightHouse repository
  ansible.builtin.git:
    repo: "{{ lighthouse_repo }}"
    dest: "{{ lighthouse_dir }}"
    version: "{{ lighthouse_branch }}"
    force: true
  notify: Restart nginx

- name: Deploy nginx configuration for LightHouse
  ansible.builtin.template:
    src: lighthouse.conf.j2
    dest: /etc/nginx/sites-available/lighthouse.conf
    owner: root
    group: root
    mode: "0644"
  notify: Restart nginx

- name: Enable LightHouse nginx site
  ansible.builtin.file:
    src: /etc/nginx/sites-available/lighthouse.conf
    dest: /etc/nginx/sites-enabled/lighthouse.conf
    state: link
  notify: Restart nginx

- name: Disable default nginx site
  ansible.builtin.file:
    path: /etc/nginx/sites-enabled/default
    state: absent
  notify: Restart nginx

- name: Validate nginx configuration
  ansible.builtin.command:
    cmd: nginx -t
  changed_when: false

- name: Enable and start nginx
  ansible.builtin.service:
    name: nginx
    enabled: true
    state: started
EOF
```

Заполним файл ```roles/lighthouse/handlers/main.yml``` следующим содержимым(создадим handler):

```
cat > roles/lighthouse/handlers/main.yml <<'EOF'
---
- name: Restart nginx
  ansible.builtin.service:
    name: nginx
    state: restarted
EOF
```

Создадим каталог шаблонов:

```
mkdir -p roles/lighthouse/templates
```

Создадим шаблон для nginx:

```
cat > roles/lighthouse/templates/lighthouse.conf.j2 <<'EOF'
server {
    listen {{ lighthouse_nginx_port }};
    listen [::]:{{ lighthouse_nginx_port }};

    server_name {{ lighthouse_server_name }};

    root {{ lighthouse_dir }};
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /clickhouse/ {
        proxy_pass http://192.168.57.11:8123/;

        proxy_http_version 1.1;
        proxy_set_header Host 192.168.57.11;
        proxy_set_header Connection "";

        proxy_connect_timeout 10s;
        proxy_read_timeout 60s;
        proxy_send_timeout 60s;
    }
}
EOF
```

Подключим роль в ```site.yml```:

```
cat > site.yml <<'EOF'
---
- name: Install and configure ClickHouse
  hosts: clickhouse
  become: true

  roles:
    - clickhouse

  tasks:
    - name: Create logs table
      ansible.builtin.command:
        argv:
          - clickhouse-client
          - --query
          - >-
            CREATE TABLE IF NOT EXISTS default.logs
            (
              timestamp String,
              message String
            )
            ENGINE = MergeTree
            ORDER BY tuple()
      changed_when: false

- name: Install and configure Vector
  hosts: vector
  become: true

  roles:
    - vector

- name: Install and configure LightHouse
  hosts: lighthouse
  become: true

  roles:
    - lighthouse
EOF
```

Проверим синтаксис и запустим playbook:

```
ansible-playbook -i inventory/prod.yml site.yml --syntax-check
ansible-playbook -i inventory/prod.yml site.yml
```

Проверим nginx:

```
ansible lighthouse -i inventory/prod.yml -b -m command -a "systemctl is-active nginx"
```

![img](img/image28.png)

Проверим конфигурацию nginx:

```
ansible lighthouse -i inventory/prod.yml -b -m command -a "nginx -t"
```

![img](img/image29.png)

Проверим наличие файлов в LightHouse:

```
ansible lighthouse -i inventory/prod.yml -b -m command -a "ls -la /var/www/lighthouse"
```

![img](img/image30.png)

Проверим доступность через браузер:

![img](img/image31.png)

Приступим к проверке идемпотентности.
Запустим playbook ещё раз:

```
ansible-playbook -i inventory/prod.yml site.yml
```

GПосле окончания процесса видим, что никаких изменений не произошло:

![img](img/image32.png)

Экспортируем проект в общую папку Vagrant:

```
cp -a ~/ansible-roles-homework /vagrant/ansible-roles-homework-export
```

Проверим, что всё скопировалось:

```
find /vagrant/ansible-roles-homework-export -maxdepth 3 -type f | sort
```

![img](img/image33.png)

Создадим на GitHub два новых репозитория: ```vector-role``` и ```lighthouse-role```:

![img](img/image34.png)

![img](img/image35.png)

Создадим директорию для репозиториев ролей:

```
mkdir D:\Homework\ansible-roles
```

Скопируем роли в эту директорию:

```
Copy-Item `
  .\ansible-roles-homework-export\roles\vector `
  D:\Homework\ansible-roles\vector-role `
  -Recurse

Copy-Item `
  .\ansible-roles-homework-export\roles\lighthouse `
  D:\Homework\ansible-roles\lighthouse-role `
  -Recurse
```

Опубликуем роль Vektor:

```
cd D:\Homework\ansible-roles\vector-role

git init
git branch -M main
git add .
git commit -m "Add Vector Ansible role"
```

![img](img/image36.png)

Подключим удалённый репозиторий:

```
git remote add origin https://github.com/myachmen/vector-role.git
```

Отправим код в удалённый репозиторий:

```
git push -u origin main
```

![img](img/image37.png)

Создадим тег версии:

```
git tag 1.0.0
git push origin 1.0.0
```

![img](img/image38.png)

Аналогичным сапособом опубликуем роль LightHouse:

```
cd D:\Homework\ansible-roles\lighthouse-role

git init
git branch -M main
git add .
git commit -m "Add LightHouse Ansible role"

git remote add origin https://github.com/myachmen/lighthouse-role.git
git push -u origin main

git tag 1.0.0
git push origin 1.0.0
```

![img](img/image39.png)

Обновим файл ```requirements.yml```.

```
cat > requirements.yml <<'EOF'
---
- src: https://github.com/AlexeySetevoi/ansible-clickhouse.git
  scm: git
  version: "1.13"
  name: clickhouse

- src: https://github.com/myachmen/vector-role.git
  scm: git
  version: "1.0.0"
  name: vector

- src: https://github.com/myachmen/lighthouse-role.git
  scm: git
  version: "1.0.0"
  name: lighthouse
EOF
```

Скачаем роли в новый каталог:

```
mkdir roles-github

ansible-galaxy role install -r requirements.yml -p roles-github
```

![img](img/image40.png)

Переименуем локальные роли:

```
mv roles roles-local-backup
```

Запустим playbook:

```
ANSIBLE_ROLES_PATH=/home/vagrant/roles-github ansible-playbook -i inventory/prod.yml site.yml
```

В процессе выполнения мы видим, что используются роли из GitHub:

![img](img/image42.png)

После окончания процесса мы видим, что никаких изменений не произошло, хотя роли скачивались из репозиториев на GitHub:

![img](img/image41.png)

Перенесём основной проект в ветку ```hw-ansible-roles```.

Создадим директорию и скопируем туда необходимые файлы:

```
mkdir -p /vagrant/ansible-roles-homework-final

cp -a inventory /vagrant/ansible-roles-homework-final/
cp -a group_vars /vagrant/ansible-roles-homework-final/
cp requirements.yml /vagrant/ansible-roles-homework-final/
cp site.yml /vagrant/ansible-roles-homework-final/
```

Перенесём файлы в основной репозиторий на GitHub:

```
mkdir ansible-roles-homework

Copy-Item `
  D:\Program\DevOps\Vagrant\Vagrant-Project\ansible-roles-lab\ansible-roles-homework-final\* `
  .\ansible-roles-homework\ `
  -Recurse -Force
```

![img](img/image43.png)

Создадим файл ```.gitignore``` следующего содержания:

```
@'
roles/
*.retry
.vagrant/
ansible_key
ansible_key.pub
'@ | Set-Content .\ansible-roles-homework\.gitignore
```

Создадим коммит и отправим файлы в удалённый репозиторий:

```
git add ansible-roles-homework
git status
git commit -m "Complete Ansible roles homework"
git push
```

![img](img/image44.png)
