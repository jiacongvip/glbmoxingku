#!/usr/bin/env python3
import json, subprocess, time, urllib.request, urllib.error, ssl, os, struct, shutil
KIT = "/Users/jiacong/Desktop/球衣套装拆图/64-Unichant-RedGeo"
TMP = os.path.join(KIT, "_过程稿")
def mysql(q):
    return subprocess.check_output(
        ['docker','exec','tpdaxiangshop_mysql','mysql','-uroot','-proot123456',
         'tpdaxiangshop','-N','-e', q], stderr=subprocess.DEVNULL).decode().strip()
key = mysql("SELECT api_key FROM ddwx_digitalavatar_provider_config WHERE aid=62 AND provider_key='duomiapi' LIMIT 1")
base = mysql("SELECT base_url FROM ddwx_digitalavatar_provider_config WHERE aid=62 AND provider_key='duomiapi' LIMIT 1").rstrip('/')
CTX = ssl.create_default_context()
urls = json.load(open(os.path.join(TMP,'oss-urls.json')))
REF = urls['64-ref-03-shorts-front.png']
PROMPT = """Isolated flat 2D soccer shorts FRONT only. 1024x1024 PNG. True transparent background. No gray board, no floor, no shadow, no text.

Match IMAGE 1: entire shorts solid bright red (pure solid red, no geometric camo, no side stripes, no panels of another color). Subtle fabric fold shading OK.
REMOVE every number completely. No jersey, no person, no logos, no Nike swoosh.
"""
payload={'model':'gpt-image-2','prompt':PROMPT,'size':'1024x1024','quality':'high','background':'transparent','image':[REF]}
def req(method, url, payload=None, timeout=60):
    data = None if payload is None else json.dumps(payload).encode()
    headers={'Authorization':'Bearer '+key,'Accept':'application/json'}
    if data is not None: headers['Content-Type']='application/json'
    r=urllib.request.Request(url,data=data,headers=headers,method=method)
    try:
        with urllib.request.urlopen(r,timeout=timeout,context=CTX) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body=e.read().decode(errors='replace')
        try: return e.code, json.loads(body)
        except Exception: return e.code, {'raw':body[:800]}
def extract_state(o):
    if not isinstance(o,dict): return ''
    return str(o.get('state') or o.get('status') or (o.get('data') or {}).get('state') or '')
def extract_url(o, img=''):
    if img: return img
    if isinstance(o,dict):
        for k,v in o.items():
            if k in ('url','image_url') and isinstance(v,str) and v.startswith('http'): return v
            img=extract_url(v,img)
            if img: return img
    elif isinstance(o,list):
        for x in o:
            img=extract_url(x,img)
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
    code,body=req('POST',base+'/v1/images/generations?async=true',payload)
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
    try: code,body=req('GET',base+'/v1/tasks/'+tid)
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
        tmpf=os.path.join(TMP,'03-duomi.png'); urllib.request.urlretrieve(img,tmpf)
        ct,w,h=png_colortype(tmpf)
        print('download colortype',ct,'size',w,h,'bytes',os.path.getsize(tmpf),'task',tid,flush=True)
        if ct not in (4,6):
            print('bad colortype',ct,flush=True)
            if retries>=1: print('MAX_RETRY_CT',flush=True); raise SystemExit(4)
            retries+=1; tid2,st2=submit()
            if st2=='balance': raise SystemExit(2)
            if tid2: tid=tid2
            continue
        dest=os.path.join(KIT,'03-短裤正面-2D.png'); shutil.copyfile(tmpf,dest)
        meta={'file':'03-短裤正面-2D.png','path':dest,'bytes':os.path.getsize(dest),'w':w,'h':h,'ct':ct,'task':tid,'cdn_url':img}
        open(os.path.join(TMP,'meta-03.json'),'w').write(json.dumps(meta,ensure_ascii=False,indent=2))
        print('SAVED',dest,os.path.getsize(dest),'task',tid,'ct',ct,flush=True); raise SystemExit(0)
print('TIMEOUT',tid,flush=True); raise SystemExit(5)
