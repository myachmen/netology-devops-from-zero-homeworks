
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


## Задание 3

1. Воспользуйтесь docker help или google, чтобы узнать как подключиться к стандартному потоку ввода/вывода/ошибок контейнера "custom-nginx-t2".
2. Подключитесь к контейнеру и нажмите комбинацию Ctrl-C.
3. Выполните docker ps -a и объясните своими словами почему контейнер остановился.
4. Перезапустите контейнер
5. Зайдите в интерактивный терминал контейнера "custom-nginx-t2" с оболочкой bash.
6. Установите любимый текстовый редактор(vim, nano итд) с помощью apt-get.
7. Отредактируйте файл "/etc/nginx/conf.d/default.conf", заменив порт "listen 80" на "listen 81".
8. Запомните(!) и выполните команду nginx -s reload, а затем внутри контейнера curl http://127.0.0.1:80 ; curl http://127.0.0.1:81.
9. Выйдите из контейнера, набрав в консоли exit или Ctrl-D.
10. Проверьте вывод команд: ss -tlpn | grep 127.0.0.1:8080 , docker port custom-nginx-t2, curl http://127.0.0.1:8080. Кратко объясните суть возникшей проблемы.
11. - Это дополнительное, необязательное задание. Попробуйте самостоятельно исправить конфигурацию контейнера, используя доступные источники в интернете. Не изменяйте конфигурацию nginx и не удаляйте контейнер. Останавливать контейнер можно. пример источника
12. Удалите запущенный контейнер "custom-nginx-t2", не останавливая его.(воспользуйтесь --help или google)

В качестве ответа приложите скриншоты консоли, где видно все введенные команды и их вывод.


## Решение 3

Для выполнения задания выполним следующие действия.

Подключимся к контейнеру:

```
docker attach custom-nginx-t2
```

После подключения нажмём ```Ctrl-C```:

![img](img/image24.png)

Проверим, что контейнер остановился:

```
docker ps -a
```

![img](img/image25.png)


В данном случае произошло следующее: коменда ```docker attach``` подключила текущий терминал к основному процессу контейнера. В контейнере nginx работает как главный процесс PID 1. Когда мы нажали Ctrl-C, сигнал прерывания был отправлен основному процессу, nginx завершился, а вместе с ним остановился и контейнер.

Перезапустим контейнер:

```
docker start custom-nginx-t2
```

Проверим его состояние:

```
docker ps
```

Видим, что контейнер снова запущен:

![img](img/image26.png)

Зайдём внутрь контейнера через bash:

```
docker exec -it custom-nginx-t2 bash
```

Дальнейшие команды будем выполнять уже внутри контейнера.

Установим текстовый редактор nano:

```
apt-get update
apt-get install -y nano
```

![img](img/image27.png)

Для изменения порта nginx с 80 на 81 отредактируем конфигурационный файл:

```
nano /etc/nginx/conf.d/default.conf
```

![img](img/image28.png)


Изменим значение параметра ```listen``` c 80 на 81:

![img](img/image29.png)

Перезагрузим nginx внутри контейнера:

```
nginx -s reload
```

![img](img/image30.png)

Для проверки выполним curl запросы на 80 и 81 порты:

```
curl http://127.0.0.1:80 
curl http://127.0.0.1:81
```
Из полученного вывода видим, что на 80 порту сервер теперь не отвечает, а на 81 отдаёт нашу страницу:

![img](img/image31.png)

Теперь выходим из контейнера:

```
exit
```

Выполним проверку доступности страницы с самого хоста:

```
ss -tlpn | grep 127.0.0.1:8080
docker port custom-nginx-t2
curl http://127.0.0.1:8080
```

Видим, что с хоста страница недоступна:

![img](img/image32.png)

Данное поведение связанно с тем, что Docker-проброс порта был создан при старте контейнера как ```127.0.0.1:8080 -> 80/tcp```. Но внутри контейнера nginx теперь слушает не 80, а 81 порт. Docker всё ещё перенаправляет запросы на порт 80 контейнера, где уже никто не слушает. Поэтому curl http://127.0.0.1:8080 перестаёт возвращать требуемую страницу.

Теперь удалим запущенный контейнер, не останавливая его.

Сначала проверим, что контейнер действительно запущен:

```
docker ps
```

![img](img/image33.png)

Выполним принудительное удаление контейнера:

```
docker rm -f custom-nginx-t2
```

Проверим еще раз:

```
docker ps -a
```

Контейнер отсутствует:

![img](img/image34.png)


## Задание 4

 - Запустите первый контейнер из образа centos c любым тегом в фоновом режиме, подключив папку текущий рабочий каталог $(pwd) на хостовой машине в /data контейнера, используя ключ -v.
 - Запустите второй контейнер из образа debian в фоновом режиме, подключив текущий рабочий каталог $(pwd) в /data контейнера.
 - Подключитесь к первому контейнеру с помощью docker exec и создайте текстовый файл любого содержания в /data.
 - Добавьте ещё один файл в текущий каталог $(pwd) на хостовой машине.
 - Подключитесь во второй контейнер и отобразите листинг и содержание файлов в /data контейнера.

В качестве ответа приложите скриншоты консоли, где видно все введенные команды и их вывод.

## Решение 4

Для выполнения задания выполним следующие действия.

Запустим контейнер CentOS:

```
docker run -d --name centos-container -v $(pwd):/data quay.io/centos/centos:stream9 sleep infinity
```

![img](img/image35.png)


Запустим контейнер Debian:

```
docker run -d --name debian-container -v $(pwd):/data debian sleep infinity
```

![img](img/image36.png)

Проверим, что контейнеры запущены:

```
docker ps
```

![img](img/image37.png)

Создадим файл внутри CentOS контейнера.

Зайдём внутрь CentOS контейнера через bash:

```
docker exec -it centos-container bash
```

Внутри контейнера создадим файл:

```
echo "Hello from CentOS container" > /data/centos-file.txt
ls -l /data
```

![img](img/image38.png)


Выйдем из CentOS контейнера:

```
exit
```

Создадим файл на хостовой машине:

```
echo "Hello from host machine" > host-file.txt
ls -l
```

![img](img/image39.png)

Зайдём внутрь Debian контейнера через bash:

```
docker exec -it debian-container bash
```

Проверим файлы внутри Debian контейнера:

```
ls -l /data
```

В выводе мы увидим оба созданных ранее файла:

![img](img/image40.png)


Это и говорит о том, что оба контейнера используют один и тот же каталог хостовой системы. Оба контейнера были запущены с bind mount текущего каталога хостовой системы в директорию /data контейнеров. Файл, созданный внутри контейнера CentOS, стал доступен как на хостовой системе, так и внутри контейнера Debian. Аналогично файл, созданный на хосте, был виден внутри обоих контейнеров. Это демонстрирует совместное использование данных между контейнерами через volume mount.


## Задание 5

1. Создайте отдельную директорию(например /tmp/netology/docker/task5) и 2 файла внутри него. "compose.yaml" с содержимым:
```
version: "3"
services:
  portainer:
    network_mode: host
    image: portainer/portainer-ce:latest
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
```

"docker-compose.yaml" с содержимым:

```
version: "3"
services:
  registry:
    image: registry:2

    ports:
    - "5000:5000"
```

И выполните команду "docker compose up -d". Какой из файлов был запущен и почему? (подсказка: https://docs.docker.com/compose/compose-application-model/#the-compose-file )

2. Отредактируйте файл compose.yaml так, чтобы были запущенны оба файла. (подсказка: https://docs.docker.com/compose/compose-file/14-include/)

3. Выполните в консоли вашей хостовой ОС необходимые команды чтобы залить образ custom-nginx как custom-nginx:latest в запущенное вами, локальное registry. Дополнительная документация: https://distribution.github.io/distribution/about/deploying/

4. Откройте страницу "https://127.0.0.1:9000" и произведите начальную настройку portainer.(логин и пароль адмнистратора)

5. Откройте страницу "http://127.0.0.1:9000/#!/home", выберите ваше local окружение. Перейдите на вкладку "stacks" и в "web editor" задеплойте следующий компоуз:

```
version: '3'

services:
  nginx:
    image: 127.0.0.1:5000/custom-nginx
    ports:
      - "9090:80"
```

6. Перейдите на страницу "http://127.0.0.1:9000/#!/2/docker/containers", выберите контейнер с nginx и нажмите на кнопку "inspect". В представлении <> Tree разверните поле "Config" и сделайте скриншот от поля "AppArmorProfile" до "Driver".

7. Удалите любой из манифестов компоуза(например compose.yaml). Выполните команду "docker compose up -d". Прочитайте warning, объясните суть предупреждения и выполните предложенное действие. Погасите compose-проект ОДНОЙ(обязательно!!) командой.

В качестве ответа приложите скриншоты консоли, где видно все введенные команды и их вывод, файл compose.yaml , скриншот portainer c задеплоенным компоузом.


## Решение 5

Для выполнения задания выполним следующие действия.

Создадим директорию:

```
mkdir -p /tmp/netology/docker/task5
cd /tmp/netology/docker/task5
```

Создадим файл compose.yaml:

```
cat > compose.yaml <<'EOF'
version: "3"
services:
  portainer:
    network_mode: host
    image: portainer/portainer-ce:latest
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
EOF
```

Создадим файл docker-compose.yaml:

```
cat > docker-compose.yaml <<'EOF'
version: "3"
services:
  registry:
    image: registry:2

    ports:
    - "5000:5000"
EOF
```

![img](img/image41.png)

Создадим Docker Compose проект и запустим контейнеры:

```
docker compose up -d
```

![img](img/image42.png)

Выведем состояние контейнеров текущего Compose-проекта:

```
docker compose ps
```

![img](img/image43.png)

Из вывода видим, что запустится только compose.yaml, то есть только portainer.
По умолчанию Docker Compose ищет compose-файлы в приоритетном порядке. Если в директории есть compose.yaml, он использует его как основной файл, docker-compose.yaml сам автоматически дополнительно не подключается.


Отредактируем содержимое файла compose.yaml следующим образом:

```
include:
  - docker-compose.yaml

services:
  portainer:
    network_mode: host
    image: portainer/portainer-ce:latest
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
```

![img](img/image44.png)


Снова запустим Compose-проект:

```
docker compose up -d
```

![img](img/image45.png)


Проверим состояние контейнеров в проекте:

```
docker compose ps
```

Из вывода мы видим, что запущены оба сервиса ```portainer``` и ```registry```:

![img](img/image46.png)

Проверим доступность локального Registry:

```
curl http://127.0.0.1:5000/v2/
```

В ответ мы получим пустой JSON-объект, что означает, что локальный Docker Registry успешно запущен и Docker Registry API v2 доступен по порту 5000.

![img](img/image47.png)


Создадим новый тег для локального Registry:

```
docker tag custom-nginx:1.0.0 127.0.0.1:5000/custom-nginx:latest
```

Проверим, что тег появился:

```
docker images
```

![img](img/image48.png)

Отправим образ в локальный Registry:

```
docker push 127.0.0.1:5000/custom-nginx:latest
```

![img](img/image49.png)

Проверим локальный Registry:

```
curl http://127.0.0.1:5000/v2/_catalog
```

Увидим, что образ появился:

![img](img/image50.png)

Так же можно проверить список тиегов:

```
curl http://127.0.0.1:5000/v2/custom-nginx/tags/list
```

![img](img/image51.png)

Теперь приступим к настройке Portainer.

Создадим пользователя ```admin```:

![img](img/image52.png)

Выберем ```local environment```:

![img](img/image53.png)

Перейдём в Stasks и добавим compose из задания:

![img](img/image54.png)

Выполним deploy добавленного compose:

![img](img/image55.png)

![img](img/image56.png)

Выполним inspect контейнера.

Для этого перейдём в ораздел ```Containers```, выберем контейнер ```
custom-nginx-stack-nginx-1``` и зайдём в него:

![img](img/image57.png)

Нажмём ```inspect```:

![img](img/image58.png)

Скриншот, необходимый по заданию:

![img](img/image59.png)

Проверим, что в каталоге ```/tmp/netology/docker/task5``` находятся оба файла манифеста:

```
ls -l
```

![img](img/image60.png)


Удалим файл compose.yaml:

```
rm compose.yaml
```

![img](img/image61.png)

Выполним запуск проекта:

```
docker compose up -d
```

В выводе видим предупреждение о том, что для проекта есть orphan containers — контейнеры, которые были созданы старой compose-конфигурацией, но теперь отсутствуют в текущем compose-файле.

![img](img/image62.png)

Выполним удаление orphan containers:

```
docker compose up -d --remove-orphans
```

![img](img/image63.png)

Погасим compose-проект одной командой:

```
docker compose down
```

![img](img/image64.png)

После удаления одного из compose-файлов Docker Compose увидел только оставшийся docker-compose.yaml, где описан только registry. Ранее созданный portainer больше не описан в текущей конфигурации, поэтому Docker Compose предупредил об orphan container.

Выполним проверку состояния проекта:

```
docker compose ps
```

![img](img/image64.png)

В выводе не увидим никаких запущеных контейнеров.