# 导入标准库
# import gettext

# 导入第三方依赖
try:
    from loguru import logger
    from cachetools import TTLCache
    # from typing_extensions import Literal, Optional, Any
except ImportError:
    pass
from dataclasses import field
import tablib

# 导入自定义模块
from .basic import _format_query_fields_dict, _format_result_dict, _check_query_fields_dict
from .basic import _, sha256, now
from .basic import * # 导入异常类
from .util import search_v2, stats_v2, host_v2

# 定义全局常量
_official_api = "https://fofa.info" # 如果修改了api, 那么官方接口可能无法正常使用
_cache_max_size = 32
_cache_ttl = 60 * 10

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
_apis = {
    'fofa': _official_api,
    'fofoapi': "https://fofoapi.com",
}
# 根据官方响应数据反推的格式
_default_res_fields = {
        'search':['link', 'ip', 'port'],
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
    """Initializes the Fofa API client.

        Args:
            key: The FOFA API key for authentication.
            api: The base URL for the FOFA API. It should not have a
                trailing slash. Defaults to the official FOFA API.
            timeout: Default request timeout in seconds. Defaults to 30.
            headers: Default custom HTTP headers to be sent with every request.
            enable_log: If `True`, enables logging of errors and warnings.
            log_engine: The logging engine to use if logging is enabled.
                Defaults to the pre-configured logger.
            enable_cache: (Not yet implemented) Flag to enable response caching.
        """
    def __init__(self,
                 # API配置
                 key: str, # API密钥
                 api: str = _official_api, # API地址 # 最后面不要带有斜杠
                 # 请求配置 # 底层接口写好了, 这里是一点都用不上的
                 # timeout: int = 30, # 超时时间
                 # headers: dict = None, # 请求头
                 # proxy: dict = None, # 代理 # 暂时不支持
                 # proxy: dict = None, # 代理 # 暂时不支持
                 # 模块注册
                 enable_log: bool = True, # 是否启用日志
                 log_engine = logger, # 日志引擎
                 enable_cache: bool = False, # 是否启用缓存
                 cache_max_size: int = _cache_max_size, # 缓存大小 32个对象
                 cache_ttl: int = _cache_ttl, # 10 分钟
                 enable_format: bool = False, # 是否启用自动数据整理
                 # 若不启用则无法使用后续的魔术方法重载效果
                 ) -> None:
        """Executes a standard asset search and returns a results container.

        This method queries the FOFA search endpoint. It can build a query from
        a `query_dict` or use a pre-formatted `query_string`.

        Note:
            It is highly recommended to provide a list of desired fields via the
            `fields` parameter. The default fields are based on minimal API
            examples and may not suit your needs. Explicitly defining `fields`
            ensures you get exactly the data you require.

        Args:
            query_string: The raw FOFA search query string. Takes precedence.
            query_dict: A dictionary of criteria to build a query from.
            fields: A list of result fields to retrieve (e.g., ['ip', 'port']).
            size: The maximum number of results to retrieve.
            page: The page number for pagination.
            headers: Custom HTTP headers for the request.
            timeout: The request timeout in seconds.

        Returns:
            A `FofaAssets` object containing the processed data, or `None` if
            the API call fails.
        """
        # 配置API链接
        _search_api = '/api/v1/search/all'
        _stats_api = '/api/v1/search/stats'
        _host_api = '/api/v1/host/{host}' # 预留format占位符
        
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
        if enable_cache:
            self.cache = TTLCache(maxsize=cache_max_size, ttl=cache_ttl)
            '''
            - 使用查询字符串、返回值字段、size和page计算得到的sha256作为key
                - mode: str = 'search' 或 'stats' 或 'host'
                - queried_at, YY-MM-DD HH:mm:ss, 查询时间
                - query_string, 查询字符串
                - assets, FofaAssets对象的__repr__
            '''
            self.dashboard = tablib.Dataset()
            # 也是开了缓存才能这样做
            self.dashboard.headers = ['index', 'mode', 'queried_at', 'query_what', 'assets_repr']
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
               **kwargs
               # 内容(可选可自由配置)
               # fields: list = ['link', 'ip', 'port']
               # size: int = 100
               # page: int = 1
               # full: bool = False
               # timeout: int = 30
               # proxies: dict = {}
               # headers: dict = {}
               # cookies: dict = {}
               # 从实例和环境中导入(函数自动导入)
               # 如有需要, 请在实例初始化后手动修改实例的私有变量
               # url: str = self._search_url # 可以通过实例初始化时的api参数修改(前缀域名)
               # logger: self._log_engine
               # translator = _
               ) -> dict:
        """Executes a FOFA asset search and returns a FofaAssets container.

        This method acts as a user-friendly interface for the `search_v2`
        function. It can construct a valid query from a dictionary if
        `query_string` is empty, or use the provided string directly.

        All optional search parameters (like `size`, `page`, `fields`, etc.)
        are passed through `**kwargs` to the underlying search logic, offering
        a flexible and clean way to customize the query.

        Upon completion, this method updates the instance's `self.results`
        (raw data) and `self.assets` (`FofaAssets` object) attributes with the
        newest data.

        Args:
            query_string: The raw, unencoded FOFA search query string (e.g.,
                'domain="example.com"'). This takes precedence over `query_dict`.
            query_dict: A dictionary of search criteria, used only if
                `query_string` is empty. The method will validate and format
                this dictionary into a valid query string.
            **kwargs: Arbitrary keyword arguments that are passed directly to
                the `search_v2` function. This allows for advanced control
                over the request. Common options include:
                - fields (List[str]): Result fields to retrieve. Defaults to
                  `['link', 'ip', 'port']`.
                - size (int): Number of results to return. Defaults to 100.
                - page (int): The page number for pagination. Defaults to 1.
                - full (bool): Set to `True` to search all data within the
                  last year. Defaults to `False`.
                - timeout (int): Request timeout in seconds.
                - proxies (dict): A dictionary of proxies for the request.

        Returns:
            A `FofaAssets` object that contains the processed search results
            and provides methods for data manipulation and export. Returns
            `None` if the API call fails and the exception is handled.

        Raises:
            ParamsMisconfiguredError: If both `query_string` and `query_dict`
                are empty, as no query can be performed.
        """
        # 首先检查查询字符串是否为空, 如果不为空那么直接传入
        size = kwargs.get('size', 100)
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
                kwargs['size'] = fixed_size # 修正size最大值
            
            # 生成格式化查询字符串
            query_string = self._format_query_dict(query_dict)
        else:
            pass
        # 硬编码的默认字段
        fields = kwargs.get('fields', 
                            ['host', 'title', 'ip', 'domain', 'port', 'country', 'city']
                            )
        # 测试时发现fields列表为空时仍然可以进行查询, 但是会导致查询结果为空
        if fields == []:
            fields = ['host', 'title', 'ip', 'domain', 'port', 'country', 'city']    
        self.fields = fields # 更新实例属性fields
        
        hash = sha256(
            ('search', query_string, fields, 
             kwargs.get('size', 1), kwargs.get('page', 1))
        )
        assets = None
        try:
            idx, mode, at, query, assets = self.cache[hash]
            # 这个__表示查询字符串, 这里是为了防止干扰上面的query_string
            # 使用format模板字符串, 确保gettext正确识别文本
            self._log_engine.info(_(
                "cache hit: {assets}, mode: {mode}, at: {at}, query: {query}. \
                    asset query step will be skipped",
            ).format(assets=assets, mode=mode, at=at, query=query))
        except Exception as e:
            self._log_engine.debug(_(
                "cache miss: {error}, hash: {hash}. asset query steps will be performed",
            ).format(error=e, hash=hash))

        if assets is None or not self._enable_cache:
            res = None
            kwargs['url'] = self._search_url
            kwargs['logger'] = self._log_engine
            kwargs['translator'] = _ # 国际化接口
            kwargs['fields'] = fields
            try:
                self._log_engine.debug(_(
                    "Executing search with query string: {query_string}, \
                        fields: {fields}"
                ).format(
                    query_string=query_string,
                    fields=fields,
                ))
                res = search_v2(
                    apikey=self._apikey,
                    query_string=query_string,
                    **kwargs
                )
                self._log_engine.info(_(
                    "Search completed with {size} results"
                ).format(size=res.get('size', 0)))
            except Exception as e:
                self._log_engine.error(e)
            self.results = res
            # 这里格式化不成功的话self.assets还是为None
            try:
                assets = FofaAssets(
                    query_results=res,
                    mode='search',
                    fields=self.fields,
                    query_string=query_string
                )
                self._log_engine.info(_(
                    "FofaAssets object created with {size} assets"
                ).format(size=len(assets)))
                new_cache = len(self.cache) + 1, 'search', now(), query_string, assets
                self.cache[hash] = new_cache
                self.dashboard.append(new_cache)
            except Exception as e:
                self._log_engine.error(e)
        else:
            pass
   
        return assets
    
    def stats(self, 
              query_string: str,
              query_dict: dict = {},
              **kwargs,
              # fields: list = ['title'],
              # headers: dict = {},
              # cookies: dict = {},
              # proxies: dict = {}, # 默认不使用系统代理
              # timeout: int = 30
              ) -> dict:
        """Executes a statistical aggregation query and returns a FofaAssets container.

        This method provides a user-friendly interface for the `stats_v2` function.
        It determines the asset scope by either using the provided `query_string` or
        by building one from `query_dict`.

        All optional parameters for the API call (e.g., `fields`, `timeout`)
        are passed via `**kwargs`, offering a flexible way to configure the request.

        The method updates `self.results` and `self.assets` and returns a
        `FofaAssets` object configured in 'stats' mode.

        Args:
            query_string: The raw FOFA search query to define the asset scope
                for aggregation. Takes precedence over `query_dict`.
            query_dict: A dictionary of search criteria to build a query from,
                used only if `query_string` is empty.
            **kwargs: Arbitrary keyword arguments passed to the underlying
                `stats_v2` function. Common options include:
                - fields (List[str]): A list of fields to aggregate on.
                Defaults to `['title']`.
                - timeout (int): Request timeout in seconds.
                - headers (dict): Custom HTTP headers.
                - proxies (dict): A dictionary of proxies for the request.

        Returns:
            A `FofaAssets` object in 'stats' mode, which provides dict-like
            access to the raw aggregation data. Returns `None` if the API call fails.

        Raises:
            ParamsMisconfiguredError: If both `query_string` and `query_dict`
                are empty.
        """
        res = None
        kwargs['url'] = self._stats_url
        kwargs['logger'] = self._log_engine
        kwargs['translator'] = _ # 国际化接口
        
        # 检查查询字符串是否为空, 若不为空, 那么不会修改查询字符串的内容
        # 若为空, 则尝试根据查询dict的内容生成格式化查询字符串
        # 最后提取查询字典的keys作为列名fields
        # 首先检查查询字符串是否为空, 如果不为空那么直接传入
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
            
        self.fields = kwargs.pop('fields', ['title'])
        if self.fields == []:
            self.fields = ['title']
            
        hash = sha256(
            ('stats', query_string, self.fields)
        )
        assets = None
        try:
            idx, mode, at, __, assets = self.cache[hash]
            self._log_engine.info(_(
                "cache hit: {assets}, mode: {mode}, at: {at}, query: {query}. \
                    asset query step will be skipped",
            ).format(assets=assets, mode=mode, at=at, query=query_string))
        except Exception as e:
            self._log_engine.debug(_(
                "cache miss: {error}, hash: {hash}. asset query steps will be performed",
            ).format(error=e, hash=hash))
        
        if assets is None or not self._enable_cache:    
            try:
                self._log_engine.debug(_(
                    "Executing stats with query_string: {query_string}, \
                        fields: {fields}"
                ).format(
                    query_string=query_string,
                    fields=self.fields,
                ))
                self.results = stats_v2(
                    apikey=self._apikey,
                    query_string=query_string,
                    fields=self.fields,
                    **kwargs
                    )
                self._log_engine.info(_(
                    "Stats query completed"
                ))
            except Exception as e:
                self._log_engine.error(e)

            try:
                assets = FofaAssets(
                    query_results=self.results,
                    mode='stats',
                    query_string=query_string
                )
                self._log_engine.info(_(
                    "FofaAssets object at 'stats' mode created successfully"
                ))
                new_cache = len(self.cache) + 1, 'stats', now(), query_string, assets
                self.cache[hash] = new_cache
                self.dashboard.append(new_cache)
            except Exception as e:
                self._log_engine.error(e)
        
        return assets
    
    def host(self,
             host: str,
             detail: bool = False,
             **kwargs
             # headers: dict = {},
             # cookies: dict = {},
             # timeout: int = 30
             ) -> dict:
        """Retrieves all available information for a single host.

        This method is a high-level wrapper for the `host_v2` function, simplifying
        calls to the FOFA `/host/{ip}` endpoint. It automatically formats the
        request URL with the provided host IP.

        Optional request parameters like `timeout` and `headers` can be passed
        flexibly via `**kwargs`.

        The method updates `self.results` and `self.assets` and returns a
        `FofaAssets` object configured in 'host' mode.

        Args:
            host: The IP address of the target host to query (e.g., "1.1.1.1").
            detail: If `True`, requests detailed information for each port, such
                as banners and products. Defaults to `False`.
            **kwargs: Arbitrary keyword arguments passed to the underlying
                `host_v2` function. Common options include:
                - timeout (int): Request timeout in seconds.
                - headers (dict): Custom HTTP headers.
                - cookies (dict): Custom cookies.
                - proxies (dict): A dictionary of proxies for the request.

        Returns:
            A `FofaAssets` object in 'host' mode, which provides dict-like
            access to the detailed host data. Returns `None` if the API call fails.
        """
        res = None
        kwargs['url'] = self._host_url.format(host)
        kwargs['logger'] = self._log_engine
        kwargs['translator'] = _
        
        hash = sha256(
            ('host', host, detail)
        )
        assets = None
        try:
            idx, mode, at, __, assets = self.cache[hash]
            self._log_engine.info(_(
                "cache hit: {assets}, mode: {mode}, at: {at}, query: {query}. \
                    asset query step will be skipped",
            ).format(assets=assets, mode=mode, at=at, query=host))
        except Exception as e:
            self._log_engine.debug(_(
                "cache miss: {error}, hash: {hash}. asset query steps will be performed",
            ).format(error=e, hash=hash))

        if assets is None or not self._enable_cache:
            try:
                self._log_engine.debug(_(
                    "Executing host with host: {host}, detail: {detail}"
                ).format(
                    host=host,
                    detail=detail,
                ))
                res = host_v2(
                    apikey=self._apikey,
                    detail=detail,
                    **kwargs
                )
                self._log_engine.info(_(
                    "Host query completed"
                ))
            except Exception as e:
                self._log_engine.error(e)
            self.results = res
            try:
                assets = FofaAssets(
                    query_results=res,
                    mode='host',
                    query_string=f'host="{host}"'
                )
                self._log_engine.info(_(
                    "FofaAssets object in 'host' mode created successfully"
                ))
                new_cache = len(self.cache) + 1, 'host', now(), host, assets
                self.cache[hash] = new_cache
                self.dashboard.append(new_cache)
            except Exception as e:
                self._log_engine.error(e)

        self.fields = kwargs.get('fields', [])
        
        return assets
    
    def history(self):
        if self._enable_cache:
            print(self.dashboard)

    def pick(self, index: int):
        if self._enable_cache:
            return self.dashboard['assets'][index - 1]
    
class FofaAssets:
    """A dynamic data container for results from the FOFA API.

    This class acts as a specialized wrapper around the raw JSON response from a
    FOFA API query. Its behavior and available features change dynamically based on
    the `mode` ('search', 'stats', or 'host') it is initialized with.

    For 'search' mode, this class provides a full-featured interface by formatting
    the data into a `tablib.Dataset`. This enables powerful, spreadsheet-like
    operations such as accessing columns/rows, adding/removing columns, and
    exporting to various formats (CSV, JSON, etc.).

    For 'stats' and 'host' modes, the functionality is currently limited. The
    class provides basic dictionary-like access to the raw, nested data but
    does not support table manipulation (add/subtract columns) or direct export
    to formats like CSV.

    Note:
        To help improve the functionality for `stats` and `host` modes, we
        encourage users to open a GitHub issue and provide sample API responses.
        This will help us understand the data structures and build better
        formatting and manipulation tools.

    Attributes:
        assets (Optional[tablib.Dataset | dict]): The processed data container.
            The type of this attribute depends on the `mode`: `tablib.Dataset`
            for 'search', and `dict` for 'stats' and 'host'.
        fields (list): A list of available field names (headers or keys) for the
            processed data.
        assets_size (int): The number of assets found. For 'search' mode, this
            is the number of rows. For 'stats' mode, it is set to -1 to indicate
            that a simple count is not applicable.
        detail (bool): A flag that is `True` if the data originated from a
            detailed `host` query (i.e., the response contains a 'ports' key).
    """
    def __init__(self,
                 query_results: dict, 
                 # 查询得到的原始json序列化结果
                 # 包括err, errrmsg, size, query那些字段
                 mode: str = 'search', # 查询结果来自的接口
                 # 可选的值有search, stats, host
                 # 必须指定
                 # 这将直接影响实例的魔术方法行为
                 query_string: str = '***', # 查询时的字符串
                 fields: list = ['host', 'title', 'ip', 'domain', 'port', 'country', 'city']
                 # 外部传入的fields列表
                 # 对于search接口, 这是必须指定的
                 ) -> None:
        """Initializes the FofaAssets object.

        Args:
            query_results: The raw dictionary object parsed from the FOFA API's
                JSON response (including 'error', 'size', etc.).
            mode: The source API endpoint for the results. Must be one of
                'search', 'stats', or 'host'. This critically determines the
                internal data structure and available functionality.
            fields: A list of headers for the data columns. This is required
                and primarily used for 'search' mode to structure the dataset.
        """
        self.assets = None
        self.fields = fields # 返回值字段
        self.query_what = query_string
        
        self.assets_size = None # 资产数目
        self.detail: bool = False # 
        # 对于host接口, 这是一个特殊字段
        # 检查是否应该返回端口详情
        
        self._raw_results = query_results
        self._format_mode = mode
        self._format_dict()
        
    # 注册函数
    def _format_dict(self):
        # 对于search接口, 正常格式化即可
        def _format_search_dict():
            self.assets = tablib.Dataset()
            self.assets.headers = self.fields
            for item in self._raw_results['results']:
                if not isinstance(item, (tuple, list)):
                    self.assets.append([item, ])
                    continue
                self.assets.append(item)
            self.assets_size = len(self.assets)
            
        def _format_stats_dict():
            self.assets = {
                'distinct': self._raw_results['distinct'],
                'aggs': self._raw_results['aggs'],
            }
            self.fields = list(
                self._raw_results['aggs'].keys()
                )
            self.assets_size = -1 # 标记为不可用
            
        def _format_host_dict():
            # 移除不必要的字段
            self._raw_results.pop('error')
            # detail=True时, 返回值字段存在ports键
            # 用于存储多个端口的详情
            self.detail = 'ports' in self._raw_results.keys()
            if not self.detail:
                self._raw_results.pop('consumed_fpoint')
                self._raw_results.pop('required_fpoints')
            self.assets = self._raw_results
            self.fields = list(self.assets.keys())

        format_methods = {
            'search': _format_search_dict,
            'stats': _format_stats_dict,
            'host': _format_host_dict
        }
        try:
            format_methods[self._format_mode]()
        except KeyError:
            raise ValueError(_('Invalid format mode'))
        
    @property
    def results(self): # 有需要的话可以把原始查询结果拿出来
        return self._raw_results
    
    def __getattr__(self, name):
        # 分成三个方法来写 
        # 以便后面补充Pythonic的写法
        def __search_res_getattr__():
            return self.assets[name]

        def __stats_res_getattr__():
            return self.assets[name]
        
        def __host_res_getattr__():
            return self.assets[name]
            
        _getattr_methods = {
            'search': __search_res_getattr__,
            'stats': __stats_res_getattr__,
            'host': __host_res_getattr__
        }
        return _getattr_methods[self._format_mode]()
    
    def __getitem__(self, key_or_index):
        def __search_res_getitem__(key_or_index):
            return self.assets[key_or_index]
        def __stats_res_getitem__(key_or_index):
            # 其实就是转接了一下对assets的操作
            return self.assets[key_or_index]
        def __host_res_getitem__(key_or_index):
            return self.assets[key_or_index]
        
        _getitem_methods = {
            'search': __search_res_getitem__,
            'stats': __stats_res_getitem__,
            'host': __host_res_getitem__
        }
        return _getitem_methods[self._format_mode](key_or_index)
    
    def __add__(self, append_column_header: str):
        if self._format_mode == 'search':
            self.assets.append_col(
                [''] * len(self.assets), header=append_column_header
            )
            self.fields.append(append_column_header)
        else: # stats和host接口不方便实现这个操作
            # 上面都没抛出异常, 这里也不用管了
            '''raise NotImplementedError(_("Currently, adding operations to the \
                columns of return values for stats and host interfaces \
                is not supported"))'''
            pass

    
    def __sub__(self, existed_column_header: str):
        if self._format_mode == 'search':
            try:
                del self.assets[existed_column_header]
            except IndexError:
                pass
        else: # stats和host接口不方便实现这个操作
            '''raise NotImplementedError(_("Currently, adding operations to the \
                columns of return values for stats and host interfaces \
                is not supported"))'''
            pass
    
    def __len__(self):
        return self.assets_size
    
    def __repr__(self):
        return _(f"<FofaAssets object queried for {self.query_what}>")
        
    def __str__(self):
        return self.__repr__()
    
    def to_text(self):
        return str(self.assets)
    
    def to_formatted_text(self):
        return str(self.assets)
    
    def to_csv(self):
        try:
            return self.assets.export('csv')
        except AttributeError:
            raise AttributeError(_('Please install tablib[all] to \
                obtain support for additional extension formats'))
    
    def to_json(self):
        try:
            return self.assets.export('json')
        except AttributeError:
            raise AttributeError(_('Please install tablib[all] to \
                obtain support for additional extension formats'))
            
    def to_yaml(self):
        try:
            return self.assets.export('yaml')
        except AttributeError:
            raise AttributeError(_('Please install tablib[all] to \
                obtain support for additional extension formats'))
            
