# 导入自定义模块
from etc import _

class FofaAPIException(Exception): # API 相关异常
    def __init__(self, message: str = "Fofa API Exception", *args, **kwargs):
        super().__init__(_(message), *args, **kwargs)
        
class FofaQueryException(Exception): # 查询相关异常
    def __init__(self, message: str = "Fofa Query Exception", *args, **kwargs):
        super().__init__(_(message), *args, **kwargs)
        
class FofaUtilException(Exception): # 工具相关异常
    def __init__(self, message: str = "Fofa Utility tools Exception", *args, **kwargs):
        super().__init__(_(message), *args, **kwargs)
        
# 具体的异常类在此
# API配置相关异常        
class EmptyKeyError(FofaAPIException):
    def __init__(self, message: str = "The API key is empty. Please check the configuration", *args, **kwargs):
        super().__init__(_(message), *args, **kwargs)
class NonOfficialKeyWarning(FofaAPIException):
    def __init__(self, message: str = "Using an unofficial key may prevent \
        some special interfaces from functioning properly", *args, **kwargs):
        super().__init__(_(message), *args, **kwargs)

# 查询相关异常
class LowCreditWarning(FofaQueryException):
    def __init__(self, message: str = "The available credit of the API \
        is too low. Please pay attention to the remaining balance", *args, **kwargs):
        super().__init__(_(message), *args, **kwargs)
class ZeroCreditWarning(FofaQueryException):
    def __init__(self, message: str = "The available credit of the API \
        has run out. Please recharge immediately", *args, **kwargs):
        super().__init__(_(message), *args, **kwargs)
class EmptyResultsWarning(FofaQueryException):
    def __init__(self, message: str = "No results were found for this query", *args, **kwargs):
        super().__init__(_(message), *args, **kwargs)
class ConnectionError(FofaQueryException):
    def __init__(self, message: str = "Connection error occurred during query execution", *args, **kwargs):
        super().__init__(_(message), *args, **kwargs)
class SyntaxError(FofaQueryException):
    def __init__(self, message: str = "Syntax error in query string", *args, **kwargs):
        super().__init__(_(message), *args, **kwargs)
        
# 工具相关异常
# 暂时置空
