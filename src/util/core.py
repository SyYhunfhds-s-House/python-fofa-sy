# 导入第三方依赖
import requests
from requests import ConnectionError, ConnectTimeout
from loguru import logger

# 导入标准库
from typing import Any, Optional, Literal, List
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
    fields: list[str] = [
        'title', 'host', 'link', 'os', 'server', 'icp', 'cert'
    ], # 返回字段
    full: bool = False, # 是否查询所有数据
    threshold_remaining_queries: int = 1 # 剩余查询次数阈值
):
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
        msg = "The available credit of the API has been exhausted, \
            and further queries cannot be made"
        logger.warning(_(msg))
        raise LowCreditWarning(msg)
    elif result['remaining_queries'] == 0:
        logger.warning(_(msg))
        raise ZeroCreditWarning(msg)
    
    if result['size'] == 0:
        logger.warning(_(msg))
        raise EmptyResultsWarning(msg)
    
    return result