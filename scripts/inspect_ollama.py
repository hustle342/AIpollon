import os, json, urllib.request
host=os.environ.get('OLLAMA_HOST','http://localhost:11434')
url=f"{host}/api/generate"
payload=json.dumps({"model": os.environ.get('OLLAMA_MODEL','qwen2.5-coder:7b'), "prompt": "masaüstüne serdar.txt oluştur"}).encode('utf-8')
req=urllib.request.Request(url, data=payload, headers={'Content-Type':'application/json'}, method='POST')
with urllib.request.urlopen(req, timeout=15) as resp:
    raw=resp.read()
    try:
        s=raw.decode('utf-8')
    except Exception:
        s=raw.decode('utf-8','backslashreplace')
    print('---RAW START---')
    print(repr(s)[:2000])
    print('---RAW END---')
