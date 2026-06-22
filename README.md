# Домашнее задание по теме "Управляющие конструкции в коде Terraform" Ячмень Марк Викторович

## Задание 1

1. Изучите проект.
2. Инициализируйте проект, выполните код.

Приложите скриншот входящих правил «Группы безопасности» в ЛК Yandex Cloud .

## Решение 1

Для выполнения задания выполним следующие действия.

Скопируем код проекта в наш репозиторий:

```
git clone --depth 1 https://github.com/netology-code/ter-homeworks.git temp-ter-homeworks
Copy-Item -Recurse .\temp-ter-homeworks\03\src\* .\terraform\
Remove-Item -Recurse -Force .\temp-ter-homeworks
cd .\terraform
dir
```

![img](img/image1.png)


После изучения файлов проекта подготовим файл с личными параметрами:

```
Copy-Item .\personal.auto.tfvars_example .\personal.auto.tfvars
```

Для заполнения файла выведем в консоль параметры из Yandex Cloud:

```
yc config list
```

![img](img/image2.png)

Создадим новый IAM-токен:

```
yc iam create-toke
```

![img](img/image3.png)

Проверим, что файл ```personal.auto.tfvars``` не попадает в репозиторий на Github:

```
git status --ignored
```

![img](img/image4.png)

Выполним инициализацию и проверку конфигурации:

```
terraform init
terraform validate
terraform plan
```

![img](img/image5.png)

![img](img/image6.png)

![img](img/image7.png)

Применим конфигурацию:

```
terraform apply
```

![img](img/image8.png)

После применения конфигурации мы видим, что в консоли Yanbndex Cloud появилась новая сеть ```develop```:

![img](img/image9.png)

![img](img/image10.png)

![img](img/image11.png)



## Задание 2

1. Создайте файл count-vm.tf. Опишите в нём создание двух одинаковых ВМ web-1 и web-2 (не web-0 и web-1) с минимальными параметрами, используя мета-аргумент count loop. Назначьте ВМ созданную в первом задании группу безопасности.(как это сделать узнайте в документации провайдера yandex/compute_instance )
2. Создайте файл for_each-vm.tf. Опишите в нём создание двух ВМ для баз данных с именами "main" и "replica" разных по cpu/ram/disk_volume , используя мета-аргумент for_each loop. Используйте для обеих ВМ одну общую переменную типа:

```
variable "each_vm" {
  type = list(object({  vm_name=string, cpu=number, ram=number, disk_volume=number }))
}
```

При желании внесите в переменную все возможные параметры. 
3. ВМ, описанные в файле count-vm.tf, должны создаваться после ВМ, описанных в файле for_each-vm.tf. 
4. Используйте функцию file в local-переменной для считывания ключа ~/.ssh/id_rsa.pub и его последующего использования в блоке metadata, взятому из ДЗ 2. 
5. Инициализируйте проект, выполните код.


## Решение 2