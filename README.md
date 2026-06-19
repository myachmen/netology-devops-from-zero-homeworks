# Домашнее задание по теме "Введение в Terraform" Ячмень Марк Викторович

## Задание 1

### Задание 1

1. Перейдите в каталог [**src**](https://github.com/netology-code/ter-homeworks/tree/main/01/src). Скачайте все необходимые зависимости, использованные в проекте. 
2. Изучите файл **.gitignore**. В каком terraform-файле, согласно этому .gitignore, допустимо сохранить личную, секретную информацию?(логины,пароли,ключи,токены итд)
3. Выполните код проекта. Найдите  в state-файле секретное содержимое созданного ресурса **random_password**, пришлите в качестве ответа конкретный ключ и его значение.
4. Раскомментируйте блок кода, примерно расположенный на строчках 29–42 файла **main.tf**.
Выполните команду ```terraform validate```. Объясните, в чём заключаются намеренно допущенные ошибки. Исправьте их.
5. Выполните код. В качестве ответа приложите: исправленный фрагмент кода и вывод команды ```docker ps```.
6. Замените имя docker-контейнера в блоке кода на ```hello_world```. Не перепутайте имя контейнера и имя образа. Мы всё ещё продолжаем использовать name = "nginx:latest". Выполните команду ```terraform apply -auto-approve```.
Объясните своими словами, в чём может быть опасность применения ключа  ```-auto-approve```. Догадайтесь или нагуглите зачем может пригодиться данный ключ? В качестве ответа дополнительно приложите вывод команды ```docker ps```.
8. Уничтожьте созданные ресурсы с помощью **terraform**. Убедитесь, что все ресурсы удалены. Приложите содержимое файла **terraform.tfstate**. 
9. Объясните, почему при этом не был удалён docker-образ **nginx:latest**. Ответ **ОБЯЗАТЕЛЬНО НАЙДИТЕ В ПРЕДОСТАВЛЕННОМ КОДЕ**, а затем **ОБЯЗАТЕЛЬНО ПОДКРЕПИТЕ** строчкой из докум

## Решение 1

Для выполнения задания выполним следующие действия.

Создадим рабочий каталог:

```
mkdir -p ~/homeworks/hw-terraform-intro
cd ~/homeworks/hw-terraform-intro
```

Скачаем исходники задания:

```
git clone https://github.com/netology-code/ter-homeworks.git
```

![img](img/image1.png)

Переходим в директорию и проверяем содержимое:

```
cd ter-homeworks/01/src
ls -la
```

![img](img/image2.png)

Скачаем зависимости Terraform:

```
terraform init
```

![img](img/image3.png)

Посмотрим на содержимое файла ```.gitignore```:

```
cat .gitignore
```

![img](img/image4.png)

Согласно файлу ```.gitignore```, личную и секретную информацию (логины, пароли, токены, ключи и т.п.) рекомендуется хранить в файле ```personal.auto.tfvars```. Этот файл исключён из системы контроля версий Git, поэтому его содержимое не будет попадать в репозиторий. На это указывает строка:

```
# own secret vars store.
personal.auto.tfvars
```

Приступим к выполнению кода проекта.
Сначала посмотрим, что Terraform собирается сделать:

```
terraform plan
```

![img](img/image5.png)

Теперь выполним:

```
terraform apply
```

![img](img/image6.png)

Посмотрим, какие ресурсы создал Terraform:

```
terraform state list
```

![img](img/image7.png)

Посмотрим информацию о созданном ресурсе:

```
terraform state show random_password.random_string
```

![img](img/image8.png)

Проверим, что файл ```terraform.tfstate``` создался и выведем в консоль его содержимое:

```
ls -l terraform.tfstate
cat terraform.tfstate
```

![img](img/image9.png)

Из вывода мы видим, что в файле terraform.tfstate секретное содержимое ресурса random_password.random_string хранится в атрибуте:

 - Ключ: ```result```
 - Значение: ```4K1Luwkpj10f9Uyn```


Теперь приступим к изучению и редактированию файла ```main.tf```.
Выведем его содержимое с номерами строк:

```
nl -ba main.tf
```

![img](img/image10.png)

Откроем файл в редакторе и раскомментируем блок кода:

```
    22  /*
    23  resource "docker_image" {
    24    name         = "nginx:latest"
    25    keep_locally = true
    26  }
    27
    28  resource "docker_container" "1nginx" {
    29    image = docker_image.nginx.image_id
    30    name  = "example_${random_password.random_string_FAKE.resulT}"
    31
    32    ports {
    33      internal = 80
    34      external = 9090
    35    }
    36  }
    37  */
```

Выполним валидацию:

```
terraform validate
```

![img](img/image11.png)

В выводе мы видим несколько ошибок.
Первая ошибка ```Error: Missing name for resource``` возникла из-за того, что в Terraform любой ресурс имеет вид:

```
resource "<тип>" "<локальное_имя>" {
```

Т.е. всегда должно быть два параметра:

1. тип ресурса;
2. его локальное имя.

В данном случае указан только тип ресурса.
Добавим имя ресурса:

```
resource "docker_image" "nginx" {
```

Вторая ошибка ```Error: Invalid resource name``` возникает из-за того, локальное имя ресурса Terraform должно начинаться:
 - с буквы;
 - либо с символа ```_```.
Нельзя наччинать имя с цифры.

Сейчас у нас ```1nginx```. Исправим на ```nginx```.

Снова выполним валидацию и увидим сообщение еще об одной ошибке:

![img](img/image12.png)

Эта ошибка укаывает на то, что в файле объявлен ресурс:

```
resource "random_password" "random_string" {
```

А далее контейнер пытается обратиться к ресурсу:

```
random_password.random_string_FAKE.result
```

Т.е. Terraform ищет ресурс ```random_string_FAKE```, которого не существует.
Так же исправим прописную ```T ``` на строчную ```t``` в аттрибуте ```resulT```.


Для этого исправим 

```
name = "example_${random_password.random_string_FAKE.result}"
```

на

```
name = "example_${random_password.random_string.result}"
```

Снова выполним валидацию и на этот раз увидим, что всё в порядке:

![img](img/image13.png)

Теперь применим конфигурацию:

```
terraform apply
```

Проверим контейнер:

```
docker ps
```

![img](img/image14.png)

Поменяем имя контейнера.
Для этого в файле ```main.tf``` заменим строку:

```
name = "example_${random_password.random_string.result}"
```

на

```
name = "hello_world"
```

Применим конфигурацию с параметром ```-auto-approve```:

```
terraform apply -auto-approve
```

![img](img/image15.png)

![img](img/image16.png)

Смысл параметра ```-auto-approve```: Terraform применяет изменения без запроса на подтверждения применения конфигурации. Это удобно для автоматизации/CI/CD, но опасно тем, что можно случайно применить разрушительные изменения без ручной проверки.

Снова проверим контейнер:

```
docker ps
```

![img](img/image17.png)


Теперь уництожим созданные ресурсы:

```
terraform destroy
```
![img](img/image18.png)

![img](img/image19.png)

![img](img/image20.png)

Проверим:

```
docker ps
docker ps -a
```

Выведем на экран содержимое файла ```terraform.tfstate```^

```
cat terraform.tfstate
```

![img](img/image21.png)

Файл ```terraform.tfstate``` после уничтожения ресурсов сохранился, однако раздел ```"resources": []``` стал пустым, что означает отсутствие ресурсов под управлением Terraform.

Проверим локальные docker-образы:

```
docker images
```

![img](img/image22.png)

Мы видим, что образ ```nginx:latest``` остался. Этот образ стался из-за строки в коде:

```
keep_locally = true
````

В документации docker_image сказано: если ```keep_locally = true```, Docker image не удаляется при destroy; если ```false```, удаляется из локального Docker storage.

![img](img/image23.png)