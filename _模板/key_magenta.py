from PIL import Image, ImageFilter
import numpy as np

def key_magenta(path, lo=15.0, hi=70.0, erode=1, blur=0.7, despill=0.85):
    im = Image.open(path).convert("RGB")
    a = np.array(im).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m = np.minimum(r, b) - g                      # 洋红程度
    af = np.clip((hi - m) / (hi - lo), 0.0, 1.0)  # 1=主体, 0=背景
    # 去溢色：越接近透明，越把 r/b 拉向 g，去掉粉色镶边
    k = (1.0 - af) * despill
    a[..., 0] = r * (1 - k) + g * k
    a[..., 2] = b * (1 - k) + g * k
    alpha = Image.fromarray((af * 255).astype(np.uint8), "L")
    if erode:
        f = 2 * erode + 1
        alpha = alpha.filter(ImageFilter.MinFilter(f)).filter(ImageFilter.MaxFilter(3))
    if blur:
        alpha = alpha.filter(ImageFilter.GaussianBlur(blur))
    out = Image.fromarray(a.clip(0, 255).astype(np.uint8)).convert("RGBA")
    out.putalpha(alpha)
    return out.crop(alpha.getbbox())

def to_canvas(im, box_w=1838, box_h=1886, canvas=2000, ox=81, oy=57):
    w, h = im.size
    s = min(box_w / w, box_h / h)
    nw, nh = int(round(w * s)), int(round(h * s))
    im2 = im.resize((nw, nh), Image.LANCZOS)
    out = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    out.alpha_composite(im2, (ox + (box_w - nw) // 2, oy + (box_h - nh) // 2))
    return out
