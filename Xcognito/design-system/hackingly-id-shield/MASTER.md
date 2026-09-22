# Design System Master File

> **LOGIC:** When building a specific page, first check `design-system/pages/[page-name].md`.
> If that file exists, its rules **override** this Master file.
> If not, strictly follow the rules below.

---

**Project:** Hackingly ID-Shield  
**Updated:** 2026-09-18  
**Category:** AI Identity Verification & Eligibility Platform  
**Style Direction:** Bold Structured Neo-Brutalist / Editorial System  
**Design Dials:** Variance 8/10 (Bold / Asymmetric) | Motion 4/10 (Snappy / Micro-interactions) | Density 8/10 (Dense / Operational Dashboard)

---

## Global Rules

### Color Palette

| Role | Hex | CSS Variable | Usage |
|------|-----|--------------|-------|
| Rust | `#BA5A5A` | `--color-rust` | Rejections, critical fraud alerts, destructive actions |
| Yellow | `#F7E49B` | `--color-yellow` | Manual triage queue, warnings, inspection badges |
| Sage | `#A4CE8B` | `--color-sage` | Approvals, success states, verified checks |
| Teal | `#86BCBD` | `--color-teal` | Primary brand accent, active tabs, primary CTAs |
| Page Background | `#F4F5F7` | `--color-bg` | Global body background |
| Card / Sidebar | `#FFFFFF` | `--color-card` | Surface background for all cards, forms, tables, modals |
| Primary Text & Borders | `#2D3748` | `--color-border-dark` | 2-4px outlines, primary text, high-contrast headings |
| Secondary Text | `#4A5568` | `--color-text-secondary` | Labels, subtitles, descriptive text |
| Neutral Borders | `#CBD5E0` | `--color-border-neutral` | Subtle dividers and inactive input borders |

**Design Principles:**
- No gradients, glassmorphism, glossy overlays, or blurred shadows.
- Solid, purposeful color blocking paired with icons/text so meaning never relies on color alone.
- 2–4px solid dark borders (`#2D3748`).
- Small 2–4px corner radii for boxes; pill shapes (`9999px`) reserved selectively for status badges.
- Hard offset shadows with NO blur (e.g., `4px 4px 0px #2D3748`).

---

### Typography

- **Interface & Headings:** `Inter` (Heavy, tightly spaced uppercase headings)
- **Numbers, Metrics & Identifiers:** `JetBrains Mono`
- **Text Hierarchy:** Reserve uppercase strictly for headings, navigation, and compact tags—never paragraphs.

**CSS Import:**
```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700;800&display=swap');
```

---

### Shadows & Elevation

Hard offset box-shadows without blur:

| Token | Value | Usage |
|-------|-------|-------|
| Small Shadow | `2px 2px 0px #2D3748` | Small badges, active indicators |
| Medium Shadow | `4px 4px 0px #2D3748` | Standard cards, tables, inputs on focus |
| Large / Hover | `5px 5px 0px #2D3748` | Lifted state on interactive hover |
| Active / Pressed | `1px 1px 0px #2D3748` | Depressed / clicked button state |

---

## Component Specs

### Buttons
Thick 2px borders, 4px corner radii, hard offset shadow:
```css
.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  border-radius: 4px;
  font-family: var(--font-sans);
  font-weight: 800;
  text-transform: uppercase;
  border: 2px solid #2D3748;
  box-shadow: 2px 2px 0px #2D3748;
  transition: transform 150ms ease, box-shadow 150ms ease;
  cursor: pointer;
}
.btn:hover:not(:disabled) {
  transform: translate(-2px, -2px);
  box-shadow: 4px 4px 0px #2D3748;
}
.btn:active:not(:disabled) {
  transform: translate(1px, 1px);
  box-shadow: 1px 1px 0px #2D3748;
}
.btn-primary {
  background-color: #86BCBD; /* Teal */
  color: #2D3748;
}
.btn-secondary {
  background-color: #FFFFFF;
  color: #2D3748;
}
.btn-danger {
  background-color: #BA5A5A; /* Rust */
  color: #FFFFFF;
}
.btn-success {
  background-color: #A4CE8B; /* Sage */
  color: #2D3748;
}
```

### Cards
White surfaces, 2px dark outlines, offset shadows, and selective colored accent edges:
```css
.card {
  background: #FFFFFF;
  border: 2px solid #2D3748;
  border-radius: 4px;
  box-shadow: 4px 4px 0px #2D3748;
  padding: 24px;
}
.card-accent-teal {
  border-left: 6px solid #86BCBD !important;
}
```

### Badges & Alerts
Solid palette colors paired with text or icons:
```css
.badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  border-radius: 9999px; /* Selective pill shape */
  font-size: 0.72rem;
  font-weight: 800;
  text-transform: uppercase;
  border: 2px solid #2D3748;
}
.badge-approved { background-color: #A4CE8B; color: #2D3748; }
.badge-review   { background-color: #F7E49B; color: #2D3748; }
.badge-rejected { background-color: #BA5A5A; color: #FFFFFF; }
.badge-teal     { background-color: #86BCBD; color: #2D3748; }
```

### Forms & Precision Controls
- Inputs: White `#FFFFFF`, border `2px solid #CBD5E0`, on focus `2px solid #2D3748` with `2px 2px 0px #2D3748` shadow.
- Range sliders: Accent color `#86BCBD`, no transforms on hover to avoid jitter during drag.

---

## Anti-Patterns (Forbidden)
- ❌ Gradients as backgrounds or button fills.
- ❌ Glassmorphism (`backdrop-filter: blur(...)`).
- ❌ Soft/blurred box shadows (`rgba(0,0,0,0.15) 0 8px 30px`).
- ❌ Moving slider thumbs or precision controls with hover transforms.
- ❌ Generic emojis as system icons (use Lucide / Phosphor vector SVGs).
- ❌ Relying solely on color for state (always pair with text label or icon).
