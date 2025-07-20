# 导入第三方依赖
import requests
from loguru import logger

# 导入标准库
from typing import Any, Optional, Literal, List

def query(
    logger, url: str, apikey: str,
    query_string: str, size: int = 10000,
    page: int = 1, fields: list[str] = [
        'title', 'host', 'link', 'os', 'server', 'icp', 'cert'
    ], full: bool = False
):
    pass