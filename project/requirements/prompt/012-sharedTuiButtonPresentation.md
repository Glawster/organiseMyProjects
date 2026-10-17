# 012: Implement shared tui button presentation

Implement requirement 012: Shared TUI button presentation.

Use the OMP-managed shared TUI stylesheet/guidance as the canonical source for standard button presentation across conforming TUI applications.

Required convention:

- standard buttons are exactly one terminal row high;
- no vertical padding or border may clip or vertically misalign the label;
- foreground/background styling is consistent unless an explicit semantic variant applies;
- adjacent buttons in one logical group use equal sizing where appropriate;
- adjacent horizontal buttons have a one-column gap;
- button groups have one row of spacing from surrounding content or frame boundaries;
- screen-specific height/border/padding overrides that merely reproduce the standard style should be removed.

Adoption case:

- update the shared style so `mailAgent` can remove its execution-screen-specific button height/border overrides;
- do not change `clannEolas`, which deliberately uses its own stylesheet.

Add focused tests or style-level regression coverage where practical, document the convention, and preserve intentional semantic button variants without weakening the shared sizing/spacing rules.
