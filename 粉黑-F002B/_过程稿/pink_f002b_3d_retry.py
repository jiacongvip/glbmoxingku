# -*- coding: utf-8 -*-
import hashlib, json, os, shutil, ssl, subprocess, sys, time, urllib.error, urllib.request
from datetime import date

ROOT = "/Users/jiacong/Desktop/球衣套装拆图"
KIT = ROOT + "/粉黑-F002B"
BACK = KIT + "/_过程稿"
COLLAR_LOCAL = KIT + "/领口再小-正面预览.png"
FRONT = KIT + "/01-上衣正面-2D.png"
BACKJ = KIT + "/02-上衣背面-2D.png"
SHORTS_F = KIT + "/03-短裤正面-2D.png"
SHORTS_B = KIT + "/04-短裤背面-2D.png"
POSE_F = "https://qiniuoss.changzhouyunshan.com/upload/202610/01_1842423141.png"
POSE_B = "https://qiniuoss.changzhouyunshan.com/upload/202610/01_1842432537.png"
LOG = BACK + "/regen-3d-log.txt"
RESULT = BACK + "/regen-3d-result.json"
WANT = sys.argv[1:] or ["05", "06"]

def sha16(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()[:16]

def png_size(path):
    with open(path, "rb") as f:
        if f.read(8) != b"\x89PNG\r\n\x1a\n":
            return 0, 0
        f.read(4)
        if f.read(4) != b"IHDR":
            return 0, 0
        return int.from_bytes(f.read(4), "big"), int.from_bytes(f.read(4), "big")

def mysql(q):
    return subprocess.check_output(
        ["docker", "exec", "tpdaxiangshop_mysql", "mysql", "-uroot", "-proot123456", "tpdaxiangshop", "-N", "-e", q],
        stderr=subprocess.DEVNULL,
    ).decode().strip()

key = mysql("SELECT api_key FROM ddwx_digitalavatar_provider_config WHERE aid=62 AND provider_key='duomiapi' LIMIT 1")
base = mysql("SELECT base_url FROM ddwx_digitalavatar_provider_config WHERE aid=62 AND provider_key='duomiapi' LIMIT 1").rstrip("/")
if not key or not base.startswith("http"):
    print("config missing", flush=True)
    raise SystemExit(1)
CTX = ssl.create_default_context()

class BalanceError(Exception):
    pass

def req(method, url, payload=None, timeout=90):
    data = None if payload is None else json.dumps(payload).encode()
    headers = {"Authorization": "Bearer " + key, "Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout, context=CTX) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"raw": body[:240]}
    except Exception as e:
        return 0, {"raw": type(e).__name__}

def extract_state(o):
    if not isinstance(o, dict):
        return ""
    d = o.get("data") if isinstance(o.get("data"), dict) else {}
    return str(o.get("state") or o.get("status") or d.get("state") or d.get("status") or "")

def extract_url(o, img=""):
    if img:
        return img
    if isinstance(o, dict):
        for kk, v in o.items():
            if kk in ("url", "image_url") and isinstance(v, str) and v.startswith("http"):
                return v
            img = extract_url(v, img)
            if img:
                return img
    elif isinstance(o, list):
        for x in o:
            img = extract_url(x, img)
            if img:
                return img
    return img

def busy_text(blob):
    return ("请稍后重试" in blob) or ("系统繁忙" in blob) or ("繁忙" in blob)

def upload(local, name):
    DATE = date.today().strftime("%Y%m%d")
    subprocess.check_call(["docker", "exec", "tpdaxiangshop_php", "mkdir", "-p", "/app/public/upload/62/%s" % DATE])
    subprocess.check_call(["docker", "cp", local, "tpdaxiangshop_php:/app/public/upload/62/%s/%s" % (DATE, name)])
    php = """<?php
if (!defined("ROOT_PATH")) define("ROOT_PATH", "/app/");
if (!defined("PRE_URL")) define("PRE_URL", "/");
require "/app/vendor/autoload.php";
$app = new think\\App();
$app->initialize();
$date=%s; $name=%s;
$actual="/app/public/upload/62/".$date."/".$name;
$picurl="http://127.0.0.1/upload/62/".$date."/".$name;
echo \\app\\admin\\common\\Pic::uploadoss($picurl, false, $actual, 62);
""" % (json.dumps(DATE), json.dumps(name))
    r = subprocess.run(["docker", "exec", "-i", "tpdaxiangshop_php", "php"], input=php.encode(), capture_output=True)
    url = (r.stdout.decode().strip().splitlines() or [""])[-1].strip()
    if not url.startswith("https://"):
        print("upload fail", name, flush=True)
        return ""
    print("up", name, flush=True)
    return url

COLLAR = (
    "COLLAR LOCK from IMAGE 2, the approved flat jersey. Copy that collar, do not restyle it. "
    "Small shallow white V. The collar band is white with ONE THICK solid black stripe across the band. "
    "The black stripe is a wide bar, about as tall as the white rib above it. It is NOT a hairline, NOT thin piping, NOT a 1-pixel outline. "
    "White edge above the black bar. Faint center seam. Neck opening stays SMALL, the same size as IMAGE 2. "
    "No crew neck, no polo, no buttons, no placket."
)
BODY = (
    "Solid pink jersey. Chest is the same solid pink. NO white chest bar, NO white rectangle. "
    "Three separate black stripes on each sleeve. Pink cuff with a thin black edge. "
    "NO text, NO numbers, NO logos, NO crests, NO stars, NO Nike, NO UNICHANT."
)
SHORTS = (
    "Black shorts copied from the shorts reference. Each side has exactly three stripes, outer to inner: white, pink, white. "
    "Do not add extra black or white stripes. No numbers, no logos."
)

def color_type(path):
    with open(path, "rb") as f:
        f.read(8)
        ln = int.from_bytes(f.read(4), "big")
        f.read(4)
        data = f.read(ln)
    return data[9]

def save_png(final, img):
    tmp = final + ".part"
    urllib.request.urlretrieve(img, tmp)
    if os.path.getsize(tmp) < 10000:
        os.remove(tmp)
        return False
    if color_type(tmp) != 6:
        print("opaque reject", os.path.basename(final), flush=True)
        os.remove(tmp)
        return False
    os.replace(tmp, final)
    w, h = png_size(final)
    print("saved", os.path.basename(final), os.path.getsize(final), "%dx%d" % (w, h), flush=True)
    return True

results = []

def record(tag, status, tid, path):
    row = {"tag": tag, "status": status, "task_id": tid or "", "path": path}
    results.append(row)
    print("RESULT", tag, status, tid or "-", flush=True)

def run(tag, final, prompt, images):
    images = [u for u in images if u][:4]
    if len(images) < 2:
        record(tag, "fail", "", final)
        return ""
    payload = {
        "model": "gpt-image-2",
        "prompt": prompt,
        "size": "1024x1024",
        "quality": "high",
        "background": "transparent",
        "image": images,
    }
    last = ""
    for attempt in range(3):
        code, body = req("POST", base + "/v1/images/generations?async=true", payload)
        blob = json.dumps(body, ensure_ascii=False)
        if "余额" in blob:
            print("BALANCE", tag, flush=True)
            raise BalanceError(tag)
        tid = str((body or {}).get("id") or "")
        busy = busy_text(blob)
        print("submit", tag, code, tid or "-", "attempt", attempt, "busy" if busy else "ok", flush=True)
        with open(LOG, "a") as f:
            f.write("submit %s %s %s %s\n" % (tag, attempt, code, tid))
        if (not tid) or busy:
            time.sleep(8)
            continue
        last = tid
        for i in range(100):
            time.sleep(5)
            code, body = req("GET", base + "/v1/tasks/" + tid)
            st = extract_state(body).lower()
            blob = json.dumps(body, ensure_ascii=False)
            if i % 6 == 0:
                print("poll", tag, i, st or "-", tid, flush=True)
            if "余额" in blob:
                print("BALANCE", tag, flush=True)
                raise BalanceError(tag)
            if busy_text(blob) or st in ("failed", "error", "failure"):
                print("fail", tag, tid, st or "busy", flush=True)
                time.sleep(8)
                break
            img = extract_url(body)
            if img and st in ("succeeded", "success", "completed", "done", "succeed"):
                if save_png(final, img):
                    record(tag, "saved", tid, final)
                    return tid
                break
        else:
            print("timeout", tag, tid, flush=True)
    record(tag, "fail", last, final)
    return ""

def main():
    os.makedirs(BACK, exist_ok=True)
    locks = {p: sha16(p) for p in (SHORTS_F, SHORTS_B, FRONT, BACKJ, COLLAR_LOCAL)}
    stamp = time.strftime("%Y%m%d-%H%M%S")
    paths = {
        "05": KIT + "/05-整套正面-3D.png",
        "06": KIT + "/06-整套背面-3D.png",
    }
    for tag in WANT:
        p = paths[tag]
        if os.path.exists(p):
            dest = os.path.join(BACK, stamp + "-" + os.path.basename(p))
            shutil.copy2(p, dest)
            print("backup", tag, dest, flush=True)
    collar = upload(COLLAR_LOCAL, "pink-collar-lock2.png")
    if not collar:
        raise SystemExit(1)
    u01 = upload(FRONT, "pink-01-lock.png")
    u02 = upload(BACKJ, "pink-02-lock.png")
    sfront = upload(SHORTS_F, "pink-03-ref2.png")
    sback = upload(SHORTS_B, "pink-04-ref2.png")
    p05 = (
        "3D ghost-mannequin soccer kit FRONT. Square canvas, transparent background, binary alpha.\n"
        "IMAGE 1 is POSE LOCK only. Keep the standing front pose, camera, framing, socks pulled up, black unbranded boots. NO Nike. "
        "Do NOT copy IMAGE 1 colors.\n"
        "IMAGE 2 is the approved pink jersey and the only collar design. " + COLLAR + " " + BODY + "\n"
        "IMAGE 3 is the flat front drawing of the same jersey. Match its collar bar thickness.\n"
        "IMAGE 4 is the shorts. " + SHORTS + "\n"
        "Socks white with a thin pink cuff. Plain black boots with NO swoosh and NO logo. Real transparent background only. Do NOT draw a checkerboard, do NOT paint a gray or white backdrop. The thick black collar bar must be obvious at a glance."
    )
    p06 = (
        "3D ghost-mannequin soccer kit BACK. Square canvas, transparent background, binary alpha.\n"
        "IMAGE 1 is POSE LOCK only. Keep the standing back pose, camera, framing, socks pulled up, black unbranded boots. NO Nike. "
        "Do NOT copy IMAGE 1 colors.\n"
        "IMAGE 2 is the approved FRONT jersey, collar lock. From behind the collar is the reverse of that small neck: white band with ONE THICK black stripe, about as tall as the white rib, not a hairline. Small neck, faint center seam. "
        + COLLAR + " " + BODY + "\n"
        "IMAGE 3 is the flat BACK drawing. Match that back, including the thick black collar stripe.\n"
        "IMAGE 4 is the shorts back. " + SHORTS + "\n"
        "Solid pink back, no name, no number, no white bar. Socks white with a thin pink cuff. Plain black boots with NO swoosh and NO logo. Real transparent background only. Do NOT draw a checkerboard, do NOT paint a gray or white backdrop."
    )
    if "05" in WANT:
        run("05", paths["05"], p05, [POSE_F, collar, u01, sfront])
    if "06" in WANT:
        run("06", paths["06"], p06, [POSE_B, collar, u02, sback])
    after = {p: sha16(p) for p in locks}
    same = after == locks
    print("locked-files", "unchanged" if same else "CHANGED", flush=True)
    with open(RESULT, "w") as f:
        json.dump({"stamp": stamp, "results": results, "locked_unchanged": same}, f, ensure_ascii=False, indent=2)
    print("ALLDONE", flush=True)

if __name__ == "__main__":
    try:
        main()
    except BalanceError as e:
        print("STOPPED balance", str(e), flush=True)
        raise SystemExit(2)
