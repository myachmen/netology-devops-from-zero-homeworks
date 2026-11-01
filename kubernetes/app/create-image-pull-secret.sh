#!/usr/bin/env bash
set -euo pipefail

KEY_FILE="${KEY_FILE:-/home/vagrant/diploma-image-puller-key.json}"
SECRET_NAME="ycr-image-pull-secret"
NAMESPACE="default"

if [[ ! -r "$KEY_FILE" ]]; then
    echo "ERROR: Cannot read key file: $KEY_FILE" >&2
    exit 1
fi

KEY_FILE="$KEY_FILE" SECRET_NAME="$SECRET_NAME" NAMESPACE="$NAMESPACE" python3 - <<'PY' | kubectl apply -f -
import base64
import json
import os
import sys

with open(os.environ["KEY_FILE"], encoding="utf-8") as f:
    key = json.load(f)

auth = base64.b64encode(
    ("json_key:" + json.dumps(key, separators=(",", ":"))).encode()
).decode()

docker_config = {
    "auths": {
        "cr.yandex": {
            "auth": auth
        }
    }
}

secret = {
    "apiVersion": "v1",
    "kind": "Secret",
    "metadata": {
        "name": os.environ["SECRET_NAME"],
        "namespace": os.environ["NAMESPACE"]
    },
    "type": "kubernetes.io/dockerconfigjson",
    "data": {
        ".dockerconfigjson": base64.b64encode(
            json.dumps(docker_config).encode()
        ).decode()
    }
}

json.dump(secret, sys.stdout)
PY
