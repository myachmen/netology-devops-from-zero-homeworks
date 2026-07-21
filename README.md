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
