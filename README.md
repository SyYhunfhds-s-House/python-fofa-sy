--- 
## 项目依赖
- loguru, 著名日志库(可选)
- cachetools, 缓存库(可选)
- typing-extensions, 类型注解库(向后兼容), 这样在Python 3.8及以下版本也可以使用`typing`模块中的类型注解
- tablib, 表格数据处理库
- requests, HTTP客户端

## 项目结构
- main.py, 主程序入口
- src/, 源代码目录

    - util/, 工具模块
        - query.py, 核心出装, fofa查询
            - `_fofa_get(
            logger, translator, url: str, params: dict, timeout: int = 3
            )`, 封装requests.get()方法, 用于查询接口的请求 (预留logger接口)
            - `search(logger, url: str, key: str, query_string: str, size: int = 10000, page: int = 1, fields: list[str] = ['title', 'host', 'link', 'os', 'server', 'icp', 'cert'], full: bool = False,)`, 查询接口封装 (预留logger接口)
            - `stats(logger, translator, url: str,
            key: str, query_string: str, fields: list[str] = ['title', 'host', 'link', 'os', 'server', 'icp', 'cert']
            )`, 统计聚合接口封装
            - `host(logger, translator, url: str, key: str,
            detail: bool = False # 是否显示端口详情
            )`, Host聚合接口封装
        - cache.py, 缓存模块(封装cachetools)
    
    - basic/, 底层模块
        - etc.py, 杂项模块
            - `_format_query_dict()`, 将查询dict格式化为查询字符串
            - `_format_result_dict()`, 将返回的数据格式化为`tablib.Dataset`对象
                - **注意**: 只有search接口的返回值处理是可以使用的, 其他两个接口的返回值则由于返回值结果存在嵌套以及嵌套层级不一致, 故暂无法实现
            - `_check_query_dict()`, 检查查询字典的键是否为API子接口所支持的键, 否则抛出语法异常 `FofaSyntaxError`
            - `ParamsMisconfiguredError`, 参数配置错误异常, 继承自`builtins.SyntaxError`, 当fields中存在当前接口不存在的字段时
            会抛出, 这样就不会在请求时才遇到查询语法错误了
            - `_`, 占位符, 预留国际化接口
        - exceptions.py, 自定义异常封装

    - factory.py, 工厂模块, 组装得到Fofa类

- locales, 国际化文件
    - en_US, 英文
    - zh_CN, 中文
- tests, 测试目录



## fofaAPI规划
- Fofa, 主类
    - *API字段* (以单下划线开头的约定为私有字段; 无特殊注明的均为成员字段而非函数内定义的字段)
        - *API配置字段* :
            - `_api`, 私有字段，API接口地址, 默认值为`https://fofa.info/api/v1`, 可接受外部初始化
            - `_apikey`, 私有字段，API密钥, 必须接受外部初始化
            - `_query_api`, 私有字段，查询接口, 默认值为`/search/all`, 如果`_api`不为官方API则该字段不会被使用(若强行使用则将报错`NotImplementedError`)
                - `_query_url`, 私有字段，查询接口URL, 由`_api + _query_api`生成

            - `_stat_api`, 私有字段，统计聚合接口, 默认值为`/search/stats`, 如果`_api`不为官方API则该字段不会被使用
                - `_stat_url`, 私有字段，统计聚合接口URL, 由`_api + _stat_api`生成

            - `_host_api`, 私有字段，Host聚合接口, 默认值为`/host/{host}`, 如果`_api`不为官方API则该字段不会被使用
                - `_host_url`, 私有字段，Host聚合接口URL, 由`_api + _host_api.format(host=host)`生成

        - *API查询字段* :
            - *函数作用域字段* :
                - `_query_dict`, 私有字段，查询字典, 可选接受外部初始化
                - `_query_string`, 私有字段，查询字符串, 可选接受外部传参(默认值为空字符串，若为空，则由`_query_dict`生成)(若两个参数都为空，则抛出报错)
                - `_size`, 私有字段，查询结果数量, 可选接受外部传参(默认值为10000)
                - `_page`, 私有字段，查询结果页码, 可选接受外部传参(默认值为1)
                - `_fields : list[str]`, 私有字段，查询结果字段, 可选接受外部传参(默认值为`['ip', 'server', 'os', 'link']`)
                - `_full : bool`, 私有字段，是否查询全部的数据, 可选接受外部传参(默认值为`False`，即默认查询一年内的数据)
        - *模块配置字段* :
            - `_enable_log`, 私有字段，是否启用日志, 可选接受外部初始化(默认值为`False`)(使用loguru实现)
                - `enable_colorful_log`, 私有字段，是否启用彩色日志, 可选接受外部初始化(默认值为`False`)(使用colorama实现)
            - `_enable_cache`, 私有字段，是否启用缓存, 可选接受外部初始化(默认值为`False`)(使用cachetools实现)
            - `_enable_format`, 私有字段，是否启用自动格式化查询结果, 可选接受外部初始化(默认值为`True`)(使用`agate`实现)
        - *公共字段* :
            - `columns`, 查询结果字段, 类型为`pylist`, 包含查询结果的列名(即`_fields`)
            - `results`, 查询结果, 类型为`pydict`, 包含查询结果的所有字段


    - *API公共方法*
        - `fofa()`, 公共方法, 封装`__init__()`, 返回值为Fofa类实例; `__init__()`也会保留, 所以会有两种操作初始化一个fofa实例, 即`Fofa()`和`Fofa.fofa()`, 两者等价
        - `search()`, 公共方法, 查询(接口)数据并返回`_format_result_dict()`格式化后的结果
        - `stat()`, 公共方法, 查询(统计聚合)数据并返回`_format_result_dict()`格式化后的结果
        - `host()`, 公共方法, 查询(Host聚合)数据并返回`_format_result_dict()`格式化后的结果
        - 重写`__getattr__()`, 特殊方法, 若查询结果中包含`fields`中的字段，则可以直接使用`instance.field_name`的方式访问查询结果中的数据
        - 重写`__getitem__()`, 特殊方法, 若查询结果中包含`fields`中的字段，则可以直接使用`instance['field_name']`的方式访问查询结果中的数据
        - 重写`__add__()`, 特殊方法, 需要临时向查询结果中添加一个列时，使用`instance + appended_column_header`的方式添加, 返回的是查询结果而非整个实例
        - 重写`__del__()`, 特殊方法, 若查询结果中包含`fields`中的字段，则可以直接使用`del instance.field_name`的方式删除查询结果中的数据( 直接删一个列包括里面的数据)
        - 重写`__sub__()`, 特殊方法, 需要临时从查询结果中删除一个列时，使用`instance - deleted_column_header`的方式删除, 返回的是查询结果而非整个实例
        - 重写`__repr__()`, 特殊方法，返回值为`<host={host} server={server} ...>`
        - `to_formatted_text()`, 公共方法, 将查询结果格式化为文本并返回
        - `to_csv()`, 公共方法, 将查询结果格式化为CSV并返回; 对应地会有`from_csv()`方法, 用于将CSV格式的字符串转换为查询结果字典
        - `to_json()`, 公共方法, 将查询结果格式化为JSON并返回`; 对应地会有`from_json()`方法, 用于将JSON格式的字符串转换为查询结果字典
        - `to_xlsx()`, 公共方法, 将查询结果格式化为XLSX并返回; 对应地会有`from_xlsx()`方法, 用于将XLSX格式的字符串转换为查询结果字典
        - *格式化数据后的公共方法*:
            - 根据`fields`中的字段，可以直接使用`instance.ip`的方式访问查询结果中的(IP地址)数据, 返回值类型为`pylist`
            - 根据`fields`中的字段，可以直接使用`instance['ip']`的方式访问查询结果中的(IP地址)数据, 返回值类型为`pylist`

    - *API私有方法*
        - *查询数据格式化* :
            - `_format_query_dict()`, 私有方法, 从`_query_dict`中取出查询字典并格式化, 返回值为base64编码接UTF8解码的字符串
        - *返回数据自动格式化* :
            - `_format_result_dict()`, 私有方法, 从返回的JSON数据中取出查询结果并格式化, 返回值为字典

- Fofa.exception, 异常模块
    - *对接的FOFA的API子模块附属异常* : `Fofa.api.exception`; 会自动加上`Fofa`前缀, 表示继承自对应的异常类
        - *API配置导致的异常* :
            - EmptyKeyError, 异常类, 当API密钥为空时抛出, 继承自ValueError
            - NonOfficialAPIError, 异常类, 当使用的不是官方API但尝试使用官方接口时抛出, 继承自NotImplementedError
        - *API查询时可能有的异常* :
            - LowAllowmentWarning, 异常类, 当可用额度为1时抛出, 继承自Warning
            - EmptyAllowmentError, 异常类, 当可用额度为0时抛出, 继承自ValueError
            - EmptyResultsWarning, 异常类, 当查询结果为空时抛出, 继承自Warning
            - ConnectionError, 异常类, 当连接API时出错时抛出, 继承自httpx.ConnectionError或requets.ConnectionError
            - SyntaxError, 异常类, 当查询语法错误时抛出, 继承自SyntaxError

    - *utility套具子模块附属异常* : `Fofa.util.exception`

***
## 项目开源证书
MIT License