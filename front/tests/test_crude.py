"""
Test prepare_for_crude_dispatch
"""

from front.crude import prepare_for_crude_dispatch
from functools import partial


# ---------------------------------------------------------------------------------------
# dispatchable function:
def apply_model(fitted_model, fvs, method='predict'):
    method_func = getattr(fitted_model, method)
    return method_func(list(fvs))


def learn_model(learner, fvs, method='fit'):
    method_func = getattr(learner, method)
    return method_func(list(fvs))


# a simple "learner" class to avoid importing from sklearn
class TinyMinMaxModel:
    def __init__(self):
        pass

    def fit(self, X, y=None):
        self.X_max = max(X)
        self.X_min = min(X)

        return self

    def predict(self, X):
        def min_max(x):
            return max(min(x, self.X_max), self.X_min)

        return [min_max(x) for x in X]


# The mall containing a store for each parameter of the apply_model and learn_model
# plus the model_results
mall = dict(
    learner=dict(TinyMinMaxModel=TinyMinMaxModel()),
    fvs=dict(train_fvs_1=[[1], [2], [3], [5], [4], [2], [1], [4], [3]],),
    fitted_model=dict(
        fitted_model_1=TinyMinMaxModel().fit(
            [[1], [2], [3], [5], [4], [2], [1], [4], [3]]
        )
    ),
    model_results=dict(),
)


def test_prepare_for_crude_dispatch():
    # Preparing the functions to be dispatched. The "dispatchable" versions will now
    # require a string for each parameter and rely on the mall above to call the
    # convert the string and call the original functions
    dispatchable_learn_model = prepare_for_crude_dispatch(
        learn_model,
        param_to_mall_map=dict(learner='learner', fvs='fvs'),
        mall=mall,
        output_store='fitted_model',
    )

    dispatchable_apply_model = prepare_for_crude_dispatch(
        apply_model,
        param_to_mall_map=dict(fitted_model='fitted_model', fvs='fvs'),
        mall=mall,
        output_store='model_results',
        save_name_param='save_name_for_apply_model',
    )

    # Here we set some defaults for both functions. This is useful in particular when
    # we want an UI to display defaults
    dispatchable_learn_model = partial(
        dispatchable_learn_model, learner='TinyMinMaxModel', fvs='train_fvs_1',
    )

    dispatchable_apply_model = partial(
        dispatchable_apply_model, fitted_model='fitted_model_1', fvs='train_fvs_1',
    )

    test_fvs = [[-100], [1], [2], [10]]

    # train a model with the dispatched function (with the defaults set above)
    tmm = dispatchable_learn_model()
    assert tmm.predict(test_fvs) == [[1], [1], [2], [5]]

    # run the dispatched function to apply a model. The output of which will saved in the
    # mall mall['model_results'], under the name 'apply_model_results'
    am = dispatchable_apply_model(save_name_for_apply_model='apply_model_results')
    assert am == [[1], [2], [3], [5], [4], [2], [1], [4], [3]]

    # checking that the store containing the results is created
    assert list(mall['model_results']) == ['apply_model_results']

    # checking the content of the results store
    assert mall['model_results']['apply_model_results'] == [
        [1],
        [2],
        [3],
        [5],
        [4],
        [2],
        [1],
        [4],
        [3],
    ]
