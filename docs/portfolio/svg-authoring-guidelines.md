# SVG Authoring Guidelines — Project 1 diagrams

Rules for creating or editing anything under [`docs/diagrams/`](../diagrams/README.md).
They exist because 26 of 44 diagrams once failed on GitHub with *Invalid image source*
(see [svg-compatibility-report.md](./svg-compatibility-report.md)).

---

## Why GitHub compatibility matters

- The diagrams are the first thing a reviewer sees in the README and the portfolio docs. A broken image
  reads as a broken project.
- GitHub shows SVGs by loading them **as images** (file preview and Markdown `![...](...)` embeds).
  In image mode a browser is strict: the file must be well-formed XML, and scripts, external
  resources, and interactivity are ignored or blocked. One stray `&` or one invalid byte turns the
  whole diagram into *Invalid image source*.
- GitHub gives no line number or parser message. Validate locally before pushing.

---

## Preferred features

| Use | Notes |
|---|---|
| `<rect>` (with `rx` **attribute**), `<line>`, `<path>`, `<polyline>`, `<polygon>`, `<circle>` | Boxes, connectors, arrowheads |
| `<text>` (optionally `<tspan>`) | Labels; one line per `<text>` element |
| `<g>` | Simple grouping only |
| `<marker>` in `<defs>` for arrowheads | Fine on GitHub; define it in the same file and reference with `marker-end="url(#id)"` |
| Presentation attributes | `fill`, `stroke`, `stroke-width`, `stroke-dasharray`, `font-family`, `font-size`, `font-weight`, `text-anchor` |
| `<title>` + `role="img"` + `aria-label` on the root | Accessibility and a meaningful tooltip |

Standard header (dimensions must match the drawing):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="900" height="520" viewBox="0 0 900 520" role="img" aria-label="Short description">
  <title>Short description</title>
```

Font stack for every text element (or set once on the root / a group):

```xml
font-family="Arial, Helvetica, sans-serif"
```

---

## Forbidden / unwanted

| Avoid | Why |
|---|---|
| `<image>`, `href`/`xlink:href` to files or URLs, `data:` URIs, base64 rasters | External or embedded rasters: blocked or non-portable, and they defeat the point of a text diagram |
| `<foreignObject>` / embedded HTML | Not rendered consistently in image mode |
| `<script>`, event attributes (`onclick`, …), animation (`<animate>`, `<set>`) | Ignored in image mode; not needed for static docs |
| External CSS (`<?xml-stylesheet?>`, `@import`), `@font-face`, font files | Blocked in image mode; do not add font files to the repo |
| `<style>` blocks and CSS classes | Not required; use presentation attributes so every renderer agrees |
| CSS geometry properties (`rx:`/`ry:` inside CSS) | SVG 2 feature ignored by some renderers — use the `rx` attribute |
| Filters, masks, clip paths, gradients for decoration | Unnecessary; prefer flat fills |
| Font names without a fallback (e.g. only `Segoe UI`) | Falls back to a serif font on macOS / Linux |
| Glyphs missing from Arial/Helvetica (e.g. `✓`, emoji) | Draw them with `<polyline>` / `<path>` instead |
| Absolute or local paths in Markdown (`C:\Users\…`, `file://`, `vscode-file://`) | Only work on one machine |

---

## Text safety

- Escape XML specials inside text: `&` → `&amp;`, `<` → `&lt;` (and `>` → `&gt;` for symmetry).
  `A & B` must be written `A &amp; B`.
- Save as **UTF-8 without BOM**. Characters such as `→ · — ≈ ≠ × …` are fine **as real UTF-8**.
- Never write SVGs through a tool that silently re-encodes text. The original corruption came from a
  write path that reduced Unicode characters to a single byte (`—` → `0x14`, `→` → `0x92`, `…` → `&`)
  or replaced them with `?`. On Windows, prefer an editor or script that writes UTF-8 explicitly
  (for example Python `open(path, "w", encoding="utf-8", newline="\n")`), and avoid PowerShell
  string interpolation for content that contains backticks.

## Geometry rules

- Every arrowhead ends on the edge of the box it points to; bus lines themselves carry no arrowhead.
- Fan-out: plain stem → plain bus → one arrowed drop per target box centre.
- Open multi-segment paths need `fill="none"` (the SVG default fill is black).
- Keep text inside its box with a few pixels of padding; keep everything inside the `viewBox`.

---

## Testing workflow

```text
draw → validate XML → render locally → inspect → GitHub preview → commit
```

1. **Draw** with the primitives above.
2. **Validate XML and encoding**:

   ```bash
   python -c "import sys,xml.dom.minidom as m; [m.parse(f) for f in sys.argv[1:]]; print('ok')" docs/diagrams/*.svg
   python -c "import sys; [open(f,encoding='utf-8',errors='strict').read() for f in sys.argv[1:]]; print('utf-8 ok')" docs/diagrams/*.svg
   ```

   On Windows PowerShell, pass file names via `(Get-ChildItem docs/diagrams/*.svg).FullName`.

3. **Scan for unwanted constructs**:

   ```bash
   grep -nE "<image|xlink:href|data:|foreignObject|<script|<style|@font-face|@import|url\((https?:|//)" docs/diagrams/*.svg
   ```

   Expected: no output.

4. **Render locally** in a browser engine, ideally through an `<img>` tag (same mode as GitHub).
   Any installed Chromium-based browser works headless, for example:

   ```bash
   msedge --headless=new --screenshot=/tmp/preview.png --window-size=900,520 file:///path/to/docs/diagrams/example.svg
   ```

   Keep previews outside the repository.
5. **Inspect** the PNG: labels legible and inside boxes, arrows visible and landing on boxes, nothing
   clipped, no black-filled shapes, no `?` or odd characters in place of symbols.
6. **GitHub preview**: after pushing, open the file on GitHub and the Markdown page that embeds it.
7. **Commit** only the `.svg` source. Do not commit PNG substitutes unless a GitHub limitation cannot be
   solved in SVG — and document why if you do.

## Referencing from Markdown

Use repository-relative paths:

```markdown
![Project 1 Reference Architecture](docs/diagrams/project1-reference-architecture.svg)
```

From a file inside `docs/`, use a path relative to that file, e.g. `../diagrams/example.svg`.
File names are case-sensitive on GitHub.

Related: [svg-compatibility-report.md](./svg-compatibility-report.md) · [diagram index](../diagrams/README.md)
