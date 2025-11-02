# app.py
import os
import io
import sys
import pathlib
import PySimpleGUI as sg
from PIL import Image, ImageSequence
import imageio
import cairosvg

# 画像処理ユーティリティ
def rasterize_svg_to_png_bytes(svg_path, out_w=None, out_h=None):
    # CairoSVG を使って SVG を PNG のバイト列に変換
    return cairosvg.svg2png(url=svg_path, output_width=out_w, output_height=out_h)

def resize_static_image_pil(img, w, h, mode='stretch', bg=(255,255,255,255)):
    w, h = int(w), int(h)
    if mode == 'stretch':
        return img.resize((w,h), Image.LANCZOS)
    if mode == 'fit':
        im = img.copy()
        im.thumbnail((w,h), Image.LANCZOS)
        return im
    if mode == 'pad':
        im = img.copy().convert('RGBA')
        im.thumbnail((w,h), Image.LANCZOS)
        canvas = Image.new('RGBA', (w,h), bg)
        x = (w - im.width)//2
        y = (h - im.height)//2
        canvas.paste(im, (x,y), im)
        return canvas
    if mode == 'fill':
        ow,oh = img.size
        ratio = max(w/ow, h/oh)
        nw,nh = int(ow*ratio), int(oh*ratio)
        im2 = img.resize((nw,nh), Image.LANCZOS)
        left = (nw - w)//2
        top = (nh - h)//2
        return im2.crop((left, top, left + w, top + h))
    return img

def process_file(in_path, out_folder, width, height, mode, bg_color, jpeg_quality=85):
    ext = pathlib.Path(in_path).suffix.lower()
    name = pathlib.Path(in_path).stem
    if ext == '.svg':
        png_bytes = rasterize_svg_to_png_bytes(in_path)
        im = Image.open(io.BytesIO(png_bytes)).convert('RGBA')
        out_img = resize_static_image_pil(im, width, height, mode, bg_color)
        out_path = os.path.join(out_folder, f"{name}.png")
        out_img.save(out_path, format='PNG')
        return out_path
    elif ext in ('.gif',):
        # アニメ GIF をフレームごとに処理して出力
        im = Image.open(in_path)
        frames = []
        durations = []
        for frame in ImageSequence.Iterator(im):
            frame = frame.convert('RGBA')
            out_frame = resize_static_image_pil(frame, width, height, mode, bg_color)
            # imageio expects ndarray or save with PIL converting to P mode for GIF
            frames.append(out_frame.convert('P', palette=Image.ADAPTIVE))
            durations.append(frame.info.get('duration', 100))
        out_path = os.path.join(out_folder, f"{name}.gif")
        frames[0].save(out_path, save_all=True, append_images=frames[1:], duration=durations, loop=im.info.get('loop',0), optimize=True)
        return out_path
    else:
        im = Image.open(in_path)
        out_img = resize_static_image_pil(im.convert('RGBA'), width, height, mode, bg_color)
        out_ext = ext if ext in ('.png', '.jpg', '.jpeg') else '.png'
        out_path = os.path.join(out_folder, f"{name}{out_ext}")
        if out_ext in ('.jpg', '.jpeg'):
            out_img = out_img.convert('RGB')
            out_img.save(out_path, format='JPEG', quality=jpeg_quality)
        else:
            out_img.save(out_path, format='PNG')
        return out_path

# GUI レイアウト
sg.theme('SystemDefault')
file_list_column = [
    [sg.Text('ドロップまたは追加')],
    [sg.Listbox(values=[], enable_events=True, size=(60,8), key='-FILES-')],
    [sg.Button('追加', key='-ADD-'), sg.Button('クリア', key='-CLEAR-')]
]

options_column = [
    [sg.Text('出力フォルダ'), sg.Input(default_text=os.path.join(os.getcwd(),'output'), key='-OUT-'), sg.FolderBrowse()],
    [sg.Text('幅'), sg.Input('800', size=(6,1), key='-W-'), sg.Text('高さ'), sg.Input('600', size=(6,1), key='-H-')],
    [sg.Text('モード'), sg.Combo(['stretch','fit','pad','fill'], default_value='pad', key='-MODE-')],
    [sg.Text('背景色（R,G,B）'), sg.Input('255,255,255', size=(12,1), key='-BG-')],
    [sg.Button('開始', key='-RUN-'), sg.Button('終了')]
]

log_column = [
    [sg.Text('ログ')],
    [sg.MLine('', size=(80,10), key='-LOG-')]
]

layout = [
    [sg.Column(file_list_column), sg.VSeperator(), sg.Column(options_column)],
    [sg.HorizontalSeparator()],
    [sg.Column(log_column)]
]

window = sg.Window('Img Resizer', layout, finalize=True)

# ドラッグ＆ドロップ設定（Windows で動作）
# PySimpleGUI の Listbox に DnD を直接は出来ないので「追加」ボタンのファイル選択を主に使う
while True:
    event, values = window.read()
    if event in (sg.WIN_CLOSED, '終了'):
        break
    if event == '-ADD-':
        files = sg.popup_get_file('ファイルを選択', multiple_files=True, file_types=(("Images","*.png;*.jpg;*.jpeg;*.gif;*.svg"),))
        if files:
            files = files.split(';')
            cur = list(window['-FILES-'].get())
            cur.extend(files)
            window['-FILES-'].update(cur)
    if event == '-CLEAR-':
        window['-FILES-'].update([])
    if event == '-RUN-':
        file_items = list(values['-FILES-'])
        out_folder = values['-OUT-'] or os.path.join(os.getcwd(),'output')
        os.makedirs(out_folder, exist_ok=True)
        try:
            w = int(values['-W-']); h = int(values['-H-'])
        except Exception:
            sg.popup('幅と高さには整数を入力してください')
            continue
        mode = values['-MODE-']
        bg = tuple(int(x.strip()) for x in values['-BG-'].split(','))
        for f in file_items:
            try:
                window['-LOG-'].print(f'処理中: {f}')
                outp = process_file(f, out_folder, w, h, mode, bg)
                window['-LOG-'].print(f'出力: {outp}')
            except Exception as e:
                window['-LOG-'].print(f'エラー: {f} -> {e}')
        sg.popup('処理完了')
window.close()
