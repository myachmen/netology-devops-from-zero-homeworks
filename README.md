
# Домашнее задание по теме "Оркестрация группой Docker контейнеров на примере Docker Compose" Ячмень Марк Викторович




## Задание 1

Сценарий выполнения задачи:

 - Установите docker и docker compose plugin на свою linux рабочую станцию или ВМ.
 - Если dockerhub недоступен создайте файл /etc/docker/daemon.json с содержимым: {"registry-mirrors": ["https://mirror.gcr.io", "https://daocloud.io", "https://c.163.com/", "https://registry.docker-cn.com"]}
 - Зарегистрируйтесь и создайте публичный репозиторий с именем "custom-nginx" на https://hub.docker.com (ТОЛЬКО ЕСЛИ У ВАС ЕСТЬ ДОСТУП);
 - скачайте образ nginx:1.29.0;
 - Создайте Dockerfile и реализуйте в нем замену дефолтной индекс-страницы(/usr/share/nginx/html/index.html), на файл index.html с содержимым:

```
<html>
<head>
Hey, Netology
</head>
<body>
<h1>I will be DevOps Engineer!</h1>
</body>
</html>
```

 - Соберите и отправьте созданный образ в свой dockerhub-репозитории c tag 1.0.0 (ТОЛЬКО ЕСЛИ ЕСТЬ ДОСТУП).
 - Предоставьте ответ в виде ссылки на https://hub.docker.com/<username_repo>/custom-nginx/general .



## Решение 1

Для выполнения задания выполним следующие действия.

Подготовим виртуальную машину с помощью Vagrant.
Для этого в папке с проектами создадим папку ```docker-compose-lab```.

С помощью команды ```vagrant init bento/ubuntu-22.04``` создадим Vagrant файл.

Отредактируем содержимое Vagrant файла следующим образом:

![img](img/image1.png)

С такими настройками виртуальная машина будетт создана в VirtualBox из образа Ubuntu-22.04.

Запустим создание виртуальной машины: ```vagrant up```:

![img](img/image2.png)

После завершения процесса создания виртуальной машины, в консоли VirtualBox можно увидеть, что новая виртуальная машина запущена:

![img](img/image3.png)

Подключимся к созданной вирптуальной машине: ```vagrant ssh```:

![img](img/image4.png)

После подключения к виртуальной машине установим пакеты, необходимые для добавления внешнего APT-репозитория Docker: ```sudo apt install -y ca-certificates curl gnupg lsb-release```:

 - ca-certificates — набор корневых сертификатов для проверки HTTPS-соединений.
 - curl — утилита для скачивания файлов по HTTP/HTTPS.
 - gnupg — утилиты для работы с GPG-ключами репозиториев.
 - lsb-release — позволяет определить кодовое имя установленной Ubuntu, например jammy.

Создадим директорию для хранения GPG-ключей APT-репозиториев: ```sudo mkdir -p /etc/apt/keyrings```.

Скачаем GPG-ключ Docker: ```curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg```.

Добавим официальный Docker-репозиторий в список источников APT:

```
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

Обновим список пакетов:

```
sudo apt update
```

После этого установим Docker Engine, Docker CLI, containerd, Buildx и Docker Compose plugin:

```
sudo apt install -y \
docker-ce \
docker-ce-cli \
containerd.io \
docker-buildx-plugin \
docker-compose-plugin
```

![img](img/image5.png)

Проверим установленные версии:

```
docker --version
docker compose version
```

![img](img/image6.png)

Добавим пользователя vagrant в группу docker:

```
sudo usermod -aG docker vagrant
```

Это нужно, чтобы выполнять команды docker без sudo.


Откроем и отредактируем конфигурационный файл HAProxy:

![img](img/image5.png)

![img](img/image6.png)

Проверим работу Docker:

```
docker run hello-world
```

Сообщение ```Hello from Docker!``` подтверждает, что Docker установлен и работает корректно.

![img](img/image7.png)

Для создания публичного репозитория зайдём на сайт https://hub.docker.com и перейдём по ссылке Create a Repository:

![img](img/image8.png)

Заполним поле Repository Name в соответствии с заданием, тип репозитория установим как Public и нажмём кнопку Create.

![img](img/image9.png)

![img](img/image10.png)


Теперь снова перейдем к работе с локальной виртуальной машиной.

Скачаем nginx:

```
docker pull nginx:1.29.0
```

![img](img/image11.png)

Проверим список загруженных Docker Images:

```
docker images
```

![img](img/image12.png)

Создадим папку для кастомизации nginx:

```
mkdir -p ~/custom-nginx
cd ~/custom-nginx
```

Создадим файл index.html следующего содержания:

```
<html>
<head>
Hey, Netology
</head>
<body>
<h1>I will be DevOps Engineer!</h1>
</body>
</html>
```

![img](img/image13.png)

Создадим Dockerfile следующего содержания:

```
FROM nginx:1.29.0

COPY index.html /usr/share/nginx/html/index.html
```

![img](img/image14.png)


Соберём образ:

```
docker build -t custom-nginx:1.0.0 .
```

![img](img/image15.png)

Выведем список Docker Images:

```
docker images
```

В списке видим только что собранный образ custom-nginx:1.0.0:

![img](img/image16.png)

Протестируем работу образа. Запустим контейнер на его базе:

```
docker run --rm -d --name test-custom-nginx -p 8080:80 custom-nginx:1.0.0
```

Выполним curl запрос:

```
curl http://127.0.0.1:8080
```

Запрос возвращает нам содержание файла index.hthl, который мы создали ранее:

![img](img/image17.png)

Остановим запущеный контейнер:

```
docker stop test-custom-nginx
```

Добавим к собранному образу тег с именем пользователя с сайта https://hub.docker.com:

```
docker tag custom-nginx:1.0.0 yamarkya/custom-nginx:1.0.0
```

Отправим образ в созданный ранее публичный репозиторий на сайте Docker:

```
docker push yamarkya/custom-nginx:1.0.0
```

![img](img/image18.png)

Теперь собранный нами образ доступен по ссылке https://hub.docker.com/repository/docker/yamarkya/custom-nginx/general :

![img](img/image19.png)












































## Задание 2

 - Запустите три simple python сервера на своей виртуальной машине на разных портах
 - Настройте балансировку Weighted Round Robin на 7 уровне, чтобы первый сервер имел вес 2, второй - 3, а третий - 4
 - HAproxy должен балансировать только тот http-трафик, который адресован домену example.local
 - На проверку направьте конфигурационный файл haproxy, скриншоты, где видно перенаправление запросов на разные серверы при обращении к HAProxy c использованием домена example.local и без него.

## Решение 2

Для выполнения задания выполним следующие действия.

Переделаем файлы index.html, предназначенные для работы python серверов:

![img](img/image9.png)

Запустим три simple python сервера на разных портах:

![img](img/image10.png)

Произведём настройку домена example.com.
Для этого добавим его в файл /etc/hosts:

![img](img/image11.png)

Отредактируем файл конфигурации HAProxy для работы с балансировкой Weighted Round Robin на 7 уровне:

![img](img/image12.png)

Перезапустим сервис HAProxy и проверим его статус:

![img](img/image13.png)

Для проверки работы алгоритма балансировки выполним несколько запросов к адресу http://example.local
и посчитаем как часто нам отвечает тот или иной сервер:

![img](img/image14.png)

Из вывода мы видим, что Server3 отвечал 7 раз из 15 запросов, Server2 - 5 раз и Server1 - 3 раза, 
что как раз и соответствует присвоенным весам.

В том случае, если запрос не будет содержать имени , то будет возвращена 404 ошибка:

![img](img/image15.png)

В репозитории представлен [конфигурационный файл](L7_haproxy.cfg) HAProxy.



