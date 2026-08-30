# Embody i18n — reference

## Source files

| Path | Role |
| --- | --- |
| `frontend/src/i18n/types.ts` | `Locale`, `DocsLocale`, storage keys, readers |
| `frontend/src/i18n/LocaleContext.tsx` | Provider, `t`/`m`, persist, `html.lang`, `syncLocale` |
| `frontend/src/i18n/messages.ts` | Nested typed catalog + `lookupMessage` / `formatMessage` |
| `frontend/src/i18n/pageStrings.ts` | Flat dotted keys (zh/en) |
| `frontend/src/i18n/runtime.ts` | Module `t`, `trText`, `applyDomI18n`, listeners |
| `frontend/src/i18n/inlineCode.ts` | `` `code` `` → escaped HTML |
| `frontend/src/i18n/evalContentI18n.ts` | Episode/unit Chinese→key maps |
| `frontend/src/i18n/actFieldLabels.ts` | ACT field labels |
| `frontend/src/components/SettingsModal.tsx` | Language tab |
| `frontend/src/pages/LoginPage.tsx` | Compact zh/en toggle |
| `frontend/src/styles/appearance.css` | `html[lang='en']` layout tweaks |

## Storage

| Key | Values | Default |
| --- | --- | --- |
| `embody.locale` | `zh` \| `en` | `zh` |
| `embody.docsLocale` | `zh` \| `en` \| `auto` | typically `auto` |

## Provider contract (sketch)

```ts
type Locale = 'zh' | 'en'
type DocsLocale = 'zh' | 'en' | 'auto'

// On setLocale / mount:
localStorage.setItem('embody.locale', locale)
document.documentElement.lang = locale === 'zh' ? 'zh-CN' : 'en'
syncLocale(locale) // updates runtime.t + notifies listeners
```

`useLocale()` must throw outside `LocaleProvider`.

## `t` / `formatMessage`

```ts
t('settings.language.applied', { lang: 'English' })
// catalog: "已应用：{lang}" / "Applied: {lang}"
```

Replace `{key}` tokens only. No plural rules.

## Settings UI

- Tab **language** / `PanelLanguage`
- Segmented UI language: 中文 / English → `setLocale`
- Segmented docs language: 中文 / English / 跟随界面 → `setDocsLocale`
- Status: `t('settings.language.applied', { lang })`

## Backend boundary

| Prefer | Avoid |
| --- | --- |
| Stable error/field **codes** translated on client | New APIs that return Chinese UI sentences |
| Domain key maps for unavoidable Chinese titles | Unmapped Chinese shown raw in EN UI |

## Port naming

Rename `embody.locale` → `<app>.locale` when copying into another product.
