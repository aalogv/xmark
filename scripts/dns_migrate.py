#!/usr/bin/env python3
"""Перенос DNS-зоны oplot-it.ru с reg.ru на Selectel DNS (actual, API v2).

Регистратор остаётся reg.ru — меняются только NS-серверы. Порядок:

  1. export   — выгрузить зону из reg.ru (REG.API v2) в zone.json
  2. plan     — показать, какие RRSet будут созданы в Selectel (ничего не меняет)
  3. apply    — создать зону и RRSet в Selectel (идемпотентно: существующие пропускает)
  4. verify   — сравнить ответы NS Selectel с NS reg.ru по каждой записи
  5. switch   — прописать NS Selectel у регистратора reg.ru (только после verify без расхождений)

Учётные данные — только из файла ~/.config/xmark/dns.env (вне репозитория), формат:
  REGRU_USER=...            логин reg.ru
  REGRU_PASS=...            пароль / альтернативный пароль API
  SEL_ACCOUNT=...           номер аккаунта Selectel (правый верхний угол панели)
  SEL_USER=...              сервисный пользователь (IAM → Сервисные пользователи)
  SEL_PASS=...              его пароль
  SEL_PROJECT=...           имя проекта, в котором создаётся DNS-зона

Запуск: python3 scripts/dns_migrate.py export|plan|apply|verify|switch
"""
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

DOMAIN = os.environ.get("DNS_DOMAIN", "oplot-it.ru")
STATE = Path.home() / ".config" / "xmark"
ENV_FILE = Path(os.environ.get("DNS_ENV_FILE", STATE / "dns.env"))
ZONE_FILE = STATE / f"{DOMAIN}.zone.json"
REGRU_API = "https://api.reg.ru/api/regru2"
SEL_AUTH = "https://cloud.api.selcloud.ru/identity/v3/auth/tokens"
SEL_API = "https://api.selectel.ru/domains/v2"
OLD_NS = ["ns1.reg.ru", "ns2.reg.ru"]
DEFAULT_TTL = 3600


# ---------- утилиты ----------

def load_env():
    if not ENV_FILE.exists():
        sys.exit(f"нет файла {ENV_FILE} — см. шапку скрипта")
    env = {}
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip("'\"")
    return env


def http(method, url, headers=None, data=None, form=None):
    body = None
    hdrs = dict(headers or {})
    if form is not None:
        body = urllib.parse.urlencode(form).encode()
        hdrs["Content-Type"] = "application/x-www-form-urlencoded"
    elif data is not None:
        body = json.dumps(data).encode()
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode()
            return r.status, dict(r.headers), (json.loads(raw) if raw.strip().startswith(("{", "[")) else raw)
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        return e.code, dict(e.headers), (json.loads(raw) if raw.strip().startswith(("{", "[")) else raw)


def fqdn(name):
    """subname из reg.ru -> FQDN с точкой."""
    if name in ("@", "", None):
        return DOMAIN + "."
    return f"{name}.{DOMAIN}."


def dig(name, rtype, ns):
    out = subprocess.run(["dig", "+short", "+time=4", "+tries=1", rtype, name, f"@{ns}"],
                         capture_output=True, text=True).stdout
    return sorted(l.strip() for l in out.splitlines() if l.strip())


# ---------- reg.ru ----------

def regru(env, method, **fields):
    form = {"username": env["REGRU_USER"], "password": env["REGRU_PASS"],
            "output_format": "json", "domain_name": DOMAIN, **fields}
    code, _, body = http("POST", f"{REGRU_API}/{method}", form=form)
    if not isinstance(body, dict) or body.get("result") != "success":
        sys.exit(f"reg.ru {method}: {json.dumps(body, ensure_ascii=False)[:600]}")
    return body["answer"]


def cmd_export(env):
    ans = regru(env, "zone/get_resource_records")
    dom = ans["domains"][0]
    if dom.get("result") != "success":
        sys.exit(f"reg.ru: {dom}")
    rrs = []
    for r in dom["rrs"]:
        rtype = r["rectype"].upper()
        if rtype in ("SOA", "NS") and r["subname"] in ("@", ""):
            continue  # SOA/NS апекса Selectel создаёт сам
        content = r["content"]
        if rtype == "MX":
            content = f'{r.get("prio", 10)} {content.rstrip(".")}.'
        elif rtype in ("CNAME", "NS"):
            content = content.rstrip(".") + "."
        elif rtype == "TXT":
            content = content if content.startswith('"') else f'"{content}"'
        elif rtype == "SRV":
            content = f'{r.get("prio", 0)} {content}'
        rrs.append({"name": fqdn(r["subname"]), "type": rtype, "content": content,
                    "ttl": int(r.get("ttl") or DEFAULT_TTL)})
    STATE.mkdir(parents=True, exist_ok=True)
    ZONE_FILE.write_text(json.dumps(rrs, ensure_ascii=False, indent=2))
    print(f"выгружено {len(rrs)} записей -> {ZONE_FILE}")
    for r in rrs:
        print(f'  {r["name"]:<50} {r["type"]:<6} {r["ttl"]:<6} {r["content"]}')


def load_zone():
    if not ZONE_FILE.exists():
        sys.exit(f"нет {ZONE_FILE} — сначала: dns_migrate.py export")
    return json.loads(ZONE_FILE.read_text())


def rrsets(rrs):
    """Группировка записей в RRSet (name, type) -> [contents], ttl = min."""
    out = {}
    for r in rrs:
        key = (r["name"], r["type"])
        s = out.setdefault(key, {"name": r["name"], "type": r["type"], "ttl": r["ttl"], "records": []})
        s["ttl"] = min(s["ttl"], r["ttl"])
        s["records"].append({"content": r["content"], "disabled": False})
    return list(out.values())


# ---------- Selectel ----------

def sel_token(env):
    data = {"auth": {"identity": {"methods": ["password"], "password": {"user": {
                "name": env["SEL_USER"], "domain": {"name": env["SEL_ACCOUNT"]}, "password": env["SEL_PASS"]}}},
            "scope": {"project": {"name": env["SEL_PROJECT"], "domain": {"name": env["SEL_ACCOUNT"]}}}}}
    code, headers, body = http("POST", SEL_AUTH, data=data)
    tok = headers.get("X-Subject-Token") or headers.get("x-subject-token")
    if code not in (200, 201) or not tok:
        sys.exit(f"Selectel auth: HTTP {code} {json.dumps(body, ensure_ascii=False)[:400]}")
    return tok


def sel(tok, method, path, data=None):
    code, _, body = http(method, f"{SEL_API}{path}", headers={"X-Auth-Token": tok}, data=data)
    if code >= 300:
        sys.exit(f"Selectel {method} {path}: HTTP {code} {json.dumps(body, ensure_ascii=False)[:600]}")
    return body


def sel_zone(tok, create=False):
    zones = sel(tok, "GET", "/zones?limit=1000")
    for z in zones.get("result", zones if isinstance(zones, list) else []):
        if z["name"].rstrip(".") == DOMAIN:
            return z
    if not create:
        return None
    return sel(tok, "POST", "/zones", {"name": DOMAIN + "."})


def sel_rrsets(tok, zone_id):
    res = sel(tok, "GET", f"/zones/{zone_id}/rrset?limit=1000")
    return res.get("result", res if isinstance(res, list) else [])


def zone_ns(tok, zone_id):
    for s in sel_rrsets(tok, zone_id):
        if s["type"] == "NS" and s["name"].rstrip(".") == DOMAIN:
            return [r["content"].rstrip(".") for r in s["records"]]
    return []


def cmd_plan(env):
    sets_ = rrsets(load_zone())
    print(f"RRSet к созданию в Selectel: {len(sets_)}")
    for s in sets_:
        print(f'  {s["name"]:<50} {s["type"]:<6} ttl={s["ttl"]:<5} ' + " | ".join(r["content"] for r in s["records"]))


def cmd_apply(env):
    tok = sel_token(env)
    zone = sel_zone(tok, create=True)
    zid = zone["id"]
    print(f"зона {zone['name']} id={zid}")
    existing = {(s["name"], s["type"]) for s in sel_rrsets(tok, zid)}
    created = skipped = 0
    for s in rrsets(load_zone()):
        if (s["name"], s["type"]) in existing:
            skipped += 1
            continue
        sel(tok, "POST", f"/zones/{zid}/rrset", s)
        created += 1
        print(f'  + {s["name"]} {s["type"]}')
    print(f"создано {created}, уже было {skipped}")
    print("NS Selectel для регистратора:", ", ".join(zone_ns(tok, zid)))


def cmd_verify(env):
    tok = sel_token(env)
    zone = sel_zone(tok)
    if not zone:
        sys.exit("зоны в Selectel нет — сначала apply")
    new_ns = zone_ns(tok, zone["id"])
    if not new_ns:
        sys.exit("у зоны нет NS-записей — зона ещё не активирована")
    print("NS Selectel:", ", ".join(new_ns))
    bad = 0
    for s in rrsets(load_zone()):
        name = s["name"].rstrip(".")
        old = dig(name, s["type"], OLD_NS[0])
        new = dig(name, s["type"], new_ns[0])
        ok = old == new
        bad += 0 if ok else 1
        print(f'  {"OK " if ok else "DIFF"} {name:<48} {s["type"]:<6} reg.ru={old} selectel={new}')
    print("расхождений:", bad)
    if bad:
        sys.exit(1)
    print("Можно переключать: dns_migrate.py switch")


def cmd_switch(env):
    tok = sel_token(env)
    zone = sel_zone(tok)
    new_ns = zone_ns(tok, zone["id"]) if zone else []
    if len(new_ns) < 2:
        sys.exit("NS Selectel не получены — сначала apply/verify")
    fields = {f"ns{i}": ns for i, ns in enumerate(new_ns)}
    ans = regru(env, "domain/update_nss", **fields)
    print("reg.ru:", json.dumps(ans, ensure_ascii=False)[:400])
    print("NS сменены на:", ", ".join(new_ns))
    print("Проверка через 10–60 минут: dig +short NS", DOMAIN, "@8.8.8.8")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    cmds = {"export": cmd_export, "plan": cmd_plan, "apply": cmd_apply, "verify": cmd_verify, "switch": cmd_switch}
    if cmd not in cmds:
        print(__doc__)
        sys.exit(1)
    cmds[cmd](load_env())


if __name__ == "__main__":
    main()
