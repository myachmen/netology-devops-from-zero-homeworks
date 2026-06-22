# Домашнее задание по теме "Управляющие конструкции в коде Terraform" Ячмень Марк Викторович

## Задание 1

1. Изучите проект.
2. Инициализируйте проект, выполните код.

Приложите скриншот входящих правил «Группы безопасности» в ЛК Yandex Cloud .

## Решение 1

Для выполнения задания выполним следующие действия.

Скопируем код проекта в наш репозиторий:

```
git clone --depth 1 https://github.com/netology-code/ter-homeworks.git temp-ter-homeworks
Copy-Item -Recurse .\temp-ter-homeworks\03\src\* .\terraform\
Remove-Item -Recurse -Force .\temp-ter-homeworks
cd .\terraform
dir
```

![img](img/image1.png)


После изучения файлов проекта подготовим файл с личными параметрами:

```
Copy-Item .\personal.auto.tfvars_example .\personal.auto.tfvars
```

Для заполнения файла выведем в консоль параметры из Yandex Cloud:

```
yc config list
```

![img](img/image2.png)

Создадим новый IAM-токен:

```
yc iam create-toke
```

![img](img/image3.png)

Проверим, что файл ```personal.auto.tfvars``` не попадает в репозиторий на Github:

```
git status --ignored
```

![img](img/image4.png)

Выполним инициализацию и проверку конфигурации:

```
terraform init
terraform validate
terraform plan
```

![img](img/image5.png)

![img](img/image6.png)

![img](img/image7.png)

Применим конфигурацию:

```
terraform apply
```

![img](img/image8.png)

После применения конфигурации мы видим, что в консоли Yanbndex Cloud появилась новая сеть ```develop```:

![img](img/image9.png)

![img](img/image10.png)

![img](img/image11.png)



## Задание 2

1. Создайте файл count-vm.tf. Опишите в нём создание двух одинаковых ВМ web-1 и web-2 (не web-0 и web-1) с минимальными параметрами, используя мета-аргумент count loop. Назначьте ВМ созданную в первом задании группу безопасности.(как это сделать узнайте в документации провайдера yandex/compute_instance )
2. Создайте файл for_each-vm.tf. Опишите в нём создание двух ВМ для баз данных с именами "main" и "replica" разных по cpu/ram/disk_volume , используя мета-аргумент for_each loop. Используйте для обеих ВМ одну общую переменную типа:

```
variable "each_vm" {
  type = list(object({  vm_name=string, cpu=number, ram=number, disk_volume=number }))
}
```

При желании внесите в переменную все возможные параметры. 
3. ВМ, описанные в файле count-vm.tf, должны создаваться после ВМ, описанных в файле for_each-vm.tf. 
4. Используйте функцию file в local-переменной для считывания ключа ~/.ssh/id_rsa.pub и его последующего использования в блоке metadata, взятому из ДЗ 2. 
5. Инициализируйте проект, выполните код.


## Решение 2

Для выполнения задания выполним следующие действия.

Создадим файл ```locals.tf``` следующего содержания:

```
locals {
  ssh_key = file("~/.ssh/id_ed25519.pub")
}
```

Создадим файл ```vms-variables.tf``` переменных для ВМ следующего содержания:

```
variable "each_vm" {
  type = list(object({
    vm_name     = string
    cpu         = number
    ram         = number
    disk_volume = number
  }))

  default = [
    {
      vm_name     = "main"
      cpu         = 2
      ram         = 2
      disk_volume = 10
    },
    {
      vm_name     = "replica"
      cpu         = 2
      ram         = 1
      disk_volume = 5
    }
  ]
}
```

Выполним проверку конфигурации:

```
terraform fmt
terraform validate
```

![img](img/image12.png)

Создадим файл ```data.tf``` следующего содержания:

```
data "yandex_compute_image" "ubuntu" {
  family = "ubuntu-2204-lts"
}
```


Создаим файл ```for_each-vm.tf``` для двух ВМ через ```for_each``` следующего содержания:

```
resource "yandex_compute_instance" "db" {
  for_each = {
    for vm in var.each_vm : vm.vm_name => vm
  }

  name        = each.value.vm_name
  platform_id = "standard-v1"
  zone        = var.default_zone

  resources {
    cores         = each.value.cpu
    memory        = each.value.ram
    core_fraction = 20
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size     = each.value.disk_volume
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.develop.id
    nat                = true
    security_group_ids = [yandex_vpc_security_group.example.id]
  }

  scheduling_policy {
    preemptible = true
  }

  metadata = {
    serial-port-enable = 1
    ssh-keys           = "ubuntu:${local.ssh_key}"
  }
}
```

Снова выполним проверку конфигурации и формирование плана:

```
terraform fmt
terraform validate
terraform plan
```

![img](img/image13.png)

![img](img/image14.png)

![img](img/image15.png)

![img](img/image16.png)


Применим конфигурацию:

```
terraform apply
```

![img](img/image17.png)


После применения конфигурации в консоли Yandex Cloud видим, что появилось две новые виртуальные машины:

![img](img/image18.png)


Теперь создадим файл ```count-vm.tf``` следующего содержания:

```
resource "yandex_compute_instance" "web" {
  count = 2

  name        = "web-${count.index + 1}"
  platform_id = "standard-v1"
  zone        = var.default_zone

  depends_on = [
    yandex_compute_instance.db
  ]

  resources {
    cores         = 2
    memory        = 1
    core_fraction = 20
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size     = 5
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.develop.id
    nat                = true
    security_group_ids = [yandex_vpc_security_group.example.id]
  }

  scheduling_policy {
    preemptible = true
  }

  metadata = {
    serial-port-enable = 1
    ssh-keys           = "ubuntu:${local.ssh_key}"
  }
}
```

Снова выполним проверку конфигурации и формирование плана:

```
terraform fmt
terraform validate
terraform plan
```

![img](img/image19.png)

![img](img/image20.png)

![img](img/image21.png)

И вывода видим, что Terraform собирается создать два новых объекта.

Применим конфигурацию:

```
terraform apply
```

![img](img/image22.png)

После применения конфигурации в консоли Yandex Cloud видим, что появилось ещё две виртуальные машины:

![img](img/image23.png)



## Задание 3

1. Создайте 3 одинаковых виртуальных диска размером 1 Гб с помощью ресурса yandex_compute_disk и мета-аргумента count в файле disk_vm.tf .
2. Создайте в том же файле одиночную(использовать count или for_each запрещено из-за задания №4) ВМ c именем "storage" . Используйте блок dynamic secondary_disk{..} и мета-аргумент for_each для подключения созданных вами дополнительных дисков.

## Решение 3

Для выполнения задания выполним следующие действия.

Создадим файл ```disk_vm.tf``` следующего содержания:

```
resource "yandex_compute_disk" "storage" {
  count = 3

  name = "storage-disk-${count.index + 1}"
  type = "network-hdd"
  zone = var.default_zone
  size = 1
}

resource "yandex_compute_instance" "storage" {
  name        = "storage"
  platform_id = "standard-v1"
  zone        = var.default_zone

  resources {
    cores         = 2
    memory        = 1
    core_fraction = 20
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.id
      size     = 5
    }
  }

  dynamic "secondary_disk" {
    for_each = yandex_compute_disk.storage

    content {
      disk_id = secondary_disk.value.id
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.develop.id
    nat                = true
    security_group_ids = [yandex_vpc_security_group.example.id]
  }

  scheduling_policy {
    preemptible = true
  }

  metadata = {
    serial-port-enable = 1
    ssh-keys           = "ubuntu:${local.ssh_key}"
  }
}
```

Выполним проверку конфигурации и формирование плана:

```
terraform fmt
terraform validate
terraform plan
```

![img](img/image24.png)

![img](img/image25.png)

![img](img/image26.png)

![img](img/image27.png)

Из вывода видим, что в этот раз Terraform собирается создать четыре новых объекта.

Применим конфигурацию:

```
terraform apply
```

![img](img/image28.png)

После применения конфигурации в консоли Yandex Cloud видим, что появилось ещё одна виртуальная машина и три новых диска:

![img](img/image29.png)

![img](img/image30.png)



## Задание 4

1. В файле ansible.tf создайте inventory-файл для ansible.
Используйте функцию tepmplatefile и файл-шаблон для создания ansible inventory-файла из лекции.
Готовый код возьмите из демонстрации к лекции [**demonstration2**](https://github.com/netology-code/ter-homeworks/tree/main/03/demo).
Передайте в него в качестве переменных группы виртуальных машин из задания 2.1, 2.2 и 3.2, т. е. 5 ВМ.
2. Инвентарь должен содержать 3 группы и быть динамическим, т. е. обработать как группу из 2-х ВМ, так и 999 ВМ.
3. Добавьте в инвентарь переменную  [**fqdn**](https://cloud.yandex.ru/docs/compute/concepts/network#hostname).
``` 
[webservers]
web-1 ansible_host=<внешний ip-адрес> fqdn=<полное доменное имя виртуальной машины>
web-2 ansible_host=<внешний ip-адрес> fqdn=<полное доменное имя виртуальной машины>

[databases]
main ansible_host=<внешний ip-адрес> fqdn=<полное доменное имя виртуальной машины>
replica ansible_host<внешний ip-адрес> fqdn=<полное доменное имя виртуальной машины>

[storage]
storage ansible_host=<внешний ip-адрес> fqdn=<полное доменное имя виртуальной машины>
```
Пример fqdn: ```web1.ru-central1.internal```(в случае указания переменной hostname(не путать с переменной name)); ```fhm8k1oojmm5lie8i22a.auto.internal```(в случае отсутвия перменной hostname - автоматическая генерация имени,  зона изменяется на auto). нужную вам переменную найдите в документации провайдера или terraform console.
4. Выполните код. Приложите скриншот получившегося файла. 

Для общего зачёта создайте в вашем GitHub-репозитории новую ветку terraform-03. Закоммитьте в эту ветку свой финальный код проекта, пришлите ссылку на коммит.   
**Удалите все созданные ресурсы**.

## Решение 4

Для выполнения задания выполним следующие действия.

Склонируем демонстрационный репозиторий себе на компьютер во временную папку:

```
git clone --depth 1 https://github.com/netology-code/ter-homeworks.git temp-ter-homeworks
```

Скопируем в свой основной репозиторий файл ```hosts.tftpl```:

```
Copy-Item .\temp-ter-homeworks\03\demo\hosts.tftpl .\
```

Добавим в файл ```hosts.tftpl``` следующий код:

```
[databases]

%{~ for i in databases ~}

${i["name"]}   ansible_host=${i["network_interface"][0]["nat_ip_address"]} fqdn=${i["fqdn"]}
%{~ endfor ~}

[storage]

%{~ for i in storage ~}

${i["name"]}   ansible_host=${i["network_interface"][0]["nat_ip_address"]} fqdn=${i["fqdn"]}
%{~ endfor ~}
```

В этом же файле исправим строку:

```
${i["name"]}   ansible_host=${i["network_interface"][0]["nat_ip_address"]}
```

на

```
${i["name"]}   ansible_host=${i["network_interface"][0]["nat_ip_address"]} fqdn=${i["fqdn"]}
```

чтобы шаблон стал одинаковым для всех групп.

Создадим файл ```ansible.tf``` следующего содержания:

```
resource "local_file" "hosts_cfg" {
  content = templatefile("${path.module}/hosts.tftpl", {
    webservers = yandex_compute_instance.web
    databases  = values(yandex_compute_instance.db)
    storage    = [yandex_compute_instance.storage]
  })

  filename = "${path.module}/hosts.cfg"
}
```

Выполним проверку конфигурации и формирование плана:

```
terraform fmt
terraform validate
terraform plan
```

![img](img/image31.png)

Получим несколько ошибок.
Данные ошибки связанны с отсутствием провайдера ```hashicorp/local```, который требуется для нового ресурса ```local_file```, но Terraform его еще не скачал.
Для этого выполним инициализацию:

```
terraform init
```

Провайдер ```hashicorp/local``` был успешно скачан и установлен:

![img](img/image32.png)

Снова выполним:

```
terraform validate
terraform plan
```

![img](img/image33.png)

![img](img/image34.png)

Применим конфигурацию:

```
terraform apply
```

![img](img/image35.png)


Выведем в консоль содержание файла ```hosts.cfg```:

```
Get-Content .\hosts.cfg
```

![img](img/image36.png)

С помощью функции ```templatefile()``` был реализован динамический шаблон inventory для Ansible.
В шаблон передаются списки виртуальных машин, созданных Terraform. При выполнении ```terraform apply``` автоматически формируется файл ```hosts.cfg```, содержащий три группы (```webservers```, ```databases```, ```storage```) с внешними IP-адресами виртуальных машин и переменной fqdn.

Использование шаблона позволяет автоматически генерировать inventory независимо от количества виртуальных машин в каждой группе без ручного редактирования файла.