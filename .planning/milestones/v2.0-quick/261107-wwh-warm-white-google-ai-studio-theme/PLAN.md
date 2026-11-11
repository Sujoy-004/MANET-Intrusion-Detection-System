# Quick Task: Google AI Studio Warm-White Theme & Typography

**Slug:** warm-white-google-ai-studio-theme  
**Date:** 2026-11-07  
**Status:** complete  

## Objective
Implement a professional warm-white theme inspired by Google AI Studio's design direction ("Gemini Warm Canvas") with matched modern typography, adding custom theme definitions to Theme Factory, registering the theme in the MANET TUI runtime, and providing dynamic theme toggling via command palette and actions.

## Tasks
- [x] Task 1: Create Google AI Studio Warm theme specification in Theme Factory skill library (`theme-factory/themes/google-ai-studio-warm.md`) and project docs (`docs/themes/google-ai-studio-warm.md`).
- [x] Task 2: Implement `AI_STUDIO_WARM` (`manet-ai-studio-warm`) theme in `manet/runtime/theme.py` with warm-alabaster background (`#f9f9f6`), clean surface (`#ffffff`), charcoal ink foreground (`#1f1f1f`), Gemini blue accent (`#1a73e8`), and full semantic color mappings.
- [x] Task 3: Register `AI_STUDIO_WARM` in `manet/app.py` with `action_toggle_warm_theme` and `action_set_theme`.
- [x] Task 4: Add `theme-warm` command in `manet/commands/registry.py` for console and palette invocation.
- [x] Task 5: Add automated unit and pilot tests in `tests/test_manet_theme.py` covering theme registration, semantic variables, and dynamic toggling.
