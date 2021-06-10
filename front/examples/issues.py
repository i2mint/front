import io
import os
from py2store import ZipReader, filt_iter
import pandas as pd
import streamlit as st

# store = state_dict[store_name]
# option = st.selectbox(message, [extra] + list(store.keys()), index=dflt_index)


class C:
    def __init__(self):
        self.val = 1

    def increment(self):
        self.val += 1
        return self.val


c = C()
my_incrementer = c.increment


def display_selectbox(store):
    _keys = filt_iter(store, filt=lambda k: k.endswith('.csv'))
    st.selectbox('Choose a file', list(_keys))


def dacc(zip_path: type(lambda a: a), file: str):  # file: list = []):
    s = ZipReader(zip_path)
    annots_df = pd.read_csv(io.BytesIO(s[file]))
    display_selectbox(s)
    return annots_df


def foo(word: str):
    return word


funcs = [dacc]

if __name__ == '__main__':
    from front.base import dispatch_funcs

    print('file: {}'.format(os.path.realpath(__file__)))

    app = dispatch_funcs(funcs)

    app()
