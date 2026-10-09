# Домашнее задание к занятию «Установка Kubernetes»

## Задание 1. Установить кластер k8s с 1 master node

### Решение 1

Создадим отдельный Host-Only адаптер для Kubernetes-кластера с адресом `192.168.57.1/24`:

```
VBoxManage hostonlyif create
```

![img](img/image1.png)

Проверим, что в конфигурации появился второй адаптер:

```
VBoxManage list hostonlyifs
```

![img](img/image2.png)

Настроим IP адрес для нового адаптера:

```
VBoxManage hostonlyif ipconfig "VirtualBox Host-Only Ethernet Adapter #2" --ip 192.168.57.1 --netmask 255.255.255.0
```

Проверим результат:

```
VBoxManage list hostonlyifs
```

![img](img/image3.png)

Создадим каталог проекта:

```
New-Item -ItemType Directory -Path "k8s-install" -Force
```

![img](img/image4.png)

В каталоге создадим `Vagrantfile` со следующим содержимым:

```

Vagrant.configure("2") do |config|
  config.vm.box = "bento/ubuntu-22.04"
  config.vm.box_version = "202510.26.0"

  config.vm.synced_folder ".", "/vagrant", disabled: true

  nodes = [
    { name: "k8s-master",   ip: "192.168.57.10", memory: 4096 },
    { name: "k8s-worker-1", ip: "192.168.57.11", memory: 2048 },
    { name: "k8s-worker-2", ip: "192.168.57.12", memory: 2048 },
    { name: "k8s-worker-3", ip: "192.168.57.13", memory: 2048 },
    { name: "k8s-worker-4", ip: "192.168.57.14", memory: 2048 }
  ]

  nodes.each do |node|
    config.vm.define node[:name] do |machine|
      machine.vm.hostname = node[:name]

      machine.vm.network "private_network",
        ip: node[:ip],
        virtualbox__intnet: false,
        name: "VirtualBox Host-Only Ethernet Adapter #2"

      machine.vm.provider "virtualbox" do |vb|
        vb.name = node[:name]
        vb.memory = node[:memory]
        vb.cpus = 2
        vb.customize [
          "modifyvm", :id,
          "--audio-enabled", "off"
        ]
      end
    end
  end
end
```

Проверим Vagrantfile и запустим создание одной виртуальной машины, для того чтобы проверить параметры:

```
vagrant validate
vagrant up k8s-master --provider=virtualbox
```

![img](img/image5.png)

Проверим IP адрес внутри созданной виртуальной машины:

```
vagrant ssh k8s-master -c "hostname; ip -4 -br addr"
```

![img](img/image6.png)





















## Ссылки на файлы

_Будут добавлены по мере выполнения задания._