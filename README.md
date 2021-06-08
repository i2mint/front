
# front
Getting from python objects to UIs exposing them


To install:	```pip install front```


# Example

```python
import os


def foo(a: int = 0, b: int = 0, c=0):
    """This is foo. It computes something"""
    return (a * b) + c


def bar(x, greeting='hello'):
    """bar greets its input"""
    return f'{greeting} {x}'


def confuser(a: int = 0, x: float = 3.14):
    return (a ** 2) * x


funcs = [foo, bar, confuser]

if __name__ == '__main__':
    from front.base import dispatch_funcs

    print('file: {}'.format(os.path.realpath(__file__)))

    app = dispatch_funcs(funcs)

    app()
    
    # ... and you get a browser based app that exposes foo, bar, and confuser

```