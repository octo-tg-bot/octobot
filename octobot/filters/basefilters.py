from ..handlers import BaseHandler
import logging
logger = logging.getLogger("basefilters")


class BaseFilter(BaseHandler):
    _filterWeight = 0
    priority = 0
    allowed_types = ['filter', 'handler', 'function']

    def __call__(self, func):
        if isinstance(func, BaseFilter) and 'filter' in self.allowed_types:
            self.function = func.function
            return self & func
        elif isinstance(func, BaseHandler) and 'handler' in self.allowed_types:
            self.function = func.handle_update
            return self
        elif callable(func) and 'function' in self.allowed_types:
            self.function = func
            return self
        else:
            raise TypeError(
                f"{func} is unsupported, this handler supports {self.allowed_types}")

    def validate(self, bot, context):
        raise RuntimeError(f"{type(self)}.validate isn't overridden!")

    def handle_update(self, bot, context):
        if self.validate(bot, context):
            self.function(bot, context)

    def __and__(self, other):
        return AndFilter(self, other)

    def __or__(self, other):
        return OrFilter(self, other)

    def __invert__(self):
        return NotFilter(self)


class LogicalBaseFilter(BaseFilter):
    allowed_types = ["filter"]

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
    def validate(self, bot, context):
        for filter in self.filters:
            if not filter.validate(bot, context):
                return False
        return True


class OrFilter(LogicalBaseFilter):
    def validate(self, bot, context):
        for filter in self.filters:
            if filter.validate(bot, context):
                return True
        return False


class NotFilter(LogicalBaseFilter):
    def __init__(self, filter):
        if not isinstance(filter, BaseFilter):
            raise TypeError("NotFilter accepts only filters")
        self.filter = filter

    def validate(self, bot, context):
        return not self.filter.validate(bot, context)
