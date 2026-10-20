"""Tooltips for functions and their arguments.

Backend-agnostic helpers that compute tooltip text, to be attached to the specs/elements
a UI framework renders.

Function tooltips are a function of the docs (``func_tooltip``): the first non-blank
line, the first few lines, or everything before the first doctest -- or an explicit string.

Argument tooltips (``param_tooltips``) are parsed from the docs (numpy, google and rest
styles are tried), overridden by a ledger (mapping) of explicit tooltips; and the params
can be selected with ``include`` / ``exclude``.

>>> def foo(a, b=2):
...     '''Add things.
...
...     More details here.
...
...     :param a: the first thing
...     :param b: the second thing
...
...     >>> foo(1)
...     3
...     '''
>>> func_tooltip(foo)
'Add things.'
>>> func_tooltip(foo, style='before_doctest')
'Add things.\\n\\nMore details here.\\n\\n:param a: the first thing\\n:param b: the second thing'
>>> func_tooltip(foo, style='Explicit text')
'Explicit text'
>>> param_tooltips(foo)
{'a': 'the first thing', 'b': 'the second thing'}
>>> param_tooltips(foo, exclude=['b'], ledger={'a': 'override'})
{'a': 'override'}
"""

import inspect
from typing import Callable, Iterable, Mapping, Optional

DFLT_N_LINES = 3
DFLT_ELLIPSIS = "... (+more)"
DFLT_DOC_STYLES = ("numpy", "google", "rest")
FUNC_TOOLTIP_STYLES = ("first_line", "first_lines", "before_doctest")


def func_tooltip(
    func: Callable,
    style: str = "first_line",
    *,
    n_lines: int = DFLT_N_LINES,
    ellipsis: str = DFLT_ELLIPSIS,
) -> str:
    """Tooltip for a function.

    :param style: One of ``'first_line'`` (first non-blank line, stripped),
        ``'first_lines'`` (first ``n_lines`` non-blank lines, with ``ellipsis`` if cut),
        ``'before_doctest'`` (everything before the first doctest), or any other string,
        which is taken as the explicit tooltip.
    """
    if style not in FUNC_TOOLTIP_STYLES:
        return style
    doc = inspect.getdoc(func) or ""
    if style == "before_doctest":
        lines = []
        for line in doc.splitlines():
            if line.lstrip().startswith(">>>"):
                break
            lines.append(line)
        return "\n".join(lines).strip()
    lines = [line.strip() for line in doc.splitlines() if line.strip()]
    if style == "first_line":
        return lines[0] if lines else ""
    text = "\n".join(lines[:n_lines])
    return f"{text}\n{ellipsis}" if len(lines) > n_lines else text


def _parsed_param_docs(func: Callable, doc_styles: Iterable[str]) -> dict:
    from i2.doc_mint import docstring_to_params

    doc = inspect.getdoc(func) or ""
    for doc_style in doc_styles:
        try:
            params = docstring_to_params(doc, doc_style=doc_style)
        except Exception:  # style doesn't match this docstring: try the next
            continue
        found = {p["name"]: p["description"] for p in params if p.get("description")}
        if found:
            return found
    return {}


def param_tooltips(
    func: Callable,
    *,
    ledger: Optional[Mapping[str, str]] = None,
    include: Optional[Iterable[str]] = None,
    exclude: Iterable[str] = (),
    doc_styles: Iterable[str] = DFLT_DOC_STYLES,
) -> dict:
    """Tooltips for the arguments of a function, as a ``{param_name: tooltip}`` dict.

    Parsed from the docstring (first style in ``doc_styles`` that yields something),
    then overridden by ``ledger`` (explicit tooltips). ``include`` ("only these")
    and ``exclude`` ("all except") restrict the names.
    """
    tooltips = {**_parsed_param_docs(func, doc_styles), **(ledger or {})}
    if include is not None:
        include = set(include)
        tooltips = {k: v for k, v in tooltips.items() if k in include}
    exclude = set(exclude)
    return {k: v for k, v in tooltips.items() if k not in exclude}


TOOLTIPS_KEY = "tooltips"
TOOLTIP_KEY = "tooltip"


def apply_tooltips(obj_spec: Mapping, obj: Callable) -> dict:
    """Return ``obj_spec`` with ``tooltip`` entries computed for ``obj`` and its params.

    The (opt-in) configuration is the ``"tooltips"`` entry of the spec, which is consumed
    here and never reaches the elements. Being part of the rendering spec, it can sit under
    a type (``Callable``) to apply to everything, or under an object's name to apply to it
    alone::

        {'tooltips': True}                       # all defaults
        {'tooltips': {'func': 'first_lines',     # or any other string: explicit tooltip
                      'params': {'exclude': ['x'], 'ledger': {'a': 'explicit'}}}}
        {'tooltips': {'func': False}}            # no function tooltip, params only

    The function tooltip goes to the spec's ``tooltip`` and the param tooltips to
    ``execution.inputs.<param>.tooltip`` (only for a spec that has an ``execution`` entry).
    A ``tooltip`` the spec already has is kept.

    Opt-in also means the element factories must accept ``tooltip``: ``FrontElementBase``
    and the base containers do, but a concrete element with its own ``__init__`` signature
    has to take it (and forward it) before the config is switched on for it.

    >>> def foo(a, b=2):
    ...     '''Add things.
    ...
    ...     :param a: the first thing
    ...     '''
    >>> spec = apply_tooltips({'tooltips': True, 'execution': {'inputs': {}}}, foo)
    >>> spec['tooltip'], spec['execution']['inputs']
    ('Add things.', {'a': {'tooltip': 'the first thing'}})
    >>> apply_tooltips({'x': 1}, foo)
    {'x': 1}
    """
    spec = dict(obj_spec)
    config = spec.pop(TOOLTIPS_KEY, None)
    if not config:
        return spec
    config = {} if config is True else dict(config)
    func_style = config.get("func", "first_line")
    if func_style is not False and TOOLTIP_KEY not in spec:
        if text := func_tooltip(obj, func_style):
            spec[TOOLTIP_KEY] = text
    params = param_tooltips(obj, **(config.get("params") or {}))
    execution = spec.get("execution")
    if params and isinstance(execution, Mapping):
        inputs = {**execution.get("inputs", {})}
        for name, text in params.items():
            inputs[name] = {TOOLTIP_KEY: text, **inputs.get(name, {})}
        spec["execution"] = {**execution, "inputs": inputs}
    return spec
