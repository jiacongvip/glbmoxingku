import sys; sys.path.insert(0,'/tmp/kit64b')
from pipe import gen
from key_magenta import key_magenta, to_canvas
from PIL import Image, ImageFilter
import pathlib

ROOT=pathlib.Path("/Users/jiacong/Desktop/球衣套装拆图")

P_FRONT="""整套球衣【上身效果图】· 正面。

图1 = 这件球衣的【最新正面成品】——花色、配色、领型严格照它，不要自己发明。
图2 = 参考图：模特姿势、黑色短裤、白色长袜、黑色球鞋、构图与背景风格照它。

要求：
- 姿势、人体比例、构图、短裤、长袜、球鞋、画面中的大小与位置，全部与图2一致。
- 只把上身的球衣换成图1这件，细节（花纹、颜色、袖口、领型）照图1。
- 领口严格照图1：不要额外画黑色领圈、不要门襟扣子（除非图1本来就有）。
- 无头/无面部模特风格与图2一致。
【画面质感】清晰锐利，布料纹理细腻，像 4K 产品摄影，不要糊、不要噪点。
【构图】人物尽量占满画面：脚接近底部、头顶接近上沿，高度约占画幅 92%~96%。
背景必须是纯品红 #FF00FF，人物四周不要发光、光晕、阴影或渐变。
无文字、无logo。"""

P_BACK="""整套球衣【上身效果图】· 背面。

图1 = 这件球衣的【背面成品】——花色、配色严格照它。
图2 = 参考图：模特姿势、黑色短裤、白色长袜、黑色球鞋、构图与背景风格照它。

要求：
- 姿势、人体比例、构图、短裤、长袜、球鞋、画面中的大小与位置，全部与图2一致。
- 只把上身的球衣换成图1这件（背面），细节（花纹、颜色、袖口、后领圈）照图1。
- 不要画前襟、不要加门襟扣子。
- 无头/无面部模特风格与图2一致。
【画面质感】清晰锐利，布料纹理细腻，像 4K 产品摄影，不要糊、不要噪点。
【构图】人物尽量占满画面：脚接近底部、头顶接近上沿，高度约占画幅 92%~96%。
背景必须是纯品红 #FF00FF，人物四周不要发光、光晕、阴影或渐变。
无文字、无logo。"""

def run(kit, tag, src, ref, prompt):
    d=[p for p in ROOT.iterdir() if p.is_dir() and p.name.startswith(kit+"-")][0]
    im=gen(prompt, [src, ref], size="2048x2048")
    raw=pathlib.Path(f"/tmp/kit64b/raw-{kit}-{tag}.png"); im.save(raw)
    keyed=key_magenta(str(raw))
    out=to_canvas(keyed).filter(ImageFilter.UnsharpMask(radius=2.0, percent=90, threshold=2))
    dst=d/f"{tag}-整套{'正' if tag=='05' else '背'}面-3D.png"
    return d, dst, out, im
