# Домашнее задание по теме "Helm" Ячмень Марк Викторович

## Задание 1. Подготовить Helm-чарт для приложения

1. Необходимо упаковать приложение в чарт для деплоя в разные окружения. 
2. Каждый компонент приложения деплоится отдельным deployment’ом или statefulset’ом.
3. В переменных чарта измените образ приложения для изменения версии.

## Решение 1

Для выполнения домашнего задания будем использовать виртуальную машину `k8s-lab` с MicroK8s, подготовленную в рамках предыдущей домашней работы.

Создаддим helm `myapp` и проверим его:

```
microk8s helm3 create myapp
find myapp -maxdepth 2 -type f | sort
ls -la myapp
```

![img](img/image1.png)

Очистим стандартные `templates`:

```
rm templates/NOTES.txt
rm templates/deployment.yaml
rm templates/hpa.yaml
rm templates/httproute.yaml
rm templates/ingress.yaml
rm templates/service.yaml
rm templates/serviceaccount.yaml
```

Проверим результат:

```
find . -maxdepth 2 -type f | sort
```

![img](img/image2.png)

Отредактируем содержание файла `values.yaml`:

```
nginx:
  replicaCount: 1
  image:
    repository: nginx
    tag: "1.27"
    pullPolicy: IfNotPresent
  service:
    type: ClusterIP
    port: 80

multitool:
  replicaCount: 1
  image:
    repository: wbitt/network-multitool
    tag: "alpine-extra"
    pullPolicy: IfNotPresent
  service:
    type: ClusterIP
    port: 80
```

Создадим шаблон Deployment для `nginx` следующего содержания:

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-nginx
  labels:
    app: {{ .Release.Name }}-nginx
spec:
  replicas: {{ .Values.nginx.replicaCount }}
  selector:
    matchLabels:
      app: {{ .Release.Name }}-nginx
  template:
    metadata:
      labels:
        app: {{ .Release.Name }}-nginx
    spec:
      containers:
        - name: nginx
          image: "{{ .Values.nginx.image.repository }}:{{ .Values.nginx.image.tag }}"
          imagePullPolicy: {{ .Values.nginx.image.pullPolicy }}
          ports:
            - containerPort: {{ .Values.nginx.service.port }}
```

Выполним тестирование:

```
microk8s helm3 template test .
```

![img](img/image3.png)

Добавим Service для nginx:

```
apiVersion: v1
kind: Service
metadata:
  name: {{ .Release.Name }}-nginx
spec:
  type: {{ .Values.nginx.service.type }}
  selector:
    app: {{ .Release.Name }}-nginx
  ports:
    - port: {{ .Values.nginx.service.port }}
      targetPort: {{ .Values.nginx.service.port }}
      protocol: TCP
```

Снова протестируем:

```
microk8s helm3 template test .
```

![img](img/image4.png)

Добавим второй компонент - `multitool`.
Создадим Deployment:

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-multitool
  labels:
    app: {{ .Release.Name }}-multitool
spec:
  replicas: {{ .Values.multitool.replicaCount }}
  selector:
    matchLabels:
      app: {{ .Release.Name }}-multitool
  template:
    metadata:
      labels:
        app: {{ .Release.Name }}-multitool
    spec:
      containers:
        - name: multitool
          image: "{{ .Values.multitool.image.repository }}:{{ .Values.multitool.image.tag }}"
          imagePullPolicy: {{ .Values.multitool.image.pullPolicy }}
          ports:
            - containerPort: {{ .Values.multitool.service.port }}
```

Создадим Service:

```
apiVersion: v1
kind: Service
metadata:
  name: {{ .Release.Name }}-multitool
spec:
  type: {{ .Values.multitool.service.type }}
  selector:
    app: {{ .Release.Name }}-multitool
  ports:
    - port: {{ .Values.multitool.service.port }}
      targetPort: {{ .Values.multitool.service.port }}
      protocol: TCP
```

Проверим структуру:

```
find . -type f | sort
```

![img](img/image5.png)

Выполним две проверки:

```
microk8s helm3 lint .
microk8s helm3 template test .
```

![img](img/image6.png)

![img](img/image7.png)