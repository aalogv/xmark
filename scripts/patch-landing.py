#!/usr/bin/env python3
"""Точечные правки лендинга index.html (экспорт бандлера, шаблон хранится JS-строкой).

Правки для соответствия требованиям реестра ПО (ПП 1236) и приказа Минцифры № 511:
  1. убрать недостоверный бейдж «Входит в реестр отечественного ПО» (hero);
  2. убрать «входит в единый реестр российского ПО» из футера;
  3. футер: реквизиты правообладателя, ссылки на документацию / стоимость / реквизиты / политику ПДн,
     email office@oplot-it.ru;
  4. навигация: пункт «Документация»;
  5. секция «Цены»: ссылка на порядок определения стоимости;
  6. подпись под формой: ссылка на политику обработки ПДн.

Скрипт идемпотентен: если правка уже применена — пропускает её. Если целевой фрагмент
не найден ровно один раз (и правка ещё не применена) — падает, ничего не записав.

Запуск: python3 scripts/patch-landing.py [--check]
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"


def esc(html: str) -> str:
    """Обычный HTML -> вид, в котором он лежит внутри JS-строки шаблона бандлера."""
    return html.replace('"', '\\"').replace("</", "<\\u002F").replace("\n", "\\n")


# ---------- целевые фрагменты (в экранированном виде) ----------

HERO_BADGE = esc(
    '  <div style="font-size: 14px; font-weight: 600; color: #2C67F2; margin-bottom: 14px">'
    'Входит в реестр отечественного ПО</div>\n'
)

NAV_CTA = esc(
    '      <a href="#contact" style="display: inline-block; background: #2C67F2; color: #fff; '
    'padding: 5px 14px; border-radius: 100px; font-weight: 500; flex-shrink: 0" '
    'style-hover="background: #3D8EF0; color: #fff">Запросить цену</a>'
)
NAV_DOCS = esc(
    '      <a href="docs/" style="color: #1D1D1F; opacity: 0.8" '
    'style-hover="opacity: 1; color: #1D1D1F">Документация</a>\n'
)

CONTACT_P_END = esc(
    'Оставьте контакты — подготовим расчёт и организуем пилот на вашей инфраструктуре.</p>\n'
)
CONTACT_LINK = esc(
    '  <p style="font-size: 15px; margin: -32px auto 40px; max-width: 600px">'
    '<a href="price.html" style="color: #2C67F2; font-weight: 500">Порядок определения стоимости лицензий →</a></p>\n'
)

CONSENT_OLD = esc('Нажимая кнопку, вы соглашаетесь с обработкой персональных данных')
CONSENT_NEW = esc(
    'Нажимая кнопку, вы соглашаетесь с <a href="privacy.html" style="color: inherit; '
    'text-decoration: underline">обработкой персональных данных</a>'
)

OS_OLD = "detail: 'Astra Linux, РЕД ОС, Ubuntu, Debian, RHEL'"
OS_NEW = "detail: 'Astra Linux SE, РЕД ОС, Альт, Ubuntu, Debian'"

FOOTER_START = esc('<footer style="background: #F5F5F7; border-top: 1px solid rgba(0,0,0,0.08)">')
FOOTER_END = esc('</footer>')

FOOTER_NEW = esc('''<footer style="background: #F5F5F7; border-top: 1px solid rgba(0,0,0,0.08)">
  <div style="max-width: 1024px; margin: 0 auto; padding: 40px 22px; font-size: 12px; color: #86868B">
    <div style="display: flex; justify-content: space-between; gap: 32px; flex-wrap: wrap; padding-bottom: 20px; border-bottom: 1px solid rgba(0,0,0,0.08)">
      <div style="max-width: 400px; line-height: 1.7">
        <img src="3838d766-6efa-4d7e-ada1-fde114033c90" alt="Оплот-ИТ" style="height: 24px; margin-bottom: 12px; display: block">
        <div style="font-weight: 600; color: #1D1D1F; margin-bottom: 4px">Общество с ограниченной ответственностью «ОПЛОТ-ИТ»</div>
        ИНН 9705227487 · КПП 770501001 · ОГРН 1247700465902<br>
        Основной ОКВЭД 62.02 — деятельность консультативная и работы в области компьютерных технологий<br>
        115054, г. Москва, ул. Большая Пионерская, д. 15, стр. 1, помещ. 1/1<br>
        Разработка цифровых продуктов и усиление команд квалифицированными инженерами.
      </div>
      <div style="display: flex; gap: 48px; flex-wrap: wrap">
        <div style="display: flex; flex-direction: column; gap: 8px">
          <span style="font-weight: 600; color: #1D1D1F">Продукт</span>
          <a href="#how" style="color: #48484C" style-hover="color: #2C67F2">Как работает</a>
          <a href="#deploy" style="color: #48484C" style-hover="color: #2C67F2">Внедрение</a>
          <a href="https://xmark-demo.k3s.dex-it.ru" target="_blank" rel="noopener" style="color: #48484C" style-hover="color: #2C67F2">Демо-стенд</a>
        </div>
        <div style="display: flex; flex-direction: column; gap: 8px">
          <span style="font-weight: 600; color: #1D1D1F">Документы</span>
          <a href="docs/" style="color: #48484C" style-hover="color: #2C67F2">Документация</a>
          <a href="price.html" style="color: #48484C" style-hover="color: #2C67F2">Стоимость и порядок её определения</a>
          <a href="company.html" style="color: #48484C" style-hover="color: #2C67F2">Сведения о правообладателе</a>
          <a href="privacy.html" style="color: #48484C" style-hover="color: #2C67F2">Политика обработки ПДн</a>
        </div>
        <div style="display: flex; flex-direction: column; gap: 8px">
          <span style="font-weight: 600; color: #1D1D1F">Контакты</span>
          <a href="tel:+74993481107" style="color: #48484C" style-hover="color: #2C67F2">+7 (499) 348-11-07</a>
          <a href="mailto:office@oplot-it.ru" style="color: #48484C" style-hover="color: #2C67F2">office@oplot-it.ru</a>
          <a href="mailto:support@oplot-it.ru" style="color: #48484C" style-hover="color: #2C67F2">support@oplot-it.ru</a>
          <a href="https://oplot-it.ru" target="_blank" rel="noopener" style="color: #48484C" style-hover="color: #2C67F2">oplot-it.ru</a>
        </div>
      </div>
    </div>
    <div style="display: flex; justify-content: space-between; gap: 16px; flex-wrap: wrap; padding-top: 16px">
      <span>© 2026 ООО «ОПЛОТ-ИТ». Все права защищены.</span>
      <span>Информация на сайте доступна без регистрации и авторизации.</span>
    </div>
  </div>
</footer>''')

FOOTER_MARKER = esc('ИНН 9705227487')  # признак, что футер уже заменён


def replace_once(src: str, old: str, new: str, name: str, done_marker: str | None = None) -> str:
    if done_marker and done_marker in src:
        print(f"  = {name}: уже применено")
        return src
    n = src.count(old)
    if n != 1:
        sys.exit(f"  ! {name}: фрагмент найден {n} раз(а), ожидался 1 — прерываю")
    print(f"  + {name}")
    return src.replace(old, new)


def main() -> None:
    check_only = "--check" in sys.argv
    src = INDEX.read_text(encoding="utf-8")
    out = src

    # 1. hero badge
    if HERO_BADGE in out:
        out = replace_once(out, HERO_BADGE, "", "hero: убрать бейдж «Входит в реестр»")
    else:
        print("  = hero: бейдж уже убран")

    # 2+3. footer целиком
    if FOOTER_MARKER in out:
        print("  = footer: уже заменён")
    else:
        s = out.find(FOOTER_START)
        e = out.find(FOOTER_END, s)
        if s < 0 or e < 0 or out.count(FOOTER_START) != 1:
            sys.exit("  ! footer: не найден ровно один раз — прерываю")
        e += len(FOOTER_END)
        old_footer = out[s:e]
        if "входит в единый реестр российского ПО" not in old_footer:
            sys.exit("  ! footer: неожиданное содержимое — прерываю")
        out = out[:s] + FOOTER_NEW + out[e:]
        print("  + footer: реквизиты, ссылки, office@, убрано «входит в реестр»")

    # 4. nav
    out = replace_once(out, NAV_CTA, NAV_DOCS + NAV_CTA, "nav: пункт «Документация»", done_marker=NAV_DOCS)

    # 5. contact
    out = replace_once(out, CONTACT_P_END, CONTACT_P_END + CONTACT_LINK, "contact: ссылка на price.html", done_marker=CONTACT_LINK)

    # 6. consent
    out = replace_once(out, CONSENT_OLD, CONSENT_NEW, "form: ссылка на privacy.html", done_marker=CONSENT_NEW)

    # 7. список ОС: RHEL — иностранная ОС, упоминание вредит экспертизе; Альт — из реестра
    out = replace_once(out, OS_OLD, OS_NEW, "deploy: список Linux без RHEL, с Альт", done_marker=OS_NEW)

    if out == src:
        print("Изменений нет.")
        return
    if check_only:
        print("--check: файл не записан.")
        return
    INDEX.write_text(out, encoding="utf-8")
    print(f"Записано: {INDEX} ({len(src)} -> {len(out)} байт)")


if __name__ == "__main__":
    main()
