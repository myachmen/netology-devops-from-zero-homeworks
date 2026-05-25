
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

 1. Запустите ваш образ custom-nginx:1.0.0 командой docker run в соответвии с требованиями:
 - имя контейнера "ФИО-custom-nginx-t2"
 - контейнер работает в фоне
 - контейнер опубликован на порту хост системы 127.0.0.1:8080
2. Не удаляя, переименуйте контейнер в "custom-nginx-t2"
3. Выполните команду ```date +"%d-%m-%Y %T.%N %Z" ; sleep 0.150 ; docker ps ; ss -tlpn | grep 127.0.0.1:8080  ; docker logs custom-nginx-t2 -n1 ; docker exec -it custom-nginx-t2 base64 /usr/share/nginx/html/index.html```
4. Убедитесь с помощью curl или веб браузера, что индекс-страница доступна.

В качестве ответа приложите скриншоты консоли, где видно все введенные команды и их вывод.

## Решение 2

Для выполнения задания выполним следующие действия.

Запустим контейнер в соответствии с требованиями задания:

```
docker run -d --name Yachmen-Mark-Viktorovich-custom-nginx-t2 -p 127.0.0.1:8080:80 custom-nginx:1.0.0
```

Проверим, что контейнер запустился:

```
docker ps
```
![img](img/image20.png)

Переименуем контейнер:

```
docker rename Yachmen-Mark-Viktorovich-custom-nginx-t2 custom-nginx-t2
```

Проверим, что изменения применились:

```
docker ps
```

![img](img/image21.png)

Теперь выполним команду из задания:

```
date +"%d-%m-%Y %T.%N %Z" ; sleep 0.150 ; docker ps ; ss -tlpn | grep 127.0.0.1:8080 ; docker logs custom-nginx-t2 -n1 ; docker exec -it custom-nginx-t2 base64 /usr/share/nginx/html/index.html
```

В выводе видно, что контейнер `custom-nginx-t2` находится в состоянии `Up`, порт `127.0.0.1:8080` опубликован и перенаправляется на порт `80/tcp` контейнера. В логах nginx отображается успешный HTTP-запрос `GET /` со статусом `200`. Команда `docker exec` прочитала файл `/usr/share/nginx/html/index.html` внутри контейнера и вывела его содержимое в кодировке Base64, что подтверждает наличие кастомной индекс-страницы в контейнере.

![img](img/image22.png)

Проверим, что страница по-прежнему доступна:

```
curl http://127.0.0.1:8080
```

![img](img/image23.png)




