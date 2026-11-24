# -*- coding: utf-8 -*-
"""正式创建前10套球衣白胚（每套1个，参考球服参数）"""
import json, os, time, urllib.request

BASE = "/Users/jiacong/Desktop/球衣套装拆图"
API = "https://qixian.zhonghengyikang.com.cn/?s=/ApiAiApi/call"
TOKEN = "ai_286454c1345a6d9708e5aa85ae3615e5c15e77e0"

with open(os.path.join(BASE, "上传素材库结果.json"), encoding="utf-8") as f:
    data = json.load(f)
urls = {}
for r in data["results"]:
    urls[(r["dir"], r["file"].replace(".png", ""))] = r["url"]

DIRS = [
    "01-Unichant", "02-Unichant-Wolves", "03-Unichant-Sky", "04-Unichant-Dark",
    "05-Unichant-Gradient", "06-Unichant-GrayRed", "07-Unichant-Pinstripe",
    "08-Unichant-Camo", "09-Unichant-Purple", "10-Unichant-GeoOrange",
]

def build_payload(d, idx):
    u_front = urls[(d, "01-上衣正面-2D")]
    u_back = urls[(d, "02-上衣背面-2D")]
    u_pf = urls[(d, "03-短裤正面-2D")]
    u_pb = urls[(d, "04-短裤背面-2D")]
    return {
        "category_id": 1362,
        "name": d,
        "cover_pic": u_front,
        "description": "Unichant 系列球衣套装",
        "price": 9.9,
        "market_price": 99,
        "freight_price": 0,
        "stock": 0,
        "status": 0,
        "sort": idx,
        "surfaces": [
            {"key": "front", "name": "上衣正面", "base_image": u_front, "overlay_image": "", "mask_image": "",
             "canvas_width": 1000, "canvas_height": 1000, "physical_width_mm": 0, "physical_height_mm": 0,
             "print_area": {"x": 0.2, "y": 0.2, "width": 0.6, "height": 0.6}},
            {"key": "back", "name": "上衣背面", "base_image": u_back, "overlay_image": "", "mask_image": "",
             "canvas_width": 1000, "canvas_height": 1000, "physical_width_mm": 0, "physical_height_mm": 0,
             "print_area": {"x": 0.2, "y": 0.2, "width": 0.6, "height": 0.6}},
            {"key": "pants_front", "name": "短裤正面", "base_image": u_pf, "overlay_image": "", "mask_image": "",
             "canvas_width": 1000, "canvas_height": 1000, "physical_width_mm": 0, "physical_height_mm": 0,
             "print_area": {"x": 0.2, "y": 0.2, "width": 0.6, "height": 0.6}},
            {"key": "pants_back", "name": "短裤背面", "base_image": u_pb, "overlay_image": "", "mask_image": "",
             "canvas_width": 1000, "canvas_height": 1000, "physical_width_mm": 0, "physical_height_mm": 0,
             "print_area": {"x": 0.2, "y": 0.2, "width": 0.6, "height": 0.6}},
        ],
        "variants": [
            {"key": "default", "name": "默认款", "color_name": "默认", "color_value": "#ffffff", "cover_pic": u_front,
             "surface_images": {"front": u_front, "back": u_back, "pants_front": u_pf, "pants_back": u_pb},
             "style_key": "style_1", "color_key": "default"}
        ],
        "sizes": [
            {"key": "S", "name": "S", "extra_price": 9.9, "stock": 0},
            {"key": "M", "name": "M", "extra_price": 0, "stock": 0},
            {"key": "L", "name": "L", "extra_price": 0, "stock": 0},
        ],
    }

def call(action, params):
    body = json.dumps({"action": action, "params": params, "dry_run": False}).encode()
    req = urllib.request.Request(API, data=body, headers={
        "Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read().decode())

results = []
failed = []
for idx, d in enumerate(DIRS, start=1):
    params = build_payload(d, idx)
    for attempt in range(3):
        try:
            r = call("customdiy.product.save", params)
            if r.get("code") == 0:
                pid = r["data"].get("id")
                results.append({"dir": d, "product_id": pid, "name": r["data"].get("name", d)})
                print("OK  %s -> 白胚ID=%s" % (d, pid))
                break
            elif r.get("code") == 429:
                print("rate-limit %s, retry %d" % (d, attempt + 1))
                time.sleep(5)
            else:
                failed.append({"dir": d, "code": r.get("code"), "msg": r.get("msg")})
                print("FAIL %s -> %s %s" % (d, r.get("code"), r.get("msg")))
                break
        except Exception as e:
            print("ERR  %s -> %s" % (d, e))
            time.sleep(3)
    time.sleep(0.5)

out = os.path.join(BASE, "白胚创建结果.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump({"total": len(results), "failed": failed, "results": results}, f, ensure_ascii=False, indent=2)
print("=== 完成: 成功 %d, 失败 %d, 结果写入 %s ===" % (len(results), len(failed), out))
