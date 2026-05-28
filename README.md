netplan ьм
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