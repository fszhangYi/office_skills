# office_skills

Cursor Agent Skills for report writing, Markdown ↔ DOCX / PDF / 立项 XLSX conversion, and Scheme A desktop packaging.

## Skills

| Skill | Purpose |
| --- | --- |
| [`md-to-docx-report`](md-to-docx-report/) | Convert Chinese research Markdown to DOCX with fixed typography (`docx 格式要求`) |
| [`docx-to-md-report`](docx-to-md-report/) | Restore DOCX reports to Markdown, with hyperlinks as `[text](url)` |
| [`pdf-to-md-report`](pdf-to-md-report/) | Convert research/arXiv PDFs to Markdown (text, tables/equations, figure crops, optional EN/ZH) |
| [`hik_report`](hik_report/) | Report writing style, content summarization, and briefing-ready sentence annotations |
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

## Install into Cursor

```bash
# project-level
cp -a md-to-docx-report /path/to/workspace/.cursor/skills/md-to-docx-report
cp -a docx-to-md-report /path/to/workspace/.cursor/skills/docx-to-md-report
cp -a pdf-to-md-report /path/to/workspace/.cursor/skills/pdf-to-md-report
cp -a hik_report /path/to/workspace/.cursor/skills/hik_report
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

# or user-level
cp -a md-to-docx-report ~/.cursor/skills/md-to-docx-report
cp -a docx-to-md-report ~/.cursor/skills/docx-to-md-report
cp -a pdf-to-md-report ~/.cursor/skills/pdf-to-md-report
cp -a hik_report ~/.cursor/skills/hik_report
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
```

Reopen the workspace or refresh Skills if they do not appear.

## License

Use as needed for internal report workflows.
