# src\resize.py
import sys
from PIL import Image

def resize_stretch(im, w, h):
    return im.resize((w,h), Image.LANCZOS)

def resize_fit(im, w, h):
    im = im.copy()
    im.thumbnail((w,h), Image.LANCZOS)
    return im

def resize_pad(im, w, h, bg=(255,255,255,255)):
    im = im.copy().convert('RGBA')
    im.thumbnail((w,h), Image.LANCZOS)
    canvas = Image.new('RGBA', (w,h), bg)
    x = (w - im.width)//2
    y = (h - im.height)//2
    canvas.paste(im, (x,y), im)
    return canvas

def resize_fill(im, w, h):
    ow,oh = im.size
    ratio = max(w/ow, h/oh)
    nw,nh = int(ow*ratio), int(oh*ratio)
    im2 = im.resize((nw,nh), Image.LANCZOS)
    left = (nw - w)//2
    top = (nh - h)//2
    return im2.crop((left, top, left + w, top + h))

def save_image(img, outp, src_format):
    fmt = (src_format or 'PNG').upper()
    if fmt in ('JPEG','JPG'):
        if img.mode in ('RGBA','LA'):
            img = img.convert('RGB')
        img.save(outp, format='JPEG', quality=85)
    else:
        if img.mode == 'RGBA' and fmt == 'PNG':
            img.save(outp, format='PNG')
        else:
            img.save(outp, format=fmt)

def main(inp, outp, w, h, mode='stretch'):
    w=int(w); h=int(h)
    with Image.open(inp) as im:
        src_fmt = im.format or 'PNG'
        if mode == 'stretch':
            out = resize_stretch(im, w, h)
        elif mode == 'fit':
            out = resize_fit(im, w, h)
        elif mode == 'pad':
            out = resize_pad(im, w, h)
        elif mode == 'fill':
            out = resize_fill(im, w, h)
        else:
            print('Unknown mode:', mode)
            return
        save_image(out, outp, src_fmt)
        print('Saved', outp, 'mode=', mode)

if __name__ == '__main__':
    # usage: python src\resize.py INPUT OUTPUT WIDTH HEIGHT [mode]
    if len(sys.argv) < 5:
        print('Usage: python src\\resize.py INPUT OUTPUT WIDTH HEIGHT [mode]')
        sys.exit(1)
    _, inp, outp, w, h, *rest = sys.argv
    mode = rest[0] if rest else 'stretch'
    main(inp, outp, w, h, mode)
