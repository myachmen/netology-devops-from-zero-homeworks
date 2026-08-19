# Домашнее задание по теме "Средство визуализации Grafana" Ячмень Марк Викторович

## Задание 1

Вам необходимо поднять в докере и связать между собой:

- elasticsearch (hot и warm ноды);
- logstash;
- kibana;
- filebeat.

Logstash следует сконфигурировать для приёма по tcp json-сообщений.

Filebeat следует сконфигурировать для отправки логов docker вашей системы в logstash.

В директории help находится манифест docker-compose и конфигурации filebeat/logstash для быстрого 
выполнения этого задания.

Результатом выполнения задания должны быть:

- скриншот `docker ps` через 5 минут после старта всех контейнеров (их должно быть 5);
- скриншот интерфейса kibana;
- docker-compose манифест (если вы не использовали директорию help);
- ваши yml-конфигурации для стека (если вы не использовали директорию help).

## Решение 1

Для выполнения задания выполним следующие действия.

Подготовим виртуальную машину с помощью Vagrant. В директории с Vagrant проектом создадим Vagrant файл следующего содержания:

```
Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/jammy64"
  config.vm.hostname = "elk-lab"

  config.vm.network "forwarded_port", guest: 5601, host: 5601
  config.vm.network "forwarded_port", guest: 9200, host: 9200

  config.vm.provider "virtualbox" do |vb|
    vb.name = "elk-lab"
    vb.memory = 6144
    vb.cpus = 4
  end
end
```

Запустим виртуальную машину ```elk-lab```:

```
vagrant up
```
![img](img/image1.png)

Подключимся к виртуальной машине по ssh и установим Docker:

```
vagrant ssh
sudo apt install -y docker.io docker-compose-v2
```

После установки включим Docker:

```
sudo systemctl enable --now docker
```

Добавим пользователя vagrant в группу docker:

```
sudo usermod -aG docker vagrant
```

Проверим установку:

```
docker --version
docker compose version
systemctl is-active docker
docker ps
```

![img](img/image2.png)

Склонируем репозиторий из задания на виртуальную машину:

```
git clone --branch MNT-video https://github.com/netology-code/mnt-homeworks.git
```

![img](img/image3.png)

Перед запуском Elasticsearch увеличим системный параметр vm.max_map_count до рекомендуемого значения 262144: 

```
sudo sysctl -w vm.max_map_count=262144
```

![img](img/image4.png)


Этот параметр определяет максимальное количество областей виртуальной памяти (memory-mapped areas), которое может использовать один процесс. Elasticsearch активно использует механизм mmap при работе с индексами, поэтому недостаточное значение может привести к ошибке запуска Elasticsearch.

Перейдём в директорию ~/mnt-homeworks/10-monitoring-04-elk/help и запустим Docker-контейнеры:

```
cd ~/mnt-homeworks/10-monitoring-04-elk/help
docker compose up -d
```

![img](img/image5.png)

Проверим состояние контейнеров:

```
docker ps
docker compose ps
```

![img](img/image6.png)

В браузере перейдём по адресу ```http://localhost:5601/``` для того чтобы попасть в web-интерфейс Kibana:

![img](img/image7.png)



## Задание 2

Перейдите в меню [создания index-patterns  в kibana](http://localhost:5601/app/management/kibana/indexPatterns/create) и создайте несколько index-patterns из имеющихся.

Перейдите в меню просмотра логов в kibana (Discover) и самостоятельно изучите, как отображаются логи и как производить поиск по логам.

В манифесте директории help также приведенно dummy-приложение, которое генерирует рандомные события в stdout-контейнера.
Эти логи должны порождать индекс logstash-* в elasticsearch. Если этого индекса нет — воспользуйтесь советами и источниками из раздела «Дополнительные ссылки» этого задания.

## Решение 2

В web-интерфейсе Kibana перейдём по ссылке ```Explore on my own```.
Затем перейдём по ссылке ```Stack Management```:

![img](img/image8.png)

Далее перейдём по ссылке ```Data Views```:

![img](img/image9.png)

Нажмём на кнопку ```Createdata view```:

![img](img/image10.png)

На открывшейся странице укажем следующие данные:

```
Name: logstash
Index pattern: logstash-*
Timestamp field: @timestamp
```

![img](img/image11.png)

Сохраним настройки нажатием на кнопку ```Save data ...```.

![img](img/image12.png)

Для просмотра логов через Discover в левом меню перейдём по ```Analytics → Discover```:

![img](img/image13.png)

![img](img/image14.png)

Проверим фильтрацию логов. Для этого в строке поиска введём:

```
message.keyword : "ERROR:root:OH NO!!!!!!"
```

и увидим отфильтрованные записи о событиях:

![img](img/image15.png)

Создадим ещё один Data View со следующими параметрами:

```
Name: logstash-2026
Index pattern: logstash-2026.*
Timestamp field: @timestamp
```

![img](img/image16.png)

В Kibana созданы Data Views для доступа к индексам Elasticsearch:

```logstash``` с шаблоном ```logstash-*```;
```logstash-2026``` с более узким шаблоном ```logstash-2026.*```.

В качестве временного поля используется @timestamp. Data View logstash установлен по умолчанию. Созданные представления позволяют обращаться к индексам Elasticsearch по различным шаблонам.
