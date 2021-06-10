import os


def foo(text: str = 'words, are, fun', options: list = []):
    return text, options


funcs = [foo]

if __name__ == '__main__':
    from front.base import dispatch_funcs

    print('file: {}'.format(os.path.realpath(__file__)))

    app = dispatch_funcs(funcs)

    app()
