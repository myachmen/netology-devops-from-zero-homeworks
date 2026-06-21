# Домашнее задание по теме "Основы Terraform. Yandex Cloud" Ячмень Марк Викторович

## Задание 1

В качестве ответа всегда полностью прикладывайте ваш terraform-код в git. Убедитесь что ваша версия Terraform ~>1.12.0

1. Изучите проект. В файле variables.tf объявлены переменные для Yandex provider.
2. Создайте сервисный аккаунт и ключ. service_account_key_file.
3. Сгенерируйте новый или используйте свой текущий ssh-ключ. Запишите его открытую(public) часть в переменную vms_ssh_public_root_key.
4. Инициализируйте проект, выполните код. Исправьте намеренно допущенные синтаксические ошибки. Ищите внимательно, посимвольно. Ответьте, в чём заключается их суть.
5. Подключитесь к консоли ВМ через ssh и выполните команду  curl ifconfig.me. Примечание: К OS ubuntu "out of a box, те из коробки" необходимо подключаться под пользователем ubuntu: "ssh ubuntu@vm_ip_address". Предварительно убедитесь, что ваш ключ добавлен в ssh-агент: eval $(ssh-agent) && ssh-add Вы познакомитесь с тем как при создании ВМ создать своего пользователя в блоке metadata в следующей лекции.;
6. Ответьте, как в процессе обучения могут пригодиться параметры preemptible = true и core_fraction=5 в параметрах ВМ.
В качестве решения приложите:

 - скриншот ЛК Yandex Cloud с созданной ВМ, где видно внешний ip-адрес;
 - скриншот консоли, curl должен отобразить тот же внешний ip-адрес;
 - ответы на вопросы.

## Решение 1

Для выполнения задания выполним следующие действия.

Скопируем исходники задания из ```ter-homeworks/02/src``` в локальную папку:

```
cd D:\Homework\netology-devops-from-zero-homeworks

git clone https://github.com/netology-code/ter-homeworks.git D:\Homework\ter-homeworks-temp

Copy-Item -Path D:\Homework\ter-homeworks-temp\02\src\* -Destination D:\Homework\netology-devops-from-zero-homeworks\terraform -Recurse -Force
```
![img](img/image1.png)

Создадим сервисный аккаунт в Yandex Cloud:

```
yc iam service-account create --name terraform-sa
```

![img](img/image2.png)

Получим ```ID``` созданного сервисного аккаунта:

```
yc iam service-account get terraform-sa
```

![img](img/image3.png)

Выдадитм права сервисному аккаунту:

```
yc resource-manager folder add-access-binding b1gi86cp8m9talsp0tsr --role editor --subject serviceAccount:ajeutaso4967kahusiro
```

![img](img/image4.png)

Создадим JSON-ключ:

```
yc iam key create --service-account-name terraform-sa --output authorized_key.json
```

![img](img/image5.png)

Внесём исправления в файл ```providers.tf```.
Заменим строку:

```
service_account_key_file = file("~/authorized_key.json")
```

на

```
service_account_key_file = file("${path.module}/authorized_key.json")
```

![img](img/image6.png)

Добавим ключ в файл ```.gitignore```.  Добавим в файл строку:

```
authorized_key.json
```

![img](img/image7.png)

Посмотрим публичный  ключ:

```
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub
```
![img](img/image8.png)

Создадим файл ```personal.auto.tfvars``` со следующим содержимым:

```
cloud_id  = "b1gctutkrnslve8437ea"
folder_id = "b1gi86cp8m9talsp0tsr"

vms_ssh_root_key = "содержимое ключа"
```

![img](img/image9.png)

Проверим Terraform:

```
terraform init
terraform validate
```

![img](img/image10.png)


Проверим план ифраструктуры в Terraform:

```
terraform plan
```
![img](img/image11.png)

![img](img/image12.png)

Запустим проект:

```
terraform apply
```

В процессе запуска получили ошибку: 

![img](img/image13.png)


Ошибка означает, что в регионе, выбранном в Yandex Cloud платформа ```standard-v4``` недоступна.
В файле ```main.tf``` заменим строку:

```
platform_id = "standart-v4"
```

на

```
platform_id = "standard-v2"
```

Запустим проект и снова получим ошибку:

![img](img/image14.png)

Эта ошибка означает, что для ```standard-v2``` нельзя указывать ```cores = 1```, а минимум ```2```, а у нас в файле ```main.tf``` указано:

```
resources {
    cores         = 1
    memory        = 1
    core_fraction = 5
  }
```

Исправим:

```
cores         = 1
```

на

```
cores         = 2
```

Снова запустим проект.
После очередных изменений проект выполнился удачно:

![img](img/image15.png)

Посмотрим, что Terrafom сохранил в состоянии:

```
terraform state list
terraform state show yandex_compute_instance.platform
```

![img](img/image16.png)

![img](img/image17.png)

Из указанного вывода нас интересует параметр ```nat_ip_address = "84.201.134.92"```.

Подключимся к созданной виртуальной машине по ssh по указанному IP адресу:

```
ssh ubuntu@84.201.134.92
```

![img](img/image18.png)

Выведем внешний IP адрес виртуальной машины к которой мы подключились:

```
curl ifconfig.me
```

![img](img/image19.png)

Видим, что в консоли виртуальной машины отображается такой же идентификатор и такой же внешний IP адрес, как и в консоли Yandex Cloud:

![img](img/image20.png)


Что касается ввопросов о параметрах виртуальной машины.

Параметр ```preemptible = true``` указывает на создание прерываемой виртуальной машины. Это позволяет значительно снизить стоимость использования виртуальной машины, что особенно полезно при обучении, тестировании и выполнении лабораторных работ, где высокая доступность не требуется.

Параметр ```core_fraction = 5``` указывает на ограничение процессорного времени. Т.е. машине выделено ``2 vCPU```, но пользоваться ими постоянно она может только на 5%. Это так же позволяет значительно снизить стоимость виртуальной машины.


## Задание 2

1. Замените все хардкод-значения для ресурсов yandex_compute_image и yandex_compute_instance на отдельные переменные. К названиям переменных ВМ добавьте в начало префикс vm_web_ . Пример: vm_web_name.
2. Объявите нужные переменные в файле variables.tf, обязательно указывайте тип переменной. Заполните их default прежними значениями из main.tf.
3. Проверьте terraform plan. Изменений быть не должно.

## Решение 2

Для выполнения задания выполним следующие действия.

Добавим в файл ```variables.tf``` следующие строки:

```
###web vm vars

variable "vm_web_image_family" {
  type        = string
  default     = "ubuntu-2004-lts"
  description = "Image family for web VM"
}

variable "vm_web_name" {
  type        = string
  default     = "netology-develop-platform-web"
  description = "Web VM name"
}

variable "vm_web_platform_id" {
  type        = string
  default     = "standard-v2"
  description = "Web VM platform ID"
}

variable "vm_web_cores" {
  type        = number
  default     = 2
  description = "Web VM CPU cores"
}

variable "vm_web_memory" {
  type        = number
  default     = 1
  description = "Web VM RAM in GB"
}

variable "vm_web_core_fraction" {
  type        = number
  default     = 5
  description = "Web VM guaranteed CPU fraction"
}
```


В файл ```main.tf``` внесём следующие изменения.

Заменим:

```
data "yandex_compute_image" "ubuntu" {
  family = "ubuntu-2004-lts"
}
```

на

```
data "yandex_compute_image" "ubuntu" {
  family = var.vm_web_image_family
}
```

В ресурсе ВМ заменим:

```
name        = "netology-develop-platform-web"
platform_id = "standard-v2"
```

на

```
name        = var.vm_web_name
platform_id = var.vm_web_platform_id
```

Заменим блок ресурсов:

```
resources {
  cores         = 2
  memory        = 1
  core_fraction = 5
}
```

на

```
resources {
  cores         = var.vm_web_cores
  memory        = var.vm_web_memory
  core_fraction = var.vm_web_core_fraction
}
```

Выполним проверку конфигурации:

```
terraform fmt
terraform validate
terraform plan
```

![img](img/image21.png)

Видим, что, как и требовалось по заданию, никаких изменений нет.



## Задание 3

1. Создайте в корне проекта файл 'vms_platform.tf' . Перенесите в него все переменные первой ВМ.
2. Скопируйте блок ресурса и создайте с его помощью вторую ВМ в файле main.tf: "netology-develop-platform-db" , cores  = 2, memory = 2, core_fraction = 20. Объявите её переменные с префиксом vm_db_ в том же файле ('vms_platform.tf'). ВМ должна работать в зоне "ru-central1-b"
3. Примените изменения.

## Решение 3

Для выполнения задания выполним следующие действия.

Создадим файл ```vms_platform.tf``` и перенесём в него всю секцию ```###web vm vars``` из файла ```variables.tf```:

![img](img/image22.png)

В файле ```variables.tf``` останутся только секции ```###cloud vars``` и ```###ssh vars```:

![img](img/image23.png)

Добавим в файл ```vms_platform.tf``` переменные для DB VM:

```
###db vm vars

variable "vm_db_name" {
  type        = string
  default     = "netology-develop-platform-db"
  description = "DB VM name"
}

variable "vm_db_platform_id" {
  type        = string
  default     = "standard-v2"
  description = "DB VM platform ID"
}

variable "vm_db_zone" {
  type        = string
  default     = "ru-central1-b"
  description = "DB VM zone"
}

variable "vm_db_cidr" {
  type        = list(string)
  default     = ["10.0.2.0/24"]
  description = "DB subnet CIDR"
}

variable "vm_db_cores" {
  type        = number
  default     = 2
  description = "DB VM CPU cores"
}

variable "vm_db_memory" {
  type        = number
  default     = 2
  description = "DB VM RAM in GB"
}

variable "vm_db_core_fraction" {
  type        = number
  default     = 20
  description = "DB VM guaranteed CPU fraction"
}

```

В файл ```main.tf``` добавим вторую подсеть, т.к. DB VM должна быть в ```ru-central1-b```:

```
resource "yandex_vpc_subnet" "develop_b" {
  name           = "${var.vpc_name}-b"
  zone           = var.vm_db_zone
  network_id     = yandex_vpc_network.develop.id
  v4_cidr_blocks = var.vm_db_cidr
}
```

Добавим в файл ```main.tf``` описание параметров DB VM:

```
resource "yandex_compute_instance" "db" {
  name        = var.vm_db_name
  platform_id = var.vm_db_platform_id
  zone        = var.vm_db_zone

  resources {
    cores         = var.vm_db_cores
    memory        = var.vm_db_memory
    core_fraction = var.vm_db_core_fraction
  }

  boot_disk {
    initialize_params {
      image_id = data.yandex_compute_image.ubuntu.image_id
    }
  }

  scheduling_policy {
    preemptible = true
  }

  network_interface {
    subnet_id = yandex_vpc_subnet.develop_b.id
    nat       = true
  }

  metadata = {
    serial-port-enable = 1
    ssh-keys           = "ubuntu:${var.vms_ssh_root_key}"
  }
}
```

Выполним проверку проекта:

```
terraform fmt
terraform validate
terraform plan
```

![img](img/image24.png)

![img](img/image25.png)

Применим изменения:

```
terraform apply
```

![img](img/image26.png)


После окончания выполнения команды, в консоли Yandex Cloud видим, что создалась еще одна виртуальная машина в требуемой зоне:

![img](img/image27.png)



## Задание 4

1. Объявите в файле outputs.tf один output , содержащий: instance_name, external_ip, fqdn для каждой из ВМ в удобном лично для вас формате.(без хардкода!!!)
2. Примените изменения.

## Решение 4

Для выполнения задания выполним следующие действия.

В файл ```outputs.tf``` добавим следующий код:

```
output "vm_info" {
  description = "Information about created virtual machines"

  value = {
    web = {
      instance_name = yandex_compute_instance.platform.name
      external_ip   = yandex_compute_instance.platform.network_interface[0].nat_ip_address
      fqdn          = yandex_compute_instance.platform.fqdn
    }

    db = {
      instance_name = yandex_compute_instance.db.name
      external_ip   = yandex_compute_instance.db.network_interface[0].nat_ip_address
      fqdn          = yandex_compute_instance.db.fqdn
    }
  }
}
```

Выполним проверку и применим изменения:

```
terraform fmt
terraform validate
terraform plan
terraform apply
```

![img](img/image28.png)

![img](img/image29.png)


Выполним вывод ```output```:

```
terraform output
```

![img](img/image30.png)


Как и положено по заданию мы видим в выводе значения параметров ```instance_name```, ```external_ip```, ```fqdn``` обоих виртуальных машин.


## Задание 5

1. В файле locals.tf опишите в одном local-блоке имя каждой ВМ, используйте интерполяцию ${..} с НЕСКОЛЬКИМИ переменными по примеру из лекции.
2. Замените переменные внутри ресурса ВМ на созданные вами local-переменные. 
3. Примените изменения.

## Решение 5

Для выполнения задания выполним следующие действия.

Добавим в файл ```vms_platform.tf``` следующий код:

```
variable "vm_project_prefix" {
  type        = string
  default     = "netology"
  description = "Project prefix for VM names"
}

variable "vm_env" {
  type        = string
  default     = "develop"
  description = "Environment name"
}

variable "vm_platform_name" {
  type        = string
  default     = "platform"
  description = "Platform name part for VM names"
}

variable "vm_web_role" {
  type        = string
  default     = "web"
  description = "Web VM role"
}

variable "vm_db_role" {
  type        = string
  default     = "db"
  description = "DB VM role"
}
```

В файл ```locals.tf``` добавим следующий код:

```
locals {
  vm_web_name = "${var.vm_project_prefix}-${var.vm_env}-${var.vm_platform_name}-${var.vm_web_role}"
  vm_db_name  = "${var.vm_project_prefix}-${var.vm_env}-${var.vm_platform_name}-${var.vm_db_role}"
}
```

В файле ```main.tf``` внесём изменения в параметры, описывающие имена VM.
Заменим:


```
name = var.vm_web_name
```

на

```
name = local.vm_web_name
```

и

```
name = local.vm_db_name
```

Выполним проверку проекта:

```
terraform fmt
terraform validate
terraform plan
```

![img](img/image31.png)


Видим, что никаких изменений в проекте не появилось.
