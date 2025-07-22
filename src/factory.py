# 导入标准库
# import gettext

# 导入第三方依赖
try:
    from loguru import logger
    from cachetools import LRUCache, TTLCache, LFUCache
    from typing_extensions import Literal, Optional, Any
except ImportError:
    pass
import tablib

# 导入自定义模块
from .basic import _format_query_fields_dict, _format_result_dict
from .basic import _
from .basic import * # 导入异常类
from .util import search, stats, host 

# 定义全局常量
_official_api = "https://fofa.info/api/v1" # 如果修改了api, 那么官方接口可能无法正常使用

# 定义无用的空模块
class FakeLogger:
    def info(self, *args, **kwargs):
        pass
    def debug(self, *args, **kwargs):
        pass
    def warning(self, *args, **kwargs):
        pass
    def error(self, *args, **kwargs):
        pass
_fake_logger = FakeLogger() # 空的日志记录器, 这样下层调用时不会报错

# 定义无用的空缓存器模块
class FakeCache:
    pass
_fake_cache = FakeCache() # 空的缓存器

class Fofa:
    def __init__(self,
                 # API配置
                 key: str, # API密钥
                 api: str = _official_api, # API地址 # 最后面不要带有斜杠
                 # 请求配置
                 # proxy: dict = None, # 代理 # 暂时不支持
                 # 模块注册
                 enable_log: bool = True, # 是否启用日志
                 log_engine = logger, # 日志引擎
                 enable_cache: bool = False, # 是否启用缓存
                 enable_format: bool = False, # 是否启用自动数据整理
                 # 若不启用则无法使用后续的魔术方法重载效果
                 ) -> None:
        # 配置API链接
        _search_api = '/search/all'
        _stats_api = '/search/stats'
        _host_api = '/host/{host}' # 预留format占位符
        
        self._api = api.__str__() # 显式避免引用拷贝问题
        self._search_url = api + _search_api
        self._stats_url = api + _stats_api
        self._host_url = api + _host_api
        # 配置其余参数
        self._apikey = key
        # 配置模块
        if not enable_log:
            self._log_engine = _fake_logger
        else:
            self._log_engine = log_engine
        self._enable_cache = enable_cache
        self._enable_format = enable_format
        
        # 注册函数
        self._format_query_dict = _format_query_fields_dict
        self._format_result_dict = _format_result_dict
        
        # 注册一些公共字段
        self.fields = [] # 查询结果的列名
        self.results = {} # 原始查询结果, json_loads之后的对象
        self.assets = None # tablib数据表

    
    # 参数和__init__一致
    @classmethod
    def fofa(self,
             **kwargs
             ):
        return Fofa(**kwargs)
    
    def search(self, 
               query_string: str,
               query_dict: dict = None,
               # 默认的返回值字段
               size: int = 10000,
               page: int = 1,
               # 请求参数
               headers: dict = {},
               timeout: int = 3
               ):
        """Executes a search query against the FOFA API and updates instance attributes.

        This method provides two ways to perform a search:
        1.  By providing a pre-formatted `query_string`.
        2.  By supplying a `query_dict`, which the method will automatically
            validate and format into a FOFA query string.

        If a `query_string` is provided, it takes precedence. If using `query_dict`,
        the method checks for invalid fields and may automatically adjust the `size`
        parameter downwards for resource-intensive fields (e.g., 'body', 'cert')
        to comply with API limitations.

        Upon a successful API call, this method produces side effects:
        - `self.results` is updated with the raw dictionary response from the API.
        - `self.assets` is updated with a `tablib.Dataset` object of the
          formatted results. If formatting fails, `self.assets` remains `None`.

        Args:
            query_string: The raw FOFA search query string. Takes precedence
                over `query_dict`.
            query_dict: A dictionary of search criteria to be formatted into
                a query string. It is only used if `query_string` is empty.
            size: The maximum number of results to retrieve. Defaults to 10000.
                This value may be automatically reduced for certain queries.
            page: The page number for pagination. Defaults to 1.
            headers: Custom HTTP headers for the request. Defaults to {}.
            timeout: The request timeout in seconds. Defaults to 3.

        Returns:
            The raw dictionary parsed from the API's JSON response. Returns
            `None` if the API call fails and the exception is caught internally.

        Raises:
            ParamsMisconfiguredError: If both `query_string` and `query_dict`
                are empty. Propagates other exceptions from validation and
                formatting helpers if they occur.
        """
        # 首先检查查询字符串是否为空, 如果不为空那么直接传入
        fields = []
        if query_string == '':
            # 如果为空, 那么尝试根据query_dict生成查询字符串
            if query_dict == {}: # 如果query_dict也为空, 那么直接报错
                raise ParamsMisconfiguredError(
                    _("The query dict is empty, \
                        which prevents the query from being executed")
                )
            # 如果不为空, 那么接下来判断query_dict是否有意料之外的字段
            fixed_size = self/_format_query_fields_dict(
                query_dict=query_dict
                ) # 这里也会抛出异常
            if fixed_size != -1 and size >= fixed_size:
                # 根据fofa文档官方要求, 如果出现了特殊字段
                # 那么最大查询条数也是要相应做出修改的
                size = fixed_size # 修正size最大值
            
            # 生成格式化查询字符串
            query_string = self._format_query_dict(query_dict)
            fields = list(query_dict.keys()) # 获取所有的键作为字段名

        # 如果fields为空, 那么就不引入fields字段列表参数
        try:
            if fields == []:
                # 开始查询
                res = search(
                    logger=self._log_engine,
                    translator=_,
                    url=self._search_url,
                    apikey=self._apikey,
                    query_string=query_string,
                    size=size,
                    page=page,
                )
            else:
                res = search(
                    logger=self._log_engine,
                    translator=_,
                    url=self._search_url,
                    apikey=self._apikey,
                    query_string=query_string,
                    size=size,
                    page=page,
                    fields=fields
                )
        except Exception as e:
            self._log_engine.error(e)
        self.results = res
        # 这里格式化不成功的话self.assets还是为None
        try:
            self.assets = _format_result_dict(
            query_results=res,
            mode='search',
            api_source='fofoapi'
        )
        except Exception as e:
            self._log_engine.error(e)
        return res # 返回的是原始的查询结果, 类型为dict
    
    def stats(self):
        pass
    
    def host(self):
        pass
    
    """def __getattribute__(self, name: str):
        pass
    
    def __getitem__(self, name: str):
        pass
    
    def __add__(self, append_column_header: str):
        pass
    
    # 重载减法 # 有返回值
    def __sub__(self, existed_column_header: str):
        pass
    
    # 无返回值
    def __delete__(self, existed_column_header: str):
        pass
    
    def __repr__(self) -> str:
        pass
    
    def __str__(self) -> str:
        pass
    
    def to_formatted_text(self):
        pass
    
    def to_csv(self):
        pass
    
    def to_json(self):
        pass"""
    
