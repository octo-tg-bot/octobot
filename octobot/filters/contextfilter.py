from .basefilters import BaseFilter
from octobot.classes import Context
from typing import Type

class ContextFilter(BaseFilter):
    def __init__(self, contextType: Type[Context], *args, **kwargs):
        if not issubclass(contextType, Context):
            raise TypeError(f"{contextType} is not a subclass of Context!")
        self.contextType = contextType
        super(ContextFilter, self).__init__(*args, **kwargs)

    async def validate(self, bot, context):
        return type(context) == self.contextType
