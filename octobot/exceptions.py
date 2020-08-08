class UnknownUpdate(ValueError):
    """
    This exception gets raised during update handle if Context failed to determine update
    """
    pass


class LoaderCommand(Exception):
    """
    Base exception for OctoBot handler commands
    """
    pass


class StopHandling(LoaderCommand):
    """
    OctoBot stops trying to use other handles if that exception was raised
    """
    pass


class CatalogCantGoDeeper(IndexError):
    """Raise this exception is maximum number of results is reached"""
    pass


class CatalogNotFound(FileNotFoundError):
    """Raise this exception if no results were found"""
    pass