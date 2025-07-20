--- 
## 项目结构
- main.py 主程序入口
- src
- locales, 国际化文件
    - en_US, 英文
    - zh_CN, 中文


## fofaAPI规划
- Fofa, 主类
    - *API字段* (以单下划线开头的约定为私有字段; 无特殊注明的均为成员字段而非函数内定义的字段)
        - *API配置字段* :
            - `_api`, 私有字段，API接口地址, 默认值为`https://fofa.info/api/v1`, 可接受外部初始化
            - `_apikey`, 私有字段，API密钥, 必须接受外部初始化
            - `_query_api`, 私有字段，查询接口, 默认值为`/search/all`, 如果`_api`不为官方API则该字段不会被使用(若强行使用则将报错`NotImplementedError`)
            - `_stat_api`, 私有字段，统计聚合接口, 默认值为`/search/stats`, 如果`_api`不为官方API则该字段不会被使用
            - `_host_api`, 私有字段，Host聚合接口, 默认值为`/host/{host}`, 如果`_api`不为官方API则该字段不会被使用
        - *API查询字段* :
            - *函数作用域字段* :
                - `_query_dict`, 私有字段，查询字典, 可选接受外部初始化
                - `_query_string`, 私有字段，查询字符串, 可选接受外部传参(默认值为空字符串，若为空，则由`_query_dict`生成)(若两个参数都为空，则抛出报错)
                - `_size`, 私有字段，查询结果数量, 可选接受外部传参(默认值为10000)
                - `_page`, 私有字段，查询结果页码, 可选接受外部传参(默认值为1)
                - `_fields : list[str]`, 私有字段，查询结果字段, 可选接受外部传参(默认值为`['ip', 'server', 'os', 'link']`)
                - `_full : bool`, 私有字段，是否查询全部的数据, 可选接受外部传参(默认值为`False`，即默认查询一年内的数据)
        - *模块配置字段* :
            - `_enable_log`, 私有字段，是否启用日志, 可选接受外部初始化(默认值为`False`)
                - `enable_colorful_log`, 私有字段，是否启用彩色日志, 可选接受外部初始化(默认值为`False`)(使用colorama实现)
            - `_enable_cache`, 私有字段，是否启用缓存, 可选接受外部初始化(默认值为`False`)(使用cachetools实现)
    - *API公共方法*
    - *API私有方法*
        - *查询数据格式化* :
            - `_format_query_dict()`, 私有方法, 从`_query_dict`中取出查询字典并格式化, 返回值为base64编码接UTF8解码的字符串
        - *返回数据自动格式化* :
            - `_format_result_dict()`, 私有方法, 从返回的JSON数据中取出查询结果并格式化, 返回值为字典