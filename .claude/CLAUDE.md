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
.venv/bin/pytest -v --tb=short              # testpaths=["tests"] only: 1 passed (see gotcha)
.venv/bin/pytest --doctest-modules front/ --ignore=front/examples --ignore=front/scrap  # 62 passed
.venv/bin/pytest front/tests                 # 15 passed — NOT in testpaths, run explicitly
.venv/bin/ruff check .
```
**Gotcha:** `[tool.pytest.ini_options].testpaths = ["tests"]` means a bare
`pytest` run collects only the one-test `tests/test_smoke.py` — `front/tests/`
(15 tests: crude, py2pydantic, state, combos, use-case) and the module doctests
must be run explicitly, as above, to actually exercise the package. `wads
ci-local` covers all three via its own invocation; a bare `pytest` locally does not.

## Docs

No `docs/`, ADRs, or shipped skills in this repo currently.

## Dependents

`extrude`, `opyratorfront`, `streamlitfront` import this package — check their
tests before changing `AppMaker`, `SpecMakerBase`, `Crudifier`, or the element
tree shape. `front` itself depends on `i2` and `meshed`.
