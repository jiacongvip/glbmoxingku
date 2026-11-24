# -*- coding: utf-8 -*-
import hashlib, json, os, shutil, ssl, subprocess, time, urllib.error, urllib.request
from datetime import date

ROOT = "/Users/jiacong/Desktop/球衣套装拆图"
KIT = ROOT + "/粉黑-F002B"
BACK = KIT + "/_过程稿"
TUBAN = ROOT + "/粉黑-F002B-图版.png"
COLLAR_LOCAL = KIT + "/领口再小-正面预览.png"
SHORTS_F = KIT + "/03-短裤正面-2D.png"
SHORTS_B = KIT + "/04-短裤背面-2D.png"
LAYOUT = "https://qiniuoss.changzhouyunshan.com/upload/202610/01_2119135640.png"
POSE_F = "https://qiniuoss.changzhouyunshan.com/upload/202610/01_1842423141.png"
POSE_B = "https://qiniuoss.changzhouyunshan.com/upload/202610/01_1842432537.png"
LOG = BACK + "/regen-f002b-log.txt"
RESULT = BACK + "/regen-f002b-result.json"

TARGETS = [
    ("board", TUBAN),
    ("01", KIT + "/01-上衣正面-2D.png"),
    ("02", KIT + "/02-上衣背面-2D.png"),
    ("05", KIT + "/05-整套正面-3D.png"),
    ("06", KIT + "/06-整套背面-3D.png"),
]
LOCKED = [SHORTS_F, SHORTS_B]

def sha16(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]

def png_size(path):
    with open(path, "rb") as f:
        sig = f.read(8)
        if sig != b"\x89PNG\r\n\x1a\n":
            return 0, 0
        f.read(4)
        if f.read(4) != b"IHDR":
            return 0, 0
        w = int.from_bytes(f.read(4), "big")
        h = int.from_bytes(f.read(4), "big")
        return w, h

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
        err = (r.stderr.decode(errors="replace") or "")[:180]
        print("upload fail", name, err, flush=True)
        return ""
    print("up", name, flush=True)
    return url

def backup_all():
    os.makedirs(BACK, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    made = []
    for tag, path in TARGETS:
        if not os.path.exists(path):
            print("backup skip missing", tag, flush=True)
            continue
        dest = os.path.join(BACK, stamp + "-" + os.path.basename(path))
        shutil.copy2(path, dest)
        made.append(dest)
        print("backup", tag, dest, os.path.getsize(dest), flush=True)
    return stamp, made

COLLAR = (
    "COLLAR LOCK: match the approved preview image exactly. Small shallow white V, not a crew neck, not a polo, not a button placket. "
    "White collar band with ONE thick black stripe across the band, white edge above and below that stripe. "
    "A faint vertical center seam through the collar. The neck opening stays SMALL, the same width and the same short V depth as the approved preview. "
    "Do not enlarge the collar, do not deepen the V, do not restyle it."
)
BODY = (
    "Solid pink soccer jersey. The chest is the same solid pink as the body. "
    "NO white chest bar, NO white rectangle, NO white band, NO pink end blocks. "
    "Three separate black stripes on each sleeve. Pink outer cuff with a thin black edge. Short sleeves almost horizontal. "
    "NO text, NO numbers, NO logos, NO crests, NO stars, NO letters, NO badges, NO Nike, NO UNICHANT."
)
SHORTS = (
    "Black soccer shorts. Copy the shorts reference images exactly: side panel is an outer white stripe, a pink stripe, and an inner white stripe. "
    "Do not redesign, recolor, or add numbers or logos."
)

def save_png(final, img):
    tmp = final + ".part"
    urllib.request.urlretrieve(img, tmp)
    if os.path.getsize(tmp) < 10000:
        os.remove(tmp)
        print("tiny file", final, flush=True)
        return False
    os.replace(tmp, final)
    w, h = png_size(final)
    print("saved", os.path.basename(final), os.path.getsize(final), "%dx%d" % (w, h), flush=True)
    return True

results = []

def record(tag, status, tid, path):
    row = {"tag": tag, "status": status, "task_id": tid or "", "path": path}
    if path and os.path.exists(path) and status == "saved":
        w, h = png_size(path)
        row["bytes"] = os.path.getsize(path)
        row["width"] = w
        row["height"] = h
    results.append(row)
    print("RESULT", tag, status, tid or "-", path, flush=True)

def run(tag, final, prompt, images, size, transparent):
    images = [u for u in images if u]
    if len(images) > 4:
        print("too many refs", tag, flush=True)
        record(tag, "fail", "", final)
        return ""
    if len(images) < 1:
        print("no refs", tag, flush=True)
        record(tag, "fail", "", final)
        return ""
    payload = {
        "model": "gpt-image-2",
        "prompt": prompt,
        "size": size,
        "quality": "high",
        "image": images,
    }
    if transparent:
        payload["background"] = "transparent"
    last = ""
    for attempt in range(4):
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
        retry = False
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
                with open(LOG, "a") as f:
                    f.write("fail %s %s %s\n" % (tag, tid, st))
                time.sleep(8)
                retry = True
                break
            img = extract_url(body)
            if img and st in ("succeeded", "success", "completed", "done", "succeed"):
                if save_png(final, img):
                    record(tag, "saved", tid, final)
                    with open(LOG, "a") as f:
                        f.write("saved %s %s\n" % (tag, tid))
                    return tid
                retry = True
                break
        else:
            print("timeout", tag, tid, flush=True)
            with open(LOG, "a") as f:
                f.write("timeout %s %s\n" % (tag, tid))
        if not retry and last:
            continue
    record(tag, "fail", last, final)
    return ""

def main():
    os.makedirs(BACK, exist_ok=True)
    for p in LOCKED + [COLLAR_LOCAL]:
        if not os.path.exists(p):
            print("missing", p, flush=True)
            raise SystemExit(1)
    locks = {p: sha16(p) for p in LOCKED}
    print("shorts-before", locks[SHORTS_F], locks[SHORTS_B], flush=True)
    stamp, made = backup_all()
    print("stamp", stamp, "backups", len(made), flush=True)

    collar = upload(COLLAR_LOCAL, "pink-collar-lock.png")
    if not collar:
        print("collar upload failed", flush=True)
        raise SystemExit(1)
    sfront = upload(SHORTS_F, "pink-03-ref.png")
    sback = upload(SHORTS_B, "pink-04-ref.png")
    print("refs", "collar", bool(collar), "shorts", bool(sfront), bool(sback), flush=True)

    board_p = (
        "Soccer kit technical flat board, portrait canvas. Gray background, NOT transparent. "
        "Exactly four views arranged like IMAGE 2. IMAGE 2 is LAYOUT LOCK only: copy the arrangement of front jersey, back jersey, front shorts, back shorts. "
        "Do NOT copy IMAGE 2 colors, collar, logos, numbers, or stripes.\n"
        "IMAGE 1 is the approved pink jersey FRONT and the COLLAR LOCK. The front jersey on this board must match IMAGE 1, including the small collar. "
        + COLLAR + " " + BODY + "\n"
        "Back jersey on the board: the back of that same pink jersey. Solid pink back, no white bar, no name, no number. "
        "Collar seen from behind is the reverse of IMAGE 1: small neck, white band, one thick black stripe, faint center seam. Same three black sleeve stripes and pink cuff with a thin black edge.\n"
        "IMAGE 3 is the existing shorts FRONT and IMAGE 4 is the existing shorts BACK. Paste those shorts unchanged. " + SHORTS + "\n"
        "No text, no numbers, no logos, no crests, no stars, no Nike, no UNICHANT anywhere on the board."
    )
    p01 = (
        "2D flat CAD technical drawing of ONE soccer jersey FRONT only. Square canvas. Isolated garment on a transparent background. "
        "No gray board, no mannequin, no person, no shorts, no shadow.\n"
        "IMAGE 1 is the approved preview. Draw a fresh jersey that matches IMAGE 1 exactly: same pink, same sleeve stripes, same cuff, and the same small collar. "
        "Do not restyle anything. " + COLLAR + " " + BODY + "\n"
        "Clean flat vector, crisp black outlines, transparent background."
    )
    p02 = (
        "2D flat CAD technical drawing of ONE soccer jersey BACK only. Square canvas. Isolated garment on a transparent background. "
        "No gray board, no mannequin, no person, no shorts, no shadow.\n"
        "IMAGE 1 is the approved FRONT of this jersey. Draw the BACK of that same shirt. "
        "Solid pink back. NO white bar, NO name, NO number. Three black sleeve stripes, pink cuff with a thin black edge, short sleeves almost horizontal.\n"
        "Collar from behind is the reverse of IMAGE 1's small shallow white V. Keep the neck SMALL, the same opening size as IMAGE 1, not wider. "
        "White collar band with ONE thick black stripe and a faint center-back seam. No buttons, no placket. " + BODY + "\n"
        "Clean flat vector, crisp black outlines, transparent background."
    )

    run("board", TUBAN, board_p, [collar, LAYOUT, sfront, sback], "1024x1536", False)
    run("01", KIT + "/01-上衣正面-2D.png", p01, [collar], "1024x1024", True)

    u01 = ""
    if os.path.exists(KIT + "/01-上衣正面-2D.png"):
        # only re-upload if this run saved 01 (result status)
        if any(r["tag"] == "01" and r["status"] == "saved" for r in results):
            u01 = upload(KIT + "/01-上衣正面-2D.png", "pink-01-new.png")

    imgs02 = [collar] + ([u01] if u01 else [])
    run("02", KIT + "/02-上衣背面-2D.png", p02, imgs02, "1024x1024", True)

    u02 = ""
    if any(r["tag"] == "02" and r["status"] == "saved" for r in results):
        u02 = upload(KIT + "/02-上衣背面-2D.png", "pink-02-new.png")

    jersey_front = u01 or collar
    p05 = (
        "3D ghost-mannequin soccer kit, FRONT view. Square canvas. Transparent checkerboard background, binary alpha, no glow.\n"
        "IMAGE 1 is POSE LOCK only from kit 28. Keep its pose, camera, framing, and lighting. Socks pulled up. Black boots with NO logo and NO Nike swoosh. "
        "Do NOT copy IMAGE 1 colors, collar, chest graphics, or stripe colors.\n"
        "IMAGE 2 is the COLLAR LOCK, the approved pink jersey front. The jersey collar must match IMAGE 2 exactly in size and construction. "
        + COLLAR + " " + BODY + "\n"
        + ("IMAGE 3 is the freshly drawn front jersey. Use it for the flat pink body and sleeves, but the collar must stay locked to IMAGE 2.\n" if u01 else "")
        + "The last image is the existing shorts FRONT. Copy those shorts exactly onto the player. " + SHORTS + "\n"
        "Socks are white with a thin pink cuff. NO text, NO numbers, NO logos, NO crests, NO stars, NO Nike, NO UNICHANT. Do not keep IMAGE 1's original kit colors."
    )
    imgs05 = [POSE_F, collar] + ([u01] if u01 else []) + ([sfront] if sfront else [])
    run("05", KIT + "/05-整套正面-3D.png", p05, imgs05[:4], "1024x1024", True)

    p06 = (
        "3D ghost-mannequin soccer kit, BACK view. Square canvas. Transparent checkerboard background, binary alpha, no glow.\n"
        "IMAGE 1 is POSE LOCK only. Keep its back pose, camera, framing, and lighting. Socks pulled up. Black boots with NO logo and NO Nike swoosh. "
        "Do NOT copy IMAGE 1 colors.\n"
        "IMAGE 2 is the approved FRONT jersey and the COLLAR LOCK. The back collar is the reverse of that small shallow white V: small neck, white band, one thick black stripe, faint center seam. "
        "Do not enlarge the neck. " + COLLAR + "\n"
        "Jersey back is solid pink. NO white bar, NO name, NO number. Three black sleeve stripes, pink cuff with a thin black edge. " + BODY + "\n"
        + ("The next image is the freshly drawn jersey BACK. Match that back drawing.\n" if u02 else "")
        + "The last image is the existing shorts BACK. Copy those shorts exactly. " + SHORTS + "\n"
        "Socks are white with a thin pink cuff. NO text, NO numbers, NO logos, NO crests, NO stars, NO Nike, NO UNICHANT."
    )
    imgs06 = [POSE_B, collar] + ([u02] if u02 else []) + ([sback] if sback else [])
    run("06", KIT + "/06-整套背面-3D.png", p06, imgs06[:4], "1024x1024", True)

    after = {p: sha16(p) for p in LOCKED}
    same = after == locks
    print("shorts-after", after[SHORTS_F], after[SHORTS_B], "unchanged" if same else "CHANGED", flush=True)
    if not same:
        print("SHORTS HASH MISMATCH", flush=True)
    with open(RESULT, "w") as f:
        json.dump({"stamp": stamp, "backups": made, "results": results, "shorts_unchanged": same, "collar_ref": collar}, f, ensure_ascii=False, indent=2)
    print("ALLDONE", flush=True)

if __name__ == "__main__":
    try:
        main()
    except BalanceError as e:
        try:
            with open(RESULT, "w") as f:
                json.dump({"balance": True, "stopped_at": str(e), "results": results}, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        print("STOPPED balance", str(e), flush=True)
        raise SystemExit(2)
