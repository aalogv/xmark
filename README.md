# Оплот.X-Mark — сайт продукта

Лендинг продукта Оплот.X-Mark (ООО «Оплот-ИТ»): невидимая маркировка экрана, по которой из скриншота или фотографии можно определить компьютер и время снимка.

- Демо-стенд: https://xmark-demo.k3s.dex-it.ru
- `index.html` — самодостаточная страница, работает без сборки

## Запуск локально

Откройте `index.html` в браузере или:

```bash
npx serve .
```

## Публикация на GitHub Pages

```bash
git init
git add .
git commit -m "Лендинг Оплот.X-Mark"
git branch -M main
git remote add origin git@github.com:<org>/oplot-x-mark-site.git
git push -u origin main
```

Затем Settings → Pages → Source: `main` / root.

## TODO

- Подключить отправку формы заявки (сейчас только визуальное подтверждение)
- Указать номер записи в реестре отечественного ПО
- Уточнить контакты компании в футере
