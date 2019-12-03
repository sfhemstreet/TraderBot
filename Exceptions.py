class Error(Exception):
    """Base class."""
    pass


class APIKeyError(Error):
    """Exception raised for missing or inaccurate API keys/secrets."""
    def __init__(self, expression, message):
        self.expression = expression
        self.message = message
        print('API key Error - ', self.message, self.expression)


class InvalidArgError(Error):
    """Exception raised for missing or inaccurate function args."""
    def __init__(self, invalidArg, message):
        self.invalidArg = invalidArg
        self.message = message
        print('Invalid Arg Error - ', self.message, '\nInvalid Arg(s) - ', invalidArg)


class WebSocketError(Error):
    """Exception raised for WebSocket Error."""
    def __init__(self, error, message):
        self.error = error
        self.message = message
        print('WebSocket Error - ', self.error, self.message)