import streamlit as st
from front.base import BasePageFunc, get_func_args_specs
from front.util import build_factory


class DataAccessPageFunc(BasePageFunc):
    def __call__(self, state):
        if self.page_title:
            st.markdown(f'''## **{self.page_title}**''')
        st.write(
            'Current value stored in state for this function is:',
            state[self.page_title],
        )
        args_specs = get_func_args_specs(self.func)
        func_inputs = {}
        for argname, spec in args_specs.items():
            if spec['element_factory'][0] is None:
                func_inputs[argname] = state
            else:
                if 'options' in spec['element_factory'][1]:
                    pass  # TODO: find some way to access the data from another input we want
                element_factory, kwargs = spec['element_factory']
                func_inputs[argname] = element_factory(**kwargs)
        submit = st.button('Submit')
        if submit:
            state[self.page_title] = self.func(**func_inputs)
            st.write(state[self.page_title])


class DataBindingExploPageFunc(BasePageFunc):
    def __call__(self, state):
        if self.page_title:
            st.markdown(f'''## **{self.page_title}**''')
        st.write(
            'Current value stored in state for this function is:',
            state[self.page_title],
        )
        args_specs = get_func_args_specs(self.func)
        int_args = dict(zip(range(len(args_specs)), args_specs))
        func_inputs = {}
        for idx, argname in int_args.items():
            # only works under the assumptions that the first argument for every function will be to pass the state
            # and the options for the selectbox are the argument directly before it is a string of comma separated
            # values
            if idx == 0:
                func_inputs[argname] = state
            else:
                if func_inputs[int_args[idx - 1]]:
                    if args_specs[argname]['element_factory'][0] is None:
                        func_inputs[argname] = state
                    else:
                        if 'options' in args_specs[argname]['element_factory'][1]:
                            options = func_inputs[int_args[idx - 1]].split(', ')
                            args_specs[argname]['element_factory'][1][
                                'options'
                            ] = options
                        element_factory, kwargs = args_specs[argname]['element_factory']
                        func_inputs[argname] = element_factory(**kwargs)
        submit = st.button('Submit')
        if submit:
            state[self.page_title] = self.func(**func_inputs)
            st.write(
                'New value stored in state for this function is:',
                state[self.page_title],
            )


class ArgsPageFunc(BasePageFunc):
    def __call__(self, state):
        if self.page_title:
            st.markdown(f'''## **{self.page_title}**''')
        args_specs = get_func_args_specs(self.func)
        # func_inputs = dict(self.sig.defaults, **state['page_state'][self.func])
        positional_inputs = []
        keyword_inputs = {}
        for argname, spec in args_specs.items():
            element_factory, kwargs = spec['element_factory']
            if isinstance(element_factory, dict):
                args = element_factory['base'](**kwargs)
                if args:
                    for idx in range(args):
                        if len(element_factory) == 3:
                            positional_inputs.append(
                                build_factory(element_factory, 'input', idx)
                            )
                        else:
                            key = build_factory(element_factory, 'key', idx)
                            value = build_factory(element_factory, 'value', idx)
                            keyword_inputs[key] = value
            else:
                keyword_inputs[argname] = element_factory(**kwargs)
        submit = st.button('Submit')
        if submit:
            st.write(f'positional inputs are {positional_inputs} and keyword inputs are {keyword_inputs}')
            # state[self.page_title] = self.func(*positional_inputs, **keyword_inputs)
            # st.write(state[self.page_title])
            # state['page_state'][self.func].clear()


class StatePageFunc(BasePageFunc):
    def __call__(self, state):
        if self.page_title:
            st.markdown(f'''## **{self.page_title}**''')
        st.write(
            'Current value stored in state for this function is:',
            state[self.page_title],
        )
        args_specs = get_func_args_specs(self.func)
        func_inputs = {}
        for argname, spec in args_specs.items():
            if spec['element_factory'][0] is None:
                func_inputs[argname] = state
            else:
                element_factory, kwargs = spec['element_factory']
                func_inputs[argname] = element_factory(**kwargs)
        submit = st.button('Submit')
        if submit:
            state[self.page_title] = self.func(**func_inputs)
            st.write(
                'New value stored in state for this function is:',
                state[self.page_title],
            )
