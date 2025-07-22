from urllib import request
import pytest
from loguru import logger
import requests

import sys
sys.path.append("F:\\CodeDev\\python-fofa-sy")
from src.util import search as query
from src.basic.exceptions import (
    FofaConnectionError, 
    FofaRequestFailed,
    FofaQuerySyntaxError,
    LowCreditWarning,
    ZeroCreditWarning,
    EmptyResultsWarning
)

# pytest-mock 是必需的测试依赖
pytest_plugins = ["pytest_mock"]

# 测试正常请求
def test_query_success(requests_mock):
    # 设置测试数据
    test_url = "https://fofa.info/api/v1/search/all"
    test_apikey = "test_api_key"
    test_query_string = "domain=\"example.com\""
    test_response = {
        "error": False,
        "results": [["test title", "example.com"]],
        "size": 1,
        "remaining_queries": 100
    }
    
    # 配置mock响应
    requests_mock.get(test_url, json=test_response, status_code=200)
    
    # 调用函数
    result = query(
        logger=logger,
        translator=lambda x: x,
        url=test_url,
        apikey=test_apikey,
        query_string=test_query_string
    )
    
    # 验证结果
    assert result == test_response

# 测试连接错误
def test_query_connection_error(requests_mock):
    test_url = "https://fofa.info/api/v1/search/all"
    test_apikey = "test_api_key"
    test_query_string = "domain=\"example.com\""
    
    # 模拟连接错误
    requests_mock.get(test_url, exc=requests.ConnectionError)
    
    with pytest.raises(FofaConnectionError):
        query(
            logger=logger,
            translator=lambda x: x,
            url=test_url,
            apikey=test_apikey,
            query_string=test_query_string
        )

# 测试请求失败(非200状态码)
def test_query_request_failed(requests_mock):
    test_url = "https://fofa.info/api/v1/search/all"
    test_apikey = "test_api_key"
    test_query_string = "domain=\"example.com\""
    
    # 模拟非200响应
    requests_mock.get(test_url, status_code=500)
    
    with pytest.raises(FofaRequestFailed):
        query(
            logger=logger,
            translator=lambda x: x,
            url=test_url,
            apikey=test_apikey,
            query_string=test_query_string
        )

# 测试API返回错误
def test_query_api_error(requests_mock):
    test_url = "https://fofa.info/api/v1/search/all"
    test_apikey = "test_api_key"
    test_query_string = "domain=\"example.com\""
    test_response = {
        "error": True,
        "errmsg": "820000: invalid query"
    }
    
    # 模拟API错误响应
    requests_mock.get(test_url, json=test_response, status_code=200)
    
    with pytest.raises(FofaQuerySyntaxError):
        query(
            logger=logger,
            translator=lambda x: x,
            url=test_url,
            apikey=test_apikey,
            query_string=test_query_string
        )

# 测试信用额度不足
def test_query_low_credit(requests_mock):
    test_url = "https://fofa.info/api/v1/search/all"
    test_apikey = "test_api_key"
    test_query_string = "domain=\"example.com\""
    test_response = {
        "error": False,
        "results": [],
        "size": 0,
        "remaining_queries": 1  # 等于阈值
    }
    
    # 模拟信用额度不足
    requests_mock.get(test_url, json=test_response, status_code=200)
    
    with pytest.raises(LowCreditWarning):
        query(
            logger=logger,
            translator=lambda x: x,
            url=test_url,
            apikey=test_apikey,
            query_string=test_query_string,
            threshold_remaining_queries=1
        )

# 测试空结果
def test_query_empty_results(requests_mock):
    test_url = "https://fofa.info/api/v1/search/all"
    test_apikey = "test_api_key"
    test_query_string = "domain=\"example.com\""
    test_response = {
        "error": False,
        "results": [],
        "size": 0,
        "remaining_queries": 100
    }
    
    # 模拟空结果
    requests_mock.get(test_url, json=test_response, status_code=200)
    
    with pytest.raises(EmptyResultsWarning):
        query(
            logger=logger,
            translator=lambda x: x,
            url=test_url,
            apikey=test_apikey,
            query_string=test_query_string
        )