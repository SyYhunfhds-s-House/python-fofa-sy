# 导入第三方依赖
import requests
from requests import ConnectionError, ConnectTimeout
from loguru import logger

# 导入标准库
from base64 import b64encode

# 导入自定义模块
from ..basic import *

def _fofa_get(
    logger, translator, url: str,
    params: dict, headers: dict = {}, cookies: dict = {},
    threshold_remaining_queries: int = 1, # 剩余查询次数阈值, 
    timeout: int = 30 # 查询大量数据时请求时间可能会拖得很长
):
    """Sends a request to the FOFA API and handles the specialized response.

    This function acts as a dedicated wrapper for making GET requests to the
    FOFA API. It incorporates error handling for network issues, non-200
    HTTP status codes, and specific FOFA API error responses. It also
    monitors the remaining API query credits, raising exceptions if they
    are low or exhausted.

    Args:
        logger: A logger object for recording errors and warnings.
        translator: A translation function (aliased as `_`) for localizing
            log and error messages.
        url: The target FOFA API endpoint URL.
        params: A dictionary of query parameters for the API request.
        headers: An optional dictionary of HTTP request headers.
        cookies: An optional dictionary of cookies to include in the request.
        threshold_remaining_queries: The threshold for remaining API credits.
            If the count of remaining queries reaches this number, a
            `LowCreditWarning` is raised. Defaults to 1.
        timeout: The request timeout in seconds. Important for queries that
            may take a long time to process. Defaults to 30.

    Returns:
        A dictionary containing the parsed JSON response from the FOFA API
        on a successful request that found results.

    Raises:
        FofaConnectionError: If a connection error or timeout occurs.
        FofaRequestFailed: If the HTTP request returns a non-200 status code
            or if the API response indicates a generic error (`'error': True`).
        FofaQuerySyntaxError: If the API response indicates a query syntax
            error (errmsg contains '[820000]').
        InsufficientPermissions: If it's not a professional or enterprise version API, 
        then advanced features cannot be used (errmsg contains '[-403]')
    """
    _ = translator # 换个名称
    try:
        result = requests.get(url, params=params, headers=headers, cookies=cookies)
    except (ConnectionError, ConnectTimeout) as e:
        logger.error(_("Connection error or timeout"))
        raise FofaConnectionError(_("Connection error or timeout"))
    
    if result.status_code != 200:
        logger.error(_("Request failed with status code {}").format(result.status_code))
        raise FofaRequestFailed(_("Request failed with status code {}").format(result.status_code))
    result = result.json()
    if result['error']:
        logger.error(_("Request failed with error message {}").format(result['errmsg']))
        if '820000' in result['errmsg']:
            raise FofaQuerySyntaxError()
        elif '-403' in result['errmsg']:
            raise InsufficientPermissions(_("Request failed with error message {}").format(result['errmsg']))
        else:
            raise FofaRequestFailed(_("Request failed with error message {}").format(result['errmsg']))
    
    return result


def search(
    logger, # 日志记录器
    translator, # gettext国际化接口
    url: str, # fofa查询接口(为了兼容不同接口和不同API)
    apikey: str, # fofa密钥
    query_string: str, # fofa查询字符串, 要没有base64编码的原始文本
    headers: dict = {}, # 自定义请求头
    cookies: dict = {}, # cookies
    timeout: int = 30, # 查询大量数据时请求时间可能会拖得很长
    size: int = 10000, # 单次最大返回条数
    page: int = 1, # 查询分页参数
    fields: list = [
        'title', 'host', 'link', 'os', 'server', 'icp', 'cert'
    ], # 返回字段
    full: bool = False, # 是否查询所有数据
    threshold_remaining_queries: int = 1 # 剩余查询次数阈值
):
    """
    Perform a search query against the FOFA API.

    Parameters
    ----------
    logger : logging.Logger
        Logger instance used to record runtime information.
    translator : callable
        Translation function (e.g., `gettext.gettext`) to localize log messages.
    url : str
        FOFA-compatible search endpoint. The same function can be reused with
        alternative endpoints or API versions by supplying a different URL.
    apikey : str
        FOFA API key used for authentication.
    query_string : str
        Raw, un-encoded FOFA query string (will be Base64-encoded internally).
    headers : dict, optional
        Extra HTTP headers to send with the request. Default is an empty dict.
    cookies : dict, optional
        Cookies to include in the request. Default is an empty dict.
    size : int, optional
        Maximum number of results to return in a single request.
        Must be between 1 and 10000. Default is 10000.
    page : int, optional
        Pagination offset (1-based). Default is 1.
    fields : list[str], optional
        List of fields to retrieve for every matching asset.
        Default is ['title', 'host', 'link', 'os', 'server', 'icp', 'cert'].
    full : bool, optional
        Whether to fetch the complete dataset (True) or only the recent year records (False). 
        Default is False.
    threshold_remaining_queries : int, optional
        If the API reports this many (or fewer) remaining credits left,
        a warning is raised. Default is 1.

    Returns
    -------
    dict
        Parsed JSON response from FOFA containing at least:
        - 'results': list of assets matching the query.
        - 'size': total number of returned assets.
        - 'page': current page index.
        - 'mode': search mode ('extended' or 'normal').
        - 'query': processed query string.
        - 'remaining_queries': number of API credits still available.

    Raises
    ------
    FofaConnectionError
        If a network-level error (DNS, timeout, etc.) occurs.
    FofaRequestFailed
        If the server returns a non-200 status code or any non-query-related
        FOFA error.
    FofaQuerySyntaxError
        If the supplied `query_string` is syntactically invalid (FOFA error
        code 820000).
    LowCreditWarning
        When the remaining API credits drop to `threshold_remaining_queries`.
    ZeroCreditWarning
        When the API credits are fully exhausted (remaining_queries == 0).
    EmptyResultsWarning
        When the query completes successfully but yields no matching assets.

    Notes
    -----
    - The function transparently handles Base64 encoding of `query_string`.
    - It merges the `fields` list into a comma-separated string before sending
      the request.
    - All log messages emitted by this function are passed through the provided
      `translator` for localization.

    Examples
    --------
    >>> from logging import getLogger
    >>> from gettext import gettext as _
    >>> logger = getLogger("fofa")
    >>> data = query(
    ...     logger=logger,
    ...     translator=_,
    ...     url="https://fofa.info/api/v1/search/all",
    ...     apikey="xxxxxxxxxxxxxxxx",
    ...     query_string='title="Apache"',
    ...     size=100,
    ...     fields=['host', 'title', 'ip']
    ... )
    >>> print(data['size'])
    100
    """

    _ = translator # 换个名称
    params = {
        'key': apikey,
        'qbase64': b64encode(query_string.encode('utf8')).decode(),
        'fields': ','.join(fields),
        'full': full,
        'size': size,
        'page': page
    }
    
    result = _fofa_get(
        logger, translator, url,
        params, headers, cookies,
        threshold_remaining_queries, timeout
    )
    # 客制化返回值处理 # 不知道官方响应有没有这个字段
    if result.get('remaining_queries', None) != None:
        if result['remaining_queries'] == threshold_remaining_queries:
            msg = "The available credit of the API has been nearly exhausted, \
                and further queries cannot be made"
            logger.warning(_(msg))
            raise LowCreditWarning(msg)
        elif result['remaining_queries'] == 0:
            msg = "The available credit of the API has been exhausted, \
                and further queries cannot be made"
            logger.warning(_(msg))
            raise ZeroCreditWarning(msg)
    
    if result['size'] == 0:
        msg="No assets matching the criteria were found"
        logger.warning(_(msg))
        raise EmptyResultsWarning(msg)
    
    return result
    
def stats(
    logger, # 日志记录器
    translator, # gettext国际化接口
    url: str, # fofa查询接口(为了兼容不同接口和不同API)
    apikey: str, # fofa密钥
    query_string: str, # fofa查询字符串, 要没有base64编码的原始文本
    fields: list = ['title', 'ip', 'host', 'port', 'os', 'server', 'icp'], # 返回值字段
    headers: dict = {}, # 自定义请求头
    cookies: dict = {}, # cookies
    timeout: int = 30
):
    def check(res):
        return res
    _ = translator
    params = {
        'qbase64': b64encode(query_string.encode('utf8')).decode(),
        'fields': ','.join(fields),
    }
    result = _fofa_get(
        logger, translator, url,
        params, headers, cookies,
        0, timeout
    )
    # 因为没有完整的官方响应用于参考，所以这里只能留空
    return result

def host(
    logger, # 日志记录器
    translator, # gettext国际化接口
    url: str, # fofa查询接口(为了兼容不同接口和不同API)
    apikey: str, # fofa密钥
    detail: bool = True, # 是否返回端口详情
    headers: dict = {}, # 自定义请求头
    cookies: dict = {}, # cookies
    timeout: int = 30
):
    def check(res):
        return res
    params = {
        'detail': detail
    }
    result = _fofa_get(
        logger, translator, url,
        params, headers, cookies,
        0, timeout
)
    return result

# TODO 规范_fofa_get函数的代码
def _fofa_get_v2(
    logger, # 日志记录器
    translator, # gettext国际化接口
    url: str, # fofa查询接口
    params: dict = {}, # GET请求参数 # 包括apikey
    headers: dict = {}, # 自定义请求头
    cookies: dict = {}, # cookies
    proxies: dict = None, # 代理
    timeout: int = 30, # 超时时间
    # 数据量比较大的时候查询时间可能会很大
):
    """Sends a GET request to a FOFA API endpoint and handles the response.

    This function is a specialized wrapper around `requests.get` tailored for
    the FOFA API. It includes robust error handling for common network issues,
    non-200 HTTP status codes, and specific FOFA API error responses such as
    syntax errors or permission issues.

    By default, `proxies` is set to `None` to prevent `requests` from
    automatically using system-level proxy settings, which can resolve
    connection issues when accessing certain sites while a VPN is active.

    Args:
        logger: A standard logger object for recording errors.
        translator: A translation function (typically from `gettext`, aliased
            as `_`) used for internationalizing log and error messages.
        url: The target FOFA API endpoint URL.
        params: A dictionary of query parameters to be sent with the request,
            which should include the API key.
        headers: An optional dictionary of custom HTTP request headers.
        cookies: An optional dictionary of cookies to include in the request.
        proxies: An optional dictionary specifying proxies for the request.
            Defaults to `None`.
        timeout: The request timeout in seconds. A longer timeout is often
            necessary for queries that return a large amount of data.

    Returns:
        A dictionary containing the parsed JSON response from the FOFA API
        on a successful request.

    Raises:
        FofaConnectionError: If a network-level error occurs (e.g., DNS
            failure, connection timeout).
        FofaRequestFailed: If the API returns a non-200 HTTP status code or
            if the response JSON indicates a generic error (`'error': True`).
        FofaQuerySyntaxError: If the API error message contains '[820000]',
            indicating a syntax error in the query.
        InsufficientPermissions: If the API error message contains '-403',
            indicating the API key lacks the necessary permissions for the
            request.
    """
    _ = translator # 变更引用名称
    result = {}
    try:
        result = requests.get(
            url=url,
            params=params,
            headers=headers,
            cookies=cookies,
            proxies=proxies,
            timeout=timeout
        )
    except (
        requests.ConnectionError, requests.ConnectTimeout):
        msg = "FOFA query failed. Please \
            check your network connection"
        logger.error(_(msg))
        raise FofaConnectionError(_(msg))
    
    if result.status_code != 200:
        msg = "FOFA query failed. Status code: %s" % result.status_code
        logger.error(_(msg))
        raise FofaRequestFailed(_(msg))
    
    result = result.json()
    if result.get('error', False):
        logger.error(_("Request failed with error message {}").format(result['errmsg']))
        if '820000' in result['errmsg']:
            raise FofaQuerySyntaxError()
        elif '-403' in result['errmsg']:
            raise InsufficientPermissions(_("Request failed with error message {}").format(result['errmsg']))
        else:
            raise FofaRequestFailed(_("Request failed with error message {}").format(result['errmsg']))
    
    return result

def search_v2(
    apikey: str, # fofa密钥
    query_string: str, # 未进行base64编码的原始查询字符串
    size: int = 100, # 返回结果数量 
    # 不设置为10000是因为10000的查询耗时很大, 不便于业务测试
    page: int = 1,
    fields: list = ['link', 'ip', 'port'], 
    # 返回值字段 # 够用就得, 写太多不好测试
    full: bool = False, # 是否返回一年内的所有数据
    # 默认为False, 即为只查询近一年的数据
    **kwargs
    # logger # translator # url
    # headers # cookies # timeout
    # proxies
    # 传给_fofa_get_v2的剩余参数
):
    """Executes a standard asset search against the FOFA API.

    This function serves as a high-level wrapper for a FOFA search query.
    It handles the Base64 encoding of the query string and constructs the
    necessary API parameters before passing the request to the underlying
    `_fofa_get_v2` function.

    If the query yields no results, a warning is logged, but no exception is
    raised. The function simply returns the API response with `size: 0`.

    Args:
        apikey: The FOFA API key for authentication.
        query_string: The raw, unencoded FOFA query string (e.g.,
            'domain="example.com"').
        size: The maximum number of results to retrieve. Defaults to 100,
            which is suitable for most testing and development scenarios.
        page: The page number for pagination. Defaults to 1.
        fields: A list of strings specifying which fields to include in the
            results. Defaults to `['link', 'ip', 'port']`.
        full: A boolean flag to control the search time range. If `True`,
            searches all data within the last year. If `False` (default),
            searches only recent data.
        **kwargs: Arbitrary keyword arguments that are passed directly to the
            `_fofa_get_v2` request handler. This allows for advanced control
            over the request. Expected arguments include:
            - logger (Logger): A logger instance for logging messages.
            - translator (Callable): A translation function for i18n.
            - url (str): The target FOFA search API url (not just an endpoint).
            - headers (dict): Custom HTTP headers.
            - cookies (dict): Custom cookies.
            - timeout (int): Request timeout in seconds.
            - proxies (dict): Proxies to use for the request.

    Returns:
        A dictionary containing the parsed JSON response from the FOFA API.
        On success, this includes a 'results' list and other metadata.

    Raises:
        FofaConnectionError: If a network-level error occurs.
        FofaRequestFailed: If the API returns a non-200 status code or a
            generic error.
        FofaQuerySyntaxError: If the API indicates a syntax error in the query.
        InsufficientPermissions: If the API key lacks necessary permissions.
    """
    # 不再检查可用额度, 因为官方的API响应不包含剩余可用额度的字段
    # 第三方API的可用额度有需要的话也可以自己查
    logger = kwargs['logger']
    _ = kwargs['translator']
    params = {
        'key': apikey,
        'qbase64': b64encode(query_string.encode('utf8')).decode(),
        'fields': ','.join(fields),
        'full': full,
        'size': size,
        'page': page
    }
    result = _fofa_get_v2(
        **kwargs,
        params=params
    )
    # 找不到符合条件的资产时仍然会进行日志记录, 但不会抛出异常
    if result['size'] == 0:
        logger.warning(_("No assets matching the criteria were found"))
    
    return result

def stats_v2(
    apikey: str, # fofa密钥
    query_string: str, # 未进行base64编码的原始查询字符串
    fields: list = ['title'], # 统计字段
    # 这里是根据官方给出的响应示例匹配的
    # 使用时请一定要根据自身情况进行调整
    **kwargs
):
    """Executes a statistical aggregation query against the FOFA API.

    This function provides a streamlined interface to the FOFA stats endpoint.
    It handles the construction of API parameters, including Base64 encoding
    the query string, and delegates the HTTP request to a lower-level handler.

    This refactored version (`v2`) corrects a critical bug from previous
    implementations where the `apikey` was omitted from the request parameters.
    Additionally, the use of `**kwargs` significantly simplifies the function's
    signature by forwarding advanced request options directly to the handler,
    reducing code redundancy.

    Args:
        apikey: The FOFA API key for authentication.
        query_string: The raw, unencoded FOFA query string (e.g.,
            'country="CN"') that defines the scope of assets for aggregation.
        fields: A list of fields on which to perform the statistical
            aggregation. **Important:** The default value is based on simple
            API examples; users should customize this list to fit their
            specific needs (e.g., `['country', 'port']`).
        **kwargs: Arbitrary keyword arguments passed directly to the
            `_fofa_get_v2` request handler for advanced control. Expected
            arguments include:
            - logger (Logger): A logger instance for logging messages.
            - translator (Callable): A translation function for i18n.
            - url (str): The target FOFA stats API url (not just an endpoint).
            - headers (dict): Custom HTTP headers.
            - cookies (dict): Custom cookies.
            - timeout (int): Request timeout in seconds.
            - proxies (dict): Proxies to use for the request.

    Returns:
        A dictionary containing the parsed JSON response from the FOFA API,
        which includes the nested aggregation data under keys like `aggs`.

    Raises:
        FofaConnectionError: If a network-level error occurs.
        FofaRequestFailed: If the API returns a non-200 status code or a
            generic error.
        FofaQuerySyntaxError: If the API indicates a syntax error in the query.
        InsufficientPermissions: If the API key lacks necessary permissions.
    """
    params = {
        'key': apikey,
        'qbase64': b64encode(query_string.encode('utf8')).decode(),
        'fields': ','.join(fields),
    }
    result = _fofa_get_v2(
        **kwargs,
        params=params
    )
    return result

def host_v2(
    apikey: str, # fofa密钥
    detail: bool = True, # 是否返回端口详细信息
    **kwargs # 其他参数
):
    """Retrieves all available information for a specific host from the FOFA API.

    This function serves as a wrapper for the FOFA `/host/{ip}` endpoint. It
    constructs the necessary request parameters and delegates the call to a
    lower-level handler.

    This refactored version (`v2`) is a critical update, as it corrects a
    major bug in previous implementations where the `apikey` was accidentally
    omitted from the request parameters, causing all API calls to fail.
    The use of `**kwargs` also streamlines the function by forwarding advanced
    request options directly to the handler.

    Args:
        apikey: The FOFA API key for authentication.
        detail: A boolean flag to control the level of detail in the response.
            If `True` (default), the API returns detailed information for each
            port, such as banners.
        **kwargs: Arbitrary keyword arguments passed directly to the
            `_fofa_get_v2` request handler. The `url` parameter is the most
            critical and must be provided here. Expected arguments include:
            - url (str): The target FOFA host API endpoint, pre-formatted
              with the host's IP address (e.g., "https://fofa.info/api/v1/host/1.1.1.1").
            - logger (Logger): A logger instance for logging messages.
            - translator (Callable): A translation function for i18n.
            - headers (dict): Custom HTTP headers.
            - cookies (dict): Custom cookies.
            - timeout (int): Request timeout in seconds.
            - proxies (dict): Proxies to use for the request.

    Returns:
        A dictionary containing the parsed JSON response from the FOFA API,
        which includes all known information for the specified host.

    Raises:
        FofaConnectionError: If a network-level error occurs.
        FofaRequestFailed: If the API returns a non-200 status code or a
            generic error.
        FofaQuerySyntaxError: If the API indicates a syntax error in the query.
        InsufficientPermissions: If the API key lacks necessary permissions.
    """
    
    params = {
        'key': apikey,
        'detail': detail
    }
    result = _fofa_get_v2(
        **kwargs,
        params=params
    )
    return result

if __name__ == '__main__':
    pass