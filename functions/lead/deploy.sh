#!/usr/bin/env bash
# Развёртывание функции приёма заявок в Yandex Cloud (ru-central1). Идемпотентно.
#
# Требует: yc CLI с профилем (yc init), выбранные облако и каталог.
# Необязательно: ~/.config/xmark/lead.env с SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASS / NOTIFY_TO
# (файл вне репозитория).
#
# Запуск: functions/lead/deploy.sh
set -euo pipefail
cd "$(dirname "$0")"
YC="${YC:-$(command -v yc || echo "$HOME/yandex-cloud/bin/yc")}"

FUNC=xmark-lead
SA=xmark-lead-sa
BUCKET="${BUCKET:-oplot-xmark-leads}"
ORIGINS="${ALLOWED_ORIGINS:-https://xmark.oplot-it.ru}"
FOLDER_ID="$($YC config get folder-id)"
[ -n "$FOLDER_ID" ] || { echo "нет folder-id: выполните yc init" >&2; exit 1; }

echo "== сервисный аккаунт"
$YC iam service-account get "$SA" >/dev/null 2>&1 || $YC iam service-account create --name "$SA" >/dev/null
SA_ID="$($YC iam service-account get "$SA" --format json | python3 -c 'import json,sys;print(json.load(sys.stdin)["id"])')"
$YC resource-manager folder add-access-binding "$FOLDER_ID" --role storage.uploader \
  --subject "serviceAccount:$SA_ID" >/dev/null 2>&1 || true

echo "== бакет $BUCKET (приватный)"
$YC storage bucket get "$BUCKET" >/dev/null 2>&1 || \
  $YC storage bucket create --name "$BUCKET" --default-storage-class standard --max-size 1073741824 >/dev/null

echo "== функция"
$YC serverless function get "$FUNC" >/dev/null 2>&1 || $YC serverless function create --name "$FUNC" >/dev/null
$YC serverless function allow-unauthenticated-invoke "$FUNC" >/dev/null

ENV="BUCKET=$BUCKET,ALLOWED_ORIGINS=$ORIGINS"
if [ -f "$HOME/.config/xmark/lead.env" ]; then
  while IFS='=' read -r k v; do
    [[ "$k" =~ ^(SMTP_HOST|SMTP_PORT|SMTP_USER|SMTP_PASS|NOTIFY_TO)$ ]] && [ -n "$v" ] && ENV="$ENV,$k=$v"
  done < "$HOME/.config/xmark/lead.env"
fi

$YC serverless function version create \
  --function-name "$FUNC" \
  --runtime python312 \
  --entrypoint index.handler \
  --memory 128m \
  --execution-timeout 15s \
  --service-account-id "$SA_ID" \
  --source-path ./index.py \
  --environment "$ENV" >/dev/null

FID="$($YC serverless function get "$FUNC" --format json | python3 -c 'import json,sys;print(json.load(sys.stdin)["id"])')"
echo "URL: https://functions.yandexcloud.net/$FID"
