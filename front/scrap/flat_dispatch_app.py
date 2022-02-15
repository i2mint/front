from streamlitfront import dispatch_funcs
from front.scrap.pydantic_wrap import SimplePageFuncPydanticWithOutput
from typing import Optional, Dict, List
from streamlit_pydantic.types import FileContent
from pydantic import Field, BaseModel
from dol import Store

mall = dict()


def get_data(x: Dict[str, int]) -> List[str]:
    mall['salary'] = x
    return list(x.keys())


funcs = [get_data]

configs = {'page_factory': SimplePageFuncPydanticWithOutput}


class SelectionValue(str, Enum):
    FOO = 'foo'
    BAR = 'bar'


class ExampleModel(BaseModel):
    single_selection: SelectionValue = Field(
        ..., description='Only select a single item from a set.'
    )


app = dispatch_funcs(funcs, configs=configs)
app()
