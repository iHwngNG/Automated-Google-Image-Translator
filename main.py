import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import asyncio
import os
import datetime
import json

from browser_manager import BrowserManager
from translator import process_images

# Thêm nhiều ngôn ngữ có thể sử dụng (theo mã của Google Translate)
LANGUAGES = {
    "English": "en",
    "Vietnamese": "vi",
    "Japanese": "ja",
    "Korean": "ko",
    "Chinese (Simplified)": "zh-CN",
    "Chinese (Traditional)": "zh-TW",
    "French": "fr",
    "Spanish": "es"
}

class ImageTranslatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Automation Google Image Translate CDP")
        self.geometry("650x650")
        self.resizable(False, False)
        
        # Configure grid weight
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        style = ttk.Style(self)
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass # Fallback to default
            
        self.browser_manager = BrowserManager()
        self.running = False
        self.app_state = {"pause": False, "stop": False}
        self.log_counter = 1
        
        self.create_widgets()
        self.load_settings()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.log_to_file("Khởi động ứng dụng UI thành công.")
        
    def create_widgets(self):
        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.src_lang = tk.StringVar(value="en")
        self.tgt_lang = tk.StringVar(value="vi")
        self.concurrency = tk.IntVar(value=3)
        self.delete_input_var = tk.BooleanVar(value=False)
        
        main_frame = ttk.Frame(self, padding=15)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(1, weight=1)
        
        # Thư mục đầu vào
        ttk.Label(main_frame, text="Input Folder:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(main_frame, textvariable=self.input_folder).grid(row=0, column=1, sticky="ew", padx=5)
        # Thư mục đầu ra
        ttk.Label(main_frame, text="Output Folder:").grid(row=1, column=0, sticky="w", pady=5)
        self.out_entry = ttk.Entry(main_frame, textvariable=self.output_folder)
        self.out_entry.grid(row=1, column=1, sticky="ew", padx=5)
        self.out_btn = ttk.Button(main_frame, text="Browser...", command=lambda: self.select_folder(self.output_folder))
        self.out_btn.grid(row=1, column=2)

        self.use_default_output = tk.BooleanVar(value=True)
        ttk.Checkbutton(main_frame, text="Tạo Output tự động theo thư mục Input", variable=self.use_default_output, command=self.toggle_output_state).grid(row=2, column=1, sticky="w", pady=2)
        
        # Ngôn ngữ nguồn
        ttk.Label(main_frame, text="Source Language:").grid(row=3, column=0, sticky="w", pady=5)
        cb_src = ttk.Combobox(main_frame, textvariable=self.src_lang, values=list(LANGUAGES.values()), state="readonly")
        cb_src.grid(row=3, column=1, columnspan=2, sticky="ew", padx=5)
        
        # Ngôn ngữ đích
        ttk.Label(main_frame, text="Target Language:").grid(row=4, column=0, sticky="w", pady=5)
        cb_tgt = ttk.Combobox(main_frame, textvariable=self.tgt_lang, values=list(LANGUAGES.values()), state="readonly")
        cb_tgt.grid(row=4, column=1, columnspan=2, sticky="ew", padx=5)
        
        # Concurrency
        ttk.Label(main_frame, text="Tabs song song:").grid(row=5, column=0, sticky="w", pady=5)
        ttk.Spinbox(main_frame, from_=1, to=20, textvariable=self.concurrency, width=10).grid(row=5, column=1, sticky="w", padx=5)
        
        # Xóa input
        ttk.Checkbutton(main_frame, text="Delete Input Folder after completion", variable=self.delete_input_var).grid(row=6, column=0, columnspan=2, sticky="w", pady=10)
        
        # Nút Run, Pause, Stop
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=7, column=0, columnspan=3, pady=15, sticky="ew")
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        btn_frame.columnconfigure(2, weight=1)
        
        self.btn_start = ttk.Button(btn_frame, text="START TRANSLATION", command=self.start_translation)
        self.btn_start.grid(row=0, column=0, ipady=8, sticky="ew", padx=2)
        
        self.btn_pause = ttk.Button(btn_frame, text="TẠM NGƯNG", command=self.pause_translation, state="disabled")
        self.btn_pause.grid(row=0, column=1, ipady=8, sticky="ew", padx=2)
        
        self.btn_stop = ttk.Button(btn_frame, text="NGƯNG HOÀN TOÀN", command=self.stop_translation, state="disabled")
        self.btn_stop.grid(row=0, column=2, ipady=8, sticky="ew", padx=2)
        
        # Log view
        ttk.Label(main_frame, text="System Logs:").grid(row=8, column=0, sticky="w")
        self.log_area = scrolledtext.ScrolledText(main_frame, height=15, state='disabled', bg="#1e1e1e", fg="#00ff00", font=("Consolas", 10))
        self.log_area.grid(row=9, column=0, columnspan=3, sticky="nsew", pady=5)
        main_frame.rowconfigure(9, weight=1)

        self.toggle_output_state()
        
    def toggle_output_state(self):
        if self.use_default_output.get():
            self.out_entry.config(state='disabled')
            self.out_btn.config(state='disabled')
        else:
            self.out_entry.config(state='normal')
            self.out_btn.config(state='normal')
        
    def load_settings(self):
        settings_file = "settings.json"
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    self.input_folder.set(settings.get("input_folder", ""))
                    self.output_folder.set(settings.get("output_folder", ""))
                    self.src_lang.set(settings.get("src_lang", "en"))
                    self.tgt_lang.set(settings.get("tgt_lang", "vi"))
                    self.concurrency.set(settings.get("concurrency", 3))
                    self.delete_input_var.set(settings.get("delete_input", False))
                    self.use_default_output.set(settings.get("default_output", True))
                    self.toggle_output_state()
            except Exception:
                pass

    def on_closing(self):
        settings_file = "settings.json"
        settings = {
            "input_folder": self.input_folder.get(),
            "output_folder": self.output_folder.get(),
            "src_lang": self.src_lang.get(),
            "tgt_lang": self.tgt_lang.get(),
            "concurrency": self.concurrency.get(),
            "delete_input": self.delete_input_var.get(),
            "default_output": self.use_default_output.get()
        }
        try:
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
        except Exception:
            pass
        self.destroy()

    def select_folder(self, var):
        folder = filedialog.askdirectory()
        if folder:
            var.set(folder)
            
    def log(self, message):
        """Hiển thị log ra màn hình và ghi vào file docs/logs.md."""
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')
        self.log_to_file(message)
        
    def log_to_file(self, message):
        """Tuân thủ rule 3: ghi chú vào logs.md với ID, datetime rõ ràng."""
        now = datetime.datetime.now()
        date_str = now.strftime("%d/%m/%Y")
        time_str = now.strftime("%I:%M:%S %p")
        log_entry = f"{self.log_counter} - {time_str} - {date_str}: {message}\n"
        
        try:
            os.makedirs("docs", exist_ok=True)
            with open("docs/logs.md", "a", encoding="utf-8") as f:
                f.write(log_entry)
            self.log_counter += 1
        except Exception:
            pass
            
    def log_error_to_file(self, error_name, target, error_type, fix):
        """Tuân thủ rule 4: Lỗi cấu trúc chuẩn."""
        log_entry = f"**Lỗi**: {error_name}\n- **Đối tượng**: {target}\n- **Loại error**: {error_type}\n- **Cách debug**: {fix}\n\n"
        try:
            os.makedirs("docs", exist_ok=True)
            with open("docs/error_debugging_logs.md", "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception:
            pass

    def start_translation(self):
        if self.running: return
        
        inp = self.input_folder.get()
        
        if not inp or not os.path.exists(inp):
            messagebox.showerror("Lỗi", "Thư mục đầu vào không tồn tại!")
            return
            
        if self.use_default_output.get():
            base_name = os.path.basename(os.path.normpath(inp))
            lang = self.tgt_lang.get()
            out = os.path.join(os.getcwd(), "outputs", f"{base_name}_translated_{lang}")
            os.makedirs(out, exist_ok=True)
            self.output_folder.set(out)
        else:
            out = self.output_folder.get()
            if not out:
                messagebox.showerror("Lỗi", "Vui lòng chọn thư mục đầu ra!")
                return
            
        self.running = True
        self.app_state["pause"] = False
        self.app_state["stop"] = False
        self.btn_start.config(state='disabled', text="TRANSLATING...")
        self.btn_pause.config(state='normal', text="TẠM NGƯNG")
        self.btn_stop.config(state='normal')
        self.log("Đã bấm nút Start, chuẩn bị chạy luồng chuyển đổi hình ảnh.")
        
        # Start a background thread so UI doesn't freeze
        threading.Thread(target=self.run_asyncio_loop, daemon=True).start()
        
    def run_asyncio_loop(self):
        ws_url = None
        try:
            self.after(0, lambda: self.log("Call BrowserManager: Khởi chạy Chrome trong môi trường CDP profile ẩn danh..."))
            ws_url = self.browser_manager.start_chrome()
            self.after(0, lambda: self.log(f"Trình duyệt đã khởi chạy xong. CDP WS: {ws_url}"))
        except Exception as e:
            self.log_error_to_file("Lỗi khởi chạy Chrome", "BrowserManager.start_chrome", type(e).__name__, "Kiểm tra quyền truy cập vào Chrome, hoặc xem có tiến trình Chrome chết chặn cổng 9222 không.")
            self.after(0, lambda: self.log(f"Lỗi khởi động Chrome: {e}"))
            self.reset_ui()
            return
            
        def safe_log(msg):
            self.after(0, lambda: self.log(msg))
            
        try:
            asyncio.run(process_images(
                ws_url=ws_url,
                input_folder=self.input_folder.get(),
                output_folder=self.output_folder.get(),
                sl=self.src_lang.get(),
                tl=self.tgt_lang.get(),
                concurrency=self.concurrency.get(),
                delete_input=self.delete_input_var.get(),
                log_callback=safe_log,
                app_state=self.app_state
            ))
        except Exception as e:
            self.log_error_to_file("Lỗi tiến trình Async", "asyncio.run", type(e).__name__, "Kiểm tra syntax lỗi unhandled trong worker hoặc Playwright crash.")
            self.after(0, lambda: self.log(f"Tiến trình lỗi: {str(e)}"))
        finally:
            self.after(0, lambda: self.log("Đang đóng trình duyệt do hệ thống đã hoàn thành hoặc lỗi..."))
            self.browser_manager.stop_chrome()
            self.after(0, lambda: self.log("Trình duyệt đã được đóng an toàn."))
            self.reset_ui()

    def pause_translation(self):
        if not self.running: return
        self.app_state["pause"] = not self.app_state["pause"]
        if self.app_state["pause"]:
            self.btn_pause.config(text="TIẾP TỤC (RESUME)")
            self.log("Đã lệnh TẠM NGƯNG... (ảnh đang dịch dở sẽ đợt hoàn thành xong và tạm dừng nhận ảnh mới).")
        else:
            self.btn_pause.config(text="TẠM NGƯNG")
            self.log("Đã lệnh TIẾP TỤC phân phát dịch.")

    def stop_translation(self):
        if not self.running: return
        self.app_state["stop"] = True
        self.btn_pause.config(state='disabled')
        self.btn_stop.config(state='disabled')
        self.log("Đã lệnh DỪNG HOÀN TOÀN... (Ép đóng Chrome ngay lập tức).")
        self.browser_manager.stop_chrome()

    def reset_ui(self):
        self.running = False
        self.after(0, lambda: self.btn_start.config(state='normal', text="START TRANSLATION"))
        self.after(0, lambda: self.btn_pause.config(state='disabled', text="TẠM NGƯNG"))
        self.after(0, lambda: self.btn_stop.config(state='disabled'))

if __name__ == "__main__":
    app = ImageTranslatorApp()
    app.mainloop()
