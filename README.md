# Домашнее задание по теме "Сетевое взаимодействие в K8S" Ячмень Марк Викторович

## Задание 1. Создать Deployment и обеспечить доступ к контейнерам приложения по разным портам из другого Pod внутри кластера

1. Создать Deployment приложения, состоящего из двух контейнеров (nginx и multitool), с количеством реплик 3 шт.
2. Создать Service, который обеспечит доступ внутри кластера до контейнеров приложения из п.1 по порту 9001 — nginx 80, по 9002 — multitool 8080.
3. Создать отдельный Pod с приложением multitool и убедиться с помощью `curl`, что из пода есть доступ до приложения из п.1 по разным портам в разные контейнеры.
4. Продемонстрировать доступ с помощью `curl` по доменному имени сервиса.
5. Предоставить манифесты Deployment и Service в решении, а также скриншоты или вывод команды п.4.


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
kubectl apply -f deployment-multi-container.yaml
```

![img](img/image3.png)

Проверим Deployment и созданные им Pod'ы:

```
kubectl get deployments
kubectl get pods -o wide
```

![img](img/image4.png)

Приступим к созданию Service.
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

Заходим внутрь созданного Pod:

```
kubectl exec -it multitool-client -- bash
```

Внутри Pod выполним две проверки.
Для nginx:

```
curl multi-container-service:9001
```

Для multitool:

```
curl multi-container-service:9002
```

DNS-разрешение имени Service:

```
nslookup multi-container-service
```

![img](img/image9.png)