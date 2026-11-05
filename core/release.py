import json
import urllib.error
import urllib.request

RELEASE_URL = 'https://api.github.com/repos/skytr1x/APS-SDK/releases/latest'
DEV = 'dev-сборка'


def release_version(fetch=None):
    try:
        if fetch is None:
            req = urllib.request.Request(RELEASE_URL, headers={'Accept': 'application/vnd.github+json', 'User-Agent': 'AnotherPluginSystem/0.9'})
            with urllib.request.urlopen(req, timeout=8) as response:
                data = response.read(65537)
        else:
            data = fetch()
        if len(data) > 65536:
            return DEV
        obj = json.loads(data.decode('utf-8'))
        tag = obj.get('tag_name') if isinstance(obj, dict) else None
        if not isinstance(tag, str):
            return DEV
        tag = tag.strip()
        if not tag or len(tag) > 128 or any(ord(c) < 32 for c in tag):
            return DEV
        return tag
    except (OSError, ValueError, UnicodeError, TypeError):
        return DEV
