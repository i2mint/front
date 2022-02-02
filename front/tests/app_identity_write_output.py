import pytest
from streamlitfront import dispatch_funcs
from front.scrap.pydantic_wrap import DFLT_CONFIGS, SimplePageFuncPydantic


def identity(x:int)->int:
	return x

funcs = [identity]

app = dispatch_funcs(funcs, configs=DFLT_CONFIGS)
app()

