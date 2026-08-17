# Домашнее задание по теме "Системы мониторинга" Ячмень Марк Викторович

## Задание 1

1. Используя директорию help внутри этого домашнего задания, запустите связку prometheus-grafana.
2. Зайдите в веб-интерфейс grafana, используя авторизационные данные, указанные в манифесте docker-compose.
3. Подключите поднятый вами prometheus, как источник данных.
4. Решение домашнего задания — скриншот веб-интерфейса grafana со списком подключенных Datasource.

## Решение 1

Для выполнения задания выполним следующие действия.

Подготовим виртуальную машину с помощью Vagrant. В директории с Vagrant проектом создадим Vagrant файл следующего содержания:

```
Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/jammy64"
  config.vm.hostname = "grafana-lab"

  config.vm.network "forwarded_port", guest: 3000, host: 3000
  config.vm.network "forwarded_port", guest: 9090, host: 9090

  config.vm.provider "virtualbox" do |vb|
    vb.name = "grafana-lab"
    vb.memory = 2048
    vb.cpus = 2
  end
end
```

Запустим виртуальную машину ```grafana-lab```:

```
vagrant up
```
![img](img/image1.png)

Подключимся к виртуальной машине по ssh и установим Docker:

```
vagrant ssh
sudo apt install -y docker.io docker-compose-v2
```

Проверим установку:

```
docker --version
docker compose version

sudo systemctl status docker --no-pager
```

![img](img/image2.png)

Добавим пользователя ```vagrant``` в группу ```docker```:

```
sudo usermod -aG docker vagrant
```

Установим Git:

```
sudo apt install -y git
```

![img](img/image3.png)

Склонируем репозиторий из задания на виртуальную машину:

```
git clone --branch MNT-video https://github.com/netology-code/mnt-homeworks.git
```

![img](img/image4.png)

Переёдём в директорию ```~/mnt-homeworks/10-monitoring-03-grafana/help``` и запустим Docker-контиейнеры:

```
~/mnt-homeworks/10-monitoring-03-grafana/help
docker compose up -d
```

![img](img/image5.png)

Проверим состояние контейнеров:

```
docker ps
```

![img](img/image6.png)

В браузере на локальной операционной системе перейдём по адресу ```http://localhost:3000```, для того, чтобы отобразить web-интерфейс Grafana:

![img](img/image7.png)

Войдём в Grafana с использованием стандартных креденшелов:

```
Login: admin
Password: admin
```

Добавим Prometheus как источник данных.
Для этого пройдём по следующему пути:

```
Configuration → Data Sources → Add data source → Prometheus
```

![img](img/image8.png)

![img](img/image9.png)

На странице конфигурации укажем адрес сервера Prometheus:

```
http://prometheus:9090
```

и сохраним изменения:

![img](img/image10.png)

![img](img/image11.png)

![img](img/image12.png)


## Задание 2

Изучите самостоятельно ресурсы:

1. [PromQL tutorial for beginners and humans](https://valyala.medium.com/promql-tutorial-for-beginners-9ab455142085).
1. [Understanding Machine CPU usage](https://www.robustperception.io/understanding-machine-cpu-usage).
1. [Introduction to PromQL, the Prometheus query language](https://grafana.com/blog/2020/02/04/introduction-to-promql-the-prometheus-query-language/).

Создайте Dashboard и в ней создайте Panels:

- утилизация CPU для nodeexporter (в процентах, 100-idle);
- CPULA 1/5/15;
- количество свободной оперативной памяти;
- количество места на файловой системе.

Для решения этого задания приведите promql-запросы для выдачи этих метрик, а также скриншот получившейся Dashboard.


## Решение 2

Создадим Dashboard и панель CPU.
Для этого в интерфейсе Grafana пройдём по пути:

```
+ → Dashboard → Add new panel
```

![img](img/image13.png)

![img](img/image14.png)

В поле запроса введём следующее:

```
100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)
```

![img](img/image15.png)


Теперь приступим к настройке панели.
В поле ```Panel title``` укажем название:

```
CPU Utilization
```

![img](img/image16.png)

На вкладке ```Field``` в параметре ```Unit``` выберем:

```
Percent (0-100)
```

![img](img/image17.png)

В редакторе запроса в параметре ``Legend``` укажем:

```
CPU Usage
```

![img](img/image18.png)


Временной интервал изменим на ```Last 15 minutes```:

![img](img/image19.png)

Сохраним результат нажатием кнопки ```Apply```:

![img](img/image20.png)

Изменим имя Dashboard -а на ```Grafana Homework```:

![img](img/image21.png)

![img](img/image22.png)

Сохраним настройки нажатием кнопки ```Save dashboard```.

Аналогичным образом настроим следующую панель ```Load Average```.

В панели будет использовано три запроса:

```
node_load1
node_load5
node_load15
```
и соответствующие ```Legend```:

```
Load 1m
Load 5m
Load 15m
```

для вывода информации за 1, 5 и 15 минут соответственно:

![img](img/image23.png)

![img](img/image24.png)

Аналогичным образом настроим следующую панель ```Free Memory```.

В панели будет использован запрос:

```
node_memory_MemFree_bytes
```

и ```Legend```:

```
Free Memory
```

На вкладке ```Field``` в параметре ```Unit``` выберем:

```
bytes (IEC)
```

![img](img/image25.png)

![img](img/image26.png)

![img](img/image27.png)


Аналогичным образом настроим следующую панель ```Free Disk Space```.

В панели будет использован запрос:

```
node_filesystem_free_bytes{mountpoint="/"}
```

и ```Legend```:

```
Free Space
```

На вкладке ```Field``` в параметре ```Unit``` выберем:

```
bytes (IEC)
```

![img](img/image28.png)

![img](img/image29.png)

![img](img/image30.png)


После всех произведённых настроек Dashboard будет выглядеть следующим образом:

![img](img/image31.png)
