# 导入标准库
# import gettext
import json

# 导入第三方依赖
import tablib # 这里会蜜汁报错导入不了包(VSC经典静态检查老毛病)

_ = lambda s: s # 接收参数但什么也不干


def _format_query_fields_dict(
    query_dict: dict, # e.g., {'title': "百度", 'domain': 'example.com', 'port': ['80', 443]}
) -> str:
    """Formats a dictionary of search terms into a FOFA query string.

    This function converts a dictionary of search criteria into a query string
    compatible with the FOFA asset search engine. The resulting query string
    is not Base64 encoded.

    - Top-level key-value pairs are treated as AND conditions, joined by '&&'.
    - If a value is a list, its elements are treated as OR conditions for
      that key, joined by '||'.
    - String values are enclosed in double quotes.
    - Boolean values are included directly without quotes.

    Args:
        query_dict: A dictionary where keys represent FOFA search fields (e.g.,
            'title', 'domain', 'port') and values are the search criteria.
            Values can be a string, integer, boolean, or a list of strings/integers.

    Returns:
        The formatted query string ready for use in a FOFA search.

    Example:
        >>> query = {
        ...     'title': "Example Site",
        ...     'domain': 'example.com',
        ...     'port': ['80', 443]
        ... }
        >>> _format_query_dict(query)
        '(title="Example Site")&&(domain="example.com")&&(port="80"||port="443")&&(is_honeypot=False)'
    Note: 
        This function is not flexible. If you have more specific requirements, please write your own query string
    """
    # Outer conditions are joined by &&
    # List items are joined by ||
    query_string_parts = []
    for field, value in query_dict.items():
        if isinstance(value, bool):
            # Format booleans directly, e.g., (is_honeypot=false)
            query_string_parts.append(f'({field}={str(value).lower()})')
        elif isinstance(value, list):
            # Format list items as OR conditions, e.g., (port="80"||port="443")
            temp = '||'.join([f'{field}="{item}"' for item in value])
            query_string_parts.append(f'({temp})')
        else:
            # Format other values as exact matches, e.g., (domain="example.com")
            query_string_parts.append(f'({field}="{value}")')

    query_string = '&&'.join(query_string_parts)
    # Example output: (title="百度")&&(domain="example.com")&&(port="80"||port="443")
    return query_string

def _format_result_dict_alpha(
    query_results: dict,
    data_headers: dict = {
        'search': {
            'fofa': [
                    'title', 'domain', 'link', 'unk1', 
                    'cert.subject.org', 'unk2', 'unk3'
                 ], # FOFA官方API默认字段列表
            # TODO 根据更多响应数据确认第三方API的真实返回字段
            'fofoapi': 
                [
                    'title', 'domain', 'link', 'unk1', 
                    'cert.subject.org', 'unk2', 'unk3'
                 ] # fofoapi第三方API默认字段列表
        },
        'stats': ['title'],
        'host': ['port', 'protocol', 'domain', 'category', 'product'],
    },
    mode: str = 'search',
    api_source: str = 'fofa', # API来源, 用于区分是不是官方API
    detail: bool = False,
) -> tablib.Dataset:
    """Formats a raw FOFA API response dictionary into a tablib.Dataset.

    This function processes the dictionary returned from a FOFA API query and
    converts it into a structured `tablib.Dataset` object for easier handling
    and potential export. The processing logic is dispatched based on the `mode`
    parameter, which corresponds to the type of FOFA API endpoint queried.

    Note:
        Currently, only the 'search' mode is fully implemented and functional.
        The 'stats' and 'host' modes are not supported due to the complex,
        nested structure of their respective API responses, and they will
        raise an error , that is `NotImplementedError`.

    Args:
        query_results: The raw dictionary object parsed from the FOFA API's
            JSON response.
        data_headers (dict, optional): A dictionary mapping a mode to a list
            of strings that will be used as the headers for the output Dataset.
            Defaults are provided for all modes.
        mode (str, optional): The type of API response to format. Determines
            which internal formatting logic to use. Defaults to 'search'.
            Must be one of 'search', 'stats', or 'host'.
        detail (bool, optional): A special flag for the 'host' mode to handle
            detailed responses. This is currently not used as the 'host'
            formatter is not implemented. Defaults to False.
        api_source (str, optional): The source of the API.
            Defaults to 'fofa'. Could be one of 'fofa', 'fofoapi' or etc.


    Returns:
        A `tablib.Dataset` instance containing the formatted data if the mode
        is 'search' and results are present.
        Returns `None` if the specified `mode` is 'stats' or 'host', as these
        are not currently implemented.
    """

    def _format_search_result_dict() -> tablib.Dataset:
        """Formats the 'results' list from a search query."""
        data = tablib.Dataset()
        # Set the headers for the dataset using the provided mapping
        data.headers = data_headers['search'][api_source]
        # Append each row from the results list to the dataset
        for row in query_results.get('results', []):
            # print(row)
            data.append(row)
        return data

    def _format_stats_result_dict() -> None:
        """
        Placeholder for formatting statistical aggregation results.
        Currently unimplemented due to complex, nested data structures.
        """
        raise NotImplementedError

    def _format_host_result_dict() -> None:
        """
        Placeholder for formatting host aggregation results.
        Currently unimplemented due to complex, nested data structures.
        """
        raise NotImplementedError

    # A dispatch table to call the correct formatting function based on mode.
    methods = {
        'search': _format_search_result_dict,
        'stats': _format_stats_result_dict,
        'host': _format_host_result_dict
    }

    # Execute the appropriate function for the given mode.
    # A KeyError will be raised by .get() if an invalid mode is provided.
    formatter = methods.get(mode)
    if formatter:
        return formatter()
    return None

# This is a placeholder for the actual function for context.
# The docstring is the key part of this response.
def _format_result_dict(
    query_results: dict,
    data_headers: dict = {
        'search': {
            'fofa': [
                    'title', 'domain', 'link', 'unk1', 
                    'cert.subject.org', 'unk2', 'unk3'
                 ], # FOFA官方API默认字段列表
            # TODO 根据更多响应数据确认第三方API的真实返回字段
            'fofoapi': 
                [
                    'title', 'domain', 'link', 'unk1', 
                    'cert.subject.org', 'unk2', 'unk3'
                 ] # fofoapi第三方API默认字段列表
        },
        'stats': ['title'],
        'host': ['port', 'protocol', 'domain', 'category', 'product'],
    },
    mode: str = 'search',
    api_source: str = 'fofa', # API来源, 用于区分是不是官方API
    detail: bool = False,
) -> tablib.Dataset:
    """Formats a raw FOFA API response dictionary into a tablib.Dataset.

    This function processes the dictionary returned from a FOFA API query and
    converts it into a structured `tablib.Dataset` object for easier handling
    and potential export. The processing logic is dispatched based on the `mode`
    parameter, which corresponds to the type of FOFA API endpoint queried.

    Note:
        Currently, only the 'search' mode is fully implemented and functional.
        The 'stats' and 'host' modes are not supported due to the complex,
        nested structure of their respective API responses, and they will
        raise an error , that is `NotImplementedError`.

    Args:
        query_results: The raw dictionary object parsed from the FOFA API's
            JSON response.
        data_headers (dict, optional): A dictionary mapping a mode to a list
            of strings that will be used as the headers for the output Dataset.
            Defaults are provided for all modes.
        mode (str, optional): The type of API response to format. Determines
            which internal formatting logic to use. Defaults to 'search'.
            Must be one of 'search', 'stats', or 'host'.
        detail (bool, optional): A special flag for the 'host' mode to handle
            detailed responses. This is currently not used as the 'host'
            formatter is not implemented. Defaults to False.
        api_source (str, optional): The source of the API.
            Defaults to 'fofa'. Could be one of 'fofa', 'fofoapi' or etc.


    Returns:
        A `tablib.Dataset` instance containing the formatted data if the mode
        is 'search' and results are present.
        Returns `None` if the specified `mode` is 'stats' or 'host', as these
        are not currently implemented.
    """

    def _format_search_result_dict() -> tablib.Dataset:
        """Formats the 'results' list from a search query."""
        data = tablib.Dataset()
        # Set the headers for the dataset using the provided mapping
        data.headers = data_headers['search'][api_source]
        # Append each row from the results list to the dataset
        for row in query_results.get('results', []):
            # print(row)
            data.append(row)
        return data

    def _format_stats_result_dict() -> None:
        """
        Placeholder for formatting statistical aggregation results.
        Currently unimplemented due to complex, nested data structures.
        """
        raise NotImplementedError

    def _format_host_result_dict() -> None:
        """
        Placeholder for formatting host aggregation results.
        Currently unimplemented due to complex, nested data structures.
        """
        raise NotImplementedError

    # A dispatch table to call the correct formatting function based on mode.
    methods = {
        'search': _format_search_result_dict,
        'stats': _format_stats_result_dict,
        'host': _format_host_result_dict
    }

    # Execute the appropriate function for the given mode.
    # A KeyError will be raised by .get() if an invalid mode is provided.
    formatter = methods.get(mode)
    if formatter:
        return formatter()
    return None

# A set of all fields allowed in a standard FOFA asset search.
_search_allowed_fields = set(
    ['ip', 'port', 'protocol', 'country', 'country_name', 'region', 'city', 'longitude',
    'latitude', 'asn', 'org', 'host', 'domain', 'os', 'server', 'icp', 'title', 'jarm',
    'header', 'banner', 'cert', 'base_protocol', 'link', 'cert.issuer.org', 'cert.issuer.cn',
    'cert.subject.org', 'cert.subject.cn', 'tls.ja3s', 'tls.version', 'cert.sn',
    'cert.not_before', 'cert.not_after', 'cert.domain', 'header_hash', 'banner_hash',
    'banner_fid', 'cname', 'lastupdatetime', 'product', 'product_category', 'product.version', 
    'icon_hash', 'cert.is_valid', 'cname_domain', 'body', 'cert.is_match', 'cert.is_qeual',
    'icon', 'fid', 'structinfo'])
# A set of all fields allowed in a FOFA statistical aggregation query.
_stats_allowed_fields = set(
    ['protocol', 'domain', 'port', 'title', 'os', 'server', 'country', 'asn', 
    'org', 'asset_type', 'fid', 'icp']
)
class ParamsMisconfiguredError(SyntaxError):
    def __init__(self, message=None, errors=None):
        super().__init__(message)
        self.errors = errors

def _check_query_fields_dict(mode: str, query_dict, translator = _):
    """Validates a query dictionary against allowed FOFA API fields for a given mode.

    This internal helper function checks if the fields provided in a query
    dictionary are valid for the specified FOFA API operation mode ('search' or
    'stats'). Its primary purpose is to catch misconfigured parameters before
    sending a request to the API.

    For 'search' mode, it also determines if resource-intensive fields
    (like 'body' or 'cert') are present and returns a suggested maximum
    result size to prevent API errors.

    Args:
        mode: The operation mode, either 'search' or 'stats'. This
            determines which set of validation rules to apply.
        query_dict: The dictionary of query parameters to be validated, where
            keys are FOFA field names.
        translator: A translation function (aliased as `_`) for internationalizing
            error messages.

    Returns:
        An integer for 'search' mode, representing a suggested maximum
        number of results (`fixed_size`). This is -1 if no specific limit
        is needed, or a lower value (e.g., 500 or 2000) for
        resource-intensive fields.
        Returns `None` for 'stats' mode upon successful validation.

    Raises:
        TypeError: If `query_dict` is not a dictionary.
        ParamsMisconfiguredError: If `query_dict` contains keys that are not
            allowed for the specified `mode`. The exception message will
            include the redundant fields.
        KeyError: If an unsupported `mode` is provided.
    """
    def _check_search_fields():
        """Validates fields for 'search' mode and returns a suggested size limit."""
        if not dict_keys <= _search_allowed_fields:
            redudant_keys = dict_keys - _search_allowed_fields
            raise ParamsMisconfiguredError(
                _('Redundant fields found ') + ', '.join(list(redudant_keys)),
            )
            # The error message and the list of keys are separated to facilitate
            # internationalization (i18n), allowing the static string to be
            # translated without runtime string formatting issues.
            
        fixed_size = -1
        # Default value, indicating no special size limit.
        # Certain fields are resource-intensive and have smaller max result limits.
        # 计算是否存在交集, 只要交集不为空即可 # isdisjoint专门用来判断两个集合是否存在交集
        if set(['cert', 'banner']) <= dict_keys:
            fixed_size = 2000
        elif set(['body']) <= dict_keys:
            fixed_size = 500
        # 如果fixed_size仍为-1，则无需在意; 
        # 如果查询参数的字典的键包含额外的字段，则抛出ParamsMisconfiguredrror,
        # 此时函数调用方需要检查参数是否合法, 毕竟多一个参数确实会导致请求异常
        return fixed_size 
            
    def _check_stats_fields() -> None:
        """Validates fields for 'stats' mode."""
        if not dict_keys <= _stats_allowed_fields:
            redundant_keys = dict_keys - _stats_allowed_fields
            raise ParamsMisconfiguredError(
                _('Redundant fields found for stats query: ') + ', '.join(list(redundant_keys)),
            )
        return None   
    
    if not isinstance(query_dict, dict):
        raise TypeError(_('query_dict must be a dict'))
    
    dict_keys = query_dict.keys()
    check_method = {
        'search': _check_search_fields,
        'stats': _check_stats_fields
    }
    return check_method[mode]()

if __name__ == '__main__':
    stats_response = {
  "error": False, # 是否出现错误
  "consumed_fpoint": 0, # 实际F点
  "required_fpoints": 0, # 应付F点
  "size": 4277422, # 查询总数量
  "distinct": {
    "ip": 32933,
    "title": 82280
  },
  "aggs": {
    "title": [
        {
            "count": 76234,
            "name": "网站未备案或已被封禁——百度智能云云主机管家服务"
        },
        {
            "count": 50220,
            "name": "百度一下, 你就知道"
        },
        {
            "count": 39532,
            "name": "百度热榜"
        },
        {
            "count": 37177,
            "name": "百度 H5 - 真正免费的 H5 页面制作平台"
        },
        {
            "count": 33986,
            "name": "百度SEO"
        }
    ]
  },
  "lastupdatetime": "2022-05-23 15:00:00"
    }
    
    def format_stats_result_dict(stats_response):
        aggeration = stats_response['aggs']
        aggs_fields = list(aggeration.keys())
        print(aggeration)
        # print(aggs_fields)
        data = tablib.Dataset()
        for field, content in aggeration.items():
            data[field] = content
        print(data)
        
    format_stats_result_dict(stats_response)