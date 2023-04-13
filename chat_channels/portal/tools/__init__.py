import re

def convertBB(var):
    search = [
        r'\[b\](.+)\[/b\]',
        r'\[br\]',
        r'\[i\](.+)\[/i\]',
        r'\[u\](.+)\[/u\]',
        r'\[img\](.+)\[/img\]',
        r'\[url\](.+)\[/url\]',
        r'\[url\=(.+)\](.+)\[/url\]',
    ]

    replace = [
        r'<strong>\1</strong>',
        '<br>',
        r'<em>\1</em>',
        r'<u>\1</u>',
        r'<img src="\1" />',
        r'<a href="\1">\1</a>',
        r'<a href="\1">\2</a>',
    ]

    for i in range(len(search)):
        var = re.sub(search[i], replace[i], var)

    return var