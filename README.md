***
# Python-Fofa-SY

受Shodan官方API启发, 个人编写的一个第三方FOFA Python API
目前版本为V1, 下面的帮助文档也是基于V1版本的。

***

### **一个新手开发者的开源之旅与诚挚请求**
*Gemini 2.5 Pro生成*

您好！非常感谢您关注并使用 `python-fofa-sy`。

作为我的第一个公开的开源项目，它的诞生与成长过程，对我而言是一次充满挑战、也收获满满的学习之旅。从最初一个仅能满足个人需求的小脚本，到如今一个可被打包、分发的工具，我踩过了许多新手开发者都会遇到的“坑”。

通过不断地重构和迭代，我解决了以下这些在早期版本中真实存在过的问题：

*   **忘记关键参数**：在最初的版本中，`stats` 和 `host` 接口的封装甚至忘记了传递最核心的 `apikey`，导致请求必然失败。
*   **代码冗长**：早期的函数设计包含了大量重复的代码，不易维护，后来通过 `**kwargs` 等方式进行了大幅精简。
*   **项目结构错误**：我曾因为不正确的打包配置，导致用户在安装后无法正常 `import` 包，这是打包过程中最经典的错误之一。
*   **元数据缺失**：在项目配置中，一度漏掉了作者、主页、许可证等重要的元数据信息，让项目看起来很不专业。

正是因为有了这些经历，我深知这个项目依然有许多可以改进的地方。因此，我真诚地欢迎并鼓励每一位使用者：

**如果您在使用中遇到任何 Bug、发现文档有不清晰之处，或者有任何功能上的建议，都请不要犹豫，通过项目的 [GitHub Issues](https://github.com/SyYhunfhds-s-House/python-fofa-sy/issues) 页面告诉我。**

您的每一个 Issue 对我来说都是极其宝贵的反馈，是帮助我这个新手不断进步、完善我第一个开源项目的最大动力。

再次感谢您的支持！

***

## 安装

```bash
# pypi源
 pip install python-fofa-sy
# testpypi源
# prelease安装
uv pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple --prerelease=allow python-fofa-sy --no-cache
# 正式版安装
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple python-fofa-sy
```
- --index-url 主索引
- --extra-index-url 备用索引
- --prerelease=allow 允许预发布版本
- --no-cache 禁用uv本地缓存

```
# 安装后
pip show python-fofa-sy      
Name: python-fofa-sy
Version: 1.0.1
Summary: Fofa引擎的Python接口 | A Python api for fofa assets-scan engine
Home-page:
Author:
Author-email:
License:
Location: e:\pythonkits\pythonversions\python37\lib\site-packages
Requires: cachetools, loguru, requests, tablib
Required-by:
```

## Fofa API 客户端使用文档

*Gemini 2.5 Pro生成*

### 1. 核心设计理念

`python-fofa-py`客户端采用了**客户端与结果容器分离**的设计模式：

-   **`Fofa` 类 (客户端)**: 它的核心职责是**配置和发起 API 请求**。通过实例化这个类来设置您的 API 密钥等全局配置。
-   **`FofaAssets` 类 (结果容器)**: `Fofa` 类的 `search`, `stats`, `host` 方法在成功请求后，会返回一个 `FofaAssets` 实例。这个实例**专门负责存储和处理该次请求返回的数据**，并提供了常用的魔术方法（如 `len()`, `[]`）和导出方法（如 `.to_csv()`）。

### 2. 快速入门

下面的示例将展示一次完整的查询流程：从初始化客户端到获取并处理结果。

```python
# 1. 导入 Fofa 客户端
from fofa_py import Fofa

# 2. 初始化客户端，并填入您的 API 密钥
# 假设您的 FOFA Key 是 "YOUR_FOFA_API_KEY"
client = Fofa(key="YOUR_FOFA_API_KEY")

# 3. 执行查询
# 我们强烈建议您通过 `fields` 参数自定义返回字段
try:
    assets = client.search(
        query_string='domain="example.com"', 
        size=10, 
        fields=['host', 'ip', 'port', 'title']
    )

    # 4. 处理返回的 FofaAssets 对象
    if assets:
        print(f"查询成功，共找到 {len(assets)} 条资产。")

        # 像操作表格一样操作数据
        print("所有 IP 地址:", assets['ip'])
        
        # 导出为 CSV 格式 # 需要tablib[all]拓展
        csv_data = assets.to_csv()
        with open("results.csv", "w", encoding="utf-8") as f:
            f.write(csv_data)
        print("结果已保存至 results.csv")

except Exception as e:
    print(f"查询失败: {e}")

```

### 3. API 详解

#### 3.1. Fofa 类的初始化

在执行任何操作之前，您必须先实例化一个 `Fofa` 对象。

```python
client = Fofa(key: str, api: str = "https://fofa.info", timeout: int = 30, **kwargs)
```

**主要参数:**

-   `key` (str): **必需**。您的 FOFA 账户 API 密钥。
-   `api` (str): 可选。FOFA API 的根地址，默认为官方地址。如果您有私有化部署，请修改此项。
-   ~~`timeout` (int): 可选。全局默认的请求超时时间（秒），默认为 30 秒。~~

#### 3.2. 查询方法

##### **`search()` 方法**

用于执行标准的资产搜索。

```python
assets = client.search(query_string: str, query_dict: dict = {}, **kwargs)
```

-   **`query_string`**: 您要查询的 FOFA 语句，例如 `'domain="example.com"'`。
-   **`query_dict`**: 仅当 `query_string` 为空时生效。一个用于构造查询语句的字典，例如 `{'domain': 'example.com'}`。
-   **`**kwargs`**: 灵活的自定义参数，用于控制查询行为。

**`search()` 的常用 `kwargs` 参数：**

-   `fields` (list): 您希望返回的结果字段列表。**强烈建议您总是手动提供此参数**，以确保获得所需数据。默认值（如 `['link', 'ip', 'port']`）仅为基础示例，通常无法满足您的业务需求。
-   `size` (int): 希望返回的资产数量，默认为 100。
-   `page` (int): 查询结果的页码，默认为 1。
-   `full` (bool): 是否查询近一年的全部数据，默认为 `False`。设为 `True` 会增加查询耗时。

**返回值**: 一个 `FofaAssets` 实例。

##### **`stats()` 方法**

用于执行统计聚合查询。

```python
assets = client.stats(query_string: str, query_dict: dict = {}, **kwargs)
```

-   **`query_string` / `query_dict`**: 用于定义需要统计的资产范围。
-   **`**kwargs`**: 灵活的自定义参数。

**`stats()` 的常用 `kwargs` 参数：**

-   `fields` (list): **必需**。您希望进行统计的字段，例如 `['country', 'port']`。

**返回值**: 一个 `FofaAssets` 实例。此模式下的实例功能有限，主要提供类似字典的访问方式来获取聚合数据。

##### **`host()` 方法**

用于获取单个 IP 的详细信息。

```python
assets = client.host(host: str, **kwargs)
```

-   `host` (str): **必需**。您要查询的目标主机的 IP 地址。
-   **`**kwargs`**: 灵活的自定义参数。

**`host()` 的常用 `kwargs` 参数：**

-   `detail` (bool): 是否返回端口的详细信息，默认为 `False`。

**返回值**: 一个 `FofaAssets` 实例。与 `stats` 类似，此模式下的实例功能有限。

### 4. `FofaAssets` 结果容器

当 `client.search()` 等方法成功返回后，您会得到一个 `FofaAssets` 对象，您可以这样使用它：

#### 4.1. 对于 `search` 接口的结果

`search` 接口返回的 `FofaAssets` 对象功能最完善，可以像操作一个表格（`tablib.Dataset`）一样操作它。

```python
# 假设 assets = client.search(...)
# 获取资产数量
num_assets = len(assets)

# 像字典一样按列名获取整列数据 (返回一个列表)
all_ips = assets['ip']
all_ports = assets['port']

# 像访问实例属性一样获取整列数据 (同样返回一个列表)
all_hosts = assets.host
all_titles = assets.title
# 注意: 由于是通过`__getattr__`实现的, 因此, IDE无法自动补全可用的返回值属性

# 像列表一样按索引获取整行数据
first_asset_row = assets[0]

# 迭代每一行
for row in assets:
    print(row) # (host, ip, port, title)

# 导出数据
json_data = assets.to_json()
csv_data = assets.to_csv()
```

#### 4.2. 对于 `stats` 和 `host` 接口的结果

由于这两个接口返回的是多层嵌套且行数不固定的 JSON 数据，`FofaAssets` 对象主要充当一个字典的代理。

```python
# 假设 assets = client.stats(...)

# 直接像字典一样访问聚合数据
aggs_data = assets['aggs']
distinct_data = assets['distinct']
print(aggs_data['country'])

# 同样，对于 host 接口
# assets = client.host('8.8.8.8')
print(assets['asn'])
print(assets['protocol'])
```
**注意**: 表格操作（如 `len()`）和导出方法（`.to_csv()`）在 `stats` 和 `host` 模式下行为不可用。

***

## 项目目前存在的问题

### 潜在的BUG
- `search`接口中返回值字段列表和返回值实际有的字段可能不一致
- `pyproject.toml`配置不全导致发布之后缺失个人联系信息

### 未实现的功能
- 国际化支持(使用gettext库实现, 暂未完成)
    1. 检查日志信息, 补充调试语句, 为国际化支持完善文本库


### 未完成的功能

*** 
## 项目依赖
- loguru, 日志库(可选)
- cachetools, 缓存库(可选)
- typing-extensions, 类型注解库(向后兼容), 这样在Python 3.8及以下版本也可以使用`typing`模块中的类型注解
- tablib, 表格数据处理库
- tablib[all], tablib的拓展版, 支持导入导出多种格式 (可选)
- requests, HTTP客户端

## 项目结构
- main.py, 主程序入口
- src/, 源代码目录

    - util/, 工具模块
        - query.py, 核心出装, fofa查询
            - `_fofa_get(
            logger, translator, url: str, params: dict, timeout: int = 3
            )`, 封装requests.get()方法, 用于查询接口的请求 (预留logger接口)
            - `search(logger, url: str, key: str, query_string: str, 
            headers: dict = {}, cookies: dict = {}, timeout: int = 30,
            size: int = 10000, page: int = 1, fields: list[str] = ['title', 'host', 'link', 'os', 'server', 'icp', 'cert'], full: bool = False, 
            threshold_remaining_queries: int = 1
            )`, 查询接口封装 (预留logger接口)
            - `stats(
                logger, # 日志记录器
                translator, # gettext国际化接口
                url: str, # fofa查询接口(为了兼容不同接口和不同API)
                apikey: str, # fofa密钥
                query_string: str, # fofa查询字符串, 要没有base64编码的原始文本
                fields: list = ['title', 'ip', 'host', 'port', 'os', 'server', 'icp'], # 返回值字段
                headers: dict = {}, # 自定义请求头
                cookies: dict = {}, # cookies
                timeout: int = 30
            )`, 统计聚合接口封装
            - `host(
                logger, # 日志记录器
                translator, # gettext国际化接口
                url: str, # fofa查询接口(为了兼容不同接口和不同API)
                apikey: str, # fofa密钥
                detail: bool = True, # 是否返回端口详情
                headers: dict = {}, # 自定义请求头
                cookies: dict = {}, # cookies
                timeout: int = 30
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
        - `Fofa`类, 主类
        - `FofaResults`类, 封装查询结果
            - 将一系列魔术方法分隔到这里, 这样可以避免干扰Fofa主类的使用

- locales, 国际化文件
    - `fofa_py_src.pot`, 提取源代码目录生成的可翻译字符串`.pot`文件, 用于生成`.po`和`.mo`文件
        - `pybabel extract -o locales/fofa_py_src.pot src/`, 提取字符串
        - `pybabel init -i locales/fofa_py_src.pot -d locales -l zh_CN`, 初始化某语言的`.po`
        - `pybabel update -i locales/fofa_py_src.pot -d locales`, 更新某语言的`.po`
        - `pybabel compile -d locales`, 编译`.po`文件为`.mo`文件, 用于运行时加载
    - en_US, 英文
    - zh_CN, 中文
- tests, 测试目录



## fofaAPI规划
- Fofa, 主类
    - *API字段* (以单下划线开头的约定为私有字段; 无特殊注明的均为成员字段而非函数内定义的字段)
        - *API配置字段* :
            - `_api`, 私有字段，API接口地址, 默认值为`https://fofa.info`, 可接受外部初始化
            - `_apikey`, 私有字段，API密钥, 必须接受外部初始化
            - `_search_api`, 私有字段，查询接口, 默认值为`/api/v1/search/all`, 如果`_api`不为官方API则该字段不会被使用(若强行使用则将报错`NotImplementedError`)
                - `_search_url`, 私有字段，查询接口URL, 由`_api + _query_api`生成

            - `_stat_api`, 私有字段，统计聚合接口, 默认值为`/api/v1/search/stats`, 如果`_api`不为官方API则该字段不会被使用
                - `_stat_url`, 私有字段，统计聚合接口URL, 由`_api + _stat_api`生成

            - `_host_api`, 私有字段，Host聚合接口, 默认值为`/api/v1/host/{host}`, 如果`_api`不为官方API则该字段不会被使用
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
            - `results`, 查询结果, 类型为`pydict`, 包含查询结果的所有字段(FOFA查询返回的原始dict)
            - `assets`, 格式化为`tablib.Dataset`的资产对象, 包含查询结果的列名和数据(即`_format_result_dict()`的返回值)


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
[MIT License](LICENSE)