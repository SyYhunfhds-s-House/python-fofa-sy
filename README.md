***
# Python-Fofa-SY

受Shodan官方API启发, 个人编写的一个第三方FOFA Python API

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
## 项目依赖
- loguru, 日志库(可选)
- cachetools, 缓存库(可选)
- typing-extensions, 类型注解库(向后兼容), 这样在Python 3.8及以下版本也可以使用`typing`模块中的类型注解
- tablib, 表格数据处理库
- tablib[all], tablib的拓展版, 支持导入导出多种格式 (可选)
- requests, HTTP客户端

## 项目API介绍
TODO: 完善API文档, 包括参数说明和返回值示例等

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

***
## 项目开源证书
[MIT License](LICENSE)