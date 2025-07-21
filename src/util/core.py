# 导入第三方依赖
import requests
from requests import ConnectionError, ConnectTimeout
from loguru import logger

# 导入标准库
from base64 import b64encode

# 导入自定义模块
from ..basic import *

def query(
    logger, # 日志记录器
    translator, # gettext国际化接口
    url: str, # fofa查询接口(为了兼容不同接口和不同API)
    apikey: str, # fofa密钥
    query_string: str, # fofa查询字符串, 要没有base64编码的原始文本
    headers: dict = {}, # 自定义请求头
    cookies: dict = {}, # cookies
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
        else:
            raise FofaRequestFailed(_("Request failed with error message {}").format(result['errmsg']))
    
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