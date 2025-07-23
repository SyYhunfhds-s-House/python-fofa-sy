from .src import Fofa

def main():
    query_string = "domain=\"baidu.com\""
    offical_api = "https://fofa.info"
    apikey = "xxxxxxxxxxxxxxxxxxxxxxx"
    fofa = Fofa(api=offical_api, key=apikey)
    print(fofa._search_url)
    res = fofa.search(
        query_string=query_string,
        size=100
    )
    print(fofa._api_source)
    print(fofa.results)
    print(res)
    print(res.fields)
    res + 'unk1'
    print(res.assets)
    print(res.fields)
    print(res.link)
    print(type(res.link))

if __name__ == "__main__":
    main()
