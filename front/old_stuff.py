

# def _get_dflt_element_factory_for_annot():
#     _ = _get_state()  # problem
#     return {
#         int: st.number_input,
#         float: st.number_input,
#         str: st.text_input,
#         bool: st.checkbox,
#         list: st.selectbox,
#         type(
#             lambda df: df
#         ): st.file_uploader,  # TODO: Find a better way to identify as file_uploader
#         type(_): None,  # use _SessionState instead?
#         typing.Iterable[int]: (st.number_input, int),
#         typing.Iterable[float]: (st.number_input, float),
#         typing.Iterable[str]: (st.number_input, str),
#         typing.Iterable[bool]: (st.number_input, bool),
#         typing.Dict[str, int]: (st.number_input, str, int),
#         typing.Dict[str, float]: (st.number_input, str, float),
#         typing.Dict[str, str]: (st.number_input, str, str),
#         typing.Dict[str, bool]: (st.number_input, str, bool),
#     }