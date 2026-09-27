# SVG Compatibility Report — Project 1 diagrams

Audit of every SVG under [`docs/diagrams/`](../diagrams/README.md) after GitHub's file preview showed
**"Error rendering embedded code — Invalid image source"** for several diagrams
(first confirmed on `docs/diagrams/argo-applicationset.svg`).

Scope: documentation only. No Kubernetes manifests, Terraform, Jenkins, Python, Ansible, Argo CD,
AWS, VMware, or application code were changed.

---

## Summary

| Metric | Result |
|---|---|
| SVGs audited | 44 |
| Failed XML parsing before the fix | **26** |
| Failed to load through `<img>` before the fix (the way GitHub embeds SVGs) | **26** (the same 26) |
| XML-valid after the fix | 44 / 44 |
| Load through `<img>` after the fix | 44 / 44 |
| Contained `<image>`, `data:` URIs, `<foreignObject>`, `<script>`, external CSS, `@font-face`, or external URLs | 0 (before and after) |
| Used an internal `<style>` block | 33 before → 0 after (inlined as presentation attributes) |
| Status | 35 FIXED · 9 PASS · 0 WARNING |

### Known problem: `argo-applicationset.svg`

| | |
|---|---|
| Previous GitHub error | `Error rendering embedded code` / `Invalid image source` (observed on the GitHub file preview before this fix) |
| Actual cause | Label text `env, path, cluster&` — an unescaped `&` (an ellipsis `…` that had been truncated to its low byte `0x26`). An XML parser rejects the file at line 21, so GitHub refuses the image. |
| New status | **Fixed and locally validated** (XML parse, `<img>` load, headless Chromium render, visual review). Diagram redrawn with an explicit ApplicationSet boundary: Generator → Parameters → Template → Generated Applications → dev / test / stage Apps → Kubernetes resources per App. |

---

## Root cause

The failure was **not** caused by embedded images, external resources, or exotic SVG features —
none of the 44 files used any. It was **text-encoding corruption introduced when the files were first written**:

| Corruption class | Example (before) | Restored | Effect |
|---|---|---|---|
| Unicode punctuation truncated to its low byte → raw control character | `0x14` | `—` (U+2014) | Illegal XML character → parse failure |
| Truncated to low byte → invalid UTF-8 byte | `0x92`, `0x91` | `→` (U+2192), `↑` (U+2191) | Invalid UTF-8 → parse failure |
| Written as a single Windows-1252 byte → invalid UTF-8 | `0xB7`, `0x97`, `0xD7` | `·`, `—`, `×` | Invalid UTF-8 → parse failure |
| Truncated to low byte `0x26` → bare ampersand | `cluster&`, `ELB / &` | `…` (U+2026) | Unescaped `&` → parse failure |
| Truncated to low byte `0x13` | `0x13` | `✓` (U+2713) | Illegal XML character → parse failure |
| Truncated to a printable ASCII byte (silent) | `Ready H 379s`, ``Node loss ` automatic`` | `≈`, `≠` | Valid XML, wrong text |
| Replaced with `?` by a lossy encoder (silent) | `Pod ? PVC ? PV`, `Jenkins ? kubectl` | `→`, `≠` | Valid XML, wrong text |

GitHub renders an SVG preview by loading it as an image. A browser loading an SVG as an image
requires well-formed XML; any parse error produces a broken image, which GitHub reports as
*Invalid image source*. This was reproduced locally: all 26 malformed files failed to load through
`<img>` in headless Chromium (Microsoft Edge) while the 18 well-formed files loaded.
It was also cross-checked on GitHub before the fix: `argo-applicationset.svg` showed the error,
while the already well-formed `project1-security-architecture.svg` rendered normally.

Each restored character was chosen from its surrounding text and cross-checked against the
Markdown documents that describe the same diagram (for example, `Jenkins ≠ kubectl deploy apps`
matches the GitOps boundary documented in ADR 003 and `docs/automation/automation-architecture.md`).

### Visual defects found during review

Rendering every diagram also exposed layout bugs that were invisible while the files could not render
(and a few in files that did render): overlapping boxes, arrows ending in open space, fan-outs where one
branch had no arrow or a box was not connected at all, open paths filled black by the SVG default fill,
a connector striking through a label, and text sitting outside its container. These were fixed with
the smallest geometry change that restores the intended relationship; labels and meaning were preserved.

---

## Standardisation applied to all 44 files

| Rule | Applied |
|---|---|
| Header | `<?xml version="1.0" encoding="UTF-8"?>` then `<svg xmlns="http://www.w3.org/2000/svg" width=… height=… viewBox="0 0 W H">` (existing dimensions kept; two diagrams grew slightly to fit content) |
| Encoding | UTF-8, no BOM, LF line endings, no control characters |
| Styling | Internal `<style>` rules inlined as presentation attributes; `rx` moved from CSS (an SVG 2 geometry property that some renderers ignore) to the `rx` attribute |
| Fonts | `font-family="Arial, Helvetica, sans-serif"` everywhere (several files used `Segoe UI` with no fallback, which renders as a serif font off Windows) |
| Glyphs | `✓` (not in Arial/Helvetica) drawn as a polyline; standalone arrow glyphs drawn as line + polygon |
| Arrows | Every `marker-end` references a `<marker>` defined in the same file; every arrowhead terminates on a box edge |
| Accessibility | Every file has `<title>`; `role="img"` and `aria-label` on the root |

---

## Validation method

All checks ran locally; temporary PNGs were written outside the repository and deleted afterwards.

1. **XML parse** of every file (Python `xml.etree` / `xml.dom.minidom`), strict UTF-8 decode, control-character scan.
2. **Construct scan**: `<image`, `href=`, `xlink:href=`, `data:`, `foreignObject`, `<script`, `<style`, `@font-face`, `@import`, `url(`, external `http(s)://` references, filters, masks, clip paths, animation.
3. **Reference check**: every `url(#id)` resolves; no unused IDs.
4. **`<img>` load test** in headless Microsoft Edge (Chromium) — mirrors how GitHub embeds SVG.
5. **Standalone render** of each SVG to PNG at native size in headless Edge.
6. **Geometry checks** on the rendered DOM: text overflowing its box or the viewBox, partially overlapping boxes, arrowheads ending in open space, open paths inheriting the default black fill.
7. **Visual review** of every PNG (all 44 diagrams, including the 10 priority diagrams listed in the audit request).
8. **Markdown link audit**: 198 Markdown files, 84 SVG links + 28 SVG image embeds — all resolve to tracked files with exact case; no `file://`, `vscode-file://`, or Windows absolute paths.
9. **Git view**: all SVGs tracked as text (`i/lf`), first bytes `<?xml`, not binary / PNG / HTML.
10. **Secret scan**: no credentials, tokens, account IDs, ARNs, passwords, or private keys. Lab identifiers already published throughout the docs (image digest, VPC CIDR, host-only VIP, destroyed EBS volume / EC2 instance IDs) were left as architecture data.

**GitHub preview:** columns below reflect local validation. "GitHub Safe" means the file meets the
GitHub-safe rules in [svg-authoring-guidelines.md](./svg-authoring-guidelines.md); it is not a claim that
each file's GitHub preview was individually re-checked.

---

## Per-file results

| SVG | XML Valid | GitHub Safe | External Images | foreignObject | External CSS | Local Render | Visual Review | Status | Change |
|---|---|---|---|---|---|---|---|---|---|
| `ansible-architecture.svg` | PASS | PASS | none | none | none (inline `<style>` removed) | PASS | PASS | **FIXED** | VMware node was not connected - fan-out redrawn |
| `argo-advanced-gitops-reference.svg` | FIXED | PASS | none | none | none (inline `<style>` removed) | PASS | PASS | **FIXED** | 3 corrupted chars (`·`, `—`); fixed overlapping Child Apps / Sync Windows boxes; Git arrow now fans out to ApplicationSet and App-of-Apps |
| `argo-app-of-apps.svg` | FIXED | PASS | none | none | none (inline `<style>` removed) | PASS | PASS | **FIXED** | 1 corrupted char (`—`); middle child was not connected - fan-out redrawn |
| `argo-applicationset.svg` | FIXED | PASS | none | none | none (inline `<style>` removed) | PASS | PASS | **FIXED** | bare `&` (truncated `…`) - **the reported GitHub error**; redrawn with ApplicationSet boundary, per-app resources |
| `argo-enterprise-gitops-composition.svg` | FIXED | PASS | none | none | none (inline `<style>` removed) | PASS | PASS | **FIXED** | 5 corrupted chars (`·`); fan-out arrows re-centred, stray bus arrowheads removed |
| `argo-project-security.svg` | PASS | PASS | none | none | none (inline `<style>` removed) | PASS | PASS | **FIXED** | arrows to Source repos / Resources ended in open space - fan-out redrawn |
| `argo-sync-lifecycle.svg` | FIXED | PASS | none | none | none (inline `<style>` removed) | PASS | PASS | **FIXED** | 3 corrupted chars (`→`) |
| `automation-vs-gitops.svg` | PASS | PASS | none | none | none (inline `<style>` removed) | PASS | PASS | **FIXED** | dashed arrow stopped short and overlapped its label - now routes to Git desired state |
| `aws-ebs-az-constraint.svg` | FIXED | PASS | none | none | none (inline `<style>` removed) | PASS | PASS | **FIXED** | 3 corrupted chars (`—`, `✓`); check mark drawn as polyline (glyph absent from Arial) |
| `aws-ebs-node-failure-recovery.svg` | FIXED | PASS | none | none | none (inline `<style>` removed) | PASS | PASS | **FIXED** | 17 corrupted chars (`—`, `→`, `·`, `≈` was `H`); AZ arrows now land on worker boxes |
| `aws-iam-vs-kubernetes-rbac.svg` | FIXED | PASS | none | none | none (inline `<style>` removed) | PASS | PASS | **FIXED** | 8 corrupted chars (`↑`, `…` was bare `&`, `—`, `→`) |
| `aws-storage-pod-recovery.svg` | FIXED | PASS | none | none | none (inline `<style>` removed) | PASS | PASS | **FIXED** | 8 corrupted chars (`—`, `·`) |
| `aws-storage-statefulset.svg` | FIXED | PASS | none | none | none (inline `<style>` removed) | PASS | PASS | **FIXED** | 13 corrupted chars (`—`, `·`, `→`) |
| `disaster-recovery-architecture.svg` | FIXED | PASS | none | none | none (inline `<style>` removed) | PASS | PASS | **FIXED** | 8 corrupted chars (`·`); Terraform box no longer overlaps Kubernetes |
| `dr-dependency-graph.svg` | FIXED | PASS | none | none | none (inline `<style>` removed) | PASS | PASS | **FIXED** | 8 corrupted chars (`·`) |
| `ebs-snapshot-recovery.svg` | PASS | PASS | none | none | none (inline `<style>` removed) | PASS | PASS | **FIXED** | connector started inside and struck through the Snapshot handle label |
| `eks-recovery-flow.svg` | FIXED | PASS | none | none | none (inline `<style>` removed) | PASS | PASS | **FIXED** | 2 corrupted chars (`·`) |
| `kubernetes-rbac-model.svg` | FIXED | PASS | none | none | none (inline `<style>` removed) | PASS | PASS | **FIXED** | 1 corrupted char (`×`) |
| `kubernetes-security-layers.svg` | FIXED | PASS | none | none | none (inline `<style>` removed) | PASS | PASS | **FIXED** | 14 corrupted chars (`·`, `—`, `→`) |
| `platform-failure-domain.svg` | PASS | PASS | none | none | none | PASS | PASS | **PASS** | title / aria-label added |
| `platform-operating-model.svg` | PASS | PASS | none | none | none | PASS | PASS | **FIXED** | connectors under Kubernetes misaligned (Network/Observability unconnected); dangling stub removed; title added |
| `platform-operations-lifecycle.svg` | PASS | PASS | none | none | none | PASS | PASS | **PASS** | title / aria-label added |
| `platform-runbook-map.svg` | PASS | PASS | none | none | none | PASS | PASS | **PASS** | title / aria-label added |
| `project1-application-lifecycle.svg` | PASS | PASS | none | none | none (inline `<style>` removed) | PASS | PASS | **PASS** | standardised only |
| `project1-automation-boundaries.svg` | PASS | PASS | none | none | none | PASS | PASS | **PASS** | standardised only |
| `project1-automation-reference.svg` | PASS | PASS | none | none | none (inline `<style>` removed) | PASS | PASS | **FIXED** | `?` restored to `≠` (Jenkins ≠ kubectl deploy apps); fan-out arrows fixed |
| `project1-control-and-data-plane.svg` | FIXED | PASS | none | none | none | PASS | PASS | **FIXED** | 4 corrupted chars (`—`, `·`) + 4 `?` in labels restored to `→`; 3 standalone `?` arrow glyphs redrawn as line + polygon |
| `project1-dr-architecture.svg` | FIXED | PASS | none | none | none | PASS | PASS | **FIXED** | 17 corrupted chars (`—`, `·`) + 4 `?` restored to `→` |
| `project1-final-study-architecture.svg` | PASS | PASS | none | none | none (inline `<style>` removed) | PASS | PASS | **PASS** | standardised only |
| `project1-learning-dependencies.svg` | PASS | PASS | none | none | none (inline `<style>` removed) | PASS | PASS | **PASS** | standardised only |
| `project1-learning-map.svg` | PASS | PASS | none | none | none (inline `<style>` removed) | PASS | PASS | **PASS** | standardised only |
| `project1-reference-architecture.svg` | FIXED | PASS | none | none | none | PASS | PASS | **FIXED** | 6 corrupted chars (`—`, `·`); DR note box widened (text overflowed) |
| `project1-reliability-stack.svg` | FIXED | PASS | none | none | none | PASS | PASS | **FIXED** | 4 corrupted chars (`·`) |
| `project1-security-architecture.svg` | PASS | PASS | none | none | none | PASS | PASS | **PASS** | standardised only |
| `python-ansible-orchestration.svg` | PASS | PASS | none | none | none (inline `<style>` removed) | PASS | PASS | **FIXED** | `?` restored to `→` in the title |
| `python-automation-stack.svg` | PASS | PASS | none | none | none (inline `<style>` removed) | PASS | PASS | **FIXED** | stray arrowheads on the fan-in bus removed |
| `rollback-decision-tree.svg` | PASS | PASS | none | none | none | PASS | PASS | **FIXED** | open elbow paths filled black by default; Yes/No branches ended in open space - redrawn |
| `serviceaccount-security.svg` | FIXED | PASS | none | none | none (inline `<style>` removed) | PASS | PASS | **FIXED** | 5 corrupted chars (`→`, `·`) |
| `storage-resilience-vmware-vs-aws.svg` | FIXED | PASS | none | none | none (inline `<style>` removed) | PASS | PASS | **FIXED** | 11 corrupted chars (`—`, `→`) |
| `storage-vmware-vs-aws.svg` | FIXED | PASS | none | none | none (inline `<style>` removed) | PASS | PASS | **FIXED** | 12 corrupted chars (`—`, `→`, `·`) |
| `vmware-storage-pod-recovery.svg` | FIXED | PASS | none | none | none (inline `<style>` removed) | PASS | PASS | **FIXED** | 4 corrupted chars (`—`, `→`, `·`) |
| `vmware-storage-statefulset.svg` | FIXED | PASS | none | none | none (inline `<style>` removed) | PASS | PASS | **FIXED** | 10 corrupted chars (`—`, `·`, `→`, `≠` was a backtick) |
| `vmware-vs-aws-dr.svg` | FIXED | PASS | none | none | none (inline `<style>` removed) | PASS | PASS | **FIXED** | 6 corrupted chars (`·`, `—`); AWS note line sat outside its panel - panels extended |
| `vmware-vs-aws-storage-abstraction.svg` | FIXED | PASS | none | none | none (inline `<style>` removed) | PASS | PASS | **FIXED** | 4 corrupted chars (`—`, `·`) + 8 `?` restored to `→` |

`XML Valid = FIXED` means the file failed XML parsing before this change and now parses.
`Status = FIXED` means the file failed parsing and/or had a visual defect that was corrected;
`PASS` means only the common standardisation was applied.

---

## Out of scope / follow-ups

- `docs/argo-advanced-patterns.md` (Markdown, not SVG) contains 4 control characters where inline-code
  backticks were consumed as PowerShell escapes (`` `a `` → BEL, `` `b `` → backspace) around
  `argo-advanced-stage`, `app-child-*`, and `backoff`. Not changed here.

Related: [svg-authoring-guidelines.md](./svg-authoring-guidelines.md) · [diagram index](../diagrams/README.md)
