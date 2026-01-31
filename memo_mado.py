import tkinter as tk
from tkinter import ttk
import json
import os
import webbrowser # URLを開くために必要

class MemoMadoKun:
    def __init__(self, root):
        self.root = root
        self.root.title("Memoまどくん")
        self.root.geometry("500x400")

        self.default_font = ("Meiryo UI", 10, "bold")
        
        # --- 設定値 ---
        self.is_topmost = False
        self.is_dark_mode = False
        self.save_file = "memo_data.json"
        self.alpha_val = 0.9
        
        # カラーパレット
        self.colors = {
            "light": {"bg": "#f4f4f4", "fg": "black", "entry_bg": "white", "entry_fg": "black", "btn_bg": "#e0e0e0"},
            "dark":  {"bg": "#2d2d2d", "fg": "#e0e0e0", "entry_bg": "#404040", "entry_fg": "#ffffff", "btn_bg": "#505050"}
        }

        self.root.attributes("-alpha", self.alpha_val)

        # --- UI構築 ---
        self.setup_ui()
        self.apply_theme() # 初期テーマ適用
        self.load_data()

    def setup_ui(self):
        """UIパーツの配置"""
        # 1. ヘッダー (操作パネル)
        self.header_frame = tk.Frame(self.root)
        self.header_frame.pack(fill="x", padx=10, pady=10)

        # 最前面ボタン
        self.pin_button = tk.Button(self.header_frame, text="📌", command=self.toggle_topmost, width=3,
                                    relief="solid", borderwidth=2, font=self.default_font)
        self.pin_button.pack(side="left")

        # ダークモード切替ボタン
        self.theme_button = tk.Button(self.header_frame, text="🌙", command=self.toggle_theme, width=3)
        self.theme_button.pack(side="left", padx=5)

        # 透明度スライダー
        tk.Label(self.header_frame, text="透明度:").pack(side="left", padx=(10, 0))
        self.alpha_scale = tk.Scale(self.header_frame, from_=0.3, to=1.0, resolution=0.05, orient="horizontal", showvalue=0, command=self.change_alpha)
        self.alpha_scale.set(self.alpha_val)
        self.alpha_scale.pack(side="left", fill="x", expand=True, padx=5)

        # 2. リストエリア (Canvas + Scrollbar)
        self.canvas_frame = tk.Frame(self.root)
        self.canvas_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.canvas = tk.Canvas(self.canvas_frame, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        
        self.scrollable_frame = tk.Frame(self.canvas)
        
        # スクロール設定
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", tags="inner_frame")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # リサイズ追従
        self.canvas.bind("<Configure>", self.on_canvas_configure)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # 3. 追加ボタン (リストの最後尾用エリア)
        # Note: 実際には scrollable_frame の一番下に配置します
        self.add_btn_frame = tk.Frame(self.scrollable_frame)
        self.add_btn_frame.pack(fill="x", pady=10)
        
        self.add_button = tk.Button(self.add_btn_frame, text="＋ 新しいメモを追加", command=self.add_new_row, height=2,
                                    relief="solid", borderwidth=2, font=self.default_font)
        self.add_button.pack(fill="x", padx=2)


    def on_canvas_configure(self, event):
        """ウィンドウ幅変更時にリスト幅を追従"""
        self.canvas.itemconfig("inner_frame", width=event.width)

    def change_alpha(self, value):
        """透明度変更"""
        self.root.attributes("-alpha", float(value))

    def toggle_topmost(self):
        """最前面固定切替"""
        self.is_topmost = not self.is_topmost
        self.root.attributes("-topmost", self.is_topmost)
        state = "ON" if self.is_topmost else "OFF"
        bg_color = "#ffecb3" if self.is_topmost else self.get_color("btn_bg")
        self.pin_button.config(bg=bg_color, relief="sunken" if self.is_topmost else "raised")

    def toggle_theme(self):
        """ダークモード切替"""
        self.is_dark_mode = not self.is_dark_mode
        self.theme_button.config(text="☀" if self.is_dark_mode else "🌙")
        self.apply_theme()

    def get_color(self, key):
        """現在のテーマの色を取得"""
        mode = "dark" if self.is_dark_mode else "light"
        return self.colors[mode][key]

    def apply_theme(self):
        """全体の色を更新"""
        c = self.get_color
        
        # 背景と文字色
        self.root.config(bg=c("bg"))
        self.header_frame.config(bg=c("bg"))
        self.canvas_frame.config(bg=c("bg"))
        self.canvas.config(bg=c("bg"))
        self.scrollable_frame.config(bg=c("bg"))
        self.add_btn_frame.config(bg=c("bg"))
        
        # ヘッダーパーツ
        label_fg = c("fg")
        for widget in self.header_frame.winfo_children():
            if isinstance(widget, tk.Label):
                widget.config(bg=c("bg"), fg=label_fg)
            elif isinstance(widget, tk.Scale):
                widget.config(bg=c("bg"), fg=label_fg, highlightthickness=0)
            elif isinstance(widget, tk.Button):
                widget.config(bg=c("btn_bg"), fg=label_fg)

        # 追加ボタン
        self.add_button.config(bg=c("btn_bg"), fg=label_fg)

        # 各行の更新
        for row in self.scrollable_frame.winfo_children():
            if row == self.add_btn_frame: continue
            row.config(bg=c("bg"))
            for widget in row.winfo_children():
                if isinstance(widget, tk.Entry):
                    # URL判定して青色にする処理を維持しつつテーマ適用
                    current_text = widget.get()
                    if widget.grid_info()["column"] == 1 and current_text.startswith("http"):
                        widget.config(bg=c("entry_bg"), fg="#4fc3f7" if self.is_dark_mode else "blue")
                    else:
                        # プレースホルダ判定（簡易）
                        if widget.cget("fg") == "grey":
                            widget.config(bg=c("entry_bg"), fg="grey")
                        else:
                            widget.config(bg=c("entry_bg"), fg=c("entry_fg"))
                            
                    widget.config(insertbackground=c("fg")) # カーソル色
                elif isinstance(widget, tk.Button):
                    # 削除ボタン
                    widget.config(bg="#ffcdd2" if not self.is_dark_mode else "#ef9a9a", fg="black")

    def add_new_row(self):
        self.add_memo_row("", "")

    def add_memo_row(self, memo_text="", note_text="", is_first=False):
        """行を追加。追加ボタンの手前に挿入する"""
        c = self.get_color
        
        row = tk.Frame(self.scrollable_frame, bg=c("bg"))
        
        # pack(before=...) を使って追加ボタンより上に表示する
        row.pack(before=self.add_btn_frame, fill="x", pady=2, padx=2)

        row.columnconfigure(0, weight=1) # メモ
        row.columnconfigure(1, weight=4) # 備考
        row.columnconfigure(2, weight=0) # 削除

        # ▼ 修正: width=1 を追加（これでサイズ追従が完璧になります）▼
        # メモ入力
        m_entry = tk.Entry(row, bg=c("entry_bg"), fg=c("entry_fg"), insertbackground=c("fg"),
                           relief="solid", borderwidth=2, font=self.default_font, width=1)
        m_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        # ▼ 修正: width=1 を追加 & デザイン修正（太枠・フォント）を適用 ▼
        # 備考入力
        n_entry = tk.Entry(row, bg=c("entry_bg"), fg=c("entry_fg"), insertbackground=c("fg"),
                           relief="solid", borderwidth=2, font=self.default_font, width=1)
        n_entry.grid(row=0, column=1, sticky="ew", padx=(0, 5))

        # ▼ 修正: デザイン修正（太枠・フォント）を適用 ▼
        # 削除ボタン
        del_btn = tk.Button(row, text="×", command=lambda: self.delete_row(row), 
                            borderwidth=2, relief="solid", font=self.default_font,
                            bg="#ffcdd2", width=3, cursor="hand2")
        del_btn.grid(row=0, column=2, sticky="e")

        # URL機能と保存のバインド
        n_entry.bind("<KeyRelease>", lambda e: self.on_note_change(n_entry))
        n_entry.bind("<Double-Button-1>", lambda e: self.open_url(n_entry))
        m_entry.bind("<KeyRelease>", lambda e: self.save_data())

        # 値のセット
        m_entry.insert(0, memo_text)
        n_entry.insert(0, note_text)
        
        # URLのスタイルチェック
        if note_text:
            self.check_url_style(n_entry)

        self.save_data()

    def on_note_change(self, entry):
        """備考欄の入力時にURL判定と保存を行う"""
        self.check_url_style(entry)
        self.save_data()

    def check_url_style(self, entry):
        """URLなら文字色を変える"""
        text = entry.get()
        if text.startswith("http://") or text.startswith("https://"):
            entry.config(fg="#4fc3f7" if self.is_dark_mode else "blue", font=("Meiryo UI", 9, "underline"))
            entry.config(cursor="hand2") # マウスカーソルを指にする
        else:
            # URLでなければ通常色に戻す（プレースホルダでない場合）
            if entry.cget("fg") != "grey":
                entry.config(fg=self.get_color("entry_fg"), font=("Meiryo UI", 9), cursor="xterm")

    def open_url(self, entry):
        """ダブルクリックでURLを開く"""
        url = entry.get()
        if url.startswith("http://") or url.startswith("https://"):
            webbrowser.open(url)

    def set_placeholder(self, entry, text):
        entry.insert(0, text)
        entry.config(fg="grey")

        def on_focus_in(event):
            if entry.get() == text and entry.cget("fg") == "grey":
                entry.delete(0, "end")
                entry.config(fg=self.get_color("entry_fg"))

        def on_focus_out(event):
            if entry.get() == "":
                entry.insert(0, text)
                entry.config(fg="grey")
            self.save_data()

        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

    def delete_row(self, row):
        row.destroy()
        self.save_data()

    def save_data(self):
        data = []
        # scrollable_frame の子供のうち、Frame型のもの（行）を探す
        # add_btn_frame は除外する
        for row in self.scrollable_frame.winfo_children():
            if row == self.add_btn_frame: continue
            
            entries = [c for c in row.winfo_children() if isinstance(c, tk.Entry)]
            if len(entries) >= 2:
                m_val = entries[0].get()
                n_val = entries[1].get()
                fg_color = entries[0].cget("fg")

                if m_val == "メモ内容" and fg_color == "grey": m_val = ""
                if str(n_val).startswith("備考") and fg_color == "grey": n_val = ""

                if m_val or n_val:
                    data.append({"memo": m_val, "note": n_val})
        
        with open(self.save_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def load_data(self):
        if os.path.exists(self.save_file):
            try:
                with open(self.save_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data:
                        for item in data:
                            self.add_memo_row(item["memo"], item["note"])
                    else:
                        self.add_memo_row(is_first=True)
            except:
                self.add_memo_row(is_first=True)
        else:
            self.add_memo_row(is_first=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = MemoMadoKun(root)
    root.mainloop()