# -*- coding: utf-8 -*-
"""批量上传57~69套球衣2D四件套到后台素材库（第三批）"""
import base64, json, os, time, urllib.request

BASE = "/Users/jiacong/Desktop/球衣套装拆图"
API = "https://qixian.zhonghengyikang.com.cn/?s=/ApiAiApi/call"
TOKEN = "ai_afb1cc255f7d4c89bcd8905df4bb77f2031be14d"

DIRS = sorted([d for d in os.listdir(BASE) if os.path.isdir(os.path.join(BASE, d)) and d[:2].isdigit() and 57 <= int(d[:2]) <= 69],
              key=lambda x: int(x[:2]))
FILES = ["01-上衣正面-2D.png", "02-上衣背面-2D.png", "03-短裤正面-2D.png", "04-短裤背面-2D.png"]

def upload(path, name):
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    body = json.dumps({
        "action": "upload.image",
        "params": {"image_base64": b64, "name": name},
        "dry_run": False,
    }).encode()
    req = urllib.request.Request(API, data=body, headers={
        "Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode())

results = []
failed = []
print("待上传目录数:", len(DIRS))
for d in DIRS:
    for f in FILES:
        path = os.path.join(BASE, d, f)
        name = d + "-" + f.replace(".png", "")
        if not os.path.isfile(path):
            failed.append({"dir": d, "file": f, "msg": "file not found"})
            continue
        for attempt in range(3):
            try:
                r = upload(path, name)
                if r.get("code") == 0:
                    results.append({"dir": d, "file": f, "url": r["data"]["url"], "upload_id": r["data"].get("upload_id")})
                    print("OK  %s / %s" % (d, f))
                    break
                else:
                    if r.get("code") == 429:
                        print("rate-limit %s, retry %d" % (path, attempt + 1))
                        time.sleep(5)
                        continue
                    failed.append({"dir": d, "file": f, "msg": "code=%s msg=%s" % (r.get("code"), r.get("msg"))})
                    print("FAIL %s / %s -> %s %s" % (d, f, r.get("code"), r.get("msg")))
                    break
            except Exception as e:
                print("ERR  %s / %s -> %s" % (d, f, e))
                time.sleep(3)
        time.sleep(0.5)

out = os.path.join(BASE, "上传素材库结果_第三批.json")
with open(out, "w", encoding="utf-8") as fp:
    json.dump({"total": len(results), "failed": failed, "results": results}, fp, ensure_ascii=False, indent=2)
print("=== 完成: 成功 %d, 失败 %d, 结果已写入 %s ===" % (len(results), len(failed), out))
