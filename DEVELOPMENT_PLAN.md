# Development Plan — Not-Meta Prompt Library

> Architecture blueprint for next-iteration enhancements and ecosystem integration.

---

## 1. Current Architecture (v1.0)

```
MainWindow
├── LibraryPanel         (SRP: display + CRUD UI)
│   └── PromptCard[]     (SRP: single card widget)
│       └── CreatePromptDialog (SRP: form modal)
└── ComposePanel         (SRP: prefix + body + suffix composition)

Services (injected, platform-agnostic)
├── PromptService        (SRP: CRUD + observer bus)
├── StorageService       (SRP: JSON file I/O)
├── ComposeService       (SRP: text assembly algorithm)
└── ClipboardService     (SRP: clipboard adapter)

Models (zero logic)
├── Prompt               (domain entity + serialisation)
└── LibraryState         (aggregate snapshot)
```

**SOLID compliance:**
- **S** – Every class has one reason to change
- **O** – Services use abstract interfaces; UI never instantiates services
- **L** – Any `StorageService` replacement must load/save `LibraryState` ✓
- **I** – `ClipboardService` is separated from persistence concern
- **D** – `MainWindow` depends on abstractions, not concrete implementations

---

## 2. Roadmap

### v1.1 – Stability & Polish ✅ SHIPPED
- [x] Keyboard shortcut overlay (`Ctrl+N` = new, `Ctrl+F` = search, `Ctrl+E` = compose)
- [x] Drag-and-drop reorder for prefix/suffix selection lists (`DragSortableList` widget)
- [x] Inline editing directly on the card (double-click name or content to edit in-place)
- [x] Category filter chips (horizontal scrollable chip bar above prompt list)
- [x] "Clear all selections" button in compose panel header

### v1.2 – SQLite Storage (local-only)
> This is a local-only exe. No cloud, no sync — all data stays in `%LOCALAPPDATA%\NotMetaPromptLibrary\`.
- [ ] Extract `IStorageBackend` Protocol: `load() → LibraryState`, `save(state) → None`
- [ ] Implement `SQLiteStorageBackend` (`prompts.db`) for indexed search and faster ranked queries
- [ ] Keep `JSONStorageBackend` (current impl) as the default fallback for portability
- [ ] `StorageService` becomes a thin facade that delegates to the active backend
- [ ] One-time migration: detect existing `prompts.json` on first launch and import into SQLite

```python
class IStorageBackend(Protocol):
    def load(self) -> LibraryState: ...
    def save(self, state: LibraryState) -> None: ...

class StorageService:
    def __init__(self, backend: IStorageBackend) -> None: ...
```

### v1.3 – Plugin / Extension Layer (OCP)
- [ ] `IPromptTransformer` interface: `transform(text: str) → str`
- [ ] Built-in transformers: `UpperCaseTransformer`, `TrimTransformer`, `MarkdownEscapeTransformer`
- [ ] Transformer pipeline selectable per compose action

### v1.4 – Import / Export & Portability
> Local-only. No WebSocket, no cloud sync, no external services.
- [ ] **JSON export**: one-click full library export to a timestamped `.json` file (already partially present)
- [ ] **JSON import with merge**: import from a file, deduplicate by name, choose overwrite or skip
- [ ] **Clipboard export**: copy entire library as formatted Markdown table
- [ ] **ECA-Hive import**: parse `HivePromptLibrary` localStorage JSON dump (schema v2) for migration from the browser extension

### v1.5 – UX Polish
- [ ] System tray icon (minimize to tray instead of closing)
- [ ] Pinned/floating always-on-top mode
- [ ] Dark/light theme toggle
- [ ] Per-category color coding

---

## 3. Testing Strategy

| Layer | Tool | Scope |
|-------|------|-------|
| Models | `pytest` | Serialise / deserialise round-trips |
| Services | `pytest` + `unittest.mock` | CRUD, compose, observer notifications |
| UI widgets | `pytest-tk` | Smoke tests for PromptCard rendering |
| Integration | `pytest` + temp dir fixtures | Full save → load → compose flow |

```bash
# Run all tests
python -m pytest tests/ -v
```

---

## 4. File Conventions

- File names: `snake_case`
- Class names: `PascalCase`
- Services return domain objects, never raw dicts
- No `Any` types — use typed dataclasses or `TypedDict`
- Observer callbacks use `Callable[[LibraryState], None]` signature
- All UI constants in `AppTheme` — zero hardcoded hex values in widgets

---

## 5. Build & Release Process

```
Tag v1.x.y
→ GitHub Actions workflow
→ build.ps1 on windows-latest runner
→ Upload dist/PromptLibrary.exe as release asset
→ SHA256 checksum attached
```

Planned CI: `.github/workflows/build.yml` with `actions/upload-artifact`.

---

*This plan is a living document — update after each completed milestone.*
