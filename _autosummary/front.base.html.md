# front.base

Base functions for front dispatching: `prepare_for_dispatch` chains the wrappers a UI needs.

### Functions

| `prepare_for_dispatch`([func, ...])   | Prepare `func` for dispatch: crudify, annotate cruded params with Enums, fix defaults.   |
|---------------------------------------|------------------------------------------------------------------------------------------|
