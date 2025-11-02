# src/tk_app.py
import os
import io
import sys
import math
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageSequence, ImageTk
from pathlib import Path

# Optional DnD and SVG
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except Exception:
    DND_AVAILABLE = False

try:
    import cairosvg
    HAVE_CAIROSVG = True
except Exception:
    cairosvg = None
    HAVE_CAIROSVG = False

# -------------------------
# 画像処理ユーティリティ（厳密版）
# -------------------------
def rasterize_svg_to_png_bytes(svg_path, out_w=None, out_h=None):
    if not HAVE_CAIROSVG:
        raise RuntimeError("SVG support requires cairosvg and native cairo installed")
    return cairosvg.svg2png(url=svg_path, output_width=out_w, output_height=out_h)

def resize_pad(img, w, h, bg=(255,255,255,255), log_func=None):
    ow, oh = img.size
    if ow == 0 or oh == 0:
        return Image.new('RGBA', (w, h), bg)
    ratio = min(w / ow, h / oh)
    nw = max(1, int(round(ow * ratio)))
    nh = max(1, int(round(oh * ratio)))
    im_resized = img.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new('RGBA', (w, h), bg)
    left = (w - nw) // 2
    top = (h - nh) // 2
    canvas.paste(im_resized, (left, top), im_resized if im_resized.mode == 'RGBA' else None)
    if canvas.size != (w, h):
        canvas = canvas.crop((0, 0, w, h)).copy()
    if log_func:
        log_func(f"resize: orig:({ow},{oh}) -> after resize:({nw},{nh}) left:{left} top:{top}")
    return canvas

def save_image(img, out_path, orig_ext, jpeg_quality=85, bg=(255,255,255)):
    ext = orig_ext.lower()
    if ext in ('.jpg', '.jpeg'):
        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, bg)
            alpha = img.split()[-1]
            background.paste(img.convert('RGB'), mask=alpha)
            background.save(out_path, format='JPEG', quality=jpeg_quality)
        else:
            img.convert('RGB').save(out_path, format='JPEG', quality=jpeg_quality)
    elif ext == '.png':
        img.save(out_path, format='PNG')
    else:
        img.save(out_path, format='PNG')

def process_static_file(in_path, out_folder, w, h, mode='pad', bg_color=(255,255,255,255), jpeg_quality=85, log_func=None):
    ext = Path(in_path).suffix.lower()
    name = Path(in_path).stem
    if ext == '.svg':
        if not HAVE_CAIROSVG:
            raise RuntimeError("SVG support requires cairosvg and native cairo installed")
        png_bytes = rasterize_svg_to_png_bytes(in_path, out_w=w if mode!='fit' else None, out_h=h if mode!='fit' else None)
        im = Image.open(io.BytesIO(png_bytes)).convert('RGBA')
        out_img = resize_pad(im, w, h, bg_color, log_func=log_func)
        out_path = os.path.join(out_folder, f"{name}.png")
        save_image(out_img, out_path, '.png', jpeg_quality)
        return out_path
    elif ext == '.gif':
        im = Image.open(in_path)
        frames = []
        durations = []
        for frame in ImageSequence.Iterator(im):
            frame_rgba = frame.convert('RGBA')
            out_frame = resize_pad(frame_rgba, w, h, bg_color, log_func=log_func)
            frames.append(out_frame.convert('P', palette=Image.ADAPTIVE))
            durations.append(frame.info.get('duration', 100))
        out_path = os.path.join(out_folder, f"{name}.gif")
        frames[0].save(out_path, save_all=True, append_images=frames[1:], duration=durations, loop=im.info.get('loop',0), optimize=True)
        return out_path
    else:
        im = Image.open(in_path).convert('RGBA')
        out_img = resize_pad(im, w, h, bg_color, log_func=log_func)
        out_ext = ext if ext in ('.png', '.jpg', '.jpeg') else '.png'
        out_path = os.path.join(out_folder, f"{name}{out_ext}")
        save_image(out_img, out_path, out_ext, jpeg_quality, bg=tuple(bg_color[:3]))
        return out_path

# -------------------------
# GUI helpers
# -------------------------
def pil_image_to_tk(pil_img, max_w, max_h):
    if pil_img.width == 0 or pil_img.height == 0:
        return None
    ratio = min(max_w / pil_img.width, max_h / pil_img.height)
    tw = max(1, int(round(pil_img.width * ratio)))
    th = max(1, int(round(pil_img.height * ratio)))
    thumb = pil_img.resize((tw, th), Image.LANCZOS)
    return ImageTk.PhotoImage(thumb)

# -------------------------
# Application
# -------------------------
class ImgResizerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Img Resizer - Debugged")
        self.files = []
        self.current_index = None
        self.orig_images = {}
        self.bg = (255,255,255,255)
        self.updating_dim = False
        self.build_ui()

    def build_ui(self):
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill='both', expand=True)

        left_col = ttk.Frame(top)
        left_col.grid(row=0, column=0, sticky='nsw', padx=(0,8))
        right_col = ttk.Frame(top)
        right_col.grid(row=0, column=1, sticky='nsew')
        top.columnconfigure(1, weight=1)

        # left controls
        btn_frame = ttk.Frame(left_col)
        btn_frame.pack(fill='x', pady=(0,6))
        ttk.Button(btn_frame, text="ファイルを追加", command=self.add_files_dialog).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="全てクリア", command=self.clear_files).pack(side='left', padx=2)

        list_frame = ttk.Frame(left_col)
        list_frame.pack(fill='both', expand=True)
        self.listbox = tk.Listbox(list_frame, width=50, height=14, selectmode=tk.SINGLE)
        self.listbox.pack(side='left', fill='both', expand=True)
        self.listbox.bind('<<ListboxSelect>>', self.on_select)
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.listbox.config(yscrollcommand=scrollbar.set)

        if DND_AVAILABLE:
            try:
                self.listbox.drop_target_register(DND_FILES)
                self.listbox.dnd_bind('<<Drop>>', self.drop_event)
            except Exception:
                pass

        # right: preview and options
        preview_frame = ttk.Frame(right_col)
        preview_frame.pack(fill='both', expand=True)

        # top area: canvases and top-right controls
        canvas_top = ttk.Frame(preview_frame)
        canvas_top.pack(fill='x')

        canvas_frame = ttk.Frame(canvas_top)
        canvas_frame.pack(side='left', fill='x', expand=True)

        top_right_ctrl = ttk.Frame(canvas_top)
        top_right_ctrl.pack(side='right', anchor='ne')

        self.orig_canvas = tk.Canvas(canvas_frame, width=420, height=300, bg='gray90', highlightthickness=1)
        self.orig_canvas.pack(side='left', padx=(0,8))
        self.resized_canvas = tk.Canvas(canvas_frame, width=420, height=300, bg='gray90', highlightthickness=1)
        self.resized_canvas.pack(side='left')

        # サイズ変更ボタン（右上に配置）
        ttk.Button(top_right_ctrl, text="サイズ変更", command=self.open_size_popup).pack(padx=4, pady=2)

        opts_frame = ttk.Frame(preview_frame)
        opts_frame.pack(fill='x', pady=(8,6))

        ttk.Label(opts_frame, text="幅").grid(row=0, column=0, sticky='e')
        self.width_var = tk.StringVar(value="800")
        ttk.Entry(opts_frame, textvariable=self.width_var, width=10).grid(row=0, column=1, sticky='w', padx=6)

        ttk.Label(opts_frame, text="高さ").grid(row=0, column=2, sticky='e')
        self.height_var = tk.StringVar(value="600")
        ttk.Entry(opts_frame, textvariable=self.height_var, width=10).grid(row=0, column=3, sticky='w', padx=6)

        self.aspect_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opts_frame, text="アスペクト比を維持", variable=self.aspect_var).grid(row=0, column=4, sticky='w', padx=12)

        self.width_var.trace_add('write', lambda *a: self.on_dim_change('w'))
        self.height_var.trace_add('write', lambda *a: self.on_dim_change('h'))

        out_row = ttk.Frame(preview_frame)
        out_row.pack(fill='x', pady=(6,4))
        ttk.Label(out_row, text="出力フォルダ:").pack(side='left')
        self.out_var = tk.StringVar(value=os.path.join(os.getcwd(), "output"))
        ttk.Entry(out_row, textvariable=self.out_var, width=56).pack(side='left', padx=6)
        ttk.Button(out_row, text="選択", command=self.pick_output_folder).pack(side='left')

        run_row = ttk.Frame(preview_frame)
        run_row.pack(fill='x', pady=(6,4))
        ttk.Button(run_row, text="プレビュー更新", command=self.update_preview).pack(side='left', padx=6)
        ttk.Button(run_row, text="保存", command=self.run_resize).pack(side='left', padx=6)

        log_frame = ttk.Frame(self.root, padding=(8,0))
        log_frame.pack(fill='both', expand=False)
        ttk.Label(log_frame, text="ログ:").pack(anchor='w')
        self.log_text = tk.Text(log_frame, width=110, height=8)
        self.log_text.pack(fill='both', expand=True)

        if not DND_AVAILABLE:
            self.log("※ Drag & Drop: tkinterdnd2 not found; use 'ファイルを追加'.")
        if not HAVE_CAIROSVG:
            self.log("※ SVG support disabled: install cairosvg + native cairo to enable.")

    # DnD handlers
    def drop_event(self, event):
        data = event.data
        paths = self._parse_dnd_files_string(data)
        self.add_files(paths)

    @staticmethod
    def _parse_dnd_files_string(s):
        out = []
        cur = ''
        in_brace = False
        for ch in s:
            if ch == '{':
                in_brace = True
                cur = ''
                continue
            if ch == '}':
                in_brace = False
                out.append(cur)
                cur = ''
                continue
            if ch.isspace() and not in_brace:
                if cur:
                    out.append(cur)
                    cur = ''
                continue
            cur += ch
        if cur:
            out.append(cur)
        return out

    # file mgmt
    def add_files_dialog(self):
        files = filedialog.askopenfilenames(title="画像を選択", filetypes=[("Images","*.png;*.jpg;*.jpeg;*.gif;*.svg")])
        if files:
            self.add_files(list(files))

    def add_files(self, paths):
        added = 0
        for p in paths:
            if not p:
                continue
            p = os.path.abspath(p)
            if p not in self.files:
                self.files.append(p)
                self.listbox.insert(tk.END, os.path.basename(p))
                added += 1
        if added:
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(tk.END)
            self.listbox.event_generate("<<ListboxSelect>>")

    def clear_files(self):
        self.files = []
        self.orig_images.clear()
        self.listbox.delete(0, tk.END)
        self.current_index = None
        self.clear_canvases()

    # selection & preview
    def on_select(self, event=None):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        self.current_index = idx
        path = self.files[idx]
        self.load_original_image(path)
        self.update_dimension_fields_from_original(path)
        self.update_preview()

    def load_original_image(self, path):
        if path in self.orig_images:
            return
        try:
            ext = Path(path).suffix.lower()
            if ext == '.svg':
                if not HAVE_CAIROSVG:
                    raise RuntimeError("SVG support not available")
                png_bytes = rasterize_svg_to_png_bytes(path)
                pil = Image.open(io.BytesIO(png_bytes)).convert('RGBA')
            else:
                pil = Image.open(path).convert('RGBA')
            self.orig_images[path] = pil
        except Exception as e:
            messagebox.showerror("読み込みエラー", f"{path}\n{e}")
            self.log(f"読み込みエラー: {path} -> {e}")

    def update_dimension_fields_from_original(self, path):
        try:
            im = self.orig_images.get(path)
            if not im:
                return
            ow, oh = im.size
            if self.aspect_var.get():
                try:
                    cur_w = int(self.width_var.get())
                    new_h = max(1, int(round(cur_w * (oh / ow))))
                    self.updating_dim = True
                    self.height_var.set(str(new_h))
                except Exception:
                    self.updating_dim = True
                    self.width_var.set(str(ow))
                    self.height_var.set(str(oh))
                finally:
                    self.updating_dim = False
            else:
                self.width_var.set(str(ow))
                self.height_var.set(str(oh))
        except Exception:
            pass

    def update_preview(self):
        if self.current_index is None:
            return
        path = self.files[self.current_index]
        if path not in self.orig_images:
            self.load_original_image(path)
        orig = self.orig_images.get(path)
        if not orig:
            return
        self.draw_on_canvas(self.orig_canvas, orig)
        try:
            w = int(self.width_var.get()); h = int(self.height_var.get())
        except Exception:
            self.log("プレビュー更新: 幅/高さが整数ではありません。プレビューを更新できません。")
            return
        resized = resize_pad(orig, w, h, self.bg, log_func=self.log)
        self.draw_on_canvas(self.resized_canvas, resized)

    def draw_on_canvas(self, canvas, pil_img):
        canvas_w = int(canvas['width'])
        canvas_h = int(canvas['height'])
        tkimg = pil_image_to_tk(pil_img, canvas_w - 4, canvas_h - 4)
        if tkimg is None:
            canvas.delete('all'); return
        canvas.image_ref = tkimg
        canvas.delete('all')
        x = (canvas_w - tkimg.width()) // 2
        y = (canvas_h - tkimg.height()) // 2
        canvas.create_image(x, y, anchor='nw', image=tkimg)

    # dimension sync
    def on_dim_change(self, which):
        if self.updating_dim:
            return
        if not self.aspect_var.get():
            self.update_preview()
            return
        if self.current_index is None:
            return
        path = self.files[self.current_index]
        im = self.orig_images.get(path)
        if not im:
            return
        ow, oh = im.size
        try:
            self.updating_dim = True
            if which == 'w':
                val = self.width_var.get()
                if not val:
                    return
                w = int(val)
                h = max(1, int(round(w * (oh / ow))))
                self.height_var.set(str(h))
            else:
                val = self.height_var.get()
                if not val:
                    return
                h = int(val)
                w = max(1, int(round(h * (ow / oh))))
                self.width_var.set(str(w))
        except Exception:
            pass
        finally:
            self.updating_dim = False
            self.update_preview()

    # run / save
    def pick_output_folder(self):
        folder = filedialog.askdirectory(title="出力フォルダを選択")
        if folder:
            self.out_var.set(folder)

    def run_resize(self):
        files = list(self.files)
        if not files:
            messagebox.showinfo("情報", "まず画像を追加してください")
            return
        out_folder = self.out_var.get() or os.path.join(os.getcwd(), "output")
        os.makedirs(out_folder, exist_ok=True)
        try:
            w = int(self.width_var.get()); h = int(self.height_var.get())
        except Exception:
            messagebox.showerror("入力エラー", "幅と高さには整数を入力してください")
            return
        success = 0
        for p in files:
            try:
                outp = process_static_file(p, out_folder, w, h, mode='pad', bg_color=self.bg, log_func=self.log)
                self.log(f"出力: {outp}")
                success += 1
            except Exception as e:
                self.log(f"エラー: {p} -> {e}")
        messagebox.showinfo("完了", f"{success} / {len(files)} 件処理しました\n出力フォルダ:\n{out_folder}")

    # size popup
    def open_size_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("サイズ変更")
        popup.transient(self.root)
        popup.resizable(False, False)

        frm = ttk.Frame(popup, padding=10)
        frm.pack(fill='both', expand=True)

        ttk.Label(frm, text="幅").grid(row=0, column=0, sticky='e', padx=(0,6))
        w_var = tk.StringVar(value=self.width_var.get())
        w_entry = ttk.Entry(frm, textvariable=w_var, width=12)
        w_entry.grid(row=0, column=1, sticky='w')

        ttk.Label(frm, text="高さ").grid(row=1, column=0, sticky='e', padx=(0,6))
        h_var = tk.StringVar(value=self.height_var.get())
        h_entry = ttk.Entry(frm, textvariable=h_var, width=12)
        h_entry.grid(row=1, column=1, sticky='w')

        def local_on_w(*a):
            if self.aspect_var.get():
                try:
                    new_w = int(w_var.get())
                    if self.current_index is not None and self.files:
                        path = self.files[self.current_index]
                        im = self.orig_images.get(path)
                        if im:
                            ow, oh = im.size
                            new_h = max(1, int(round(new_w * (oh / ow))))
                            h_var.set(str(new_h))
                except Exception:
                    pass

        def local_on_h(*a):
            if self.aspect_var.get():
                try:
                    new_h = int(h_var.get())
                    if self.current_index is not None and self.files:
                        path = self.files[self.current_index]
                        im = self.orig_images.get(path)
                        if im:
                            ow, oh = im.size
                            new_w = max(1, int(round(new_h * (ow / oh))))
                            w_var.set(str(new_w))
                except Exception:
                    pass

        w_var.trace_add('write', lambda *a: local_on_w())
        h_var.trace_add('write', lambda *a: local_on_h())

        btn_fr = ttk.Frame(frm)
        btn_fr.grid(row=2, column=0, columnspan=2, pady=(10,0))

        def on_ok():
            try:
                new_w = int(w_var.get()); new_h = int(h_var.get())
            except Exception:
                messagebox.showerror("入力エラー", "幅と高さには整数を入力してください", parent=popup)
                return
            self.width_var.set(str(new_w))
            self.height_var.set(str(new_h))
            self.update_preview()
            popup.destroy()

        def on_cancel():
            popup.destroy()

        ttk.Button(btn_fr, text="OK", command=on_ok).pack(side='left', padx=6)
        ttk.Button(btn_fr, text="キャンセル", command=on_cancel).pack(side='left', padx=6)

        w_entry.focus_set()
        popup.grab_set()
        popup.wait_window()

    def log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)

    def clear_canvases(self):
        self.orig_canvas.delete('all')
        self.resized_canvas.delete('all')
        self.orig_canvas.image_ref = None
        self.resized_canvas.image_ref = None

# Entrypoint
def main():
    if DND_AVAILABLE:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    app = ImgResizerApp(root)
    root.geometry("1200x675")
    root.minsize(900, 500)
    root.mainloop()

if __name__ == "__main__":
    main()
