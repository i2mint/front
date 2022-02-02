import pytest
from streamlitfront import dispatch_funcs
from front.scrap.pydantic_wrap import DFLT_CONFIGS, SimplePageFuncPydanticWithOutput


def identity(x:int)->int:
	return x

funcs = [identity]

configs = {'page_factory': SimplePageFuncPydantic}


app = dispatch_funcs(funcs, configs=configs)
app()