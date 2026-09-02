# Домашнее задание по теме "Сетевое взаимодействие в K8S" Ячмень Марк Викторович

## Задание 1. Настройка Service (ClusterIP и NodePort)

Развернуть приложение из двух контейнеров (nginx и multitool) и обеспечить доступ к ним:

 - Внутри кластера через ClusterIP.
 - Снаружи через NodePort.


## Решение 1

Подготовим окружение.

Для выполнения домашнего задания будем использовать виртуальную машину `k8s-lab` с MicroK8s, подготовленную в рамках предыдущей домашней работы.

После запуска виртуальной машины проверено состояние кластера:

```
microk8s status
kubectl get nodes -o wide
kubectl get pods -A
```

![img](img/image1.png)

MicroK8s запущен, нода `k8s-lab` находится в состоянии `Ready`.

Перед выполнением текущего задания удалим ресурсы, созданные в рамках предыдущей работы:

```
kubectl delete deployment nginx-init nginx-multitool
kubectl delete pod multitool-client
kubectl delete service nginx-init-service nginx-multitool-service
```

![img](img/image2.png)

После удаления ресурсов предыдущей домашней работы в namespace `default` остался только стандартный Service `kubernetes`.

Создадим файл манифеста `deployment-multi-container.yaml` следующего содержания:

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: multi-container
spec:
  replicas: 3
  selector:
    matchLabels:
      app: multi-container
  template:
    metadata:
      labels:
        app: multi-container
    spec:
      containers:
        - name: nginx
          image: nginx:1.27
          ports:
            - containerPort: 80

        - name: multitool
          image: wbitt/network-multitool
          env:
            - name: HTTP_PORT
              value: "8080"
          ports:
            - containerPort: 8080
```

Применим созданный манифест:

```
kubectl apply --dry-run=client -f ~/manifests/deployment-multi-container.yaml
kubectl apply -f ~/manifests/deployment-multi-container.yaml
```

![img](img/image3.png)

Проверим Deployment и созданные им Pod:

```
kubectl get deployments
kubectl get pods -o wide
```

![img](img/image4.png)

Deployment успешно создан. Запущены три Pod, каждый из которых содержит два контейнера (`2/2 Running`).

Создадим Service типа `ClusterIP`, который обеспечит доступ к контейнерам приложения:
- порт `9001` Service направляется на порт `80` контейнера `nginx`;
- порт `9002` Service направляется на порт `8080` контейнера `multitool`.

Создадим файл манифеста `service-clusterip.yaml` следующего содержания:

```
apiVersion: v1
kind: Service
metadata:
  name: multi-container-service
spec:
  type: ClusterIP
  selector:
    app: multi-container
  ports:
    - name: nginx
      port: 9001
      targetPort: 80

    - name: multitool
      port: 9002
      targetPort: 8080
```

Применим созданный манифест:

```
kubectl apply --dry-run=client -f ~/manifests/service-clusterip.yaml
kubectl apply -f ~/manifests/service-clusterip.yaml
```

![img](img/image5.png)

Проверим:

```
kubectl get services
kubectl describe service multi-container-service
```

![img](img/image6.png)

Оба Service типа `ClusterIP` успешно созданы и связаны с соответствующими Pod по селекторам `app=frontend` и `app=backend`.

Service типа `ClusterIP` успешно создан. По селектору `app=multi-container` он обнаружил все три Pod приложения.

Настроено перенаправление:
- `9001/TCP` → `80/TCP` (`nginx`);
- `9002/TCP` → `8080/TCP` (`multitool`).

Создадим тестовый Pod:

```
kubectl run multitool-client \
  --image=wbitt/network-multitool \
  --restart=Never \
  --command -- sleep 3600
```

![img](img/image7.png)

Проверим:

```
kubectl get pod multitool-client
```

![img](img/image8.png)

Подключимся к созданному Pod:

```
kubectl exec -it multitool-client -- bash
```

Из Pod проверим доступ к обоим контейнерам по доменному имени Service.

Для `nginx`:

```
curl multi-container-service:9001
```

Для `multitool`:

```
curl multi-container-service:9002
```

Дополнительно проверим DNS-разрешение имени Service:

```
nslookup multi-container-service
```

![img](img/image9.png)

Проверка показала, что по доменному имени `multi-container-service` доступны оба контейнера приложения:

- `multi-container-service:9001` — `nginx`;
- `multi-container-service:9002` — `network-multitool`.

DNS Kubernetes успешно разрешает имя `multi-container-service` в полное имя `multi-container-service.default.svc.cluster.local` и ClusterIP Service.

Таким образом, доступ к контейнерам приложения по разным портам из другого Pod внутри кластера обеспечен.

Для обеспечения доступа к приложению с локального компьютера создадим Service типа `NodePort`.

Создадим файл манифеста `service-nodeport.yaml` следующего содержания:

```
apiVersion: v1
kind: Service
metadata:
  name: nginx-nodeport
spec:
  type: NodePort
  selector:
    app: multi-container
  ports:
    - name: nginx
      port: 80
      targetPort: 80
      protocol: TCP
```

Проверим и применим манифест:

```
kubectl apply --dry-run=client -f ~/manifests/service-nodeport.yaml
kubectl apply -f ~/manifests/service-nodeport.yaml
```

![img](img/image10.png)

Проверим созданный Service:

```
kubectl get services
kubectl describe service nginx-nodeport
```

![img](img/image11.png)

Проверим доступ к `nginx` с локального компьютера:

```
curl.exe http://192.168.56.10:30088
Test-NetConnection 192.168.56.10 -Port 30088
```

![img](img/image12.png)

В результате `curl` успешно получил страницу `nginx`, а `Test-NetConnection` подтвердил доступность TCP-порта `30088`.
Таким образом, приложение доступно внутри кластера через Service типа `ClusterIP`, а `nginx` доступен с локального компьютера через Service типа `NodePort`.


## Задание 2. Настройка Ingress

Развернуть два приложения (frontend и backend) и обеспечить доступ к ним через Ingress по разным путям.


## Решение 2

Создадим два файла манифеста следующего содержания.

`deployment-frontend.yaml`:

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
spec:
  replicas: 1
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
        - name: nginx
          image: nginx:1.27
          ports:
            - containerPort: 80
```

`deployment-backend.yaml`:

```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  replicas: 1
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
        - name: multitool
          image: wbitt/network-multitool
          ports:
            - containerPort: 80
```


Проверим и применим манифесты:

```
kubectl apply --dry-run=client -f ~/manifests/deployment-frontend.yaml
kubectl apply --dry-run=client -f ~/manifests/deployment-backend.yaml

kubectl apply -f ~/manifests/deployment-frontend.yaml
kubectl apply -f ~/manifests/deployment-backend.yaml
```

![img](img/image13.png)

Проверим:

```
kubectl get deployments
kubectl get pods -o wide
```

![img](img/image14.png)

Оба Deployment успешно созданы. Pod `frontend` с контейнером `nginx` и Pod `backend` с контейнером `network-multitool` находятся в состоянии `Running`.

Создадим два файла манифеста следующего содержания.

`service-frontend.yaml`:

```
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
spec:
  selector:
    app: frontend
  ports:
    - name: http
      port: 80
      targetPort: 80
      protocol: TCP
```

`service-backend.yaml`:

```
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  selector:
    app: backend
  ports:
    - name: http
      port: 80
      targetPort: 80
      protocol: TCP
```

Проверим и применим манифесты:

```
kubectl apply --dry-run=client -f ~/manifests/service-frontend.yaml
kubectl apply --dry-run=client -f ~/manifests/service-backend.yaml

kubectl apply -f ~/manifests/service-frontend.yaml
kubectl apply -f ~/manifests/service-backend.yaml
```

![img](img/image15.png)

Проверим:

```
kubectl get services

kubectl describe service frontend-service
kubectl describe service backend-service
```

![img](img/image16.png)

Включим Ingress-controller в MicroK8s:

```
microk8s enable ingress
```

Проверим:

```
microk8s status
kubectl get pods -n ingress
kubectl get services -n ingress
```

![img](img/image18.png)

Создадим файл манифеста `ingress.yaml` следующего содержания:

```
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
  annotations:
    traefik.ingress.kubernetes.io/router.middlewares: default-strip-api@kubernetescrd
spec:
  ingressClassName: public
  rules:
    - http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service:
                name: backend-service
                port:
                  number: 80

          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend-service
                port:
                  number: 80
```

Проверим и применим манифест:

```
kubectl apply --dry-run=client -f ~/manifests/ingress.yaml
kubectl apply -f ~/manifests/ingress.yaml
```

![img](img/image19.png)

Проверим:

```
kubectl get ingress
kubectl describe ingress app-ingress
```

![img](img/image20.png)

Проверим, как именно Traefik опубликован наружу:

```
kubectl get pods -n ingress
kubectl get services -n ingress
```

![img](img/image21.png)

В текущей версии MicroK8s в качестве Ingress Controller используется Traefik. Поэтому вместо аннотации `nginx.ingress.kubernetes.io/rewrite-target`, приведённой в шаблоне задания, для обработки маршрута `/api` используем Traefik Middleware `StripPrefix`, удаляющий префикс `/api` перед передачей запроса backend-приложению.

Создадим Middleware.
Создадим файл манифеста `middleware-strip-api.yaml` следующего содержания:

```
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
  name: strip-api
spec:
  stripPrefix:
    prefixes:
      - /api
```

Проверим и применим манифест:

```
kubectl apply --dry-run=client -f ~/manifests/middleware-strip-api.yaml
kubectl apply -f ~/manifests/middleware-strip-api.yaml
```

![img](img/image22.png)

После применения конфигурации проверим маршрутизацию с локального компьютера:

```
curl.exe http://192.168.56.10:30710/
curl.exe http://192.168.56.10:30710/api
```

![img](img/image23.png)

Проверка показала, что маршрутизация через Ingress работает корректно:

- запрос к `/` направляется в `frontend-service` и возвращает страницу `nginx`;
- запрос к `/api` направляется в `backend-service`, при этом Middleware `StripPrefix` удаляет префикс `/api`, после чего получен ответ от `network-multitool`.

Таким образом, доступ к приложениям `frontend` и `backend` через Ingress по разным путям успешно настроен.


## Ссылки на манифесты

### Задание 1

- [deployment-multi-container.yaml](manifests/deployment-multi-container.yaml)
- [service-clusterip.yaml](manifests/service-clusterip.yaml)
- [service-nodeport.yaml](manifests/service-nodeport.yaml)

### Задание 2

- [deployment-frontend.yaml](manifests/deployment-frontend.yaml)
- [deployment-backend.yaml](manifests/deployment-backend.yaml)
- [service-frontend.yaml](manifests/service-frontend.yaml)
- [service-backend.yaml](manifests/service-backend.yaml)
- [ingress.yaml](manifests/ingress.yaml)
- [middleware-strip-api.yaml](manifests/middleware-strip-api.yaml)