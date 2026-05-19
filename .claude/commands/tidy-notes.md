---
description: Clean up messy Markdown notes into clear, structured notes
argument-hint: <raw notes, pasted text, or @file>
allowed-tools: Read
---

You are tidying rough Markdown notes.

Input notes:

$ARGUMENTS

Your task is to rewrite the notes into clean, well-structured Markdown.

Rules:

1. Preserve the original meaning.
2. Do not invent facts.
3. Do not remove useful technical details.
4. Fix Markdown formatting.
5. Straighten the hierarchy of sections.
6. Convert bare links into Markdown links when the destination is obvious.
7. Keep short fragments if they are meaningful.
8. Group related bullets under sensible headings.
9. Remove duplicated or empty headings.
10. Make the notes easier to scan, but do not make them overly polished or verbose.
11. Keep the style practical, research-note-like, and compact.
12. If something is unclear, keep it under a heading called `Open questions` rather than guessing.

Formatting preferences:

- Use one clear `#` title.
- Use `##` for major sections.
- Use `###` only when genuinely helpful.
- Prefer bullets over long paragraphs.
- Keep model names, dataset names, and tools in code formatting when useful.
- Keep URLs as links.
- Add a short `Summary` section only if it helps.
- Add an `Action items` section only if the notes imply next steps.

Output only the cleaned Markdown.
Do not explain what you changed.