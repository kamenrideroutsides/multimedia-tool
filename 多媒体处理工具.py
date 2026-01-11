#!/usr/bin/env python3
"""
全能媒体工具箱
- 视频抽帧、MP4转MP3、MP4转GIF
- 图片格式转换、网格裁剪、合成GIF
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image
import cv2
import os
import threading
import subprocess
import shutil


class MediaToolbox:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("全能媒体工具箱")
        self.window.geometry("650x500")

        # 调试开关：若你仍觉得“浏览没反应”，改成 True 看终端输出
        self.debug = False

        # 创建标签页
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # 各功能页面
        self.create_frame_extract_tab()    # 视频抽帧
        self.create_video_convert_tab()    # 视频转换
        self.create_image_convert_tab()    # 图片格式转换
        self.create_grid_crop_tab()        # 网格裁剪
        self.create_gif_maker_tab()        # 图片合成GIF

    # ================== 视频抽帧 ==================
    def create_frame_extract_tab(self):
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="视频抽帧")

        ttk.Label(tab, text="视频文件:").grid(row=0, column=0, sticky="w", pady=5)
        self.extract_video_path = tk.StringVar()
        ttk.Entry(tab, textvariable=self.extract_video_path, width=45).grid(row=0, column=1, pady=5)
        ttk.Button(tab, text="浏览", command=lambda: self.browse_file(
            self.extract_video_path, [("视频文件", "*.mp4 *.avi *.mkv *.mov *.wmv")]
        )).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(tab, text="输出目录:").grid(row=1, column=0, sticky="w", pady=5)
        self.extract_output_dir = tk.StringVar()
        ttk.Entry(tab, textvariable=self.extract_output_dir, width=45).grid(row=1, column=1, pady=5)
        ttk.Button(tab, text="浏览", command=lambda: self.browse_dir(self.extract_output_dir)).grid(row=1, column=2, padx=5, pady=5)

        ttk.Label(tab, text="抽取数量:").grid(row=2, column=0, sticky="w", pady=5)
        self.extract_count = tk.StringVar(value="100")
        ttk.Entry(tab, textvariable=self.extract_count, width=10).grid(row=2, column=1, sticky="w", pady=5)

        ttk.Label(tab, text="输出格式:").grid(row=3, column=0, sticky="w", pady=5)
        self.extract_format = tk.StringVar(value="jpg")
        format_frame = ttk.Frame(tab)
        format_frame.grid(row=3, column=1, sticky="w", pady=5)
        for fmt in ["jpg", "png", "jpeg"]:
            ttk.Radiobutton(format_frame, text=fmt.upper(), variable=self.extract_format, value=fmt).pack(side="left", padx=10)

        self.extract_progress = ttk.Progressbar(tab, length=400, mode="determinate")
        self.extract_progress.grid(row=4, column=0, columnspan=3, pady=15)

        self.extract_status = tk.StringVar(value="就绪")
        ttk.Label(tab, textvariable=self.extract_status).grid(row=5, column=0, columnspan=3)

        ttk.Button(tab, text="开始抽帧", command=self.start_extract_frames).grid(row=6, column=0, columnspan=3, pady=15)

    def start_extract_frames(self):
        video_path = self.extract_video_path.get().strip()
        output_dir = self.extract_output_dir.get().strip()

        if not video_path or not os.path.exists(video_path):
            messagebox.showerror("错误", "请选择有效的视频文件")
            return
        if not output_dir:
            messagebox.showerror("错误", "请选择输出目录")
            return

        try:
            count = int(self.extract_count.get())
            if count <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("错误", "请输入有效的抽帧数量")
            return

        os.makedirs(output_dir, exist_ok=True)
        threading.Thread(target=self.extract_frames_thread, args=(video_path, output_dir, count), daemon=True).start()

    def extract_frames_thread(self, video_path, output_dir, count):
        try:
            cap = cv2.VideoCapture(video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            if total_frames <= 0:
                raise Exception("无法读取视频帧数，请确认视频文件是否损坏或编码不受支持")

            if count > total_frames:
                count = total_frames

            indices = [int(i * total_frames / count) for i in range(count)]
            fmt = self.extract_format.get().strip().lower()
            video_name = os.path.splitext(os.path.basename(video_path))[0]

            for i, frame_idx in enumerate(indices):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if ret:
                    output_path = os.path.join(output_dir, f"{video_name}_{i+1:04d}.{fmt}")
                    cv2.imwrite(output_path, frame)

                progress = (i + 1) / count * 100
                self.extract_progress["value"] = progress
                self.extract_status.set(f"处理中: {i+1}/{count}")
                self.window.update_idletasks()

            cap.release()
            self.extract_status.set("完成!")
            messagebox.showinfo("完成", f"成功抽取 {count} 帧到：\n{output_dir}")
        except Exception as e:
            self.extract_status.set("出错了")
            messagebox.showerror("错误", str(e))

    # ================== 视频转换 ==================
    def create_video_convert_tab(self):
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="视频转换")

        ttk.Label(tab, text="视频文件:").grid(row=0, column=0, sticky="w", pady=5)
        self.convert_video_path = tk.StringVar()
        ttk.Entry(tab, textvariable=self.convert_video_path, width=45).grid(row=0, column=1, pady=5)
        ttk.Button(tab, text="浏览", command=lambda: self.browse_file(
            self.convert_video_path, [("视频文件", "*.mp4 *.avi *.mkv *.mov *.wmv")]
        )).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(tab, text="输出目录:").grid(row=1, column=0, sticky="w", pady=5)
        self.convert_output_dir = tk.StringVar()
        ttk.Entry(tab, textvariable=self.convert_output_dir, width=45).grid(row=1, column=1, pady=5)
        ttk.Button(tab, text="浏览", command=lambda: self.browse_dir(self.convert_output_dir)).grid(row=1, column=2, padx=5, pady=5)

        ttk.Label(tab, text="转换为：").grid(row=2, column=0, sticky="w", pady=5)
        self.convert_type = tk.StringVar(value="mp3")
        type_frame = ttk.Frame(tab)
        type_frame.grid(row=2, column=1, sticky="w", pady=5)
        ttk.Radiobutton(type_frame, text="MP3 (提取音频)", variable=self.convert_type, value="mp3").pack(anchor="w")
        ttk.Radiobutton(type_frame, text="GIF (转动图)", variable=self.convert_type, value="gif").pack(anchor="w")

        gif_frame = ttk.LabelFrame(tab, text="GIF设置", padding=10)
        gif_frame.grid(row=3, column=0, columnspan=3, sticky="ew", pady=10)

        ttk.Label(gif_frame, text="帧率(FPS):").grid(row=0, column=0, padx=5)
        self.gif_fps = tk.StringVar(value="10")
        ttk.Entry(gif_frame, textvariable=self.gif_fps, width=8).grid(row=0, column=1, padx=5)

        ttk.Label(gif_frame, text="缩放比例:").grid(row=0, column=2, padx=5)
        self.gif_scale = tk.StringVar(value="0.5")
        ttk.Entry(gif_frame, textvariable=self.gif_scale, width=8).grid(row=0, column=3, padx=5)

        self.convert_progress = ttk.Progressbar(tab, length=400, mode="indeterminate")
        self.convert_progress.grid(row=4, column=0, columnspan=3, pady=15)

        self.convert_status = tk.StringVar(value="就绪")
        ttk.Label(tab, textvariable=self.convert_status).grid(row=5, column=0, columnspan=3)

        ttk.Button(tab, text="开始转换", command=self.start_video_convert).grid(row=6, column=0, columnspan=3, pady=15)

    def start_video_convert(self):
        video_path = self.convert_video_path.get().strip()
        output_dir = self.convert_output_dir.get().strip()

        if not video_path or not os.path.exists(video_path):
            messagebox.showerror("错误", "请选择有效的视频文件")
            return
        if not output_dir:
            messagebox.showerror("错误", "请选择输出目录")
            return

        os.makedirs(output_dir, exist_ok=True)
        self.convert_progress.start()
        threading.Thread(target=self.video_convert_thread, args=(video_path, output_dir), daemon=True).start()

    def video_convert_thread(self, video_path, output_dir):
        try:
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            convert_type = self.convert_type.get().strip().lower()

            if convert_type == "mp3":
                output_path = os.path.join(output_dir, f"{video_name}.mp3")
                self.convert_status.set("正在提取音频...")

                # 优先 moviepy，失败再 ffmpeg
                try:
                    from moviepy.editor import VideoFileClip
                    video = VideoFileClip(video_path)
                    if video.audio is None:
                        video.close()
                        raise Exception("该视频没有音轨，无法导出 MP3")
                    video.audio.write_audiofile(output_path)
                    video.close()
                except ImportError:
                    if shutil.which("ffmpeg"):
                        cmd = [
                            "ffmpeg", "-y",
                            "-i", video_path,
                            "-vn",
                            "-acodec", "libmp3lame",
                            "-q:a", "2",
                            output_path
                        ]
                        p = subprocess.run(cmd, capture_output=True, text=True)
                        if p.returncode != 0:
                            raise Exception(p.stderr.strip() or "ffmpeg 转换失败")
                    else:
                        raise Exception("请安装 moviepy: pip install moviepy  或者安装 ffmpeg 并加入 PATH")

            elif convert_type == "gif":
                output_path = os.path.join(output_dir, f"{video_name}.gif")
                self.convert_status.set("正在转换为GIF...")

                try:
                    fps = int(self.gif_fps.get())
                    if fps <= 0:
                        raise ValueError
                except ValueError:
                    raise Exception("FPS 必须是正整数")

                try:
                    scale = float(self.gif_scale.get())
                    if scale <= 0:
                        raise ValueError
                except ValueError:
                    raise Exception("缩放比例必须是大于 0 的数字（例如 0.5）")

                cap = cv2.VideoCapture(video_path)
                if not cap.isOpened():
                    raise Exception("无法打开视频文件")

                original_fps = cap.get(cv2.CAP_PROP_FPS)
                if original_fps is None or original_fps <= 0:
                    original_fps = fps  # 取不到就用目标 fps 兜底

                step = max(1, int(round(original_fps / fps)))

                frames = []
                idx = 0
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break

                    # 按步长采样，避免全部读入
                    if idx % step != 0:
                        idx += 1
                        continue
                    idx += 1

                    if scale != 1.0:
                        h, w = frame.shape[:2]
                        new_w = max(1, int(w * scale))
                        new_h = max(1, int(h * scale))
                        frame = cv2.resize(frame, (new_w, new_h))

                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frames.append(Image.fromarray(frame_rgb))

                cap.release()

                if not frames:
                    raise Exception("没有读取到任何帧，无法生成 GIF")

                duration_ms = max(1, int(1000 / fps))
                frames[0].save(
                    output_path,
                    save_all=True,
                    append_images=frames[1:],
                    duration=duration_ms,
                    loop=0,
                    format="GIF"
                )

            else:
                raise Exception("未知转换类型")

            self.convert_progress.stop()
            self.convert_status.set("完成!")
            messagebox.showinfo("完成", f"转换完成:\n{output_path}")

        except Exception as e:
            self.convert_progress.stop()
            self.convert_status.set("出错了")
            messagebox.showerror("错误", str(e))

    # ================== 图片格式转换 ==================
    def create_image_convert_tab(self):
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="图片转换")

        ttk.Label(tab, text="选择图片 (可多选):").pack(anchor="w")

        list_frame = ttk.Frame(tab)
        list_frame.pack(fill="both", expand=True, pady=5)

        self.image_listbox = tk.Listbox(list_frame, height=8, selectmode="extended")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.image_listbox.yview)
        self.image_listbox.configure(yscrollcommand=scrollbar.set)
        self.image_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.image_files = []

        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="添加图片", command=self.add_images).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="清空列表", command=self.clear_images).pack(side="left", padx=5)

        dir_frame = ttk.Frame(tab)
        dir_frame.pack(fill="x", pady=5)
        ttk.Label(dir_frame, text="输出目录:").pack(side="left")
        self.img_convert_output = tk.StringVar()
        ttk.Entry(dir_frame, textvariable=self.img_convert_output, width=35).pack(side="left", padx=5)
        ttk.Button(dir_frame, text="浏览", command=lambda: self.browse_dir(self.img_convert_output)).pack(side="left")

        fmt_frame = ttk.Frame(tab)
        fmt_frame.pack(fill="x", pady=5)
        ttk.Label(fmt_frame, text="转换为：").pack(side="left")
        self.img_output_format = tk.StringVar(value="png")
        for fmt in ["png", "jpg", "jpeg", "bmp", "webp"]:
            ttk.Radiobutton(fmt_frame, text=fmt.upper(), variable=self.img_output_format, value=fmt).pack(side="left", padx=8)

        ttk.Button(tab, text="开始转换", command=self.convert_images).pack(pady=15)

    def add_images(self):
        files = filedialog.askopenfilenames(filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp *.webp *.gif")])
        for f in files:
            if f and f not in self.image_files:
                self.image_files.append(f)
                self.image_listbox.insert("end", os.path.basename(f))

    def clear_images(self):
        self.image_files.clear()
        self.image_listbox.delete(0, "end")

    def convert_images(self):
        if not self.image_files:
            messagebox.showerror("错误", "请先添加图片")
            return

        output_dir = self.img_convert_output.get().strip()
        if not output_dir:
            messagebox.showerror("错误", "请选择输出目录")
            return

        os.makedirs(output_dir, exist_ok=True)
        fmt = self.img_output_format.get().strip().lower()

        try:
            for img_path in self.image_files:
                img = Image.open(img_path)
                if img.mode == "RGBA" and fmt in ["jpg", "jpeg"]:
                    img = img.convert("RGB")

                name = os.path.splitext(os.path.basename(img_path))[0]
                output_path = os.path.join(output_dir, f"{name}.{fmt}")
                img.save(output_path)

            messagebox.showinfo("完成", f"成功转换 {len(self.image_files)} 张图片")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    # ================== 网格裁剪 ==================
    def create_grid_crop_tab(self):
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="网格裁剪")

        ttk.Label(tab, text="选择图片:").grid(row=0, column=0, sticky="w", pady=5)
        self.crop_image_path = tk.StringVar()
        ttk.Entry(tab, textvariable=self.crop_image_path, width=40).grid(row=0, column=1, pady=5)
        ttk.Button(tab, text="浏览", command=self.browse_crop_image).grid(row=0, column=2, padx=5, pady=5)

        self.crop_image_info = tk.StringVar(value="尺寸: 未选择")
        ttk.Label(tab, textvariable=self.crop_image_info).grid(row=1, column=0, columnspan=3, sticky="w", pady=5)

        grid_frame = ttk.LabelFrame(tab, text="网格设置", padding=10)
        grid_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=10)

        ttk.Label(grid_frame, text="横向切割数:").grid(row=0, column=0, padx=5, pady=5)
        self.crop_cols = tk.StringVar(value="4")
        ttk.Entry(grid_frame, textvariable=self.crop_cols, width=8).grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(grid_frame, text="纵向切割数:").grid(row=0, column=2, padx=5, pady=5)
        self.crop_rows = tk.StringVar(value="4")
        ttk.Entry(grid_frame, textvariable=self.crop_rows, width=8).grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(grid_frame, text="快捷预设:").grid(row=1, column=0, padx=5, pady=5)
        preset_frame = ttk.Frame(grid_frame)
        preset_frame.grid(row=1, column=1, columnspan=3, sticky="w", pady=5)

        ttk.Button(preset_frame, text="2x2", command=lambda: self.set_grid(2, 2)).pack(side="left", padx=3)
        ttk.Button(preset_frame, text="3x3", command=lambda: self.set_grid(3, 3)).pack(side="left", padx=3)
        ttk.Button(preset_frame, text="4x4", command=lambda: self.set_grid(4, 4)).pack(side="left", padx=3)
        ttk.Button(preset_frame, text="4x2", command=lambda: self.set_grid(4, 2)).pack(side="left", padx=3)
        ttk.Button(preset_frame, text="2x8", command=lambda: self.set_grid(2, 8)).pack(side="left", padx=3)

        ttk.Label(tab, text="输出目录:").grid(row=3, column=0, sticky="w", pady=5)
        self.crop_output_dir = tk.StringVar()
        ttk.Entry(tab, textvariable=self.crop_output_dir, width=40).grid(row=3, column=1, pady=5)
        ttk.Button(tab, text="浏览", command=lambda: self.browse_dir(self.crop_output_dir)).grid(row=3, column=2, padx=5, pady=5)

        ttk.Label(tab, text="输出格式:").grid(row=4, column=0, sticky="w", pady=5)
        self.crop_format = tk.StringVar(value="png")
        fmt_frame = ttk.Frame(tab)
        fmt_frame.grid(row=4, column=1, sticky="w", pady=5)
        for fmt in ["png", "jpg", "jpeg"]:
            ttk.Radiobutton(fmt_frame, text=fmt.upper(), variable=self.crop_format, value=fmt).pack(side="left", padx=8)

        ttk.Button(tab, text="开始裁剪", command=self.start_grid_crop).grid(row=5, column=0, columnspan=3, pady=20)

    def browse_crop_image(self):
        file = filedialog.askopenfilename(filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp *.webp")])
        if file:
            file = file.strip()
            self.crop_image_path.set(file)
            img = Image.open(file)
            self.crop_image_info.set(f"尺寸： {img.width} x {img.height}")

    def set_grid(self, cols, rows):
        self.crop_cols.set(str(cols))
        self.crop_rows.set(str(rows))

    def start_grid_crop(self):
        img_path = self.crop_image_path.get().strip()
        output_dir = self.crop_output_dir.get().strip()

        if not img_path or not os.path.exists(img_path):
            messagebox.showerror("错误", "请选择有效的图片")
            return
        if not output_dir:
            messagebox.showerror("错误", "请选择输出目录")
            return

        try:
            cols = int(self.crop_cols.get())
            rows = int(self.crop_rows.get())
            if cols <= 0 or rows <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("错误", "请输入有效的切割数量")
            return

        os.makedirs(output_dir, exist_ok=True)

        try:
            img = Image.open(img_path)
            w, h = img.size
            cell_w = w // cols
            cell_h = h // rows

            fmt = self.crop_format.get().strip().lower()
            name = os.path.splitext(os.path.basename(img_path))[0]

            count = 0
            for row in range(rows):
                for col in range(cols):
                    left = col * cell_w
                    top = row * cell_h
                    right = left + cell_w
                    bottom = top + cell_h

                    cell = img.crop((left, top, right, bottom))
                    if cell.mode == "RGBA" and fmt in ["jpg", "jpeg"]:
                        cell = cell.convert("RGB")

                    output_path = os.path.join(output_dir, f"{name}_{row+1:02d}_{col+1:02d}.{fmt}")
                    cell.save(output_path)
                    count += 1

            messagebox.showinfo("完成", f"成功裁剪为 {count} 张图片\n每张尺寸: {cell_w} x {cell_h}")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    # ================== 图片合成GIF ==================
    def create_gif_maker_tab(self):
        tab = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(tab, text="合成GIF")

        ttk.Label(tab, text="选择图片 (可多选，按顺序添加):").pack(anchor="w")

        list_frame = ttk.Frame(tab)
        list_frame.pack(fill="both", expand=True, pady=5)

        self.gif_listbox = tk.Listbox(list_frame, height=8, selectmode="extended")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.gif_listbox.yview)
        self.gif_listbox.configure(yscrollcommand=scrollbar.set)
        self.gif_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.gif_files = []

        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="添加图片", command=self.add_gif_images).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="上移", command=self.move_gif_up).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="下移", command=self.move_gif_down).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="清空", command=self.clear_gif_images).pack(side="left", padx=5)

        setting_frame = ttk.Frame(tab)
        setting_frame.pack(fill="x", pady=5)

        ttk.Label(setting_frame, text="帧间隔(毫秒):").pack(side="left")
        self.gif_duration = tk.StringVar(value="100")
        ttk.Entry(setting_frame, textvariable=self.gif_duration, width=8).pack(side="left", padx=5)

        self.gif_loop = tk.BooleanVar(value=True)
        ttk.Checkbutton(setting_frame, text="循环播放", variable=self.gif_loop).pack(side="left", padx=20)

        out_frame = ttk.Frame(tab)
        out_frame.pack(fill="x", pady=5)
        ttk.Label(out_frame, text="输出文件:").pack(side="left")
        self.gif_output_path = tk.StringVar()
        ttk.Entry(out_frame, textvariable=self.gif_output_path, width=35).pack(side="left", padx=5)
        ttk.Button(out_frame, text="浏览", command=self.browse_gif_output).pack(side="left")

        ttk.Button(tab, text="生成GIF", command=self.create_gif).pack(pady=15)

    def add_gif_images(self):
        files = filedialog.askopenfilenames(filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp *.webp")])
        for f in files:
            if f and f not in self.gif_files:
                self.gif_files.append(f)
                self.gif_listbox.insert("end", os.path.basename(f))

    def move_gif_up(self):
        selection = self.gif_listbox.curselection()
        if selection and selection[0] > 0:
            idx = selection[0]
            self.gif_files[idx], self.gif_files[idx - 1] = self.gif_files[idx - 1], self.gif_files[idx]
            self.refresh_gif_listbox()
            self.gif_listbox.selection_set(idx - 1)

    def move_gif_down(self):
        selection = self.gif_listbox.curselection()
        if selection and selection[0] < len(self.gif_files) - 1:
            idx = selection[0]
            self.gif_files[idx], self.gif_files[idx + 1] = self.gif_files[idx + 1], self.gif_files[idx]
            self.refresh_gif_listbox()
            self.gif_listbox.selection_set(idx + 1)

    def refresh_gif_listbox(self):
        self.gif_listbox.delete(0, "end")
        for f in self.gif_files:
            self.gif_listbox.insert("end", os.path.basename(f))

    def clear_gif_images(self):
        self.gif_files.clear()
        self.gif_listbox.delete(0, "end")

    def browse_gif_output(self):
        file = filedialog.asksaveasfilename(
            defaultextension=".gif",
            filetypes=[("GIF 文件", "*.gif"), ("所有文件", "*.*")]
        )
        if self.debug:
            print("asksaveasfilename returned:", repr(file))

        if file:
            file = file.strip()
            if not file.lower().endswith(".gif"):
                file += ".gif"
            self.gif_output_path.set(file)

    def create_gif(self):
        if not self.gif_files:
            messagebox.showerror("错误", "请先添加图片")
            return

        output_path = self.gif_output_path.get().strip()
        if not output_path:
            messagebox.showerror("错误", "请选择输出路径（需要是一个 .gif 文件名）")
            return

        if os.path.isdir(output_path):
            messagebox.showerror("错误", "输出路径是文件夹，请选择一个 .gif 文件名（例如：out.gif）")
            return

        if not output_path.lower().endswith(".gif"):
            output_path += ".gif"
            self.gif_output_path.set(output_path)

        try:
            duration = int(self.gif_duration.get())
            if duration <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("错误", "请输入有效的帧间隔（正整数，单位毫秒）")
            return

        try:
            images = []
            for f in self.gif_files:
                img = Image.open(f)
                if img.mode != "RGBA":
                    img = img.convert("RGBA")
                images.append(img)

            loop = 0 if self.gif_loop.get() else 1
            images[0].save(
                output_path,
                save_all=True,
                append_images=images[1:],
                duration=duration,
                loop=loop,
                format="GIF"
            )

            messagebox.showinfo("完成", f"GIF已生成:\n{output_path}")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    # ================== 通用方法 ==================
    def browse_file(self, var, filetypes):
        file = filedialog.askopenfilename(filetypes=filetypes)
        if file:
            var.set(file.strip())

    def browse_dir(self, var):
        dir_path = filedialog.askdirectory()
        if dir_path:
            var.set(dir_path.strip())

    def run(self):
        self.window.mainloop()


if __name__ == "__main__":
    app = MediaToolbox()
    app.run()
