import base64, io, json, pathlib, subprocess, time, requests
from PIL import Image

HEJU = "https://www.hejuapi.com/v1/images/generations"
KEY = pathlib.Path("/tmp/kit64b/heju.key").read_text().strip()

def upload(path, suffix="_src"):
    subprocess.run(["docker","cp",str(path),"tpdaxiangshop_php:/tmp/_up.png"],check=True)
    out=subprocess.run(["docker","exec","tpdaxiangshop_php","php","/app/runtime/k85_oss_upload.php","/tmp/_up.png",suffix],
                       capture_output=True,text=True,check=True)
    return out.stdout.strip()

def gen(prompt, image_paths=(), size="1024x1024", model="gpt-image-2.5-flare", timeout=300):
    urls=[upload(p, f"_in{int(time.time()*1000)%100000}") for p in image_paths]
    body={"model":model,"size":size,"quality":"high","prompt":prompt}
    if urls: body["image"]=urls
    r=requests.post(HEJU, headers={"Authorization":f"Bearer {KEY}"}, json=body, timeout=timeout)
    j=r.json()
    if "data" in j and j["data"]:
        d=j["data"][0]
        if "b64_json" in d:
            return Image.open(io.BytesIO(base64.b64decode(d["b64_json"]))).convert("RGBA")
        if "url" in d:
            return Image.open(io.BytesIO(requests.get(d["url"],timeout=120).content)).convert("RGBA")
    raise RuntimeError(f"gen failed: {r.status_code} {str(j)[:300]}")
