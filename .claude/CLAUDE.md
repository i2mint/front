# front

Backend-agnostic core library for dispatching Python functions as webservices,
Docker containers and GUIs. Compiles a short-language configuration into a spec
(`SpecMakerBase`), builds a UI element tree from it (`ElementTreeMaker`), and
assembles the app (`AppMaker`). Concrete UI frameworks (e.g. `streamlitfront`)
build on `front`; `front` itself renders nothing.

## Module map (`front/`)

- `app_maker.py` — `AppMaker`: configuration + convention -> compiled spec -> app.
- `spec_maker_base.py` — the "short language -> long language" compiler:
  builds a `FrontSpec` from a configuration.
- `elements/` — `tree_maker_base.py` (`ElementTreeMaker`), `elements.py`
  (the dataclass-based composite element tree — no bitflags, despite some old
  issue language), `implementation.py`.
- `crude.py` — **CRUDE = CRUD-Execution**: `Crudifier` / `prepare_for_crude_dispatch`
  let functions with complex arguments be operated through string keys into
  stores (mall-backed). This is the mature machinery several old open issues
  (store access, param handling) turn out to already be substantially solved by.
- `dag.py` — crudifies the variable nodes of a `meshed` DAG (the producing
  function's output gets stored and referenced by key).
- `data_binding.py` / `state.py` — `BoundData` wraps a keyed slot in `State`,
  connecting element values to a backing store; `GetterSetter`/`StateType`/`Forbidden`.
- `py2pydantic.py` — bridges plain functions to pydantic v2 input models.
- `base.py` — `prepare_for_dispatch`: chains the wrappers a UI needs.
- `tools.py`, `util.py`, `types.py` — general helpers, signature/mapping
  utilities, shared type aliases/dataclasses (`Configuration`, etc.).

## Tests & lint (verified)

```bash
uv venv .venv && uv pip install -e . pytest ruff
.venv/bin/pytest -v --tb=short   # tests/ + front/ (incl. front/tests and module doctests)
.venv/bin/ruff check .
```
`[tool.pytest.ini_options]` sets `testpaths = ["tests", "front"]` and
`addopts = --doctest-modules --ignore=front/examples --ignore=front/scrap`, so a
bare `pytest` (locally and in the wads CI) runs `tests/`, `front/tests/` and every
module doctest. Before that, CI collected only `tests/`, which is how the
`front/dag.py` doctests broke unnoticed (i2mint/front#47).

## Docs

No `docs/`, ADRs, or shipped skills in this repo currently.

## Dependents

`extrude`, `opyratorfront`, `streamlitfront` import this package — check their
tests before changing `AppMaker`, `SpecMakerBase`, `Crudifier`, or the element
tree shape. `front` itself depends on `i2` and `meshed`.
