class BaseHelper:
    function = None

    def __call__(self, func):
        assert self.function is None
        self.function = func
        return self

    insert_func = __call__

    @property
    def filters(self):
        raise RuntimeError(".filters property is not defined")
