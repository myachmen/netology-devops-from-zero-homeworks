# Домашнее задание по теме "Создание собственных модулей" Ячмень Марк Викторович

## Подготовка к выполнению

1. Создайте пустой публичный репозиторий в своём любом проекте: `my_own_collection`.
2. Скачайте репозиторий Ansible: `git clone https://github.com/ansible/ansible.git` по любому, удобному вам пути.
3. Зайдите в директорию Ansible: `cd ansible`.
4. Создайте виртуальное окружение: `python3 -m venv venv`.
5. Активируйте виртуальное окружение: `. venv/bin/activate`. Дальнейшие действия производятся только в виртуальном окружении.
6. Установите зависимости `pip install -r requirements.txt`.
7. Запустите настройку окружения `. hacking/env-setup`.
8. Если все шаги прошли успешно — выйдите из виртуального окружения `deactivate`.
9. Ваше окружение настроено. Чтобы запустить его, нужно находиться в директории `ansible` и выполнить конструкцию `. venv/bin/activate && . hacking/env-setup`.


## Основная часть

Ваша цель — написать собственный module, который вы можете использовать в своей role через playbook. Всё это должно быть собрано в виде collection и отправлено в ваш репозиторий.

**Шаг 1.** В виртуальном окружении создайте новый `my_own_module.py` файл.

**Шаг 2.** Наполните его содержимым:

```python
#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: my_test

short_description: This is my test module

# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"

description: This is my longer description explaining my test module.

options:
    name:
        description: This is the message to send to the test module.
        required: true
        type: str
    new:
        description:
            - Control to demo if the result of this module is changed or not.
            - Parameter description can be a list as well.
        required: false
        type: bool
# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
extends_documentation_fragment:
    - my_namespace.my_collection.my_doc_fragment_name

author:
    - Your Name (@yourGitHubHandle)
'''

EXAMPLES = r'''
# Pass in a message
- name: Test with a message
  my_namespace.my_collection.my_test:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_namespace.my_collection.my_test:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_namespace.my_collection.my_test:
    name: fail me
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
original_message:
    description: The original name param that was passed in.
    type: str
    returned: always
    sample: 'hello world'
message:
    description: The output message that the test module generates.
    type: str
    returned: always
    sample: 'goodbye'
'''

from ansible.module_utils.basic import AnsibleModule


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        name=dict(type='str', required=True),
        new=dict(type='bool', required=False, default=False)
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # changed is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        module.exit_json(**result)

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    result['original_message'] = module.params['name']
    result['message'] = 'goodbye'

    # use whatever logic you need to determine whether or not this module
    # made any modifications to your target
    if module.params['new']:
        result['changed'] = True

    # during the execution of the module, if there is an exception or a
    # conditional state that effectively causes a failure, run
    # AnsibleModule.fail_json() to pass in the message and the result
    if module.params['name'] == 'fail me':
        module.fail_json(msg='You requested this to fail', **result)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
```
Или возьмите это наполнение [из статьи](https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_general.html#creating-a-module).

**Шаг 3.** Заполните файл в соответствии с требованиями Ansible так, чтобы он выполнял основную задачу: module должен создавать текстовый файл на удалённом хосте по пути, определённом в параметре `path`, с содержимым, определённым в параметре `content`.

**Шаг 4.** Проверьте module на исполняемость локально.

**Шаг 5.** Напишите single task playbook и используйте module в нём.

**Шаг 6.** Проверьте через playbook на идемпотентность.

**Шаг 7.** Выйдите из виртуального окружения.

**Шаг 8.** Инициализируйте новую collection: `ansible-galaxy collection init my_own_namespace.yandex_cloud_elk`.

**Шаг 9.** В эту collection перенесите свой module в соответствующую директорию.

**Шаг 10.** Single task playbook преобразуйте в single task role и перенесите в collection. У role должны быть default всех параметров module.

**Шаг 11.** Создайте playbook для использования этой role.

**Шаг 12.** Заполните всю документацию по collection, выложите в свой репозиторий, поставьте тег `1.0.0` на этот коммит.

**Шаг 13.** Создайте .tar.gz этой collection: `ansible-galaxy collection build` в корневой директории collection.

**Шаг 14.** Создайте ещё одну директорию любого наименования, перенесите туда single task playbook и архив c collection.

**Шаг 15.** Установите collection из локального архива: `ansible-galaxy collection install <archivename>.tar.gz`.

**Шаг 16.** Запустите playbook, убедитесь, что он работает.

**Шаг 17.** В ответ необходимо прислать ссылки на collection и tar.gz архив, а также скриншоты выполнения пунктов 4, 6, 15 и 16.


## Решение 1

Для выполнения задания выполним следующие действия.

Создадим на GitHub отдельный репозиторий для собственных коллекций:

![img](img/image1.png)

![img](img/image2.png)

Подготовим виртуальные машины с помощью Vagrant. В директории с Vagrant проектом создадим Vagrant файл следующего содержания:

```
Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/jammy64"
  config.vm.hostname = "ansible-dev"

  config.vm.provider "virtualbox" do |vb|
    vb.name = "ansible-dev"
    vb.memory = 4096
    vb.cpus = 2
  end
end
```

Запустим виртуальную машину:

```
vagrant up
```

![img](img/image3.png)

Подключимся к созданной виртуальной машине:

```
vagrant ssh
```

и установим необходимые пакеты:

```
sudo apt install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    git \
    curl \
    jq \
    tree
```

Проверим версии пакетов:

```
python3 -m pip --version
python3 -m venv --help | head -n 1
```
![img](img/image4.png)

Настроим Git:

```
git config --global user.name "Mark Yachmen"
git config --global user.email "m.yachmen@gmail.com"

git config --global --list
```

![img](img/image5.png)

Приступим к подготовке окружения.
Создадим рабочую директорию:

```
mkdir -p ~/ansible-module-work
cd ~/ansible-module-work
```

Склонируем исходный репозиторий Ansible:

```
git clone https://github.com/ansible/ansible.git
cd ansible
```

и проверим результат:

```
cd ~/ansible-module-work/ansible

git status
git branch --show-current
```

![img](img/image6.png)

![img](img/image7.png)

Создадим ```Python virtual environment```:

```
python3 -m venv venv
source venv/bin/activate
```

![img](img/image8.png)

Обновим инструменты Python:

```
python -m pip install --upgrade pip setuptools wheel
```

![img](img/image9.png)

Установим зависимости Ansible:

```
python -m pip install -r requirements.txt
```

![img](img/image10.png)

Подключим ```hacking/env-setup```:

```
source hacking/env-setup
```

![img](img/image11.png)

Выполним тестовый запуск:

```
ansible localhost -m ping -c local
```

![img](img/image12.png)

Создадим рабочий каталог для собственного модуля:

```
mkdir -p ~/ansible-module-work/my-module
cd ~/ansible-module-work/my-module
```

Создадим Python файл следующего содерржания:

```
#!/usr/bin/python

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = r'''
---
module: my_own_module
short_description: Creates a text file with specified content
version_added: "1.0.0"
description:
  - Creates a text file at the specified path.
  - Updates the file only when its content differs.
options:
  path:
    description:
      - Path to the file.
    required: true
    type: path
  content:
    description:
      - Content that should be written to the file.
    required: true
    type: str
author:
  - Mark Yachmen
'''

EXAMPLES = r'''
- name: Create a text file
  my_own_module:
    path: /tmp/example.txt
    content: Hello from my own module
'''

RETURN = r'''
path:
  description: Path to the managed file.
  returned: always
  type: str
  sample: /tmp/example.txt
changed:
  description: Whether the file was created or changed.
  returned: always
  type: bool
  sample: true
'''

import os

from ansible.module_utils.basic import AnsibleModule


def run_module():
    module_args = dict(
        path=dict(type="path", required=True),
        content=dict(type="str", required=True),
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )

    path = module.params["path"]
    content = module.params["content"]

    current_content = None

    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as file:
                current_content = file.read()
        except OSError as error:
            module.fail_json(
                msg=f"Failed to read file: {error}",
                path=path,
            )

    changed = current_content != content

    if changed and not module.check_mode:
        try:
            parent_directory = os.path.dirname(path)

            if parent_directory:
                os.makedirs(parent_directory, exist_ok=True)

            with open(path, "w", encoding="utf-8") as file:
                file.write(content)
        except OSError as error:
            module.fail_json(
                msg=f"Failed to write file: {error}",
                path=path,
            )

    module.exit_json(
        changed=changed,
        path=path,
        message="File content is already correct"
        if not changed
        else "File was created or updated",
    )


def main():
    run_module()


if __name__ == "__main__":
    main()
```


Сделаем Python файл исполняемым:

```
chmod +x my_own_module.py
```

Выполним проверку синтаксиса Python файла:

```
python -m py_compile my_own_module.py
```

Скопируем модуль во временный каталог модулей Ansible:

```
cd ~/ansible-module-work/ansible

cp ~/ansible-module-work/my-module/my_own_module.py lib/ansible/modules/my_own_module.py

```

Запустим sanity-проверку только для собственного модуля:

```
ansible-test sanity --test compile lib/ansible/modules/my_own_module.py
```

![img](img/image13.png)

Проверим документацию модуля:

```
ansible-doc -t module my_own_module
```

![img](img/image14.png)

Создадим тестовые аргументы.
В директории с собственным модулем создадим файл ```args.json``` следующего содержания:

```
cat > args.json <<'EOF'
{
  "ANSIBLE_MODULE_ARGS": {
    "path": "/tmp/my_own_module_test.txt",
    "content": "Hello from my own module"
  }
}
EOF
```

Запустим модуль напрямую:

```
python my_own_module.py < args.json
```

![img](img/image15.png)

Проверим содержимое файла ```my_own_module_test.txt```:

```
cat /tmp/my_own_module_test.txt
```

![img](img/image16.png)

Запустим модуль второй раз:

```
python my_own_module.py < args.json
```

![img](img/image17.png)

В сообщении мы видим: 

```
"changed": false
```

а это знаачит, что при повторном запуске никаких изменений не произошло, что подтверждает идемпотентность.

Приступим к созданию playbook.
Создадим файл ```test_module.yml``` следующего содержания:

```
---
- name: Test custom module
  hosts: localhost
  connection: local
  gather_facts: false

  tasks:
    - name: Create test file
      my_own_module:
        path: /tmp/my_own_module_playbook.txt
        content: "Created by Ansible playbook"
```

Запустим playbook, явно указав путь к каталогу модуля:

```
ANSIBLE_LIBRARY=~/ansible-module-work/my-module ansible-playbook test_module.yml
```

![img](img/image18.png)

После окончания процесса в логе видим сообщение:

```
changed=1  
```

Запустим playbook ещё раз:

![img](img/image19.png)

В этот раз в логе видим сообщение:

```
changed=0  
```

что говорит о том, что после повтороного запуска никаких изменений не произошло.

Проверим содержимое файла ```my_own_module_playbook.txt```^

```
cat /tmp/my_own_module_playbook.txt
```

![img](img/image20.png)

Приступим к созданию Collection.

Склонируем созданный в начале репозиторий:

```
cd ~/ansible-module-work
git clone https://github.com/myachmen/my_own_collection.git
cd my_own_collection
```

Инициализируем collection:

```
ansible-galaxy collection init myachmen.my_own_collection --init-path .
```

![img](img/image21.png)

Создадим каталог для модуля и перенесём его:

```
mkdir -p plugins/modules
cp ~/ansible-module-work/my-module/my_own_module.py plugins/modules/my_own_module.py
```

Создадим структуру role:

```
mkdir -p roles/my_own_role/{defaults,tasks}
```

Создадим файл ```roles/my_own_role/defaults/main.yml``` переменных по умолчанию  следующего содержания:

```
---
my_own_module_path: /tmp/my_own_collection_file.txt
my_own_module_content: "Created by my_own_role"
```

Создадим файл ```roles/my_own_role/tasks/main.yml``` с задачами role следующего содержания:

```
---
- name: Create file with custom module
  myachmen.my_own_collection.my_own_module:
    path: "{{ my_own_module_path }}"
    content: "{{ my_own_module_content }}"
```

Проверим структуру:

```
tree -a -L 5
```

![img](img/image22.png)

Создадим playbook, который будет вызывать роль из collection.

```
cd ~/ansible-module-work/my_own_collection
mkdir -p playbooks
```

Создаддим файл ```playbooks/test_role.yml``` следующего содержания:

```
---
- name: Test custom collection role
  hosts: localhost
  connection: local
  gather_facts: false

  roles:
    - role: myachmen.my_own_collection.my_own_role
```

Отредактируем файл galaxy.yml.
Пропишем следующие значения полей:

```
namespace: myachmen
name: my_own_collection
version: 1.0.0
readme: README.md

authors:
  - Mark Yachmen

description: Collection with a custom Ansible module for managing text files

license:
  - GPL-2.0-or-later

tags:
  - ansible
  - module
  - collection

dependencies: {}

repository: https://github.com/myachmen/my_own_collection
documentation: https://github.com/myachmen/my_own_collection
homepage: https://github.com/myachmen/my_own_collection
issues: https://github.com/myachmen/my_own_collection/issues

build_ignore:
  - "*.tar.gz"
  - ".git"
```

Выполним первичную сборку:

```
ansible-galaxy collection build
```

![img](img/image23.png)

Создадим полностью отдельный каталог, чтобы Ansible не использовал исходники collection:

```
mkdir -p ~/ansible-module-work/collection-test
cd ~/ansible-module-work/collection-test
```

Скопируем туда архив и playbook:

```
cp ~/ansible-module-work/my_own_collection/myachmen-my_own_collection-1.0.0.tar.gz .
cp ~/ansible-module-work/my_own_collection/playbooks/test_role.yml .
```

Создадим отдельный каталог для установки:

```
mkdir -p collections
```

Установим collection именно из архива:

```
ansible-galaxy collection install ./myachmen-my_own_collection-1.0.0.tar.gz -p ./collections
```

![img](img/image24.png)

Проверим структуру установки:

```
tree collections -L 6
```

![img](img/image25.png)

Запустим установленную collection, но перед запуском удалим файл от предыдущих проверок:

```
rm -f /tmp/my_own_collection_file.txt
```

Запустиv playbook:

```
ANSIBLE_COLLECTIONS_PATH=./collections \
ansible-playbook test_role.yml
```

![img](img/image26.png)

После окончания процесса в логах мы видим сообщение:

```
changed=1
```

а это значит, что изменения применились.

Проверим содержимое файла ```my_own_collection_file.txt```:

```
cat /tmp/my_own_collection_file.txt
```

![img](img/image27.png)

Запустим playbook повторно:

```
ANSIBLE_COLLECTIONS_PATH=./collections \
ansible-playbook test_role.yml
```

![img](img/image28.png)

После окончания процесса в логах мы видим сообщение:

```
changed=0
```

а это значит, что при пповторном запуске изменений не произошло и модуль сохранил идемпотентность.

Сохраняем collection в GitHub.

Вернёмся в локальный репозиторий:

```
cd ~/ansible-module-work/my_own_collection
```

и проверим состояние:

```
git status

```

![img](img/image29.png)

Создадим файл ```.gitignore``` следующего содержания:

```
cat > .gitignore <<'EOF'
*.tar.gz
__pycache__/
*.pyc
EOF
```


Сделаем коммит:

```
git add .
git commit -m "Add custom Ansible module and collection role"
git push -u origin main
```

![img](img/image30.png)

Создадим требуемый тег:

```
git tag 1.0.0
git push origin 1.0.0
```

![img](img/image31.png)

Скопируем получившийся архив на локальную машину:

```
cp ~/ansible-module-work/my_own_collection/myachmen-my_own_collection-1.0.0.tar.gz /vagrant/
```


Создадим Release через GitHub:

![img](img/image32.png)

![img](img/image33.png)

![img](img/image34.png)

![img](img/image35.png)

