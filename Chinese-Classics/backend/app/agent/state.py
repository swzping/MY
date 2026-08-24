from typing import Annotated, Sequence, TypedDict, Union, List
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    question: str
    documents: List[str]
    generation: str
    next_step: str
