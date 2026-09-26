#!/usr/bin/env bash
# Управление записью xmark.oplot-it.ru через REG.API v2 (https://api.reg.ru/api/regru2).
#
# Учётные данные — только через переменные окружения, в репозиторий не попадают:
#   REGRU_USER  логин reg.ru (или e-mail)
#   REGRU_PASS  пароль аккаунта или «альтернативный пароль для API»
#
# Перед первым запуском в личном кабинете reg.ru: Настройки → Безопасность → API —
# разрешить доступ и добавить свой IP в белый список (иначе ответ ACCESS_DENIED_FROM_IP).
#
# Использование:
#   scripts/regru-dns.sh list                 показать все записи зоны
#   scripts/regru-dns.sh switch-to-pages      удалить A xmark, добавить CNAME xmark -> aalogv.github.io
#   scripts/regru-dns.sh check                dig + HTTPS-проверка
set -euo pipefail

DOMAIN="${REGRU_DOMAIN:-oplot-it.ru}"   # REGRU_DOMAIN=test.ru — демо-зона reg.ru для проверки
SUB="xmark"
TARGET="aalogv.github.io"
API="https://api.reg.ru/api/regru2"

need_creds() {
  : "${REGRU_USER:?задайте REGRU_USER}" "${REGRU_PASS:?задайте REGRU_PASS}"
}

call() { # call <method> [extra form fields...]
  local method="$1"; shift
  curl -sS -X POST "$API/$method" \
    --data-urlencode "username=$REGRU_USER" \
    --data-urlencode "password=$REGRU_PASS" \
    --data-urlencode "output_format=json" \
    --data-urlencode "domain_name=$DOMAIN" \
    "$@"
}

PY_LIST=$(cat <<'PY'
import json, sys
d = json.load(sys.stdin)
if d.get("result") != "success":
    print(json.dumps(d, ensure_ascii=False, indent=2)); sys.exit(1)
for dom in d["answer"]["domains"]:
    if dom.get("result") != "success":
        print(dom); continue
    for r in dom["rrs"]:
        print("%-12s %-6s %-4s %s" % (r["subname"], r["rectype"], r.get("prio", ""), r["content"]))
PY
)

ok() { python3 -c 'import json,sys; d=json.load(sys.stdin); print(json.dumps(d,ensure_ascii=False,indent=2)); sys.exit(0 if d.get("result")=="success" else 1)'; }

case "${1:-}" in
  list)
    need_creds
    call zone/get_resource_records | python3 -c "$PY_LIST"
    ;;
  switch-to-pages)
    need_creds
    echo "1/2 удаляю A-запись $SUB.$DOMAIN"
    call zone/remove_record --data-urlencode "subdomain=$SUB" --data-urlencode "record_type=A" | ok
    echo "2/2 добавляю CNAME $SUB.$DOMAIN -> $TARGET"
    call zone/add_cname --data-urlencode "subdomain=$SUB" --data-urlencode "canonical_name=$TARGET" | ok
    echo "Готово. Проверка через 5–30 минут: scripts/regru-dns.sh check"
    ;;
  check)
    echo "dig:"; dig +short "$SUB.$DOMAIN" CNAME; dig +short "$SUB.$DOMAIN" A
    echo "https:"; curl -sI -m 10 "https://$SUB.$DOMAIN/docs/" | head -1 || true
    ;;
  *)
    sed -n '2,15p' "$0"; exit 1
    ;;
esac
