#!/bin/bash
set -euo pipefail
KIT="/Users/jiacong/Desktop/球衣套装拆图/66-Unichant-BlueCamoBlack"
TMP="$KIT/_过程稿"
python3 - <<'PY'
import json, subprocess, os, time
kit="/Users/jiacong/Desktop/球衣套装拆图/66-Unichant-BlueCamoBlack"
tmp=os.path.join(kit,"_过程稿")
urls={
  "F013-front":"https://qiniuoss.changzhouyunshan.com/upload/202610/12_2030573172.png",
  "F013-back":"https://qiniuoss.changzhouyunshan.com/upload/202610/12_2030596760.png",
  "POSE_F":"https://qiniuoss.changzhouyunshan.com/upload/202610/01_1842423141.png",
  "POSE_B":"https://qiniuoss.changzhouyunshan.com/upload/202610/01_1842432537.png",
}
mapping=[
  ("66-ref-01-jersey-front.png","ref-01-jersey-front.png"),
  ("66-ref-02-jersey-back.png","ref-02-jersey-back.png"),
  ("66-ref-03-shorts-front.png","ref-03-shorts-front.png"),
  ("66-ref-04-shorts-back.png","ref-04-shorts-back.png"),
]
subprocess.check_call(["docker","cp",os.path.join(tmp,"oss_upload.php"),"tpdaxiangshop_php:/tmp/oss_upload.php"])
for key, fname in mapping:
    local=os.path.join(tmp,fname)
    remote=f"/tmp/{key}"
    subprocess.check_call(["docker","cp",local,f"tpdaxiangshop_php:{remote}"])
    out=subprocess.check_output(["docker","exec","tpdaxiangshop_php","php","/tmp/oss_upload.php",remote], text=True).strip()
    print(key, out)
    urls[key]=out
    time.sleep(1)
open(os.path.join(tmp,"oss-urls.json"),"w").write(json.dumps(urls,indent=2,ensure_ascii=False))
print("wrote oss-urls.json")
print(json.dumps(urls,indent=2))
PY
