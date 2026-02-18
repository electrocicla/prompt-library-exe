# Not-Meta Prompt Library

A standalone Windows desktop application for managing and composing AI prompts — extracted from the **Not-Meta ECA-Hive VS Code Studio** panel.

Built with Python + customtkinter for a native dark UI. No Electron, no browser.

---

## Features

- **Prompt Library** — Create, edit, delete, and star prompts with categories and roles
- **Role System** — Assign each prompt as `Body`, `Prefix`, or `Suffix`
- **Multi-select Composition** — Check any number of prefixes + write a body + check any number of suffixes → compose into a single string and copy to clipboard
- **Copy on click** — Every prompt card has a one-click copy button
- **Usage-ranked list** — Most-used prompts float to the top automatically
- **Search** — Instant filter across name, content, and category
- **Favourites** — Star important prompts for a score boost
- **Export / Import** — JSON backup and restore with merge or replace mode
- **Separator options** — New line, space, blank line, or custom separator between parts
- **Resizable panels** — Drag the divider between Library and Compose panels; minimum widths enforced
- **Panel toggles** — Hide or show Library and Compose panels independently via toolbar buttons or keyboard shortcuts
- **Persistent layout** — Window size, sash position, and panel visibility are saved and restored between sessions
- **Persistent storage** — Prompts saved to `%LOCALAPPDATA%\NotMetaPromptLibrary\prompts.json`

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New prompt |
| `Ctrl+F` | Focus search |
| `Ctrl+E` | Compose & copy |
| `Ctrl+[` | Toggle Library panel |
| `Ctrl+]` | Toggle Compose panel |
| `Ctrl+W` | Close application |

---

## Quick Start

### Run from source

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src/main.py
```

### Build .exe

```powershell
.\build.ps1
# Output: dist/PromptLibrary.exe
```

---

## Project Structure

```
prompt-library-exe/
├── src/
│   ├── main.py                        # Entry point
│   ├── models/
│   │   ├── prompt.py                  # Prompt domain model
│   │   └── library_state.py           # Serialisable state container
│   ├── services/
│   │   ├── storage_service.py         # JSON file persistence
│   │   ├── prompt_service.py          # CRUD + observer notifications
│   │   ├── compose_service.py         # Prefix/body/suffix composition
│   │   └── clipboard_service.py       # Clipboard abstraction
│   └── ui/
│       ├── app_theme.py               # Colour & font constants
│       ├── main_window.py             # Root CTk window + DI wiring
│       ├── panels/
│       │   ├── library_panel.py       # Left panel: list + toolbar
│       │   └── compose_panel.py       # Right panel: compose + copy
│       ├── widgets/
│       │   └── prompt_card.py         # Single prompt card widget
│       └── dialogs/
│           └── create_prompt_dialog.py # Create / edit modal
├── assets/
│   └── generate_icon.py               # Icon generator (Pillow)
├── build.ps1                            # PowerShell build script
├── requirements.txt                     # Runtime + build dependencies
└── LICENSE                              # MIT
```

---

## Architecture

This project follows **SOLID** and **SRP** principles:

| Layer | Responsibility |
|-------|---------------|
| `models/` | Pure data definitions, no I/O or UI |
| `services/` | Single-purpose business logic, no UI coupling |
| `ui/` | Presentation only, no direct persistence |
| `assets/` | Static resources |

Services are wired together in `MainWindow` (Dependency Injection). Panels communicate through `PromptService` observer callbacks — they never talk to each other directly.

---

## Requirements

- Python 3.10+
- Windows 10/11 (for the .exe build)
- customtkinter ≥ 5.2.2
- Pillow ≥ 10.0.0
- PyInstaller ≥ 6.0.0 (build only)

---

## License

MIT — see [LICENSE](LICENSE)

---

*Part of the [Not-Meta](https://github.com/not-meta) ecosystem.*
