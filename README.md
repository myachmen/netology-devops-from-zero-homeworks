
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


