# office_skills

Cursor Agent Skills for report writing and Markdown ↔ DOCX conversion.

## Skills

| Skill | Purpose |
| --- | --- |
| [`md-to-docx-report`](md-to-docx-report/) | Convert Chinese research Markdown to DOCX with fixed typography (`docx 格式要求`) |
| [`docx-to-md-report`](docx-to-md-report/) | Restore DOCX reports to Markdown, with hyperlinks as `[text](url)` |
| [`hik_report`](hik_report/) | Report writing style, content summarization, and briefing-ready sentence annotations |

## Install into Cursor

```bash
# project-level
cp -a md-to-docx-report /path/to/workspace/.cursor/skills/md-to-docx-report
cp -a docx-to-md-report /path/to/workspace/.cursor/skills/docx-to-md-report
cp -a hik_report /path/to/workspace/.cursor/skills/hik_report

# or user-level
cp -a md-to-docx-report ~/.cursor/skills/md-to-docx-report
cp -a docx-to-md-report ~/.cursor/skills/docx-to-md-report
cp -a hik_report ~/.cursor/skills/hik_report
```

Reopen the workspace or refresh Skills if they do not appear.

## License

Use as needed for internal report workflows.
