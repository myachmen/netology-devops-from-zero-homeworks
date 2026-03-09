
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

Проведите атаку на подбор пароля для службы SSH:

**hydra -L users.txt -P pass.txt < ip-адрес > ssh**

	1. Настройка hydra:
		- создайте два файла: users.txt и pass.txt;
		- в каждой строчке первого файла должны быть имена пользователей, второго — пароли. В нашем случае это могут быть случайные строки, но ради эксперимента можете добавить имя и пароль существующего пользователя.
Дополнительная информация по hydra: https://kali.tools/?p=1847.

	2. Включение защиты SSH для Fail2Ban:
		- открыть файл /etc/fail2ban/jail.conf,
		- найти секцию ssh,
		- установить enabled в true.
Дополнительная информация по Fail2Ban:https://putty.org.ru/articles/fail2ban-ssh.html.

*В качестве ответа пришлите события, которые попали в логи Suricata и Fail2Ban, прокомментируйте результат.*


## Решение 2

Для выполнения задания сначала проверим, что Fail2Ban защищает SSH.
Для этого на виртуальной машине defender создадим конфигурационный файл:

![img](img/image9.png)

со следующим содержанием:

![img](img/image10.png)

Перезапустим Fail2Ban:

![img](img/image11.png)

Проверим, что jail активен:

![img](img/image12.png)

Проверим пордробнее:

![img](img/image13.png)

Из обоих выводов видно, что ssh находится под защитой.

Теперь приступим к настройке Hydra на виртуальной машине attacker.

Создадим файл users.txt со следующим содержанием:

![img](img/image14.png)

Создадим файл pass.txt со следующим содержанием:

![img](img/image15.png)

Для запуска атаки на виртуальной машине attacker выполним команду:

![img](img/image16.png)

В выводе команды мы видим сообщение:

```[ERROR] target ssh://192.168.56.10:22/ does not support password authentication (method reply 4).```

Данное сообщение связанно с тем, что виртуальная машина defender настроена на подключение с помощью файла ключа и на ней отключена аутентификация  по паролю.
Это говорит на о полезности такого подхода для защиты подключений по ssh.

Для корректной демонстрации работы Hydra и Fail2Ban включим аутентификацию по паролю на виртуальной машине defender.
Для этого в файл */etc/ssh/sshd_config* добавим следующие строки:

![img](img/image17.png)

Так же произведём корректировку аналогичной настройки в файле *cat /etc/ssh/sshd_config.d/60-cloudimg-settings.conf*.
Изменим *PasswordAuthentication no* на *PasswordAuthentication yes*:

![img](img/image18.png)

Перезапустим SSH:

![img](img/image19.png)

Проверим возможгность подключения по ssh с помощью пароля к виртуальной машине defender с виртуальной машины attacker:

![img](img/image20.png)

Из вывода мы видим, что подбор пароля удался: 

![img](img/image21.png)

Fail2Ban не заблокировал IP атакующей машины в виду того, что он реагирует только на неудачные попытки входа, как правило их должно быть больше 5.

Для демонстрации работы Fail2Ban удалим из файла pass.txt правильный пароль и снова запустим атаку:

![img](img/image22.png)

В выводе мы видим, что соединение было разорвано.

В логах Fail2Ban на виртуальной машине defender мы видим, что IP адрес атакующей машины был забанен:

![img](img/image23.png)