
# Домашнее задание по теме "Защита сети" Ячмень Марк Викторович

## Подготовка к выполнению заданий
 1. Подготовка защищаемой системы:
	- установите Suricata,
	- установите Fail2Ban.

 2. Подготовка системы злоумышленника: установите nmap и thc-hydra либо скачайте и установите Kali linux.

Обе системы должны находится в одной подсети.


## Задание 1

Проведите разведку системы и определите, какие сетевые службы запущены на защищаемой системе:

sudo nmap -sA < ip-адрес >

sudo nmap -sT < ip-адрес >

sudo nmap -sS < ip-адрес >

sudo nmap -sV < ip-адрес >

По желанию можете поэкспериментировать с опциями: https://nmap.org/man/ru/man-briefoptions.html.

*В качестве ответа пришлите события, которые попали в логи Suricata и Fail2Ban, прокомментируйте результат.*



## Решение 1

Для выполнения задания выполним следующие действия.

С помощью Vagrant создадим две виртуальных машины: защищаемую(defender) и атакующую(attacker).
Для этого создадим папку проекта и внутри неё файл Vagrantfile со следующим содержимым:

```
Vagrant.configure("2") do |config|

  config.vm.box = "ubuntu/jammy64"

  # Defender
  config.vm.define "defender" do |defender|
    defender.vm.hostname = "defender"
    defender.vm.network "private_network", ip: "192.168.56.10"

    defender.vm.provider "virtualbox" do |vb|
      vb.memory = 2048
      vb.cpus = 2
    end

    defender.vm.provision "shell", inline: <<-SHELL
      apt update
      apt install -y suricata fail2ban openssh-server
      systemctl enable suricata
      systemctl start suricata
      systemctl enable fail2ban
      systemctl start fail2ban
    SHELL
  end

  # Attacker
  config.vm.define "attacker" do |attacker|
    attacker.vm.hostname = "attacker"
    attacker.vm.network "private_network", ip: "192.168.56.11"

    attacker.vm.provider "virtualbox" do |vb|
      vb.memory = 1024
    end

    attacker.vm.provision "shell", inline: <<-SHELL
      apt update
      apt install -y nmap hydra
    SHELL
  end

end
```
После этого перейдём в консоли PowerShell перейдём в папку проекта и выполним команду:

![img](img/image1.png)

После окончания выполнения команды в VirtualBox появятся две виртуальных машины:

![img](img/image2.png)

Подключимся к атакующей машине и начнём выполнение команд.

Выполним команду ```sudo nmap -sA 192.168.56.10```

![img](img/image4.png)

Полученный вывод 

```All 1000 scanned ports on 192.168.56.10 are unfiltered```

означает, что ACK-скан используется для проверки фильтрации firewall:
 - ```unfiltered``` - пакеты проходят
 - firewall не блокирует соединения.

Выполним команду ```sudo nmap -sT 192.168.56.10```

![img](img/image5.png)

Полученный вывод 

```
PORT   STATE SERVICE
22/tcp open  ssh
```

означает, что:
 - порт 22 открыт
 - работает сервис SSH

Выполним команду ```sudo nmap -sS 192.168.56.10```

![img](img/image6.png)

Это half-open scan.
Вывод этой команды будет таким же, как и у предыдущей, но команда работает иначе:
 - отправляется SYN
 - получаем SYN/ACK
 - соединение не завершается

Поэтому его часто называют:

stealth scan

Выполним команду ```sudo nmap -sV 192.168.56.10```

![img](img/image7.png)

В выводе мы видим:

```
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 8.9p1 Ubuntu 3ubuntu0.13 (Ubuntu Linux; protocol 2.0)
```
т.е. кроме открытого порта мы смогли определить еще и версию операционной системы на защищаемой виртуальной машине.

Подключимся к защищаемой машине и запустим команду просмотра логов Suricata:

![img](img/image8.png)

В логах мы видим записи типа:

```
src_ip: 192.168.56.11
dest_ip: 192.168.56.10
event_type: flow
proto: TCP
```

это свидетельствует о том, что IDS анализирует сетевой трафик и фиксирует попытки подключения к различным портам.


## Задание 2

Что нужно сделать:

1. Запушьте репозиторий на GitLab, изменив origin. Это изучалось на занятии по Git.
2. Создайте .gitlab-ci.yml, описав в нём все необходимые, на ваш взгляд, этапы.

В качестве ответа в шаблон с решением добавьте:

* файл gitlab-ci.yml для своего проекта или вставьте код в соответствующее поле в шаблоне;
* скриншоты с успешно собранными сборками.


## Решение 2

Для выполнения задания подготовим локальный репозиторий.
Для этого в консоли выполним команды:

![img](img/image19.png)

В созданной папке создадим файл .gitlab-ci.yml со следующим содержанием:

![img](img/image20.png)

Теперь выполним push локального репозитория в репозиторий GitLab:

![img](img/image21.png)

![img](img/image22.png)

После этого перейдём в web-интерфейс GitLab и увидим, что job выполнился:

![img](img/image23.png)

В логах можем увидеть сообщение об успешном запуске:

![img](img/image24.png)


