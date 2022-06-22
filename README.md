# front

[Documentation here](https://i2mint.github.io/front/)

Getting from python objects to UIs exposing them.
Note the absence of the G in front of UI. 
This is because a UI (User Interface) is not necessarily graphical.
Though graphical interfaces will be our main focus, we are concerned here 
will the slightly more general problem of UIs, that could take the form of 
web-services, command-line interfaces, could be web-based or not, etc.

To install:	```pip install front```

# How to use it

``front`` is not a framework but a core library meant to be used to implement concrete ``front`` frameworks (e.g. [streamlitfront](https://github.com/i2mint/streamlitfront/)).

Here are the steps to follow to implement a new concrete ``front`` framework:

## Implement concrete UI elements

You need to add a concrete implementation of the UI elements to render according to the framework you are using for the concrete ``front`` (e.g. streamlit for ``streamlitfront``). 

There are two types of elements:

  1. **Components**. These are the elements the final user will interact with (e.g. a number input or a slider). A component must extend ``FrontComponentBase``. Note that you can use ``implement_component`` (from ``front.elements``) to easily implement a component.

  2. **Containers**. These elements contains components and/or other containers. They define the structure of the UI (i.e. the layout for a GUI). A container must extend ``FrontContainerBase``.

To implement an element, you must implement its ``render`` method.

A bunch of base elements are defined in [front/elements/elements.py](https://github.com/i2mint/front/blob/0576bad1aa0e7163854cf4b50861edeced0dc0f4/front/elements/elements.py). They gather the common logic and properties for a type of element (e.g. ``NamedContainerBase`` for any container with a name or ``InputBase`` for any input component). You can use those base elements depending on your needs.

Example (from [streamlitfront](https://github.com/i2mint/streamlitfront/blob/f14fcd358268e766f618c41198d9039d4402436f/streamlitfront/elements/elements.py)):

```python
from functools import partial
import streamlit as st
from front.elements import DagViewBase, InputBase, TextInputBase, IntInputBase, FloatInputBase, NamedContainerBase, implement_component

from streamlitfront.session_state import _SessionState, get_state


class App(NamedContainerBase):
    """Implementation of the app root container for streamlitfront."""
    def render(self):
        # Page setup
        st.set_page_config(layout='wide')

        # Make page objects
        views = {
            view.name: view.render
            for view in self.children
        }
        st.session_state['views'] = views

        # TODO: The above is static: Should the above be done only once, and cached?
        #   Perhaps views should be cached in state?

        # Setup navigation
        with st.sidebar:
            st.title(self.name)
            view_key = st.radio(options=tuple(views.keys()), label='Select your view')
        # view_key = _get_view_key(tuple(views.keys()), label='Select your view')

        # Display the selected page with the session state
        # This is the part that actually runs the functionality that pages specifies
        view_runner = views[view_key]  # gets the page runner
        view_runner()  # runs the page with the state


class DagView(DagViewBase):
    """Implementation of ``DagViewBase`` for streamlitfront."""
    def render(self):
        st.markdown(f'''## **{self.name}**''')
        func_inputs = {}
        for child in self.children:
            func_inputs[child.label] = child.render()
        submit = st.button('Submit')
        # output_key = f'{self.func.__name__}_output'
        if submit:
            # state = get_state_with_hash_funcs()
            output = self.func(**func_inputs)
            st.session_state[f'{self.func.__name__}_output'] = output
            st.write(output)
        # elif output_key in state:
        #     st.write(state[output_key])


def store_input_value_in_state(input_value, component: InputBase):
    st.session_state[component.input_key] = input_value


implement_component_with_input_value_callback = partial(
    implement_component,
    input_value_callback=store_input_value_in_state
)
implement_component_with_init_value = partial(
    implement_component_with_input_value_callback,
    value='init_value'
)
implement_float_input_component = partial(
    implement_component_with_init_value,
    base_cls=FloatInputBase
)

TextInput = implement_component_with_init_value(TextInputBase, st.text_input)
IntInput = implement_component_with_init_value(IntInputBase, st.number_input)
FloatInput = implement_float_input_component(component_factory=st.number_input)
FloatSliderInput = implement_float_input_component(component_factory=st.slider)
```

## Implement a concrete Tree Maker

The Tree Maker makes the bridge between the rendering specification and your concrete elements. It is also responsible for how the elements are communicating between each other.

You need to implement a concrete Tree Maker by extending ``ElementTreeMakerBase`` and implement the following methods:

  1. ``_element_mapping``. Mapping between element flags and concrete element classes.

  2. ``_get_stored_value``. Defines how to retrieve a previously cached or stored value for a specific key.

Example (from [streamlitfront](https://github.com/i2mint/streamlitfront/blob/f14fcd358268e766f618c41198d9039d4402436f/streamlitfront/elements/tree_maker.py)):

```python
from typing import Any, Mapping
from front.elements import (
    ElementTreeMakerBase,
    FrontElementBase,
    APP_CONTAINER,
    VIEW_CONTAINER,
    TEXT_INPUT_COMPONENT,
    INT_INPUT_COMPONENT,
    FLOAT_INPUT_COMPONENT,
    FLOAT_INPUT_SLIDER_COMPONENT,
)
import streamlit as st

from streamlitfront.elements.elements import (
    App,
    FloatInput,
    FloatSliderInput,
    IntInput,
    TextInput,
    DagView,
)


class ElementTreeMaker(ElementTreeMakerBase):
    """Tree maker class for streamlitfront. Defines the streamlitfront-speceific
    element mapping and state management.
    """

    @property
    def _element_mapping(cls) -> Mapping[int, FrontElementBase]:
        return {
            APP_CONTAINER: App,
            VIEW_CONTAINER: DagView,
            TEXT_INPUT_COMPONENT: TextInput,
            INT_INPUT_COMPONENT: IntInput,
            FLOAT_INPUT_COMPONENT: FloatInput,
            FLOAT_INPUT_SLIDER_COMPONENT: FloatSliderInput,
        }

    def _get_stored_value(cls, key: str) -> Any:
        return st.session_state[key] if key in st.session_state else None
```

## Implement the App Maker

The App Maker is the bandmaster of front. It defines the workflow from the configuration to the application object:
1. Make the specification from config and convention objects.
2. Wrap the target objects according to the specification.
3. Make the element tree from the rendering specification and the concrete element classes.
4. Make the application object from the app specification and element tree.

You need to implement a concrete App Maker by extending ``AppMakerBase``. If you don't need to modify the workflow, you just need to define your concrete Tree Maker as default Tree Maker for the App Maker.

Example (from [streamlitfront](https://github.com/i2mint/streamlitfront/blob/f14fcd358268e766f618c41198d9039d4402436f/streamlitfront/app_maker.py)):

```python
from typing import Callable
from front.app_maker_base import AppMakerBase
from front.elements import FrontElementBase

from streamlitfront.elements.tree_maker import ElementTreeMaker


class AppMaker(AppMakerBase):
    """App maker class for streamlitfront. Defines ``ElementTreeMaker`` as default tree
    maker
    """

    def __init__(self, element_tree_maker_factory: Callable = ElementTreeMaker):
        super().__init__(element_tree_maker_factory)
```

Everything is set up now! You just need to create an instance of your App Maker and make an app object:

```python
def foo(a: int = 1, b: int = 2, c=3):
    """This is foo. It computes something"""
    return (a * b) + c

app_maker = AppMaker()
app = app_maker.mk_app([foo])
app()
```

# Workflow

Here is a diagram of the workflow described above.

![image](https://user-images.githubusercontent.com/63666082/174157691-5edf72bd-383d-4c07-8dc3-9272ac55561d.png)
