from functools import partial
from random import choice, randint, uniform
import string
from i2 import Sig


rdm_int = partial(randint, a=-100, b=100)
rdm_float = partial(uniform, a=-100.0, b=100.0)


def rdm_str():
    nb_char = randint(5, 15)
    return ''.join(choice(string.ascii_letters + string.digits) for _ in range(nb_char))


PRIMITIVE_TYPES = [bool, str, int, float]


def get_var_nodes_to_crudify(funcs):
    var_nodes = set()
    for func in funcs:
        sig = Sig(func)
        for param, annotation in sig.annotations.items():
            if annotation not in PRIMITIVE_TYPES:
                var_nodes.add(param)
    return list(var_nodes)
