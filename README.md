# Домашнее задание по теме "Настройка приложений и управление доступом в Kubernetes" Ячмень Марк Викторович

## Задание 1. Работа с ConfigMaps

Развернуть приложение (nginx + multitool), решить проблему конфигурации через ConfigMap и подключить веб-страницу.

## Решение 1

Для выполнения домашнего задания будем использовать виртуальную машину `k8s-lab` с MicroK8s, подготовленную в рамках предыдущей домашней работы.

Создадим манифест `configmap-web.yaml` следующего содержания:

```
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-config
data:
  index.html: |
    <html>
      <head>
        <title>Netology Kubernetes</title>
      </head>
      <body>
        <h1>Hello from Netology!</h1>
        <p>This page is stored in Kubernetes ConfigMap.</p>
      </body>
    </html>
```

Создадим манифест `deployment.yaml` следующего содержания:

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-multitool
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx-multitool
  template:
    metadata:
      labels:
        app: nginx-multitool
    spec:
      containers:
        - name: nginx
          image: nginx:1.27
          ports:
            - containerPort: 80
          volumeMounts:
            - name: nginx-config-volume
              mountPath: /usr/share/nginx/html/index.html
              subPath: index.html

        - name: multitool
          image: wbitt/network-multitool
          env:
            - name: HTTP_PORT
              value: "8080"
          ports:
            - containerPort: 8080

      volumes:
        - name: nginx-config-volume
          configMap:
            name: nginx-config
```

Создадим манифест `service.yaml` следующего содержания:

```
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
spec:
  selector:
    app: nginx-multitool
  ports:
    - name: http
      port: 80
      targetPort: 80
```

Выполним проверку манифестов:

```
microk8s kubectl apply --dry-run=client -f configmap-web.yaml
microk8s kubectl apply --dry-run=client -f deployment.yaml
microk8s kubectl apply --dry-run=client -f service.yaml
```

![img](img/image1.png)

Применим манифесты:

```
microk8s kubectl apply -f configmap-web.yaml
microk8s kubectl apply -f deployment.yaml
microk8s kubectl apply -f service.yaml
```

![img](img/image2.png)

Проверим созданные ресурсы:

```
microk8s kubectl get configmap nginx-config
microk8s kubectl get deployment nginx-multitool
microk8s kubectl get pods -o wide
microk8s kubectl get svc nginx-service
```

![img](img/image3.png)

Проверим ConfigMap.
Посмотрим, что Kubernetes действительно хранит нашу HTML-страницу:

```
microk8s kubectl describe configmap nginx-config
microk8s kubectl get configmap nginx-config -o yaml
```

![img](img/image4.png)

Теперь файл внутри nginx.
Получим имя Pod автоматически:

```
POD=$(microk8s kubectl get pods -l app=nginx-multitool -o jsonpath='{.items[0].metadata.name}')
echo $POD
```

![img](img/image5.png)

Проверим файл:

```
microk8s kubectl exec "$POD" -c nginx -- cat /usr/share/nginx/html/index.html
```

![img](img/image6.png)

Проверим страницу через Service.
Выполним проверку из второго контейнера `multitool`:

```
microk8s kubectl exec "$POD" -c multitool -- curl -s http://nginx-service
```

В результате обращения из контейнера `multitool` к сервису `nginx-service`
получена HTML-страница, содержимое которой было задано в ConfigMap.

![img](img/image7.png)

Таким образом, ConfigMap успешно подключён к контейнеру `nginx`,
а доступ к веб-странице через Service из второго контейнера работает корректно.