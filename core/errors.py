class APSError(Exception):
    def __init__(self, key, **params):
        super().__init__(key)
        self.key = key
        self.params = params


def error_parts(exc):
    key = getattr(exc, 'key', None)
    if isinstance(key, str):
        return key, getattr(exc, 'params', {})
    return None, {}
