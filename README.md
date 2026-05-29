# Домашнее задание по теме "Практическое применение Docker" Ячмень Марк Викторович

## Задание 0

1. Убедитесь что у вас НЕ(!) установлен docker-compose, для этого получите следующую ошибку от команды ```docker-compose --version```

```
Command 'docker-compose' not found, but can be installed with:

sudo snap install docker          # version 24.0.5, or
sudo apt  install docker-compose  # version 1.25.0-1

See 'snap info docker' for additional versions.
```

В случае наличия установленного в системе docker-compose - удалите его.
2. Убедитесь что у вас УСТАНОВЛЕН ```docker compose``` (без тире) версии не менее v2.24.X, для это выполните команду docker compose version

## Решение 0

Для выполнения задания выполним следующие действия.

Подготовим виртуальную машину с помощью Vagrant.
Для этого в папке с проектами создадим папку ```docker-practice```.

Cоздадим пустой Vagrant файл.

Отредактируем содержимое Vagrant файла следующим образом:

```
Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/jammy64"
  config.vm.hostname = "docker-practice"

  config.vm.provider "virtualbox" do |vb|
    vb.name = "docker-practice"
    vb.memory = 4096
    vb.cpus = 2
  end

  config.vm.network "forwarded_port", guest: 8090, host: 8090
  config.vm.network "forwarded_port", guest: 8080, host: 8080
  config.vm.network "forwarded_port", guest: 5000, host: 5000
  
  config.vm.synced_folder "D:/Homework/netology-devops-from-zero-homeworks", "/home/vagrant/homeworks"

  config.vm.provision "shell", inline: <<-SHELL
    apt-get update
    apt-get install -y ca-certificates curl git gnupg lsb-release

    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
      | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

    chmod a+r /etc/apt/keyrings/docker.gpg

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" \
      > /etc/apt/sources.list.d/docker.list

    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    usermod -aG docker vagrant
  SHELL
end
```

С такими настройками виртуальная машина будет создана в VirtualBox из образа Ubuntu-22.04 в которой:
 - будет устанавлен Docker Engine;
 - будет устанавлен Docker Compose Plugin;
 - пользователь vagrant будет добавлен в docker group.

Запустим создание виртуальной машины с помощью команды ```vagrant up```:

![img](img/image1.png)

После завершения процесса создания виртуальной машины, в консоли VirtualBox можно увидеть, что новая виртуальная машина запущена:

![img](img/image2.png)

Подключимся к созданной виртуальной машине с помощью команды ```vagrant ssh``` и проверим, что установлены требуемые по заданию пакеты:

![img](img/image3.png)


## Задание 1

1. Сделайте в своем GitHub пространстве fork репозитория.

2. Создайте файл ```Dockerfile.python``` на основе существующего ```Dockerfile```:

 - Используйте базовый образ python:3.12-slim
 - Обязательно используйте конструкцию COPY . . в Dockerfile
 - Создайте .dockerignore файл для исключения ненужных файлов
 - Используйте CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"] для запуска
 - Протестируйте корректность сборки 2.1 Используйте multistage сборку вместо single stage.

3. (Необязательная часть, *) Изучите инструкцию в проекте и запустите web-приложение без использования docker, с помощью venv. (Mysql БД можно запустить в docker run).

4. (Необязательная часть, *) Изучите код приложения и добавьте управление названием таблицы через ENV переменную.


## Решение 1

Для выполнения задания выполним следующие действия.

Перейдём по ссылке из задания и сделаем fork репозитория.

![img](img/image4.png)

![img](img/image5.png)

![img](img/image6.png)

Теперь склонируем полученный fork на локальную машину:

```
git clone https://github.com/myachmen/shvirtd-example-python.git
```

![img](img/image7.png)

Удалим .git файл из склонированного репозитория:

```
Remove-Item -Recurse -Force .\hw-docker-in-practice\.git
```

В папке ```hw-docker-in-practice``` создадим файл ```Dockerfile.python``` следующего содержания:

```
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
```

Подключимся к виртуальной машине и запустим сборку Docker-образа shvirtd-fastapi на основе файла Dockerfile.python из текущего каталога проекта.

```
docker build -f Dockerfile.python -t shvirtd-fastapi .
```

![img](img/image8.png)

Проверим список образов:

```
docker image ls
```

![img](img/image9.png)


Запустим контейнер:

```
docker run -d --name fastapi-test -p 5000:5000 shvirtd-fastapi
```

Проверим состояние контейнера:

```
docker ps
```

![img](img/image10.png)

Создадим файл ```compose.yaml``` следующего содержания:

```
include:
  - proxy.yaml

services:
  web:
    build:
      context: .
      dockerfile: Dockerfile.python
    image: shvirtd-fastapi
    container_name: shvirtd-web
    restart: always
    env_file:
      - .env
    environment:
      DB_HOST: db
      DB_NAME: ${MYSQL_DATABASE}
      DB_USER: ${MYSQL_USER}
      DB_PASSWORD: ${MYSQL_PASSWORD}
    networks:
      backend:
        ipv4_address: 172.20.0.5
    depends_on:
      - db

  db:
    image: mysql:8.0
    container_name: shvirtd-db
    restart: always
    env_file:
      - .env
    networks:
      backend:
        ipv4_address: 172.20.0.10
    volumes:
      - db_data:/var/lib/mysql

volumes:
  db_data:
  ```

Запустим сборку Docker-образа, создание сети и томов Docker Compose, а также запуск контейнеров web, db, nginx и haproxy в фоновом режиме.

```
docker compose up -d --build
```

![img](img/image11.png)


Проверим состояние контейнеров, запущенных через Docker Compose:

```
docker compose ps
```

В выводе подтвержден успешный запуск сервисов приложения и проброс необходимых сетевых портов:

![img](img/image12.png)

Проверим доступность веб-приложения через цепочку reverse proxy (nginx → haproxy → FastAPI):

```
curl http://127.0.0.1:8090
```

Полученный ответ подтверждает корректную работу приложения и взаимодействие контейнеров внутри Docker Compose инфраструктуры.

![img](img/image13.png)

Теперь переделаем сборку в multistage-формате.

Изменим содержание ```Dockerfile.python``` на:

```
FROM python:3.12-slim AS builder

WORKDIR /install

COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /install /usr/local

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
```
В данном случае Dockerfile.python был переписан в multistage-формате. На первом этапе builder устанавливаются Python-зависимости, а на втором этапе создаётся финальный runtime-образ, в который копируются только установленные зависимости и файл приложения main.py.

Остановим и удалим текущую инфраструктуру Compose:

```
docker compose down
```

![img](img/image14.png)

Снова запустим сборку Docker-образа:

```
docker compose up -d --build
```

![img](img/image15.png)

Проверим состояние контейнеров, запущенных через Docker Compose:

```
docker compose ps
```

![img](img/image16.png)

Проверим доступность веб-приложения через цепочку reverse proxy (nginx → haproxy → FastAPI):

![img](img/image17.png)

Single-stage сборка создаёт Docker-образ, содержащий одновременно среду сборки и runtime-окружение приложения.
Multistage сборка разделяет процесс на несколько этапов: отдельный этап сборки (builder) и финальный runtime-этап. В результате итоговый Docker-образ содержит только необходимые для запуска приложения файлы и зависимости.
В рамках домашнего задания различие по функциональности между single-stage и multistage отсутствует, однако multistage подход позволяет уменьшить размер образа, повысить безопасность и ускорить доставку контейнеров в production-средах.


Создадим файл .dockerignore.
Для этого в папке ```hw-docker-in-practice``` создадим файл .dockerignore следующего содержания:

```
.git
.gitignore
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
.env.local
.venv/
venv/
.DS_Store
.idea/
.vscode/
*.log
schema.pdf
```

Повторим вышеописаный процес сборки и проверки:

![img](img/image18.png)


Теперь попробуем запустить web-приложение без использования docker, с помощью venv.

Для этого сначала остановим compose-инфраструктуру:

```
docker compose down
```

![img](img/image19.png)


Запустим только MySQL отдельным контейнером:

```
docker run -d --name mysql-venv-test -e MYSQL_ROOT_PASSWORD=YtReWq4321 -e MYSQL_DATABASE=virtd -e MYSQL_USER=app -e MYSQL_PASSWORD=QwErTy1234 -p 3306:3306 mysql:8.0
```

Проверим, что MySQL поднялся:

```
docker ps
```

![img](img/image20.png)


Установим пакет ```python3-venv```:

```
sudo apt update
sudo apt install -y python3-venv
```

Запустим Python-приложение без Docker, через venv:

```
python3 -m venv ~/venvs/shvirtd
source ~/venvs/shvirtd/bin/activate
pip install -r requirements.txt
```

![img](img/image21.png)

![img](img/image22.png)

Передадим приложению переменные окружения:

```
export DB_HOST=127.0.0.1
export DB_NAME=virtd
export DB_USER=app
export DB_PASSWORD=QwErTy1234
```

Запустим FastAPI:

```
uvicorn main:app --host 0.0.0.0 --port 5000
```

![img](img/image23.png)

Выполним проверку работы приложения.
Откроем вторую ssh-сессию и в ней выполним curl запрос:

```
curl http://127.0.0.1:5000
```

Получим следующий вывод:

![img](img/image24.png)

При прямом обращении к FastAPI-приложению на порт 5000 приложение выводило предупреждение о неверном способе доступа. Это связано с тем, что приложение ожидает передачу IP-адреса клиента через reverse proxy (nginx/haproxy) с использованием заголовков X-Forwarded-For и X-Real-IP.
При обращении через nginx на порт 8090 приложение корректно определяло IP-адрес клиента.

Теперь добавим управление названием таблицы через ENV переменную.
Сейчас таблица ```requests``` жёстко прописана в main.py. Нужно вынести её имя в переменную окружения.

Остановим ```unicorn`` в первой ssh-сессии:

```
Ctrl + C
```

Остановим MySQL-контейнер:

```
docker stop mysql-venv-test
docker rm mysql-venv-test
```

В файл ```.env``` добавим строку:

```
DB_TABLE="requests"
```


В файл ```main.py``` добавим переменную:

```
db_table = os.environ.get('DB_TABLE', 'requests')
```

Также требуется заменить все упоминания ```requests``` на ```{db_table}```:

```
CREATE TABLE IF NOT EXISTS {db_name}.{db_table} (
```

```
query = INSERT INTO {db_table} (request_date, request_ip) VALUES (%s, %s)"

query = SELECT id, request_date, request_ip FROM {db_table} ORDER BY id DESC LIMIT 50"
```


Пересоберём compose:

```
docker compose up -d --build
```

![img](img/image25.png)

Проверим работу приложения:

```
curl http://127.0.0.1:8090
```

![img](img/image26.png)



## Задание 2

1. Создайте в yandex cloud container registry с именем "test" с помощью "yc tool" . Инструкция
2. Настройте аутентификацию вашего локального docker в yandex container registry.
3. Соберите и залейте в него образ с python приложением из задания №1.
4. Просканируйте образ на уязвимости.
5. В качестве ответа приложите отчет сканирования.


## Решение 2

Для выполнения задания выполним следующие действия.

Установим Yandex Cloud CLI на виртуальную машину:

```
curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash
```

![img](img/image27.png)


Перезайдём в ssh-сессию и проверим, что Yandex Cloud CLI установлен:

```
exit
vagrant ssh
```

```
yc --version
```

Выполним инициализацию CLI:

```
yc init
```

![img](img/image28.png)

В процессе инициализации потребуется указать OAuth token, который можно получить открыв ссылку, указанную в выводе команды инициализации в браузере.

После указания токена ответим еще на несколько вопросов:

![img](img/image29.png)

Создадим Container Registry:

```
yc container registry create --name test
```

![img](img/image30.png)

Настроим Docker для работы с Yandex Registry:

```
yc container registry configure-docker
```

и проверяем настройку:

```
cat ~/.docker/config.json
```

![img](img/image31.png)

Тегируем локальный образ:

```
docker tag shvirtd-fastapi:latest cr.yandex/crpdjb042ijeirepo7lu/shvirtd-fastapi:latest
```

Проверим тег:

```
docker images
```

![img](img/image32.png)

Загрузим образ в registry:

```
docker push cr.yandex/crpdjb042ijeirepo7lu/shvirtd-fastapi:latest
```

![img](img/image33.png)

Проверим, что образ загрузился:

```
yc container image list --registry-name test
```

![img](img/image34.png)

Просканируем образ на уязвимости:

```
yc container image scan crprjc1k240io3k7cnd6
```

После окончания сканирования будет выведен отчёт:

![img](img/image35.png)



## Задание 3

1. Изучите файл "proxy.yaml"
2. Создайте в репозитории с проектом файл compose.yaml. С помощью директивы "include" подключите к нему файл "proxy.yaml".
3. Опишите в файле ```compose.yaml``` следующие сервисы:

```web```. Образ приложения должен ИЛИ собираться при запуске compose из файла Dockerfile.python ИЛИ скачиваться из yandex cloud container registry(из задание №2 со *). Контейнер должен работать в bridge-сети с названием backend и иметь фиксированный ipv4-адрес 172.20.0.5. Сервис должен всегда перезапускаться в случае ошибок. Передайте необходимые ENV-переменные для подключения к Mysql базе данных по сетевому имени сервиса web

```db```. image=mysql:8. Контейнер должен работать в bridge-сети с названием backend и иметь фиксированный ipv4-адрес 172.20.0.10. Явно перезапуск сервиса в случае ошибок. Передайте необходимые ENV-переменные для создания: пароля root пользователя, создания базы данных, пользователя и пароля для web-приложения.Обязательно используйте уже существующий .env file для назначения секретных ENV-переменных!

2. Запустите проект локально с помощью docker compose , добейтесь его стабильной работы: команда ```curl -L http://127.0.0.1:8090``` должна возвращать в качестве ответа время и локальный IP-адрес. Если сервисы не стартуют воспользуйтесь командами: ```docker ps -a```  и ```docker logs <container_name>``` . Если вместо IP-адреса вы получаете информационную ошибку --убедитесь, что вы шлете запрос на порт ```8090```, а не 5000.

3. Подключитесь к БД mysql с помощью команды docker exec -ti <имя_контейнера> mysql -uroot -p<пароль root-пользователя>(обратите внимание что между ключем -u и логином root нет пробела. это важно!!! тоже самое с паролем) . Введите последовательно команды (не забываем в конце символ ; ): show databases; use <имя вашей базы данных(по-умолчанию virtd, как это указано в .env)>; show tables; SELECT * from requests LIMIT 10;. Примечание: таблица в БД создается после первого поступившего запроса к приложению.

4. Остановите проект. В качестве ответа приложите скриншот sql-запроса.


## Решение 3

Часть требований задания №3 была выполнена в процессе выполнения предыдущих заданий и отладки проекта. Ранее были настроены:

 - Docker Compose конфигурация;
 - подключение proxy.yaml через include;
 - сервисы web и db;
 - bridge-сеть backend со статическими IP-адресами;
 - ENV-переменные для подключения к MySQL;
 - запуск приложения через Docker Compose;
 - проверка доступности приложения через curl http://127.0.0.1:8090.


Теперь приступим к части, где требуется проверка работы MySQL.

Зайдём в MySQL:

```
docker exec -ti shvirtd-db mysql -uroot -pYtReWq4321
```

![img](img/image36.png)

Выполним необходимые команды:

```
show databases;
use virtd;
show tables;
SELECT * from requests LIMIT 10;
```

![img](img/image37.png)

Выйдем из MySQL:

```
exit
```

![img](img/image38.png)

Остановим проект:

```
docker compose down
```

![img](img/image39.png)


## Задание 4

1. Запустите в Yandex Cloud ВМ (вам хватит 2 Гб Ram).
2. Подключитесь к Вм по ssh и установите docker.
3. Напишите bash-скрипт, который скачает ваш fork-репозиторий в каталог /opt и запустит проект целиком.
4. Зайдите на сайт проверки http подключений, например(или аналогичный): ```https://check-host.net/check-http``` и запустите проверку вашего сервиса ```http://<внешний_IP-адрес_вашей_ВМ>:8090```. Таким образом трафик будет направлен в ingress-proxy. Трафик должен пройти через цепочки: Пользователь → Internet → Nginx → HAProxy → FastAPI(запись в БД) → HAProxy → Nginx → Internet → Пользователь
5. (Необязательная часть) Дополнительно настройте remote ssh context к вашему серверу. Отобразите список контекстов и результат удаленного выполнения ```docker ps -a```
6. Повторите SQL-запрос на сервере и приложите скриншот и ссылку на fork.

## Решение 4

С помощью web-консоли создадим виртуальную машину в Yandex Cloud:

![img](img/image40.png)

![img](img/image41.png)

Установим Docker на созданной виртуальной машине:

```
sudo apt update
sudo apt install -y ca-certificates curl git gnupg
sudo install -m 0755 -d /etc/apt/keyrings

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update

sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Добавим пользователя в группу docker:

```
sudo usermod -aG docker yc-user
```

Переподключимся к виртуальной машине по ssh и проверим Docker:

```
docker --version
docker compose version
docker ps
```

![img](img/image42.png)

Подготовим требуемый bash-скрипт следующего содержания:

```
#!/bin/bash

set -e

REPO_URL="https://github.com/myachmen/netology-devops-from-zero-homeworks.git"
PROJECT_DIR="/opt/netology-devops-from-zero-homeworks"

echo "=== Установка git ==="
sudo apt update
sudo apt install -y git

echo "=== Клонирование репозитория ==="

if [ -d "$PROJECT_DIR" ]; then
    echo "Каталог уже существует, выполняем обновление"
    cd "$PROJECT_DIR"
    git pull
else
    sudo git clone -b hw-docker-in-practice "$REPO_URL" "$PROJECT_DIR"
    sudo chown -R $USER:$USER "$PROJECT_DIR"
fi

echo "=== Переход в каталог проекта ==="
cd "$PROJECT_DIR/hw-docker-in-practice"

echo "=== Запуск docker compose ==="
docker compose up -d --build

echo "=== Проверка контейнеров ==="
docker compose ps

echo "=== Проверка приложения ==="
curl http://127.0.0.1:8090

echo "=== Готово ==="
```

С очередным коммитом отправим файл скрипта ```deploy.sh``` в репозиторий на GitHub, а затем скачаем его на виртуальную машину:

```
cd /tmp
curl -L -o deploy.sh https://raw.githubusercontent.com/myachmen/netology-devops-from-zero-homeworks/hw-docker-in-practice/deploy.sh
```

![img](img/image43.png)

Cделаем скрипт исполняемым:

```
chmod +x deploy.sh
```

Запустим скрипт:

```
./deploy.sh
```

![img](img/image44.png)

![img](img/image45.png)

Выполним проверку доступности приложения через сайт ```https://check-host.net/check-http```:

![img](img/image46.png)

Снова выполним SQL-запрос на сервере, для проверки того, что запросы от внешнего сайта попали в базу.
Подключимся к MySQL:

```
docker exec -ti shvirtd-db mysql -uroot -p
```

![img](img/image47.png)

В самой MySQL выполним команды:

```
show databases;
use virtd;
show tables;
SELECT * FROM requests ORDER BY id DESC LIMIT 20;
```

![img](img/image48.png)

В последних записях видем большое количество внешних IP адресов, с которых происходила проверка доступности.


Ссылка на fork-репозиторий с выполненным заданием:

https://github.com/myachmen/netology-devops-from-zero-homeworks/tree/hw-docker-in-practice/hw-docker-in-practice


Теперь настроим Docker context:

```
docker context create yc-vm --docker "host=ssh://yc-user@111.88.254.122"
```

Проверим список контекстов:

```
docker context ls
```

![img](img/image49.png)


Проверим удалённое выполнение команды:

```
docker --context yc-vm ps -a
```

![img](img/image50.png)

Команда показала контейнеры, запущенные на удалённой VM в Yandex Cloud.


## Задание 5

1. Напишите и задеплойте на вашу облачную ВМ bash скрипт, который произведет резервное копирование БД mysql в директорию "/opt/backup" с помощью запуска в сети "backend" контейнера из образа ```schnitzler/mysqldump``` при помощи ```docker run ...``` команды. Подсказка: "документация образа."
2. Протестируйте ручной запуск
3. Настройте выполнение скрипта раз в 1 минуту через cron, crontab или systemctl timer. Придумайте способ не светить логин/пароль в git!!
4. Предоставьте скрипт, cron-task и скриншот с несколькими резервными копиями в "/opt/backup"

## Решение 5

На виртуальной машине в Yandex Cloud подготовим директорию для резервного копирования:

```
sudo mkdir -p /opt/backup
sudo chown yc-user:yc-user /opt/backup
```

Создадим файл, в котором мы будем хранить учётные данные: 

```
mkdir -p ~/.backup
nano ~/.backup/mysql.env
```

со следующим содержимым:

```
MYSQL_HOST=shvirtd-db
MYSQL_DATABASE=virtd
MYSQL_USER=root
MYSQL_PASSWORD=YtReWq4321
```

![img](img/image51.png)

Ограничим права на созданный файл:

```
chmod 600 ~/.backup/mysql.env
```

Создадим файл скрипта резервного копирования: 

```
nano ~/mysql_backup.sh
```

со следующим содержимым:

```
#!/bin/bash

set -e

source ~/.backup/mysql.env

BACKUP_DIR="/opt/backup"
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/mysql_${DATE}.sql"
TMP_FILE="${BACKUP_FILE}.tmp"

docker run --rm \
  --network hw-docker-in-practice_backend \
  --entrypoint mysqldump \
  -e MYSQL_PWD="$MYSQL_PASSWORD" \
  schnitzler/mysqldump \
  --host="$MYSQL_HOST" \
  --user="$MYSQL_USER" \
  "$MYSQL_DATABASE" \
  > "$TMP_FILE"

if [ -s "$TMP_FILE" ]; then
    mv "$TMP_FILE" "$BACKUP_FILE"
    echo "Backup created: $BACKUP_FILE"
else
    rm -f "$TMP_FILE"
    echo "Backup failed: empty dump"
    exit 1
fi
```

Выдадим права на выполнение:

```
chmod +x ~/mysql_backup.sh
```

Проверим работу скрипта при запуске вручную:

```
~/mysql_backup.sh
```

![img](img/image52.png)

Проверим, что файл бекапа создался и выведем содержимое файла:

```
ls -lh /opt/backup
head -20 /opt/backup/mysql_*.sql
```

![img](img/image53.png)

Настироим запуск скрипта раз в минуту:

```
crontab -e
```

Добавим строку:

```
* * * * * /home/yc-user/mysql_backup.sh >/dev/null 2>&1
```

Проверим:

```
crontab -l
```

![img](img/image54.png)

![img](img/image55.png)

Через несколько минут проверим директорию для бекапов и увидим, что бекапы выполнябтся стабильно раз в минуту.

![img](img/image56.png)

Что касается вопроса о том, чтобы не светить пароль в Git.
Для исключения хранения чувствительных данных в репозитории Git логин и пароль от базы данных вынесены в отдельный конфигурационный файл ```~/.backup/mysql.env```.
Скрипт резервного копирования не содержит учётных данных в явном виде и получает их из внешнего файла через команду:

```
source ~/.backup/mysql.env
```

Файл mysql.env расположен в домашнем каталоге пользователя на сервере и не входит в состав Git-репозитория, поэтому при публикации кода на GitHub учётные данные не раскрываются.





## Задание 6

Скачайте docker образ hashicorp/terraform:latest и скопируйте бинарный файл /bin/terraform на свою локальную машину, используя dive и docker save. Предоставьте скриншоты действий .

## Решение 6

Скачаем образ Terraform:

```
docker pull hashicorp/terraform:latest
```

![img](img/image57.png)

Проверим, что образ скачался:

```
docker images | grep terraform
```

![img](img/image58.png)

Установим ```dive```:

```
wget --no-check-certificate https://github.com/wagoodman/dive/releases/download/v0.13.1/dive_0.13.1_linux_amd64.deb
sudo apt install -y ./dive_0.13.1_linux_amd64.deb
```

![img](img/image64.png)

Просмотрим образ через ```dive```:

```
dive hashicorp/terraform:latest
```

![img](img/image65.png)

![img](img/image66.png)

Сохраним образ в файл через ```docker save```:

```
docker save hashicorp/terraform:latest -o terraform-image.tar
```

Проверим, что файл сохранился:

```
ls -lh terraform-image.tar
```

![img](img/image59.png)



## Задание 6.1

Добейтесь аналогичного результата, используя docker cp.
Предоставьте скриншоты действий .

## Решение 6.1


Создадим контейнер:

```
docker create --name terraform-copy hashicorp/terraform:latest
```

![img](img/image67.png)

Проверим, что контейнер создался:

```
docker ps -a | grep terraform-copy
```

![img](img/image60.png)

Скопируем ```/bin/terraform``` из контейнера на машину:

```
mkdir -p ~/terraform-bin

docker cp terraform-copy:/bin/terraform ~/terraform-bin/terraform
```

![img](img/image68.png)

Проверим, что файл скопировался:

```
ls -lh ~/terraform-bin/terraform
```

![img](img/image62.png) 


Проверим работу Terraform:

```
~/terraform-bin/terraform version
```

![img](img/image69.png)

Удалиv временный контейнер:

```
docker rm terraform-copy
```










