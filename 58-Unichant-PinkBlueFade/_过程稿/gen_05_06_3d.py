# -*- coding: utf-8 -*-
import json, os, shutil, ssl, subprocess, sys, time, urllib.error, urllib.request
from datetime import date

ROOT = "/Users/jiacong/Desktop/球衣套装拆图"
KIT = ROOT + "/58-Unichant-PinkBlueFade"
BACK = KIT + "/_过程稿"
FRONT = KIT + "/01-上衣正面-2D.png"
BACKJ = KIT + "/02-上衣背面-2D.png"
SHORTS_F = KIT + "/03-短裤正面-2D.png"
SHORTS_B = KIT + "/04-短裤背面-2D.png"
POSE_F = "https://qiniuoss.changzhouyunshan.com/upload/202610/01_1842423141.png"
POSE_B = "https://qiniuoss.changzhouyunshan.com/upload/202610/01_1842432537.png"
LOG = BACK + "/gen-3d-log.txt"
RESULT = BACK + "/gen-3d-result.json"

PROMPT_05 = """3D ghost-mannequin soccer kit FRONT. 1024x1024 PNG. True transparent background.

KEEP IMAGE 1 presentation only: same pose, camera, lighting, slim athletic ghost mannequin, black unbranded soccer boots. NO Nike swoosh. Do NOT copy IMAGE 1 colors, polo collar, buttons, or stripes.

SOCKS MUST match IMAGE 1 height: white socks pulled UP inside the shorts, covering the knees. Sock tops disappear under the shorts hem. No bare thigh gap. Thin pink cuff. No gray smoke between the legs.

JERSEY from IMAGE 2 exactly, including its collar:
- pink-to-cyan vertical body gradient, white sleeves
- viewer-left cuff pink, viewer-right cuff cyan blue
- white F-013 collar fabric (top band, two pointed wings, lower V band solid white); single inner shield pink; crisp black outlines; one downward point; do not add a second inner white V; no buttons

SHORTS from IMAGE 3: solid white; viewer-left hem pink; viewer-right hem cyan blue. No number.
REMOVE all names, numbers, logos. No studio backdrop."""

PROMPT_06 = """3D ghost-mannequin soccer kit BACK. 1024x1024 PNG. True transparent background.

KEEP IMAGE 1 presentation only: same back pose, camera, lighting, slim athletic ghost mannequin, black unbranded soccer boots. NO Nike swoosh. Do NOT copy IMAGE 1 colors, polo collar, buttons, or stripes.

SOCKS MUST match IMAGE 1 height: white socks pulled UP inside the shorts, covering the knees. Sock tops disappear under the shorts hem. No bare thigh gap. Thin pink cuff. The space between the legs is empty transparent background. No gray cloud, no smoke, no white blob.

JERSEY BACK from IMAGE 2 exactly:
- pink-to-cyan vertical back gradient; sleeve cuffs swapped vs front (viewer-left cyan blue, viewer-right pink)
- short white back neck band with crisp black outer outline and one thin black inner line; shallow curve; no pointed front wings, no shield, no hanging V, no buttons, no name, no number

SHORTS BACK from IMAGE 3: solid white with center back seam; viewer-left hem cyan blue; viewer-right hem pink. No number.
REMOVE all names, numbers, logos. No studio backdrop."""

def png_size(path):
    with open(path, "rb") as f:
        if f.read(8) != b"\x89PNG\r\n\x1a\n":
            return 0, 0
        f.read(4)
        if f.read(4) != b"IHDR":
            return 0, 0
        return int.from_bytes(f.read(4), "big"), int.from_bytes(f.read(4), "big")

def color_type(path):
    with open(path, "rb") as f:
        f.read(8)
        ln = int.from_bytes(f.read(4), "big")
        f.read(4)
        data = f.read(ln)
    return data[9]

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

def log(msg):
    print(msg, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

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
        return 0, {"raw": type(e).__name__ + ":" + str(e)[:200]}

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
    out = r.stdout.decode().strip()
    err = r.stderr.decode().strip()
    url = (out.splitlines() or [""])[-1].strip()
    if not url.startswith("https://"):
        log("upload fail %s out=%s err=%s" % (name, out[:300], err[:300]))
        return ""
    log("up %s -> %s" % (name, url))
    return url

def save_png(final, img):
    tmp = final + ".part"
    urllib.request.urlretrieve(img, tmp)
    if os.path.getsize(tmp) < 10000:
        os.remove(tmp)
        log("too small reject %s" % os.path.basename(final))
        return False, 0
    ct = color_type(tmp)
    if ct not in (4, 6):
        log("colortype reject %s ct=%s" % (os.path.basename(final), ct))
        os.remove(tmp)
        return False, ct
    os.replace(tmp, final)
    w, h = png_size(final)
    log("saved %s bytes=%d %dx%d ct=%d" % (os.path.basename(final), os.path.getsize(final), w, h, ct))
    return True, ct

results = []

def record(tag, status, tid, path, extra=None):
    row = {"tag": tag, "status": status, "task_id": tid or "", "path": path}
    if extra:
        row.update(extra)
    results.append(row)
    log("RESULT %s %s %s" % (tag, status, tid or "-"))

def run_one(tag, final, prompt, images, max_gen_attempts=2):
    """max_gen_attempts=2 means original + one retry."""
    images = [u for u in images if u][:4]
    if len(images) < 3:
        record(tag, "fail_refs", "", final, {"images": images})
        return False
    last_tid = ""
    for attempt in range(max_gen_attempts):
        payload = {
            "model": "gpt-image-2",
            "prompt": prompt,
            "size": "1024x1024",
            "quality": "high",
            "background": "transparent",
            "image": images,
        }
        code, body = req("POST", base + "/v1/images/generations?async=true", payload)
        blob = json.dumps(body, ensure_ascii=False)
        if "余额" in blob:
            raise BalanceError(tag)
        tid = str((body or {}).get("id") or "")
        busy = busy_text(blob)
        log("submit %s code=%s tid=%s attempt=%s %s" % (tag, code, tid or "-", attempt, "busy" if busy else "ok"))
        if (not tid) or busy:
            # one busy retry of submit
            if busy and attempt == 0:
                time.sleep(8)
                code, body = req("POST", base + "/v1/images/generations?async=true", payload)
                blob = json.dumps(body, ensure_ascii=False)
                if "余额" in blob:
                    raise BalanceError(tag)
                tid = str((body or {}).get("id") or "")
                log("resubmit-busy %s code=%s tid=%s" % (tag, code, tid or "-"))
            if not tid:
                continue
        last_tid = tid
        # poll until done; on timeout keep polling same task (no new submit)
        for i in range(180):
            time.sleep(5)
            code, body = req("GET", base + "/v1/tasks/" + tid)
            st = extract_state(body).lower()
            blob = json.dumps(body, ensure_ascii=False)
            if i % 6 == 0:
                log("poll %s i=%s st=%s tid=%s" % (tag, i, st or "-", tid))
            if "余额" in blob:
                raise BalanceError(tag)
            if busy_text(blob) or st in ("failed", "error", "failure"):
                log("task-fail %s tid=%s st=%s" % (tag, tid, st or "busy"))
                break
            img = extract_url(body)
            if img and st in ("succeeded", "success", "completed", "done", "succeed"):
                ok, ct = save_png(final, img)
                if ok:
                    w, h = png_size(final)
                    record(tag, "saved", tid, final, {
                        "bytes": os.path.getsize(final),
                        "width": w, "height": h, "colortype": ct,
                        "attempt": attempt,
                    })
                    return True
                # colortype bad -> retry generate once
                record(tag, "colortype_reject", tid, final, {"colortype": ct, "attempt": attempt})
                break
        else:
            log("still-polling-timeout window %s tid=%s — continue same task" % (tag, tid))
            # extra poll window for same task
            for i in range(60):
                time.sleep(5)
                code, body = req("GET", base + "/v1/tasks/" + tid)
                st = extract_state(body).lower()
                img = extract_url(body)
                if img and st in ("succeeded", "success", "completed", "done", "succeed"):
                    ok, ct = save_png(final, img)
                    if ok:
                        w, h = png_size(final)
                        record(tag, "saved", tid, final, {
                            "bytes": os.path.getsize(final),
                            "width": w, "height": h, "colortype": ct,
                            "attempt": attempt,
                        })
                        return True
                    record(tag, "colortype_reject", tid, final, {"colortype": ct, "attempt": attempt})
                    break
                if st in ("failed", "error", "failure"):
                    break
            else:
                record(tag, "timeout", tid, final)
                return False
    record(tag, "fail", last_tid, final)
    return False

def main():
    os.makedirs(BACK, exist_ok=True)
    open(LOG, "w").close()
    stamp = time.strftime("%Y%m%d-%H%M%S")
    paths = {
        "05": KIT + "/05-整套正面-3D.png",
        "06": KIT + "/06-整套背面-3D.png",
    }
    for tag, p in paths.items():
        if os.path.exists(p):
            dest = os.path.join(BACK, stamp + "-" + os.path.basename(p))
            shutil.copy2(p, dest)
            log("backup %s -> %s" % (tag, dest))

    # Upload kit 2D refs
    u01 = upload(FRONT, "58-01-front-2d.png")
    u02 = upload(BACKJ, "58-02-back-2d.png")
    u03 = upload(SHORTS_F, "58-03-shorts-front-2d.png")
    u04 = upload(SHORTS_B, "58-04-shorts-back-2d.png")
    refs = {"u01": u01, "u02": u02, "u03": u03, "u04": u04, "POSE_F": POSE_F, "POSE_B": POSE_B}
    log("refs " + json.dumps(refs, ensure_ascii=False))
    if not all([u01, u02, u03, u04]):
        with open(RESULT, "w") as f:
            json.dump({"error": "upload_failed", "refs": refs, "results": results}, f, ensure_ascii=False, indent=2)
        raise SystemExit(1)

    ok05 = run_one("05", paths["05"], PROMPT_05, [POSE_F, u01, u03])
    if not ok05:
        with open(RESULT, "w") as f:
            json.dump({"refs": refs, "results": results}, f, ensure_ascii=False, indent=2)
        raise SystemExit(1)

    ok06 = run_one("06", paths["06"], PROMPT_06, [POSE_B, u02, u04])
    with open(RESULT, "w") as f:
        json.dump({"refs": refs, "results": results, "ok05": ok05, "ok06": ok06}, f, ensure_ascii=False, indent=2)
    log("ALLDONE ok05=%s ok06=%s" % (ok05, ok06))
    if not ok06:
        raise SystemExit(1)

if __name__ == "__main__":
    try:
        main()
    except BalanceError as e:
        log("STOPPED balance " + str(e))
        with open(RESULT, "w") as f:
            json.dump({"error": "balance", "tag": str(e), "results": results}, f, ensure_ascii=False, indent=2)
        raise SystemExit(2)
