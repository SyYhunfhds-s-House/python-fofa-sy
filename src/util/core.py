# 导入第三方依赖
import requests
from loguru import logger

# 导入标准库
from typing import Any, Optional, Literal, List
from base64 import b64encode

# 导入自定义模块
from ..basic import *

def query(
    logger, translator, url: str, apikey: str, query_string: str, 
    headers: dict = {}, cookies: dict = {},
    size: int = 10000, page: int = 1, fields: list[str] = [
        'title', 'host', 'link', 'os', 'server', 'icp', 'cert'
    ], full: bool = False
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
    result = requests.get(url, params=params, headers=headers, cookies=cookies)

    
    pass