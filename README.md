# Домашнее задание по теме "Teamcity" Ячмень Марк Викторович

## Подготовка к выполнению

1. В Yandex Cloud создайте новый инстанс (4CPU4RAM) на основе образа ```jetbrains/teamcity-server```.
2. Дождитесь запуска teamcity, выполните первоначальную настройку.
3. Создайте ещё один инстанс (2CPU4RAM) на основе образа ```jetbrains/teamcity-agent```. Пропишите к нему переменную окружения ```SERVER_URL: "http://<teamcity_url>:8111"```.
4. Авторизуйте агент.
5. Сделайте fork [репозитория](https://github.com/aragastmatb/example-teamcity).
6. Создайте VM (2CPU4RAM) и запустите [playbook](https://github.com/netology-code/mnt-homeworks/tree/MNT-video/09-ci-05-teamcity/infrastructure).

## Выполнение подготовки

На текущий момент в Yandex Cloud отсутствует требуемый образ, поэтому подготовим всю необходимую инфраструктуру вручную.

Создадим виртуальную машину с TeamCity Server.

![img](img/image1.png)

![img](img/image2.png)

![img](img/image3.png)

После окончания процесса создания сервера подключимся к нему по shh и установим все имеющиеся обновления.

Установим Docker из официального репозитория.
Установим необходимые пакеты:

```
sudo apt install -y ca-certificates curl gnupg
```

Создадим каталог для ключей:

```
sudo install -m 0755 -d /etc/apt/keyrings
```

Добавим GPG-ключ Docker:

```
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
```

Назначим необходимые права:

```
sudo chmod a+r /etc/apt/keyrings/docker.gpg
```

Добавим репозиторий Docker:

```
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

Обновим список пакетов и установим Docker:

```
sudo apt update

sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Проверим, что Docker установился корректно:

```
docker --version
docker compose version
sudo docker run hello-world
```

![img](img/image4.png)

Добавим пользователя ```ubuntu``` в группу ```docker```, чтобы не использовать ```sudo``` для каждой команды:

```
sudo usermod -aG docker ubuntu
```

Перед установкой контейнера Teamcity Server подготовим структуру каталогов:

```
sudo mkdir -p /opt/teamcity
cd /opt/teamcity
sudo mkdir data logs
sudo chown -R ubuntu:ubuntu /opt/teamcity
ls -l /opt/teamcity
```

![img](img/image5.png)

Подготовим файл ```compose.yaml``` следующего содержания:

```
services:
  teamcity:
    image: jetbrains/teamcity-server:latest

    container_name: teamcity-server

    restart: unless-stopped

    ports:
      - "8111:8111"

    volumes:
      - ./data:/data/teamcity_server/datadir
      - ./logs:/opt/teamcity/logs
```

Запустим контейнер Teamcity Server:

```
docker compose up -d
```
![img](img/image6.png)

Проверим состояние контейнера:

```
docker compose ps
```

![img](img/image7.png)

Локально проверим порт 8111:

```
curl -I http://localhost:8111
8111/tcp -> 0.0.0.0:8111
```

![img](img/image8.png)

Откроем порт 8111 в Yandex Cloud:

![img](img/image9.png)

Проверим, что порт доступен снаружи. Для этого в браузере откроем адрес ```http://158.160.168.126:8111``` :

![img](img/image10.png)

Приступим к настройке TeamCity Server. Для работы приложения выберем Internal БД:

![img](img/image11.png)

Примем лицензионное соглашение:

![img](img/image12.png)

![img](img/image13.png)

Создадим аккаунт администратора:

![img](img/image14.png)

Войдем в приложение под созданным аккаунтом:

![img](img/image15.png)

Создадим виртуальную машину с TeamCity Agent:

![img](img/image16.png)

![img](img/image17.png)

![img](img/image18.png)

Подключимся ук созданной виртуальной машине ```teamcity-agent``` и выполним те же шаги, что и на первой виртуальной машине (установка обновлений и установка Docker).

Перед установкой контейнера Teamcity Agent подготовим структуру каталогов:

```
sudo mkdir -p /opt/teamcity-agent/{conf,logs,work,temp,system}
sudo chown -R ubuntu:ubuntu /opt/teamcity-agent
```

Подготовим файл ```compose.yaml``` следующего содержания:

```
services:
  teamcity-agent:
    image: jetbrains/teamcity-agent:latest
    container_name: teamcity-agent

    restart: unless-stopped

    environment:
      SERVER_URL: "http://10.130.0.8:8111"
      AGENT_NAME: "yc-agent"

    volumes:
      - /opt/teamcity-agent/conf:/data/teamcity_agent/conf
      - /opt/teamcity-agent/logs:/opt/buildagent/logs
      - /opt/teamcity-agent/work:/opt/buildagent/work
      - /opt/teamcity-agent/temp:/opt/buildagent/temp
      - /opt/teamcity-agent/system:/opt/buildagent/system

      - /var/run/docker.sock:/var/run/docker.sock

    privileged: true
```
    
Запустим контейнер Teamcity Agent:

```
docker compose up -d
```

Проверим состояние контейнера:

```
docker compose ps
```

![img](img/image19.png)

Проверим на TeamCity Server, что агент виден:

![img](img/image20.png)

Авторизуем агента нажав кнопку ```Authorize...```:

![img](img/image21.png)

Проверим, что агент готов к работе, для этого перейдём на вкладку ```Parameters```:

![img](img/image22.png)

Создадим fork учебного проекта:

![img](img/image23.png)

Создадим новый проект в TeamCity:

![img](img/image24.png)

Подключим к проекту репозиторий:

![img](img/image25.png)

![img](img/image26.png)

![img](img/image27.png)

Откроем созданный проект:

![img](img/image28.png)

Создадим Build step:

![img](img/image29.png)

![img](img/image30.png)

Запустим первую сборку, нажав кнопку ```Run``` в интерфейсе TeamCity Server:

![img](img/image31.png)

Первая тестовая сборка проекта выполнена успешно. TeamCity получил исходный код из репозитория GitHub, передал задачу агенту ```yc-agent```, выполнил Maven-команду clean test и успешно завершил сборку. Все 5 автоматических тестов были пройдены без ошибок.