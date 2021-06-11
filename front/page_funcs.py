import streamlit as st
from front.base import BasePageFunc, get_func_args_specs


class DataAccessPageFunc(BasePageFunc):
    def __call__(self, state):
        if self.page_title:
            st.markdown(f'''## **{self.page_title}**''')
        st.write(
            'Current value stored in state for this function is:', state[self.page_title],
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
            'Current value stored in state for this function is:', state[self.page_title],
        )
        args_specs = get_func_args_specs(self.func)
        i = 0
        temp = {}
        for key in args_specs.keys():
            temp[i] = key
            i += 1
        func_inputs = {}
        for num, argname in temp.items():
            # only works under the assumptions that the first argument for every function will be to pass the state
            # and the options for the selectbox are the argument directly before it is a string of comma separated
            # values
            if num == 0:
                func_inputs[argname] = state
            else:
                if func_inputs[temp[num - 1]]:
                    if args_specs[argname]['element_factory'][0] is None:
                        func_inputs[argname] = state
                    else:
                        if 'options' in args_specs[argname]['element_factory'][1]:
                            options = func_inputs[temp[num - 1]].split(', ')
                            args_specs[argname]['element_factory'][1]['options'] = options
                        element_factory, kwargs = args_specs[argname]['element_factory']
                        func_inputs[argname] = element_factory(**kwargs)
        submit = st.button('Submit')
        if submit:
            state[self.page_title] = self.func(**func_inputs)
            st.write(
                'New value stored in state for this function is:', state[self.page_title],
            )