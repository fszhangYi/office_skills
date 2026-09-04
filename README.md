# office_skills

Cursor Agent Skills for report writing, Markdown ↔ DOCX / PDF / 立项 XLSX conversion, and Scheme A desktop packaging.

## Skills

| Skill | Purpose |
| --- | --- |
| [`md-to-docx-report`](md-to-docx-report/) | Convert Chinese research Markdown to DOCX with fixed typography (`docx 格式要求`) |
| [`docx-to-md-report`](docx-to-md-report/) | Restore DOCX reports to Markdown, with hyperlinks as `[text](url)` |
| [`pdf-to-md-report`](pdf-to-md-report/) | Convert research/arXiv PDFs to Markdown (text, tables/equations, figure crops, optional EN/ZH) |
| [`hik_report`](hik_report/) | Report writing style, content summarization, and briefing-ready sentence annotations |
| [`hik-get-dumber`](hik-get-dumber/) | Rewrite engineer/research reports into short GM decision briefs (cut depth, elevate route choice) |
| [`hik-project-md2xlsx`](hik-project-md2xlsx/) | Convert 立项/预研 Markdown to 立项报告-style 2-column XLSX |
| [`hik-project-xlsx2md`](hik-project-xlsx2md/) | Restore 立项报告 XLSX to Markdown (`##` sections) |
| [`graspvla-repro`](graspvla-repro/) | Reproduce GraspVLA (preflight on disk/memory/CUDA, then Model Server + `offline_test`) |
| [`autodl-disk-cleanup`](autodl-disk-cleanup/) | Free AutoDL system disk: clean `/tmp`/apt cache, migrate conda/venv to `autodl-tmp` |
| [`scheme-a-desktop-compat`](scheme-a-desktop-compat/) | Check Scheme A stack; add cross-platform desktop packaging compat code |
| [`scheme-a-linux-to-windows-desktop`](scheme-a-linux-to-windows-desktop/) | Linux host → self-contained Windows desktop (Wine + PyInstaller) |
| [`scheme-a-linux-to-linux-desktop`](scheme-a-linux-to-linux-desktop/) | Linux host → self-contained Linux desktop (PyInstaller onedir) |
| [`archive-split-restore`](archive-split-restore/) | Split/restore large archives (zip/tar.gz/…) into fixed-size chunks |
| [`cookie-session-auth`](cookie-session-auth/) | Cookie + opaque session login for Python HTTP + React SPA (embody_model_eval pattern) |
| [`embody-ui-style`](embody-ui-style/) | Embody Model Eval visual design: teal/spark tokens, page CSS, glass/pill chrome |
| [`embody-appearance-theme`](embody-appearance-theme/) | Embody light/dark + density prefs: data-theme, AppearanceProvider, FOUC boot |
| [`embody-i18n`](embody-i18n/) | Embody zh/en LocaleProvider, messages/pageStrings, runtime t without i18next |
| [`embody-login-page`](embody-login-page/) | Embody /login UI: card, CSS atmosphere, from-redirect, lang chrome |
| [`embody-path-picker`](embody-path-picker/) | Embody server-scoped cascade PathPickerModal + `/api/fs/children` |
| [`add-favicon`](add-favicon/) | Brand favicon/app icon for FastAPI HTML + PyInstaller Windows EXE |

## Install into Cursor

```bash
# project-level
cp -a md-to-docx-report /path/to/workspace/.cursor/skills/md-to-docx-report
cp -a docx-to-md-report /path/to/workspace/.cursor/skills/docx-to-md-report
cp -a pdf-to-md-report /path/to/workspace/.cursor/skills/pdf-to-md-report
cp -a hik_report /path/to/workspace/.cursor/skills/hik_report
cp -a hik-get-dumber /path/to/workspace/.cursor/skills/hik-get-dumber
cp -a hik-project-md2xlsx /path/to/workspace/.cursor/skills/hik-project-md2xlsx
cp -a hik-project-xlsx2md /path/to/workspace/.cursor/skills/hik-project-xlsx2md
cp -a graspvla-repro /path/to/workspace/.cursor/skills/graspvla-repro
cp -a autodl-disk-cleanup /path/to/workspace/.cursor/skills/autodl-disk-cleanup
cp -a scheme-a-desktop-compat /path/to/workspace/.cursor/skills/scheme-a-desktop-compat
cp -a scheme-a-linux-to-windows-desktop /path/to/workspace/.cursor/skills/scheme-a-linux-to-windows-desktop
cp -a scheme-a-linux-to-linux-desktop /path/to/workspace/.cursor/skills/scheme-a-linux-to-linux-desktop
cp -a archive-split-restore /path/to/workspace/.cursor/skills/archive-split-restore
cp -a cookie-session-auth /path/to/workspace/.cursor/skills/cookie-session-auth
cp -a embody-ui-style /path/to/workspace/.cursor/skills/embody-ui-style
cp -a embody-appearance-theme /path/to/workspace/.cursor/skills/embody-appearance-theme
cp -a embody-i18n /path/to/workspace/.cursor/skills/embody-i18n
cp -a embody-login-page /path/to/workspace/.cursor/skills/embody-login-page
cp -a embody-path-picker /path/to/workspace/.cursor/skills/embody-path-picker
cp -a add-favicon /path/to/workspace/.cursor/skills/add-favicon

# or user-level
cp -a md-to-docx-report ~/.cursor/skills/md-to-docx-report
cp -a docx-to-md-report ~/.cursor/skills/docx-to-md-report
cp -a pdf-to-md-report ~/.cursor/skills/pdf-to-md-report
cp -a hik_report ~/.cursor/skills/hik_report
cp -a hik-get-dumber ~/.cursor/skills/hik-get-dumber
cp -a hik-project-md2xlsx ~/.cursor/skills/hik-project-md2xlsx
cp -a hik-project-xlsx2md ~/.cursor/skills/hik-project-xlsx2md
cp -a graspvla-repro ~/.cursor/skills/graspvla-repro
cp -a autodl-disk-cleanup ~/.cursor/skills/autodl-disk-cleanup
cp -a scheme-a-desktop-compat ~/.cursor/skills/scheme-a-desktop-compat
cp -a scheme-a-linux-to-windows-desktop ~/.cursor/skills/scheme-a-linux-to-windows-desktop
cp -a scheme-a-linux-to-linux-desktop ~/.cursor/skills/scheme-a-linux-to-linux-desktop
cp -a archive-split-restore ~/.cursor/skills/archive-split-restore
cp -a cookie-session-auth ~/.cursor/skills/cookie-session-auth
cp -a embody-ui-style ~/.cursor/skills/embody-ui-style
cp -a embody-appearance-theme ~/.cursor/skills/embody-appearance-theme
cp -a embody-i18n ~/.cursor/skills/embody-i18n
cp -a embody-login-page ~/.cursor/skills/embody-login-page
cp -a embody-path-picker ~/.cursor/skills/embody-path-picker
cp -a add-favicon ~/.cursor/skills/add-favicon
```

Reopen the workspace or refresh Skills if they do not appear.

## License

Use as needed for internal report workflows.
