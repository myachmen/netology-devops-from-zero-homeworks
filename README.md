
# Домашнее задание по теме "GitLab" Ячмень Марк Викторович




## Задание 1

**Elasticsearch**

Установите и запустите Elasticsearch, после чего поменяйте параметр cluster_name на случайный.

*Приведите скриншот команды 'curl -X GET 'localhost:9200/_cluster/health?pretty', сделанной на сервере с установленным Elasticsearch. Где будет виден нестандартный cluster_name.*



## Решение 1

Для выполнения задания выполним следующие действия.

Установим OpenJDK, т.к. Elasticsearch требует Java:

![img](img/image1.png)

![img](img/image2.png)

Добавим репозиторий Elastic:

![img](img/image3.png)

Наблюдаем, что репозитроий Elastic недоступен, скдя по всему из-за географических ограничений.
Переключим сервер на работу через VPN и проверим доступность репозитория ещё раз:

![img](img/image4.png)

Установим Elasticsearch:

![img](img/image5.png)

![img](img/image6.png)

Запустим Elastic и включим его автозапуск:

![img](img/image7.png)

Для изменения параметра cluster_name выполним следующие действия.

Остановим службу Elasticsearch:

![img](img/image8.png)

Откроем конфигурационный файл для редактирования:

![img](img/image9.png)

Найдём, раскомментируем и изменим строку *cluster.name: hw-elk* :

![img](img/image10.png)