import os
from odat.mdat.local_kgl import mk_dacc
import dill
from front.session_state import _get_state, _SessionState


def create_kaggle_dacc(
    zip_path: type(lambda a: a),
    annots_path: str,
    wrangle_func: type(lambda a: a),
    extension: str = '.wav',
    key_path: str = '',
):
    wrangle_func = dill.load(wrangle_func)
    return mk_dacc(
        zip_path, annots_path, wrangle_func, extension=extension, key_path=key_path,
    )


def build_and_run_model(tag: str):
    return tag


funcs = [create_kaggle_dacc, build_and_run_model]

if __name__ == '__main__':
    from front.base import dispatch_funcs

    print('file: {}'.format(os.path.realpath(__file__)))

    app = dispatch_funcs(funcs)

    app()
