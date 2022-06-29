from octobot import PluginInfo
import logging
from typing import Any
from octobot.exceptions import handle_exception
logger = logging.getLogger("basefilters")


class BaseFilter():
    _filterWeight = 0
    priority = 0
    allowed_types = ['filter', 'function']
    plugin = PluginInfo(name="not set")
    loud_exceptions = False
    function = None

    def __call__(self, func):
        assert self.function is None
        if isinstance(func, BaseFilter) and 'filter' in self.allowed_types:
            self.function = func.function
            return self & func
        elif callable(func) and 'function' in self.allowed_types:
            self.function = func
            return self
        else:
            raise TypeError(
                f"{func} is unsupported, this handler supports {self.allowed_types}")

    insert_func = __call__

    async def validate(self, bot, context):
        raise RuntimeError(f"{type(self)}.validate isn't overridden!")

    async def handle_update(self, bot, context):
        if await self.validate(bot, context):
            try:
                await self.function(bot, context)
            except Exception as e:
                await handle_exception(bot, context, e, self.loud_exceptions)

    def __and__(self, other):
        return AndFilter(self, other)

    def __or__(self, other):
        return OrFilter(self, other)

    def __invert__(self):
        return NotFilter(self)


class LogicalBaseFilter(BaseFilter):
    # allowed_types = ["filter"]

    def __init__(self, *filters):
        self.filters = []
        self.all_filters = []
        for filter in filters:
            if isinstance(filter, LogicalBaseFilter):
                self.all_filters.append(filter)
            if isinstance(filter, type(self)):
                self.filters += filter.filters
            else:
                self.filters.append(filter)
        for filter in self.filters:
            if getattr(filter, "function", False) and callable(filter.function):
                self.function = filter.function
        logger.debug("sorting filters, before: %s", self.filters)
        self.filters = sorted(
            self.filters, key=lambda filter: filter._filterWeight, reverse=True)
        logger.debug("sorting filters, after: %s", self.filters)


class AndFilter(LogicalBaseFilter):
    async def validate(self, bot, context):
        for filter in self.filters:
            if not await filter.validate(bot, context):
                return False
        return True


class OrFilter(LogicalBaseFilter):
    async def validate(self, bot, context):
        for filter in self.filters:
            if await filter.validate(bot, context):
                return True
        return False


class NotFilter(LogicalBaseFilter):
    def __init__(self, filter):
        if not isinstance(filter, BaseFilter):
            raise TypeError("NotFilter accepts only filters")
        self.filter = filter

    async def validate(self, bot, context):
        return not await self.filter.validate(bot, context)
