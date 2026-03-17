# Домашнее задание по теме "Инструменты Git" Ячмень Марк Викторович


## Задание 1. Создать и настроить репозиторий для дальнейшей работы на курсе

Полный текст задания можно посмотреть [в репозитории Netology](https://github.com/netology-code/sysadm-homeworks/blob/devsys10/02-git-04-tools/README.md).


## Решение 1

Для выполнения задания выполним следующие действия.

Склонируем репозиторий, ссылка на который указана в задании.
Для этого выполним команду ```git clone https://github.com/hashicorp/terraform.git```:

![img](img/image1.png)

Проверим, что история и теги доступны. Выполним команды ```git log --oneline -n 5``` и ```git tag | tail```:

![img](img/image2.png)

Найдем полный хеш коммита ```aefea```. Выполним команды ```git log --oneline | grep aefea``` и ```git rev-parse aefea```:

![img](img/image3.png)

Полный хеш коммита ```aefea``` имеет значение **aefead2207ef7e2aa5dc81a34aedf0cad4c32545** и комментарий **Update CHANGELOG.md**.

Определим тег для коммита ```85024d3```. Выполним команду ```git describe --tags 85024d3```:

![img](img/image4.png)

Для коммита ```85024d3``` определился тег **v0.12.23**.

Найдём родителей коммита ```b8d720```. Выполним команду ```git show --pretty=raw --no-patch b8d720```:

![img](img/image5.png)

Из вывода видно, что коммит имеет двух родителей:
- 56cd7859e05c36c06b56d013b55a252d0bb7e158
- 9ea88f22fc6269854151c571162c5bcf958bee2b

Это merge-коммит.

Выведем коммиты между тегами ```v0.12.23``` и ```v0.12.24```. Выполним команду ```git log --pretty=format:"%h %s" v0.12.23..v0.12.24```:

![img](img/image6.png)

Коммиты между тегами ```v0.12.23``` и ```v0.12.24```:

 - b14b74c493 [Website] vmc provider links  
 - 3f235065b9 Update CHANGELOG.md  
 - 6ae64e247b registry: Fix panic when server is unreachable  
 - 5c619ca1ba website: Remove links to the getting started guide's old location  
 - 06275647e2 Update CHANGELOG.md  
 - d5f9411f51 command: Fix bug when using terraform login on Windows  
 - 4b6d06cc5d Update CHANGELOG.md  
 - dd01a35078 Update CHANGELOG.md  
 - 225466bc3e Cleanup after v0.12.23 release
 
Найдём коммит создания функции ```providerSource```. Сначала найдём фай выполнив команду ```git grep "func providerSource"```:

![img](img/image7.png)

По найденному файлу найдём историю. Выполним команду ```git log --reverse -S "func providerSource" -- provider_source.go```:

![img](img/image8.png)

Из вывода понятно, что искомый коммит это:

 - 8c928e83589d90a031f811fae52a81be7153e82f — main: Consult local directories as potential mirrors of providers.
 
Найдём все коммиты, в которых была изменена функция ```globalPluginDirs```. Выполним команду ````git grep "func globalPluginDirs"```:
 
![img](img/image9.png)

Коммиты в которых была изменена функция ```globalPluginDirs```:

 - 7c4aeac5f30aed09c5ef3198141b033eea9912be — stacks: load credentials from config file on startup (#35952)
 - 65c4ba736375607b6af6c035972f7f151232b6c6 — Remove terraform binary
 - 125eb51dc40b049b38bf2ed11c32c6f594c8ef96 — Remove accidentally-committed binary
 - 8364383c359a6b738a436d1b7745ccdce178df47 — Push plugin discovery down into command package.
 
Определим автора функции ```synchronizedWriters```. Выполним команду ```git grep "func synchronizedWriters"``` для поиска коммитов где встречается функция:   

![img](img/image10.png)

Найдём самый первый коммит. Выполним команду ```git log --reverse -S "synchronizedWriters"```:

![img](img/image11.png)

Первый коммит в списке это момент создания функции.

Так же мы види автора коммита: **Martin Atkins <mart@degeneration.co.uk>**.






