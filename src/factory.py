# 导入标准库
# import gettext

# 导入第三方依赖
try:
    from loguru import logger
    from cachetools import LRUCache, TTLCache, LFUCache
    from typing_extensions import Literal, Optional, Any
except ImportError:
    pass
import stat
from typing import Any
import tablib

# 导入自定义模块
from .basic import _format_query_fields_dict, _format_result_dict, _check_query_fields_dict
from .basic import _
from .basic import * # 导入异常类
from .util import search, stats, host 

# 定义全局常量
_official_api = "https://fofa.info/api/v1" # 如果修改了api, 那么官方接口可能无法正常使用
_apis = {
    'fofa': _official_api,
    'fofoapi': "https://fofoapi.com/api/v1",
}
_default_res_fields = { # 从etc.py拿的
        'search': {
            'fofa': ['link', 'ip', 'port'], # FOFA官方API默认字段列表
            # TODO 根据更多响应数据确认第三方API的真实返回字段
            'fofoapi': 
                [
                    'title', 'domain', 'link', 'unk1', 
                    'cert.subject.org', 'unk2', 'unk3'
                 ] # fofoapi第三方API默认字段列表
        },
        'stats': ['title'],
        'host': ['port', 'protocol', 'domain', 'category', 'product'],
}


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
        self._api_source = 'fofa' # 显式标记API来源
        for source, url in _apis.items():
            if api in url:
                self._api_source = source
                break
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
        self._check_query_dict = _check_query_fields_dict
        
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
               query_dict: dict = {},
               # 默认的返回值字段
               size: int = 10000,
               page: int = 1,
               # 请求参数
               headers: dict = {},
               timeout: int = 30
               ) -> dict:
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
            timeout: The request timeout in seconds. Defaults to 30.

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
            fixed_size = self._check_query_dict(
                mode='search',
                query_dict=query_dict
                ) # 这里也会抛出异常
            if fixed_size != -1 and size >= fixed_size:
                # 根据fofa文档官方要求, 如果出现了特殊字段
                # 那么最大查询条数也是要相应做出修改的
                size = fixed_size # 修正size最大值
            
            # 生成格式化查询字符串
            query_string = self._format_query_dict(query_dict)
            fields = list(query_dict.keys()) # 获取所有的键作为字段名
            self.fields = fields # 更新实例属性fields    
        
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
            api_source=self._api_source
        )
        except Exception as e:
            self._log_engine.error(e)
        
        # 最后重新设置一下返回值字段
        self.fields = _default_res_fields['search'][self._api_source]
            
        return res # 返回的是原始的查询结果, 类型为dict
    
    # TODO 根据stats响应数据完善接口
    def stats(self, 
              query_string: str,
              query_dict: dict = {},
              fields: list = ['title', 'ip', 'host', 'port', 'os', 'server', 'icp'],
              
              headers: dict = {},
              cookies: dict = {},
              timeout: int = 30
              ) -> dict:
        """Executes a statistical aggregation query against the FOFA API.

        This method queries the FOFA stats endpoint to get aggregated data based
        on a set of fields for a given search query. It defines the asset scope
        using either a `query_string` or a `query_dict`.

        A list of fields to aggregate on must be provided via the `fields`
        parameter.

        Note on Side Effects:
        - `self.results` is updated with the raw dictionary response from the API.
        - `self.assets` is intended to hold formatted results. However, the
          formatting logic for 'stats' mode is not currently implemented, so
          `self.assets` will likely remain `None` after this call.

        Args:
            query_string: The raw FOFA search query to define the asset scope
                for aggregation. Takes precedence over `query_dict`.
            query_dict: A dictionary of search criteria to define the asset
                scope. Used only if `query_string` is empty.
            fields: A list of fields to perform the statistical aggregation on.
                For example, `['country', 'port']` will return counts for each
                country and port combination found within the query scope.
            headers: Custom HTTP headers for the request. Defaults to {}.
            timeout: The request timeout in seconds. Defaults to 30.

        Returns:
            The raw dictionary parsed from the API's JSON response, containing
            the nested aggregation data. Returns `None` if the API call fails
            and the exception is caught internally.

        Raises:
            ParamsMisconfiguredError: If both `query_string` and `query_dict`
                are empty. Propagates other exceptions from validation helpers.
        """
        func_params = {
            'logger': self._log_engine,
            'translator': _,
            'url': self._stats_url,
            'apikey': self._apikey,
            'query_string': query_string,
            'headers': headers,
            'cookies': cookies,
            'timeout': timeout
        }
        # 检查查询字符串是否为空, 若不为空, 那么不会修改查询字符串的内容
        # 若为空, 则尝试根据查询dict的内容生成格式化查询字符串
        # 最后提取查询字典的keys作为列名fields
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
            fixed_size = self._check_query_dict(
                mode='stats',
                query_dict=query_dict
                ) # 这里也会抛出异常
            if fixed_size != -1 and size >= fixed_size:
                # 根据fofa文档官方要求, 如果出现了特殊字段
                # 那么最大查询条数也是要相应做出修改的
                size = fixed_size # 修正size最大值
            
            # 生成格式化查询字符串
            query_string = self._format_query_dict(query_dict)
            fields = list(query_dict.keys()) # 获取所有的键作为字段名
            self.fields = fields
            
        if fields != []: # 如果列名不为空就可以加进去了
            func_params['fields'] = fields
        try:
            self.results = stats(**func_params)
        except Exception as e:
            logger.error(e)
        # 由于统计接口的返回值处理并没有做好
        # 所以下面是肯定会抛出异常的
        # self.assets仍然为None
        try:
            self.assets = _format_result_dict(
            query_results=self.results,
            mode='stats',
            api_source=self._api_source
        )
        except Exception as e:
            self._log_engine.error(e)
        
        # 最后重新设置一下返回值字段
        self.fields = _default_res_fields['stats']
        
        return self.results
    
    # TODO 编写完成host接口封装
    def host(self,
             host: str,
             detail: bool = False,
             
             headers: dict = {},
             cookies: dict = {},
             timeout: int = 30
             ) -> dict:
        """Retrieves all available information for a specific host IP from the FOFA API.

        This method queries the `/host/{ip}` endpoint to get all port and
        protocol information associated with a single host.

        Note on Side Effects:
        - This method attempts to populate `self.assets` with formatted data.
          However, the formatting logic for 'host' mode is not currently
          implemented, so `self.assets` will likely remain `None` or unchanged
          after this call.

        Args:
            host: The IP address of the target host to query (e.g., "1.1.1.1").
            detail (bool, optional): If set to `True`, the API will return more
                detailed information for each port, such as banners.
                Defaults to `False`.
            headers (dict, optional): Custom HTTP headers for the request.
                Defaults to {}.
            cookies (dict, optional): Cookies to include in the request.
                Defaults to {}.
            timeout (int, optional): The request timeout in seconds.
                Defaults to 30.

        Returns:
            The raw dictionary parsed from the API's JSON response containing
            the host's details. Returns `None` if the API call fails and the
            exception is caught internally.
        """
        func_params = {
            'logger': self._log_engine,
            'translator': _,
            'url': self._host_url.format(host=host), # /host/{host} 占位符用在这里
            'apikey': self._apikey,
            'detail': detail,
            'headers': headers,
            'cookies': cookies,
            'timeout': timeout
        }
        res = None
        try:
            res = host(**func_params)
        except Exception as e:
            self._log_engine.error(e)
        self.results = res
        try:
            self.assets = _format_result_dict(
            query_results=res,
            mode='host',
            api_source=self._api_source
        )
        except Exception as e:
            self._log_engine.error(e)

        self.fields = _default_res_fields['host']
        
        return res
    
    '''
    不要尝试重写`__getattribute__`方法
    因为不管是访问实例本身的属性还是访问实例的属性的属性，
    都会调用到这个方法
    这样很容易就会触发递归异常
    '''
    
    def __getattr__(self, name: str):
        # 当访问一个不存在的属性就可以触发这个方法了
        try:
            return self.assets[name]
        except Exception as e:
            self._log_engine.error(e)
            
    def __getitem__(self, name: str):
        try:
            return self.assets[name]
        except Exception as e:
            self._log_engine.error(e)
            
    def __sub__(self, existed_column_header: str):
        # 删除数据表的某一列
        if self.assets is not None:
            del self.assets[existed_column_header]
        else:
            pass
        
    def __len__(self):
        # 返回查询到的数据的条数
        # 注意, 只有返回值被正常格式化的时候这些魔术方法才可以使用
        if self.assets is not None:
            return len(self.assets)
        else:
            return -1
        
    def __add__(self, append_column_header: str):
        # 增加一个空的列
        if self.assets is not None:
            self.assets.append_col(
                [''] * len(self.assets), header=append_column_header
            )
        else:
            pass
        
    def __delattr__(self, name: str) -> None:
        if self.assets is not None:
            del self.assets[name]
        else:
            return super().__delattr__(name)
    
    def __repr__(self):
        return f"<{self.__class__.__name__} api:{self._api} \
            key:{self._apikey:3}>"
            
    def __str__(self):
        if self.assets is not None:
            return f'{self.assets}'
        else:
            return _('The asset data cannot be formatted. \
                Please access the "fofa.results" property to \
                    obtain the original data')
    
    def to_formatted_text(self):
        return self.__str__()
    
    def to_csv(self):
        return self.assets.export('csv')
    
    def to_json(self):
        return self.assets.export('json')
    
