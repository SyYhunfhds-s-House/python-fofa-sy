from .etc import _

# 总封装
class FofaException(Exception):
    def __init__(self, message: str = "Fofa Exception", *args, **kwargs):
        super().__init__(_(message), *args, **kwargs)

class FofaAPIException(FofaException): # API 相关异常
    def __init__(self, message: str = "Fofa API Exception", *args, **kwargs):
        super().__init__(message, *args, **kwargs)
        
class FofaQueryException(FofaException): # 查询相关异常
    def __init__(self, message: str = "Fofa Query Exception", *args, **kwargs):
        super().__init__(message, *args, **kwargs)
        
class FofaUtilException(FofaException): # 工具相关异常
    def __init__(self, message: str = "Fofa Utility tools Exception", *args, **kwargs):
        super().__init__(message, *args, **kwargs)
        
# 具体的异常类在此
# API配置相关异常        
class EmptyKeyError(FofaAPIException):
    def __init__(self, message: str = "The API key is empty. Please check the configuration", *args, **kwargs):
        super().__init__(message, *args, **kwargs)
class NonOfficialKeyWarning(FofaAPIException):
    def __init__(self, message: str = "Using an unofficial key may prevent \
        some special interfaces from functioning properly", *args, **kwargs):
        super().__init__(message, *args, **kwargs)
# 权限不足异常
class InsufficientPermissions(FofaAPIException):
    def __init__(self, message: str = "Insufficient permissions", *args, **kwargs):
        super().__init__(message, *args, **kwargs)

# 查询相关异常
class LowCreditWarning(FofaQueryException):
    def __init__(self, message: str = "The available credit of the API \
        is too low. Please pay attention to the remaining balance", *args, **kwargs):
        super().__init__(message, *args, **kwargs)
class ZeroCreditWarning(FofaQueryException):
    def __init__(self, message: str = "The available credit of the API \
        has run out. Please recharge immediately", *args, **kwargs):
        super().__init__(message, *args, **kwargs)
class EmptyResultsWarning(FofaQueryException):
    def __init__(self, message: str = "No results were found for this query", *args, **kwargs):
        super().__init__(message, *args, **kwargs)
class FofaConnectionError(FofaQueryException):
    def __init__(self, message: str = "Connection error occurred during query execution", *args, **kwargs):
        super().__init__(message, *args, **kwargs)
class FofaRequestFailed(FofaQueryException):
    def __init__(self, message: str = "Request failed", *args, **kwargs):
        super().__init__(message, *args, **kwargs)
class FofaQuerySyntaxError(FofaQueryException):
    def __init__(self, message: str = "Syntax error in query string", *args, **kwargs):
        super().__init__(message, *args, **kwargs)
        
# 工具相关异常
# 暂时置空
