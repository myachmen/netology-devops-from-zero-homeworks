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


