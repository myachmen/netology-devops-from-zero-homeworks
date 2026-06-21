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