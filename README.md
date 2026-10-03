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



## Задание 2. Настройка HTTPS с Secrets

Развернуть приложение с доступом по HTTPS, используя самоподписанный сертификат.

## Решение 2

Сгенерируем сертификат. 
Для этого выполним команду:

```
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout tls.key -out tls.crt -subj "/CN=myapp.example.com"
```

Проверим, что файлы появились и посмотрим параметры сертификата:

```
ls -l tls.key tls.crt
openssl x509 -in tls.crt -noout -subject -issuer -dates
```

![img](img/image8.png)

Создадим TLS Secret. 
Сделаем Secret непосредственно из сертификата и ключа:

```
microk8s kubectl create secret tls tls-secret --cert=tls.crt --key=tls.key
```
![img](img/image9.png)

Проверим метаданные, не выводя содержимое секрета:

```
microk8s kubectl get secret tls-secret
microk8s kubectl describe secret tls-secret
```

![img](img/image10.png)

Рабочий TLS Secret был создан непосредственно из локальных файлов
сертификата и приватного ключа командой `kubectl create secret tls`,
приведённой выше.

В целях исключения публикации приватного ключа в открытом Git-репозитории
в манифесте `secret-tls.yaml` значения сертификата и ключа заменены
условными обозначениями:

```
apiVersion: v1
kind: Secret
metadata:
  name: tls-secret
type: kubernetes.io/tls
data:
  tls.crt: <BASE64_CERTIFICATE>
  tls.key: <BASE64_PRIVATE_KEY>
```

Создадим манифест `ingress-tls.yaml` следующего содержания:

```
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: nginx-tls-ingress
spec:
  tls:
    - hosts:
        - myapp.example.com
      secretName: tls-secret
  rules:
    - host: myapp.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: nginx-service
                port:
                  number: 80
```

Проверим манифест:

```
microk8s kubectl apply --dry-run=client -f ingress-tls.yaml
```

![img](img/image11.png)

Применим манифест `ingress-tls.yaml` и проверим:

```
microk8s kubectl apply -f ingress-tls.yaml
microk8s kubectl get ingress
microk8s kubectl describe ingress nginx-tls-ingress
```

![img](img/image12.png)

Проверим доступ к приложению по HTTPS через Ingress.

Так как в виртуальной машине настроен HTTP/HTTPS proxy, для локального
обращения к Ingress исключим использование proxy с помощью параметра
`--noproxy`. Параметр `--resolve` используется для сопоставления имени
`myapp.example.com` с IP-адресом виртуальной машины без изменения DNS.

```
curl --noproxy '*' -k --resolve myapp.example.com:443:192.168.56.10 https://myapp.example.com
```

![img](img/image13.png)

В результате HTTPS-запрос успешно обработан Ingress-контроллером и
перенаправлен на сервис `nginx-service`. Для TLS используется созданный
Secret `tls-secret` с самоподписанным сертификатом.

Таким образом, доступ к приложению по HTTPS через Ingress настроен и
работает корректно.



## Задание 3. Настройка RBAC

Создать пользователя с ограниченными правами (только просмотр логов и описания подов).

## Решение 3

Включим RBAC:

```
microk8s enable rbac
```

Проверим и убедимся, что кластер после изменения нормально отвечает:

```
microk8s status
microk8s kubectl get pods
```

![img](img/image14.png)

Создадим ключ и CSR пользователя `developer`:

```
openssl genrsa -out developer.key 2048
```

Создадим запрос на сертификат:

```
openssl req -new -key developer.key -out developer.csr -subj "/CN=developer"
```

Проверим CSR:

```
openssl req -in developer.csr -noout -subject
```

![img](img/image15.png)

Подпишем CSR пользователя `developer`:

```
sudo openssl x509 -req \
  -in developer.csr \
  -CA /var/snap/microk8s/current/certs/ca.crt \
  -CAkey /var/snap/microk8s/current/certs/ca.key \
  -CAcreateserial \
  -out developer.crt \
  -days 365 \
  -sha256
```

Проверим полученный сертификат:

```
openssl x509 -in developer.crt -noout -subject -issuer -dates
```

Проверим, что сертификат действительно доверен CA MicroK8s:

```
sudo openssl verify \
  -CAfile /var/snap/microk8s/current/certs/ca.crt \
  developer.crt
```

![img](img/image16.png)

Создадим манифест `role-pod-reader.yaml` следующего содержания:

```
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: default
rules:
  - apiGroups: [""]
    resources:
      - pods
      - pods/log
    verbs:
      - get
      - list
      - watch
```

Создадим манифест `rolebinding-developer.yaml` следующего содержания:

```
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: developer-pod-reader
  namespace: default
subjects:
  - kind: User
    name: developer
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

Проверим манифесты:

```
microk8s kubectl apply --dry-run=client -f role-pod-reader.yaml
microk8s kubectl apply --dry-run=client -f rolebinding-developer.yaml
```

![img](img/image17.png)

Применим оба манифеста:

```
microk8s kubectl apply -f role-pod-reader.yaml
microk8s kubectl apply -f rolebinding-developer.yaml
```

Проверим созданные объекты:

```
microk8s kubectl get role pod-reader
microk8s kubectl get rolebinding developer-pod-reader
```

![img](img/image18.png)

Проверим, какие права Kubernetes реально выдал `developer`:

```
microk8s kubectl auth can-i --list --as=developer
```

![img](img/image19.png)

После создания `Role` и `RoleBinding` проверим права пользователя `developer`.

Сначала проверим возможность просмотра списка Pod:

```
microk8s kubectl get pods --as=developer
```

![img](img/image20.png)

Пользователь `developer` успешно получил список Pod в namespace `default`.

Для дальнейшей проверки определим имя Pod приложения:

```
POD=$(microk8s kubectl get pods --as=developer \
  -l app=nginx-multitool \
  -o jsonpath='{.items[0].metadata.name}')

echo "$POD"
```

![img](img/image21.png)

Проверим возможность просмотра подробной информации о Pod:

```
microk8s kubectl describe pod "$POD" --as=developer
```

![img](img/image22.png)

Команда выполнена успешно, пользователь `developer` имеет возможность просматривать информацию о Pod.

Проверим доступ к логам контейнера `nginx`:

```
microk8s kubectl logs "$POD" -c nginx --as=developer --tail=10
```

![img](img/image23.png)

Логи контейнера успешно получены от имени пользователя `developer`.

Дополнительно проверим, что пользователь не обладает правами на изменение ресурсов. Попробуем удалить Pod:

```
microk8s kubectl delete pod "$POD" --as=developer
```

![img](img/image24.png)

Kubernetes вернул ошибку `Forbidden`: пользователь `developer` не имеет права удалять Pod в namespace `default`.

Таким образом, настроенная RBAC-политика предоставляет пользователю `developer` права на просмотр Pod и их логов, но не предоставляет права на удаление Pod.