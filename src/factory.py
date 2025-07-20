# 导入内置模块
from typing import Any, Optional, List, Dict, Set

# 导入第三方依赖
from loguru import logger

# 导入自定义模块

# 定义全局常量
_official_api = "https://fofa.info/api/v1" # 如果修改了api, 那么官方接口可能无法正常使用

class Fofa:
    def __init__(self,
                 # API配置
                 key: str, # API密钥
                 api: str = _official_api, # API地址
                 # 请求配置
                 timeout: int = 3, # 超时时间
                 headers: Optional[Dict[str, str]] = None, # 请求头
                 proxy: Optional[str] = None, # 代理
                 # 模块注册
                 enable_log: bool = False, # 是否启用日志
                 log_engine = logger, # 日志引擎
                 enable_cache: bool = False, # 是否启用缓存
                 enable_format: bool = False, # 是否启用自动数据整理
                 # 若不启用则无法使用后续的魔术方法重载效果
                 ) -> None:
        pass
    
    # 参数和__init__一致
    @classmethod
    def fofa(self,
             **kwargs
             ):
        return Fofa(**kwargs)
    
    def _format_query_dict(self):
        pass
    
    def _format_result_dict(self):
        pass
    
    def search(self):
        pass
    
    def stat(self):
        pass
    
    def host(self):
        pass
    
    def __getattribute__(self, name: str) -> Any:
        pass
    
    def __getitem__(self, name: str) -> Any:
        pass
    
    def __add__(self, append_column_header: str):
        pass
    
    # 重载减法
    def __sub__(self, existed_column_header: str):
        pass
    
    def __repr__(self) -> str:
        pass
    
    def to_formatted_text(self):
        pass
    
    def to_csv(self):
        pass
    
    def to_json(self):
        pass