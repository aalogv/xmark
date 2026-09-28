#!/usr/bin/env python3
"""Точечные правки лендинга index.html (экспорт бандлера, шаблон хранится JS-строкой).

Правки для соответствия требованиям реестра ПО (ПП 1236) и приказа Минцифры № 511:
  1. убрать недостоверный бейдж «Входит в реестр отечественного ПО» (hero);
  2. убрать «входит в единый реестр российского ПО» из футера;
  3. футер: реквизиты правообладателя, ссылки на документацию / стоимость / реквизиты / политику ПДн,
     email office@oplot-it.ru;
  4. навигация: пункт «Документация»;
  5. секция «Цены»: ссылка на порядок определения стоимости;
  6. подпись под формой: ссылка на политику обработки ПДн;
  7. список Linux в «Внедрении»: без RHEL, с Альт;
  8. шаг «Установка драйвера» → «Установка агента»;
  9. мокапы: время без секунд, «Владелец» → «Пользователь»;
 10. тексты о результате: компьютер, пользователь и время, а не «ID в метке»;
 11. hero-стат: «минимальная нагрузка» вместо «< 1 % CPU»;
 12. отрасли: «ОПК» вместо «Оборонки»;
 13. блок «Анализ снимка»: демо кодирования и декодирования на API стенда (xmark2.oplot-it.ru:8080);
 14. формулировки под ограничения ФСТЭК: «малозаметная» (не «невидимая»), источник копии (не «утечка»), без DLP;\n 15. ссылки на презентацию (assets/oplot-xmark-presentation.pdf) в hero и футере.

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

INSTALL_OLD = "title: 'Установка драйвера'"
INSTALL_NEW = "title: 'Установка агента'"

HERO_TIME_OLD = "'16.09.2026 14:32:07'"
HERO_TIME_NEW = "'16.09.2026 14:32'"
PANEL_TIME_OLD = "'16.09.2026, 14:32:07'"
PANEL_TIME_NEW = "'16.09.2026, 14:32'"

# подписи мокапа выровнены пробелами под моноширинный шрифт
PANEL_PC_OLD = "'Компьютер: '"
PANEL_PC_NEW = "'Компьютер:    '"
PANEL_USER_OLD = "'Владелец:  '), e('span', { style: { color: '#F5F5F7' } }, 'Отдел аналитики')"
PANEL_USER_NEW = "'Пользователь: '), e('span', { style: { color: '#F5F5F7' } }, 'a.petrova')"
PANEL_SHOT_OLD = "'Снято:     '"
PANEL_SHOT_NEW = "'Снято:        '"

STEP_OLD = "'Драйвер подмешивает в вывод на монитор стойкую метку с ID компьютера и точным временем.'"
STEP_NEW = "'Драйвер подмешивает в вывод на монитор стойкую метку, невидимую для глаза.'"

QUOTE_OLD = esc('Из любого снимка извлекаются идентификатор компьютера и точное время отображения.')
QUOTE_NEW = esc('По любому снимку устанавливаются компьютер, пользователь и время, когда изображение было на экране.')

LOAD_OLD = esc('&lt; 1%</div><div style="font-size: 15px; color: #48484C; margin-top: 6px">нагрузка на CPU</div>')
LOAD_NEW = esc('Минимальная</div><div style="font-size: 15px; color: #48484C; margin-top: 6px">нагрузка на рабочую станцию</div>')

OPK_OLD = "name: 'Оборонка и промышленность'"
OPK_NEW = "name: 'ОПК и промышленность'"

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
        115054, г. Москва, вн.тер.г. муниципальный округ Замоскворечье, ул. Большая Пионерская, д. 15, стр. 1, помещ. 1/1<br>
        Разработка цифровых продуктов и усиление команд квалифицированными инженерами.
      </div>
      <div style="display: flex; gap: 48px; flex-wrap: wrap">
        <div style="display: flex; flex-direction: column; gap: 8px">
          <span style="font-weight: 600; color: #1D1D1F">Продукт</span>
          <a href="#how" style="color: #48484C" style-hover="color: #2C67F2">Как работает</a>
          <a href="#deploy" style="color: #48484C" style-hover="color: #2C67F2">Внедрение</a>
          <a href="https://xmark2.oplot-it.ru:8080" target="_blank" rel="noopener" style="color: #48484C" style-hover="color: #2C67F2">Демо-стенд</a>
        </div>
        <div style="display: flex; flex-direction: column; gap: 8px">
          <span style="font-weight: 600; color: #1D1D1F">Документы</span>
          <a href="docs/" style="color: #48484C" style-hover="color: #2C67F2">Документация</a>
          <a href="price.html" style="color: #48484C" style-hover="color: #2C67F2">Стоимость и порядок её определения</a>
          <a href="company.html" style="color: #48484C" style-hover="color: #2C67F2">Сведения о правообладателе</a>
          <a href="assets/oplot-xmark-presentation.pdf" download style="color: #48484C" style-hover="color: #2C67F2">Презентация продукта (PDF, 0,6 МБ)</a>
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

# ---------- блок «Анализ снимка» ----------
# Демо-сервер (ASP.NET Kestrel): POST /api/decode (multipart: file, mode) -> {jobId};
# GET /api/decode/{jobId} -> {status, found, payload, payloadHex, scale, rotationDegrees,
# offsetX, offsetY, meanAbsLlr, elapsedSeconds, message}. Режим corners (разметка углов)
# на лендинг не переносится — ссылка на полное демо.
ANALYZE_API = "https://xmark2.oplot-it.ru:8080"
ANALYZE_MARKER = "// ANALYZE_V2:"  # версия живого блока; смена маркера = перевыпуск блока
LIVE_MARKER = "const API = '" + ANALYZE_API + "';"  # любая версия живого блока (для защиты шага 9)

STATE_OLD = "state = { sent: false, name: '', company: '', phone: '', seats: '', comment: '' };"
STATE_V1 = (
    "state = { sent: false, name: '', company: '', phone: '', seats: '', comment: '', "
    "az: { file: null, preview: null, mode: 'screen', busy: false, result: null, error: null } };"
)
STATE_NEW = (
    "state = { sent: false, name: '', company: '', phone: '', seats: '', comment: '', "
    "az: { tab: 'encode', sample: 'doc', payload: '12345', delta: 3, encBusy: false, encError: null, encUrl: null, samples: null, "
    "file: null, preview: null, mode: 'screen', busy: false, result: null, error: null } };"
)

ANALYZE_START = esc("  analyzeMock() {")
ANALYZE_END = esc("  renderVals() {")

# Внимание: код ниже попадает внутрь JSON-строки шаблона. Нельзя использовать обратный слэш
# и последовательность "</" (esc() экранирует только кавычки, "</" и переводы строк).
ANALYZE_NEW = esc(r'''  analyzeMock() {
    // ANALYZE_V2: демо кодирования и декодирования на API стенда
    const e = React.createElement;
    const az = this.state.az;
    const API = 'https://xmark2.oplot-it.ru:8080';
    const setAz = (p) => this.setState({ az: Object.assign({}, this.state.az, p) });
    const SAMPLES = az.samples || [['doc', 'Документ'], ['ide', 'IDE'], ['schema', 'Схема'], ['ui', 'Приложение']];
    if (!this._azInit) {
      this._azInit = true;
      fetch(API + '/api/samples').then((r) => r.ok ? r.json() : null).then((list) => {
        if (Array.isArray(list) && list.length) setAz({ samples: list.map((s) => [s.id, s.title]) });
      }).catch(() => {});
      document.addEventListener('fullscreenchange', () => {
        if (!document.fullscreenElement && this.state.az.encUrl) {
          URL.revokeObjectURL(this.state.az.encUrl);
          setAz({ encUrl: null });
        }
      });
    }
    const payloadOk = (raw) => {
      const v = String(raw || '').trim();
      if (/^0x[0-9a-f]{1,8}$/i.test(v)) return true;
      return /^[0-9]{1,10}$/.test(v) && Number(v) <= 4294967295;
    };
    const closeFs = () => {
      if (document.fullscreenElement) { document.exitFullscreen().catch(() => {}); }
      if (this.state.az.encUrl) URL.revokeObjectURL(this.state.az.encUrl);
      setAz({ encUrl: null });
    };
    const encode = async () => {
      const cur = this.state.az;
      if (cur.encBusy || !payloadOk(cur.payload)) return;
      setAz({ encBusy: true, encError: null });
      try {
        const resp = await fetch(API + '/api/encode', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ sample: cur.sample, payload: String(cur.payload).trim(), delta: Number(cur.delta) })
        });
        if (!resp.ok) throw new Error(await resp.text());
        const url = URL.createObjectURL(await resp.blob());
        setAz({ encBusy: false, encUrl: url });
        const el = this._fsEl;
        if (el && el.requestFullscreen) { el.requestFullscreen().catch(() => {}); }
      } catch (err) {
        const msg = (err && err.message) ? err.message : '';
        setAz({ encBusy: false, encError: msg && msg !== 'Failed to fetch' ? msg : 'Сервис кодирования недоступен. Попробуйте позже или откройте демо-стенд.' });
      }
    };
    const pick = (file) => {
      if (!file) return;
      if (!file.type || file.type.indexOf('image/') !== 0) { setAz({ error: 'Нужен файл PNG или JPG' }); return; }
      if (this.state.az.preview) URL.revokeObjectURL(this.state.az.preview);
      setAz({ file: file, preview: URL.createObjectURL(file), result: null, error: null });
    };
    const run = async () => {
      const cur = this.state.az;
      if (!cur.file || cur.busy) return;
      setAz({ busy: true, result: null, error: null });
      try {
        const form = new FormData();
        form.append('file', cur.file);
        form.append('mode', cur.mode);
        const resp = await fetch(API + '/api/decode', { method: 'POST', body: form });
        if (!resp.ok) throw new Error(await resp.text());
        const job = await resp.json();
        let r;
        for (;;) {
          await new Promise((res) => setTimeout(res, 2000));
          const st = await fetch(API + '/api/decode/' + job.jobId);
          if (!st.ok) throw new Error(await st.text());
          r = await st.json();
          if (r.status === 'done') break;
          if (r.status === 'error') throw new Error(r.message || 'Ошибка декодирования');
        }
        setAz({ busy: false, result: r });
      } catch (err) {
        const msg = (err && err.message) ? err.message : '';
        setAz({ busy: false, error: msg && msg !== 'Failed to fetch' ? msg : 'Сервис анализа недоступен. Попробуйте позже или откройте демо-стенд.' });
      }
    };
    const mono = "'JetBrains Mono', monospace";
    const muted = { color: '#86868B' };
    const pill = (active, label, onClick, extra) => e('button', Object.assign({
      type: 'button', onClick: onClick,
      style: { background: active ? '#2C67F2' : 'rgba(255,255,255,0.08)', color: '#F5F5F7', border: 'none', borderRadius: 100, padding: '5px 12px', fontSize: 12, fontWeight: 500, cursor: 'pointer', fontFamily: 'inherit' }
    }, extra || {}), label);
    const row = (k, v, color) => e('div', null, e('span', { style: muted }, k), e('span', { style: { color: color || '#F5F5F7' } }, v));
    const box = (children) => e('div', { style: { margin: '0 20px 20px', background: '#0A0A0A', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 14, padding: 18, fontFamily: mono, fontSize: 12.5, lineHeight: 2, whiteSpace: 'pre-wrap' } }, children);
    const isEncode = az.tab !== 'decode';

    // ---------- вкладка «Закодировать» ----------
    const encodeTab = [
      e('div', { key: 'g', style: { margin: '0 20px 14px', display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 } },
        SAMPLES.map((s) => e('div', {
          key: s[0], onClick: () => setAz({ sample: s[0] }),
          style: { cursor: 'pointer', borderRadius: 10, overflow: 'hidden', border: az.sample === s[0] ? '2px solid #2C67F2' : '2px solid rgba(255,255,255,0.08)', background: '#0A0A0A' }
        },
          e('img', { src: API + '/api/samples/' + s[0], alt: s[1], loading: 'lazy', style: { display: 'block', width: '100%', aspectRatio: '16 / 9', objectFit: 'cover', opacity: az.sample === s[0] ? 1 : 0.7 } }),
          e('div', { style: { fontSize: 11, textAlign: 'center', padding: '4px 2px', color: az.sample === s[0] ? '#F5F5F7' : '#86868B' } }, s[1])))),
      e('div', { key: 'f', style: { margin: '0 20px 14px', display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' } },
        e('label', { style: { display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#86868B' } }, 'Метка',
          e('input', {
            value: az.payload, maxLength: 10, spellCheck: false, onChange: (ev) => setAz({ payload: ev.target.value }),
            style: { width: 110, background: '#0A0A0A', color: '#F5F5F7', border: '1px solid ' + (payloadOk(az.payload) ? 'rgba(255,255,255,0.15)' : '#FF6B6B'), borderRadius: 8, padding: '5px 8px', fontFamily: mono, fontSize: 12.5 }
          })),
        e('span', { style: { display: 'flex', alignItems: 'center', gap: 4, fontSize: 12, color: '#86868B' } }, 'Сила',
          [2, 3, 4, 5].map((d) => pill(az.delta === d, String(d), () => setAz({ delta: d }), { key: d, style: { background: az.delta === d ? '#2C67F2' : 'rgba(255,255,255,0.08)', color: '#F5F5F7', border: 'none', borderRadius: 100, padding: '4px 9px', fontSize: 12, cursor: 'pointer', fontFamily: 'inherit' } }))),
        e('button', {
          type: 'button', onClick: encode, disabled: az.encBusy || !payloadOk(az.payload),
          style: { marginLeft: 'auto', background: (az.encBusy || !payloadOk(az.payload)) ? 'rgba(255,255,255,0.12)' : '#30D158', color: (az.encBusy || !payloadOk(az.payload)) ? '#86868B' : '#000', border: 'none', borderRadius: 100, padding: '6px 16px', fontSize: 13, fontWeight: 600, cursor: (az.encBusy || !payloadOk(az.payload)) ? 'default' : 'pointer', fontFamily: 'inherit' }
        }, az.encBusy ? 'Кодируем…' : 'Закодировать')),
      box(az.encError
        ? e('div', { style: { color: '#FF6B6B', lineHeight: 1.5 } }, az.encError)
        : [
          e('div', { key: 'h', style: { color: '#F5F5F7', lineHeight: 1.6, whiteSpace: 'normal', fontFamily: 'inherit', fontSize: 13 } },
            'Образец с малозаметной меткой откроется на весь экран 1:1. Сделайте скриншот (масштаб 100 %) или сфотографируйте экран — затем декодируйте снимок на соседней вкладке.'),
          e('div', { key: 'p', style: { marginTop: 6 } }, e('span', { style: muted }, 'Метка: '), e('span', { style: { color: '#62CFF4' } }, payloadOk(az.payload) ? String(az.payload).trim() : '0…4294967295 или 0x0…0xFFFFFFFF'))
        ])
    ];

    // ---------- вкладка «Декодировать» ----------
    let body;
    if (az.busy) {
      body = e('div', { style: { color: '#62CFF4' } }, az.mode === 'photo' ? 'Поиск метки без разметки… может занять минуты' : 'Поиск метки… секунды–минуты');
    } else if (az.error) {
      body = e('div', { style: { color: '#FF6B6B', lineHeight: 1.5 } }, az.error);
    } else if (az.result && az.result.found) {
      const r = az.result;
      body = [
        e('div', { key: 'ok', style: { color: '#30D158', marginBottom: 4 } }, '✓ Метка обнаружена'),
        row('Метка:     ', r.payloadHex + ' (' + r.payload + ')', '#62CFF4'),
        row('Геометрия: ', 'масштаб ' + Number(r.scale).toFixed(3) + ', поворот ' + Number(r.rotationDegrees).toFixed(2) + '°'),
        row('Поиск:     ', r.elapsedSeconds + ' с')
      ];
    } else if (az.result) {
      const r = az.result;
      body = [
        e('div', { key: 'no', style: { color: '#FF9F0A', marginBottom: 4 } }, '✗ Метка не найдена'),
        row('Поиск:     ', r.elapsedSeconds + ' с' + (r.meanAbsLlr != null ? ', meanAbsLlr ' + Number(r.meanAbsLlr).toFixed(1) : ''))
      ];
    } else {
      body = [
        e('div', { key: 'demo', style: muted }, 'Результат появится здесь. Пример:'),
        row('Метка:     ', '0x3039 (12345)', '#62CFF4'),
        row('Поиск:     ', '4 с')
      ];
    }
    const decodeTab = [
      e('div', {
        key: 'd',
        onDragOver: (ev) => ev.preventDefault(),
        onDrop: (ev) => { ev.preventDefault(); pick(ev.dataTransfer.files && ev.dataTransfer.files[0]); },
        style: { margin: '0 20px 14px', border: '1.5px dashed rgba(98,207,244,0.4)', borderRadius: 14, padding: '22px 18px', textAlign: 'center', background: 'rgba(44,103,242,0.06)' }
      },
        az.preview
          ? e('img', { src: az.preview, alt: '', style: { maxWidth: '100%', maxHeight: 150, borderRadius: 8, display: 'block', margin: '0 auto 10px' } })
          : e('div', { style: { color: '#62CFF4', display: 'flex', justifyContent: 'center', marginBottom: 10 } },
              this.icon(['M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4', 'M17 8l-5-5-5 5', 'M12 3v12'], 28)),
        e('div', { style: { fontSize: 14, fontWeight: 500 } },
          az.file ? az.file.name : 'Перетащите скриншот или фото экрана'),
        e('label', { style: { fontSize: 12, color: '#62CFF4', cursor: 'pointer', display: 'inline-block', marginTop: 4 } },
          az.file ? 'выбрать другой файл' : 'или выберите файл',
          e('input', { type: 'file', accept: 'image/*', style: { display: 'none' }, onChange: (ev) => pick(ev.target.files && ev.target.files[0]) })),
        e('div', { style: { fontSize: 12, color: '#86868B', marginTop: 4 } }, 'PNG, JPG — включая пересъёмку на смартфон')),
      e('div', { key: 'm', style: { margin: '0 20px 14px', display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' } },
        pill(az.mode === 'screen', 'Скриншот', () => setAz({ mode: 'screen' })),
        pill(az.mode === 'photo', 'Фото экрана', () => setAz({ mode: 'photo' })),
        e('button', {
          type: 'button', onClick: run, disabled: !az.file || az.busy,
          style: { marginLeft: 'auto', background: (!az.file || az.busy) ? 'rgba(255,255,255,0.12)' : '#30D158', color: (!az.file || az.busy) ? '#86868B' : '#000', border: 'none', borderRadius: 100, padding: '6px 16px', fontSize: 13, fontWeight: 600, cursor: (!az.file || az.busy) ? 'default' : 'pointer', fontFamily: 'inherit' }
        }, az.busy ? 'Ищем…' : 'Декодировать')),
      box(body)
    ];

    // ---------- полноэкранный показ закодированного образца ----------
    const fullscreen = e('div', {
      ref: (el) => { this._fsEl = el; },
      style: az.encUrl
        ? { position: 'fixed', inset: 0, zIndex: 10000, background: '#000', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }
        : { display: 'none' }
    },
      az.encUrl ? e('img', {
        src: az.encUrl, alt: 'Закодированный образец',
        onLoad: (ev) => { ev.target.style.width = (ev.target.naturalWidth / (window.devicePixelRatio || 1)) + 'px'; },
        style: { display: 'block', maxWidth: 'none' }
      }) : null,
      az.encUrl ? e('button', {
        type: 'button', onClick: closeFs, title: 'Закрыть',
        style: { position: 'absolute', top: 12, right: 12, background: 'rgba(255,255,255,0.15)', color: '#fff', border: 'none', borderRadius: 100, padding: '6px 14px', fontSize: 13, cursor: 'pointer', fontFamily: 'inherit', opacity: 0.6 }
      }, 'Закрыть · Esc') : null);

    return e('div', { style: { background: '#1C1C1E', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 20, overflow: 'hidden' } },
      e('div', { style: { padding: '14px 20px', borderBottom: '1px solid rgba(255,255,255,0.08)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap' } },
        e('div', { style: { display: 'flex', gap: 6 } },
          pill(isEncode, 'Закодировать', () => setAz({ tab: 'encode' })),
          pill(!isEncode, 'Декодировать', () => setAz({ tab: 'decode' }))),
        e('a', { href: API + '/', target: '_blank', rel: 'noopener', style: { fontSize: 12, fontWeight: 500, color: '#62CFF4' } }, 'Полное демо ›')),
      e('div', { style: { height: 14 } }),
      isEncode ? encodeTab : decodeTab,
      fullscreen);
  }
''')
assert "\\" not in ANALYZE_NEW.replace('\\"', '').replace('\\n', '').replace('\\u002F', ''), "в коде анализа есть обратный слэш — сломает JSON шаблона"


# ---------- 14. позиционирование: маркировка контента, не СЗИ (ограничения ФСТЭК, ПП № 171) ----------
# «невидимая» — неправда: метка малозаметна при обычном просмотре. Без «утечка», «DLP», «защита».
WORDING = [
    ("<title>Оплот.X-Mark — невидимая маркировка экрана<\\u002Ftitle>",
     "<title>Оплот.X-Mark — малозаметная маркировка цифрового контента<\\u002Ftitle>",
     "title в шаблоне"),
    ("Невидимая маркировка экрана.<br>", "Малозаметная маркировка экрана.<br>", "hero h1, строка 1"),
    (">Видимый источник утечки.<\\u002Fspan>", ">Известный источник каждой копии.<\\u002Fspan>", "hero h1, строка 2"),
    ("Драйвер подмешивает в изображение на мониторе незаметный сигнал. По скриншоту или фотографии экрана вы узнаете компьютер и точное время.",
     "Агент встраивает в изображение на мониторе малозаметную метку. По скриншоту или фотографии экрана можно установить компьютер, пользователя и время показа.",
     "hero p"),
    (">100%<\\u002Fdiv>", ">Малозаметно<\\u002Fdiv>", "stat-tile: значение"),
    (">незаметно для глаза<\\u002Fdiv>", ">при обычном просмотре<\\u002Fdiv>", "stat-tile: подпись"),
    ("'Метка невидима на экране — но читается из любого снимка'", "'Метка малозаметна на экране — но читается из любого снимка'", "hero-mock подпись"),
    (">От драйвера до источника. Четыре шага.<", ">От метки до источника копии. Четыре шага.<", "how h2"),
    ("{ title: 'Невидимый сигнал', text: 'Драйвер подмешивает в вывод на монитор стойкую метку, невидимую для глаза.'",
     "{ title: 'Малозаметная метка', text: 'Агент встраивает в вывод на монитор стойкую метку, малозаметную при обычном просмотре.'",
     "how шаг 2"),
    ("{ title: 'Утечка снимка', text: 'Скриншот или фотография экрана попадает наружу — в мессенджер, СМИ или к конкуренту.'",
     "{ title: 'Копия уходит', text: 'Скриншот или фотография экрана попадает в мессенджер, СМИ или к третьим лицам.'",
     "how шаг 3"),
    ("{ title: 'Идентификация', text: 'Загрузите снимок в панель — система назовёт компьютер и момент, когда он был сделан.'",
     "{ title: 'Установление источника', text: 'Загрузите снимок в панель — система установит компьютер, пользователя и момент показа.'",
     "how шаг 4"),
    (">Где фотография экрана — реальный канал утечки.<", ">Где важно знать источник каждой копии экрана.<", "industries h2"),
    (">Оплот.X-Mark закрывает канал, который не видят DLP-системы.<",
     ">Оплот.X-Mark не блокирует снимки экрана — он позволяет установить, откуда пришла копия.<",
     "industries p"),
    ("'Образец с невидимой меткой откроется", "'Образец с малозаметной меткой откроется", "демо-блок"),
]
HEAD_TITLE_OLD = "<title>Оплот.X-Mark — невидимая маркировка экрана</title>"
HEAD_TITLE_NEW = "<title>Оплот.X-Mark — малозаметная маркировка цифрового контента</title>"

# ---------- 15. презентация (PDF) ----------
PRES_HREF = "assets/oplot-xmark-presentation.pdf"
PRES_HERO_OLD = esc('<a href="https://xmark2.oplot-it.ru:8080" target="_blank" rel="noopener" style="white-space: nowrap">Открыть демо ›</a>\n')
PRES_HERO_NEW = PRES_HERO_OLD + esc('    <a href="' + PRES_HREF + '" download style="white-space: nowrap">Презентация (PDF) ↓</a>\n')
PRES_FOOTER_OLD = esc('          <a href="privacy.html" style="color: #48484C" style-hover="color: #2C67F2">Политика обработки ПДн</a>\n')
PRES_FOOTER_NEW = esc('          <a href="' + PRES_HREF + '" download style="color: #48484C" style-hover="color: #2C67F2">Презентация продукта (PDF, 0,6 МБ)</a>\n') + PRES_FOOTER_OLD

def replace_once(src: str, old: str, new: str, name: str, done_marker=None) -> str:
    markers = done_marker if isinstance(done_marker, tuple) else ((done_marker,) if done_marker else ())
    if any(m in src for m in markers):
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

    # 8. шаг «Как работает»: ставится агент (драйвер — его часть), как и в тексте шага
    out = replace_once(out, INSTALL_OLD, INSTALL_NEW, "how: «Установка агента»", done_marker=INSTALL_NEW)

    # 9. мокапы: время до минуты, в панели — пользователь, а не подразделение
    out = replace_once(out, HERO_TIME_OLD, HERO_TIME_NEW, "hero: время без секунд", done_marker=HERO_TIME_NEW)
    if LIVE_MARKER in out:
        print("  = panel: статичный мокап уже заменён живым блоком (шаг 13)")
    else:
        out = replace_once(out, PANEL_TIME_OLD, PANEL_TIME_NEW, "panel: время без секунд", done_marker=PANEL_TIME_NEW)
        out = replace_once(out, PANEL_PC_OLD, PANEL_PC_NEW, "panel: подпись «Компьютер»", done_marker=PANEL_PC_NEW)
        out = replace_once(out, PANEL_USER_OLD, PANEL_USER_NEW, "panel: «Пользователь»", done_marker=PANEL_USER_NEW)
        out = replace_once(out, PANEL_SHOT_OLD, PANEL_SHOT_NEW, "panel: подпись «Снято»", done_marker=PANEL_SHOT_NEW)

    # 10. метка несёт одноразовый идентификатор показа, а не ID компьютера и время
    out = replace_once(out, STEP_OLD, STEP_NEW, "how: «Невидимый сигнал»", done_marker=(STEP_NEW, "title: 'Малозаметная метка'"))
    out = replace_once(out, QUOTE_OLD, QUOTE_NEW, "цитата о результате", done_marker=QUOTE_NEW)

    # 11. нагрузку в процентах не замеряли
    out = replace_once(out, LOAD_OLD, LOAD_NEW, "hero: нагрузка", done_marker=LOAD_NEW)

    # 12. отрасли
    out = replace_once(out, OPK_OLD, OPK_NEW, "отрасли: ОПК", done_marker=OPK_NEW)

    # 13. блок «Анализ снимка»: демо кодирования и декодирования на API стенда (вместо статичного макета)
    if STATE_NEW in out:
        print("  = state: поле az: уже применено")
    elif STATE_V1 in out:
        out = replace_once(out, STATE_V1, STATE_NEW, "state: поле az (обновление с v1)")
    else:
        out = replace_once(out, STATE_OLD, STATE_NEW, "state: поле az для анализа снимка")
    if ANALYZE_MARKER in out:
        print("  = analyzeMock: уже заменён")
    else:
        s = out.find(ANALYZE_START)
        e = out.find(ANALYZE_END, s)
        if s < 0 or e < 0 or out.count(ANALYZE_START) != 1:
            sys.exit("  ! analyzeMock: блок не найден ровно один раз — прерываю")
        out = out[:s] + ANALYZE_NEW + out[e:]
        print("  + analyzeMock: реальная загрузка в API")

    # 14. позиционирование: малозаметная маркировка, источник копии — без «утечка/DLP/невидимая»
    for old, new, name in WORDING:
        out = replace_once(out, old, new, "wording: " + name, done_marker=new)
    out = replace_once(out, HEAD_TITLE_OLD, HEAD_TITLE_NEW, "wording: title в <head>", done_marker=HEAD_TITLE_NEW)

    # 15. презентация: ссылка в hero и в футере
    out = replace_once(out, PRES_HERO_OLD, PRES_HERO_NEW, "hero: ссылка на презентацию", done_marker=PRES_HERO_NEW)
    out = replace_once(out, PRES_FOOTER_OLD, PRES_FOOTER_NEW, "footer: ссылка на презентацию", done_marker=PRES_FOOTER_NEW)

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
