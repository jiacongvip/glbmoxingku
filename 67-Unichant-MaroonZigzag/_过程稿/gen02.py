#!/usr/bin/env python3
import json, subprocess, time, urllib.request, urllib.error, ssl, os, struct, shutil
KIT = "/Users/jiacong/Desktop/球衣套装拆图/67-Unichant-MaroonZigzag"
TMP = os.path.join(KIT, "_过程稿")
def mysql(q):
    return subprocess.check_output(
        ['docker','exec','tpdaxiangshop_mysql','mysql','-uroot','-proot123456',
         'tpdaxiangshop','-N','-e', q], stderr=subprocess.DEVNULL).decode().strip()
key = mysql("SELECT api_key FROM ddwx_digitalavatar_provider_config WHERE aid=62 AND provider_key='duomiapi' LIMIT 1")
base = mysql("SELECT base_url FROM ddwx_digitalavatar_provider_config WHERE aid=62 AND provider_key='duomiapi' LIMIT 1").rstrip('/')
CTX = ssl.create_default_context()
urls = json.load(open(os.path.join(TMP,'oss-urls.json')))
REF02 = urls['67-ref-02-jersey-back.png']
F013B = urls['F013-back']
PROMPT_02 = """Isolated flat 2D soccer jersey BACK only. 1024x1024 PNG. True transparent background. No gray board, no floor, no shadow, no text, no number.

IMAGE 1 is the back body to keep:
- main back torso: deep maroon / burgundy base with repeating tonal horizontal zig-zag / chevron pattern (same as front torso)
- BOTH sleeves: solid WHITE raglan sleeves (NOT maroon, NOT patterned), extending to the neckline
- each cuff finished with TWO thin horizontal MAROON stripes
- vertical WHITE side stripe on the side (keep)
Delete every number and logo (PLAYER, 42, Unichant, L, KICHIJOJI, crest, Nike). Discard IMAGE 1's plain white round crew / V neck.

IMAGE 2 is the only collar geometry. Ignore the gray F-013 label and the white paper. Copy that short back neck band exactly. Collar fabric is solid WHITE (light collar, same as the neck on the design sheet):
- solid WHITE fabric
- thin BLACK outer outline, one thin BLACK inner line (light collar uses black outlines)
- shallow curve, center dips slightly
- no pointed wings, no inner shield, no hanging V, no second line, no vertical center line down the back
- not a polo, no buttons, no placket, no round crew

No shorts, no mannequin, no person, no logo."""
payload = {'model':'gpt-image-2','prompt':PROMPT_02,'size':'1024x1024','quality':'high','background':'transparent','image':[REF02,F013B]}
def req(method, url, payload=None, timeout=60):
    data = None if payload is None else json.dumps(payload).encode()
    headers = {'Authorization':'Bearer '+key,'Accept':'application/json'}
    if data is not None: headers['Content-Type']='application/json'
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=timeout, context=CTX) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors='replace')
        try: return e.code, json.loads(body)
        except Exception: return e.code, {'raw': body[:800]}
def extract_state(o):
    if not isinstance(o, dict): return ''
    return str(o.get('state') or o.get('status') or (o.get('data') or {}).get('state') or '')
def extract_url(o, img=''):
    if img: return img
    if isinstance(o, dict):
        for k,v in o.items():
            if k in ('url','image_url') and isinstance(v,str) and v.startswith('http'): return v
            img = extract_url(v, img)
            if img: return img
    elif isinstance(o, list):
        for x in o:
            img = extract_url(x, img)
            if img: return img
    return img
def png_colortype(path):
    with open(path,'rb') as f:
        if f.read(8)!=b'\x89PNG\r\n\x1a\n': return None,None,None
        length=struct.unpack('>I',f.read(4))[0]; ctype=f.read(4); data=f.read(length)
        if ctype!=b'IHDR' or length<13: return None,None,None
        w,h=struct.unpack('>II',data[0:8]); return data[9],w,h
def is_balance_error(body):
    s=json.dumps(body,ensure_ascii=False) if not isinstance(body,str) else body
    return ('余额不足' in s) or ('API账户余额不足' in s)
def is_busy(body):
    s=json.dumps(body,ensure_ascii=False) if not isinstance(body,str) else body
    return '系统繁忙' in s
def submit():
    code, body = req('POST', base+'/v1/images/generations?async=true', payload)
    tid=str((body or {}).get('id') or '')
    if not tid and isinstance(body,dict):
        data=body.get('data') or {}
        if isinstance(data,dict): tid=str(data.get('id') or '')
    print('submit',code,tid,str(body)[:300],flush=True)
    if is_balance_error(body): print('BALANCE',flush=True); return None,'balance'
    if not tid: return None,'notid'
    return tid,'ok'
tid,st=submit()
if st=='balance': raise SystemExit(2)
if not tid:
    time.sleep(3); tid,st=submit()
    if st=='balance': raise SystemExit(2)
    if not tid: raise SystemExit(1)
retries=0
for i in range(120):
    time.sleep(5)
    try: code,body=req('GET', base+'/v1/tasks/'+tid)
    except Exception as e:
        print('poll_net_err',e,'keep',tid,flush=True); continue
    stt=extract_state(body).lower(); print('poll',i,stt,flush=True)
    if is_balance_error(body): print('BALANCE',flush=True); raise SystemExit(2)
    if stt in ('failed','error','failure') or is_busy(body):
        print('fail',str(body)[:400],flush=True)
        if retries>=1: print('MAX_RETRY',flush=True); raise SystemExit(3)
        retries+=1; tid2,st2=submit()
        if st2=='balance': raise SystemExit(2)
        if tid2: tid=tid2
        continue
    img=extract_url(body)
    if img and stt in ('succeeded','success','completed','done'):
        tmp=os.path.join(TMP,'02-duomi.png'); urllib.request.urlretrieve(img,tmp)
        ct,w,h=png_colortype(tmp)
        print('download colortype',ct,'size',w,h,'bytes',os.path.getsize(tmp),'task',tid,flush=True)
        if ct not in (4,6):
            print('bad colortype',ct,flush=True)
            if retries>=1: print('MAX_RETRY_CT',flush=True); raise SystemExit(4)
            retries+=1; tid2,st2=submit()
            if st2=='balance': raise SystemExit(2)
            if tid2: tid=tid2
            continue
        dest=os.path.join(KIT,'02-上衣背面-2D.png'); shutil.copyfile(tmp,dest)
        meta={'file':'02-上衣背面-2D.png','path':dest,'bytes':os.path.getsize(dest),'w':w,'h':h,'ct':ct,'task':tid,'cdn_url':img}
        open(os.path.join(TMP,'meta-02.json'),'w').write(json.dumps(meta,ensure_ascii=False,indent=2))
        print('SAVED',dest,os.path.getsize(dest),'task',tid,'ct',ct,flush=True); raise SystemExit(0)
print('TIMEOUT',tid,flush=True); raise SystemExit(5)
