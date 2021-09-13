from ..handlers import BaseHandler


class BaseFilter(BaseHandler):
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


class LogicalFilter(BaseFilter):
    allowed_types = ["filter"]

    def __init__(self, *filters):
        self.filters = []
        for filter in filters:
            if isinstance(filter, type(self)):
                self.filters += filter.filters
            else:
                self.filters.append(filter)


class AndFilter(LogicalFilter):
    def validate(self, bot, context):
        for filter in self.filters:
            if not filter.validate(bot, context):
                return False
        return True


class OrFilter(LogicalFilter):
    def validate(self, bot, context):
        for filter in self.filters:
            if filter.validate(bot, context):
                return True
        return False


class NotFilter(LogicalFilter):
    def __init__(self, filter):
        if not isinstance(filter, BaseFilter):
            raise TypeError("NotFilter accepts only filters")
        self.filter = filter

    def validate(self, bot, context):
        return not self.filter.validate(bot, context)
