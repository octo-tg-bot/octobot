from .basefilters import BaseFilter
from octobot.classes import Context


class ContextFilter(BaseFilter):
    def __init__(self, contextType: Context, *args, **kwargs):
        if not issubclass(contextType, Context):
            raise TypeError(f"{contextType} is not a subclass of Context!")
        self.contextType = contextType
        super(ContextFilter, self).__init__(*args, **kwargs)

    async def validate(self, bot, context):
        return type(context) == self.contextType
