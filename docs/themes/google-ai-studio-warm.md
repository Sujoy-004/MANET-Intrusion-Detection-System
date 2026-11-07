# Google AI Studio Warm Theme

A modern, warm-white editorial theme inspired by Google AI Studio's signature clean canvas aesthetic, balancing visual comfort, high readability, and professional AI engineering presence.

## Color Palette

| Role | Color Name | Hex Code | Visual Application |
|------|------------|----------|-------------------|
| **Canvas Background** | Warm Alabaster | `#f9f9f6` | Soft, glare-free warm-white foundation |
| **Surfaces & Cards** | Paper White | `#ffffff` | Crisp, elevated component containers |
| **Panels & Dividers** | Warm Sand | `#f1f0ea` | Neutral framing, sub-panels, and separators |
| **Primary Text** | Obsidian Charcoal | `#1f1f1f` | Deep warm ink for clear, strain-free reading |
| **Secondary Text** | Studio Slate | `#5f6368` | Subtle secondary labels and metadata |
| **Primary Brand Accent** | Gemini Blue | `#1a73e8` | Interactive actions, active tabs, and navigation |
| **Secondary Accent** | Deep Indigo | `#0b57d0` | Focus states and informational accents |
| **Highlight Accent** | Gemini Sparkle Violet | `#7c3aed` | Model badges and special features |
| **Success / Healthy** | Google Studio Green | `#137333` | Normal operations and positive verification |
| **Warning / Degraded** | Horizon Amber | `#b06000` | Caution notices and threshold warnings |
| **Error / Intrusion** | Crimson Red | `#c5221f` | Critical alerts, attack detection, and errors |

## Typography & Font System

- **Headers & Display**: `Google Sans`, `Outfit`, `Inter` (Bold, clean geometric sans-serif)
- **Body & Content Text**: `Roboto`, `Google Sans Text` (Regular, balanced proportional spacing)
- **Code & Terminal Monospace**: `Google Sans Code`, `JetBrains Mono`, `Fira Code` (Crisp technical glyphs)

## Terminal & TUI Implementation

In Textual TUI (`manet`), the theme is registered as `manet-ai-studio-warm` with `dark=False`:
- Background: `#f9f9f6`
- Surface: `#ffffff`
- Panel: `#f1f0ea`
- Foreground: `#1f1f1f`
- Primary: `#1a73e8`
- Secondary: `#0b57d0`
- Accent: `#7c3aed`
- Semantic mappings:
  - `$navigation-cyan`: `#1a73e8` (Google Blue)
  - `$info-blue`: `#0b57d0` (Deep Indigo)
  - `$healthy-green`: `#137333` (Google Green)
  - `$warning-amber`: `#b06000` (Amber)
  - `$critical-red`: `#c5221f` (Crimson)
  - `$footer-key-foreground`: `#1a73e8`
