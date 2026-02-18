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

### v1.2 – Storage Abstraction (SRP evolution)
- [ ] Extract `IStorageBackend` interface: `load() → LibraryState`, `save(state) → None`
- [ ] Implement `SQLiteStorageBackend` for indexed search performance
- [ ] Implement `CloudStorageBackend` (Neon REST or Supabase) for cross-device sync
- [ ] `StorageService` becomes a facade that delegates to the active backend

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

### v1.4 – Not-Meta Ecosystem Integration
- [ ] **WebSocket Gateway**: expose a local WS server (`ws://127.0.0.1:9010`) that the Hydrogen frontend can connect to for library sync
- [ ] **IPC Protocol**: define JSON message schema for `PROMPT_COPY`, `PROMPT_CREATE`, `STATE_SYNC`
- [ ] **ECA-Hive bridge**: re-use `HivePromptLibrary` localStorage format (schema v2) for seamless import
- [ ] **Shared type definitions**: extract `PromptEntry` type to a shared TypeScript + Python codegen contract

```
Not-Meta Hydrogen (browser)
    ↕ WebSocket (port 9010)
PromptLibrary.exe (Python)
    ↕ JSON file / SQLite
%LOCALAPPDATA%\NotMetaPromptLibrary\
```

### v1.5 – Multi-user / Collaboration
- [ ] Named "workspaces" (personal, team-a, project-x)
- [ ] Read-only shared libraries via URL share (export → Gist import)
- [ ] Role-based access control preparation

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
