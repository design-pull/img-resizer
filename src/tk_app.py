# src/tk_app.py
import os
import io
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageSequence
import cairosvg
from pathlib import Path

# -------------------------
# 画像処理ユーティリティ（自己完結）
# -------------------------
def rasterize_svg_to_png_bytes(svg_path, out_w=None, out_h=None):
    return cairosvg.svg2png(url=svg_path, output_width=out_w, output_height=out_h)

def resize_stretch(img, w, h):
    return img.resize((w, h), Image.LANCZOS)

def resize_fit(img, w, h):
    im = img.copy()
    im.thumbnail((w, h), Image.LANCZOS)
    return im

def resize_pad(img, w, h, bg=(255,255,255,255)):
    im = img.copy().convert('RGBA')
    im.thumbnail((w, h), Image.LANCZOS)
    canvas = Image.new('RGBA', (w, h), bg)
    x = (w - im.width)//2
    y = (h - im.height)//2
    canvas.paste(im, (x, y), im)
    return canvas

def resize_fill(img, w, h):
    ow, oh = img.size
    ratio = max(w/ow, h/oh)
    nw, nh = int(ow*ratio), int(oh*ratio)
    im2 = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - w)//2
    top = (nh - h)//2
    return im2.crop((left, top, left + w, top + h))

def save_image(img, out_path, orig_ext, jpeg_quality=85):
    ext = orig_ext.lower()
    if ext in ('.jpg', '.jpeg'):
        if img.mode in ('RGBA', 'LA'):
            img = img.convert('RGB')
        img.save(out_path, format='JPEG', quality=jpeg_quality)
    elif ext == '.png':
        if img.mode == 'RGBA':
            img.save(out_path, format='PNG')
        else:
            img.save(out_path, format='PNG')
    else:
        # default to PNG for unknowns
        img.save(out_path, format='PNG')

def process_static_file(in_path, out_folder, w, h, mode, bg_color, jpeg_quality=85):
    ext = Path(in_path).suffix.lower()
    name = Path(in_path).stem
    if ext == '.svg':
        png_bytes = rasterize_svg_to_png_bytes(in_path, out_w=w if mode!='fit' else None, out_h=h if mode!='fit' else None)
        im = Image.open(io.BytesIO(png_bytes)).convert('RGBA')
        # ensure we apply chosen mode after rasterize
        img_out = {
            'stretch': resize_stretch,
            'fit': resize_fit,
            'pad': resize_pad,
            'fill': resize_fill
        }[mode](im, w, h) if mode in ('stretch','fit','pad','fill') else resize_stretch(im, w, h)
        out_path = os.path.join(out_folder, f"{name}.png")
        save_image(img_out, out_path, '.png', jpeg_quality)
        return out_path

    elif ext == '.gif':
        # animated GIF: process each frame and re-save GIF preserving durations and loop
        im = Image.open(in_path)
        frames = []
        durations = []
        for frame in ImageSequence.Iterator(im):
            frame_rgba = frame.convert('RGBA')
            frame_out = {
                'stretch': resize_stretch,
                'fit': resize_fit,
                'pad': resize_pad,
                'fill': resize_fill
            }[mode](frame_rgba, w, h) if mode in ('stretch','fit','pad','fill') else resize_stretch(frame_rgba, w, h)
            # convert to paletted frame for GIF
            frame_p = frame_out.convert('P', palette=Image.ADAPTIVE)
            frames.append(frame_p)
            durations.append(frame.info.get('duration', 100))
        out_path = os.path.join(out_folder, f"{name}.gif")
        frames[0].save(out_path, save_all=True, append_images=frames[1:], duration=durations, loop=im.info.get('loop',0), optimize=True)
        return out_path

    else:
        im = Image.open(in_path).convert('RGBA')
        img_out = {
            'stretch': resize_stretch,
            'fit': resize_fit,
            'pad': resize_pad,
            'fill': resize_fill
        }[mode](im, w, h) if mode in ('stretch','fit','pad','fill') else resize_stretch(im, w, h)
        out_ext = ext if ext in ('.png', '.jpg', '.jpeg') else '.png'
        out_path = os.path.join(out_folder, f"{name}{out_ext}")
        save_image(img_out, out_path, out_ext, jpeg_quality)
        return out_path

# -------------------------
# Tkinter GUI
# -------------------------
def pick_files():
    files = filedialog.askopenfilenames(title="画像を選択", filetypes=[("Images","*.png;*.jpg;*.jpeg;*.gif;*.svg")])
    if files:
        listbox.delete(0, tk.END)
        for f in files:
            listbox.insert(tk.END, f)

def pick_output_folder():
    folder = filedialog.askdirectory(title="出力フォルダを選択")
    if folder:
        out_var.set(folder)

def run_resize():
    files = listbox.get(0, tk.END)
    if not files:
        messagebox.showinfo("Info", "まず画像を選択してください")
        return
    out_folder = out_var.get() or os.path.join(os.getcwd(), "output")
    os.makedirs(out_folder, exist_ok=True)
    try:
        w = int(width_var.get()); h = int(height_var.get())
    except ValueError:
        messagebox.showerror("Error", "幅と高さには整数を入力してください")
        return
    mode = mode_var.get()
    try:
        bg_parts = [int(x.strip()) for x in bg_var.get().split(',')]
        if len(bg_parts) == 3:
            bg = (bg_parts[0], bg_parts[1], bg_parts[2], 255)
        elif len(bg_parts) == 4:
            bg = tuple(bg_parts)
        else:
            raise ValueError
    except Exception:
        messagebox.showerror("Error", "背景色は R,G,B または R,G,B,A の形式で入力してください")
        return

    log_text.delete(1.0, tk.END)
    success = 0
    for f in files:
        try:
            log_text.insert(tk.END, f"処理中: {f}\n")
            outp = process_static_file(f, out_folder, w, h, mode, bg)
            log_text.insert(tk.END, f"出力: {outp}\n")
            success += 1
        except Exception as e:
            log_text.insert(tk.END, f"エラー: {f} -> {e}\n")
    messagebox.showinfo("完了", f"{success} / {len(files)} 件処理しました\n出力フォルダ:\n{out_folder}")

# ウィンドウ作成
root = tk.Tk()
root.title("Img Resizer - Simple (Tkinter)")

frame = tk.Frame(root, padx=10, pady=10)
frame.pack(fill='both', expand=True)

btn_frame = tk.Frame(frame)
btn_frame.grid(row=0, column=0, sticky='w')

tk.Button(btn_frame, text="ファイルを選択", command=pick_files).pack(side='left', padx=2)
tk.Button(btn_frame, text="出力フォルダ選択", command=pick_output_folder).pack(side='left', padx=2)
tk.Button(btn_frame, text="終了", command=root.quit).pack(side='left', padx=2)

listbox = tk.Listbox(frame, width=80, height=8)
listbox.grid(row=1, column=0, columnspan=3, pady=8)

opts_frame = tk.Frame(frame)
opts_frame.grid(row=2, column=0, sticky='w')

tk.Label(opts_frame, text="幅:").grid(row=0, column=0, sticky='e')
width_var = tk.StringVar(value="800")
tk.Entry(opts_frame, textvariable=width_var, width=8).grid(row=0, column=1, sticky='w', padx=4)

tk.Label(opts_frame, text="高さ:").grid(row=0, column=2, sticky='e')
height_var = tk.StringVar(value="600")
tk.Entry(opts_frame, textvariable=height_var, width=8).grid(row=0, column=3, sticky='w', padx=4)

tk.Label(opts_frame, text="モード:").grid(row=1, column=0, sticky='e')
mode_var = tk.StringVar(value="pad")
tk.OptionMenu(opts_frame, mode_var, "stretch", "fit", "pad", "fill").grid(row=1, column=1, sticky='w', padx=4)

tk.Label(opts_frame, text="背景色 (R,G,B) :").grid(row=1, column=2, sticky='e')
bg_var = tk.StringVar(value="255,255,255")
tk.Entry(opts_frame, textvariable=bg_var, width=12).grid(row=1, column=3, sticky='w', padx=4)

out_var = tk.StringVar(value=os.path.join(os.getcwd(), "output"))
tk.Label(frame, text="出力フォルダ:").grid(row=3, column=0, sticky='w')
tk.Entry(frame, textvariable=out_var, width=60).grid(row=4, column=0, sticky='w', pady=4)

run_frame = tk.Frame(frame)
run_frame.grid(row=5, column=0, pady=6, sticky='w')
tk.Button(run_frame, text="開始", command=run_resize, bg="#4CAF50", fg="white").pack(side='left', padx=6)
tk.Button(run_frame, text="クリア", command=lambda: listbox.delete(0, tk.END)).pack(side='left', padx=6)

log_label = tk.Label(frame, text="ログ:")
log_label.grid(row=6, column=0, sticky='w')
log_text = tk.Text(frame, width=80, height=10)
log_text.grid(row=7, column=0, pady=6)

root.mainloop()
