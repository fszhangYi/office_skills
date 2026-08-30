---
name: embody-i18n
description: >-
  Port or extend embody_model_eval-style React+Vite i18n: LocaleProvider,
  nested messages + flat pageStrings, runtime t/trText/applyDomI18n,
  localStorage locale, html lang, Settings language tab. Use when the user
  asks for embody i18n, LocaleContext, pageStrings, useLocale, setLocale,
  bilingual zh/en UI, data-i18n, trText, docsLocale, or React Vite locale
  persistence without i18next.
---

# Embody i18n

Canonical: `/root/autodl-tmp/embody_model_eval/frontend/src/i18n/`.

Homegrown React i18n — **no** `react-i18next` / Lingui. Default locale **`zh`**. Catalogs: **zh + en** with zh fallback.

## Architecture

```text
LocaleProvider
  ├─ localStorage: embody.locale / embody.docsLocale
  ├─ document.documentElement.lang = zh-CN | en
  ├─ syncLocale() → runtime module state + listeners
  ├─ messages[locale] → nested typed tree (m.*)
  └─ t(path) → pageStrings flat first, then nested → formatMessage({vars})
```

Dual APIs:

| API | Use |
| --- | --- |
| `useLocale()` → `{ locale, t, m, setLocale, docsLocale, … }` | React components |
| `runtime`: `t` / `trText` / `applyDomI18n` / `onLocaleChange` | Legacy `mount*` / HTML shells |

## Port checklist

```text
- [ ] 1. Copy types.ts, LocaleContext.tsx, slim messages.ts, runtime.ts (+ inlineCode if needed)
- [ ] 2. Wrap app with LocaleProvider above router/auth
- [ ] 3. Persist locale; set html.lang on change (zh → zh-CN)
- [ ] 4. Nested catalog for chrome (nav/settings/home); flat pageStrings for features
- [ ] 5. Settings language panel; optional Login compact toggle
- [ ] 6. Prefer stable backend codes over Chinese UI text; avoid new trText for fresh APIs
- [ ] 7. Keep zh/en key parity; optional CSS html[lang='en'] for wrapping
- [ ] 8. Wire document.title if needed (source app leaves it static)
```

## Catalog rules

1. **Nested typed tree** (`messages.ts`): `common`, `nav`, `settings`, `home`, `login` → `m.settings.language.ui`
2. **Flat dotted dict** (`pageStrings.ts`): features (`sensors.*`, `eval.*`, …) → `t('sensors.arm.subtitle')`
3. **Interpolation**: `{name}` only — no ICU plurals
4. **Fallback**: missing key → try **zh** → return raw path
5. Side maps OK for pipeline field labels / content reverse-lookup — don’t invent a third full catalog style without reason

### Lookup order

`pageStrings[locale][path]` → walk nested `messages[locale]` by dotted path → zh → path string.

## Component recipes

```tsx
const { m, t, locale, setLocale } = useLocale()
// Shell: m.home.title
// Feature: t('sensors.arm.subtitle')
// With vars: t('settings.language.applied', { lang: 'English' })
```

- Imperative features: `import { t } from '../i18n/runtime'` and include `locale` in `useMemo` deps or subscribe `onLocaleChange`
- HTML shells: `data-i18n="eval.title"` + `applyDomI18n`
- `trText(chineseFromApi)`: reverse-lookup via zh `pageStrings` — fragile; prefer codes

## Locale / docs axes

| Pref | Storage | Effect today |
| --- | --- | --- |
| UI `locale` | `embody.locale` | Almost all strings + `html[lang]` |
| `docsLocale` `zh\|en\|auto` | `embody.docsLocale` | Settings only — **mostly unused** elsewhere |

Default UI locale: **`zh`** (not `navigator.language`).

No server `Accept-Language`. Pipeline backends often emit Chinese labels — map with domain wrappers (`actFieldLabels`, `sensorI18n`, …).

## Pitfalls

1. Half-wired `docsLocale` — don’t assume docs follow it
2. `trText` first-wins on duplicate Chinese; English API text won’t match
3. Static `document.title` / some exports hardcode `zh-CN`
4. `toLocaleString()` without app locale ignores UI language
5. Dual `t` (context vs runtime) — keep `syncLocale` on every `setLocale`
6. Adding strings to the wrong catalog (nested vs flat vs inline `{zh,en}`)

## Additional resources

- File map and API details: [reference.md](reference.md)
- Theme prefs sibling: `embody-appearance-theme`
- Visual chrome: `embody-ui-style`
