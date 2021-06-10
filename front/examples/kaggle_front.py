import os
from odat.mdat.local_kgl import mk_dacc
import dill
from front.session_state import _get_state, _SessionState
from front.util import produce_results

def create_kaggle_dacc(
    # state: type(_get_state()),
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


def build_and_run_model(state: type(_get_state()), tag: str):
    dacc = state['Create Kaggle Dacc']
    chks, tags = zip(*dacc.chk_tag_gen(tag))
    scores, fvs, featurizer, model = produce_results(chks, tags)
    state['tags'] = tags
    state['scores'] = scores
    return str(
        'Percentage correct: '
        + str(sum(scores == tags) / len(tags))
        + ' vs. Random guessing: '
        + str(1 / len(set(tags)))
    )


funcs = [create_kaggle_dacc, build_and_run_model]

if __name__ == '__main__':
    from front.base import dispatch_funcs

    print('file: {}'.format(os.path.realpath(__file__)))

    app = dispatch_funcs(funcs)

    app()
