from .src import Fofa

def main():
    query_string = "domain=\"example.com\""
    offical_api = "https://fofa.info"
    apikey = "xxxxxxxxxxxx"
    fofa = Fofa(api=offical_api, key=apikey)
    print(fofa._search_url)
    res = fofa.search(
        query_string=query_string,
        size=100
    )
    print(fofa.fields)
    fofa - 'unk1' # 删除一些列
    fofa - 'unk2'
    fofa - 'unk3' 
    print(fofa.assets)
    print(fofa.fields)
    print(fofa.domain) # 获取domain list
    print(type(fofa.domain))
    fofa - 'new_empty_col' # 可以增加一个空列
    print(len(fofa)) # 获取结果数量

if __name__ == "__main__":
    main()
