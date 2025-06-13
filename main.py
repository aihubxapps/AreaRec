import mss
import mss.tools
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import time
import keyboard # ホットキー機能のために残します

class ScreenshotApp:
    def __init__(self, master):
        self.master = master
        master.title("範囲指定スクリーンショット")

        self.region = {"top": 200, "left": 100, "width": 400, "height": 300} # デフォルトの撮影範囲

        # GUI要素の作成
        self.create_widgets()

        # ホットキーの設定
        keyboard.add_hotkey('ctrl+alt+s', self.take_screenshot_hotkey)
        print("Ctrl+Alt+S でスクリーンショットを撮影できます。")


    def create_widgets(self):
        # 撮影範囲設定用のフレーム
        region_frame = tk.LabelFrame(self.master, text="撮影範囲設定", padx=10, pady=10)
        region_frame.pack(pady=10)

        # top, left, width, height の入力フィールド
        self.labels = {}
        self.entries = {}
        for i, key in enumerate(["top", "left", "width", "height"]):
            label = tk.Label(region_frame, text=f"{key.capitalize()}:")
            label.grid(row=i, column=0, sticky="w")
            self.labels[key] = label

            entry = tk.Entry(region_frame, width=10)
            entry.grid(row=i, column=1, sticky="ew")
            entry.insert(0, str(self.region[key])) # デフォルト値を設定
            self.entries[key] = entry
            entry.bind("<FocusOut>", self.update_region_from_entry) # フォーカスが外れたら更新
            entry.bind("<Return>", self.update_region_from_entry) # Enterキーでも更新

        # 撮影ボタン
        self.screenshot_button = tk.Button(self.master, text="スクリーンショットを撮影", command=self.take_screenshot_button)
        self.screenshot_button.pack(pady=5)

        # 保存パス表示ラベル
        self.save_path_label = tk.Label(self.master, text="保存先: (未設定)")
        self.save_path_label.pack(pady=5)

        # 保存先設定ボタン
        self.set_save_path_button = tk.Button(self.master, text="保存先フォルダを選択", command=self.select_save_directory)
        self.set_save_path_button.pack(pady=5)
        self.save_directory = None # 保存ディレクトリのパス

        # プレビュー表示用キャンバス（簡略化）
        self.preview_canvas = tk.Canvas(self.master, width=400, height=300, bg="lightgray", relief="sunken", borderwidth=1)
        self.preview_canvas.pack(pady=10)
        self.preview_text = self.preview_canvas.create_text(200, 150, text="プレビューエリア", fill="gray", font=("Arial", 16))


    def update_region_from_entry(self, event=None):
        try:
            for key in ["top", "left", "width", "height"]:
                self.region[key] = int(self.entries[key].get())
            print(f"撮影範囲を更新しました: {self.region}")
            self.update_preview_area()
        except ValueError:
            print("無効な数値が入力されました。整数を入力してください。")

    def update_preview_area(self):
        # プレビューエリアのサイズを更新（視覚的な目安として）
        self.preview_canvas.config(width=self.region["width"], height=self.region["height"])
        self.preview_canvas.coords(self.preview_text, self.region["width"]/2, self.region["height"]/2)
        self.preview_canvas.itemconfig(self.preview_text, text=f"W:{self.region['width']} H:{self.region['height']}")


    def select_save_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.save_directory = directory
            self.save_path_label.config(text=f"保存先: {self.save_directory}")
            print(f"保存先フォルダを設定しました: {self.save_directory}")

    def take_screenshot(self, save_path=None):
        if self.save_directory is None and save_path is None:
            print("保存先フォルダが設定されていません。")
            # デフォルトでカレントディレクトリに保存するか、エラーメッセージを出すなど
            # 今回はエラーメッセージを出して、ユーザーに設定を促す
            return

        try:
            with mss.mss() as sct:
                sct_img = sct.grab(self.region)
                
                if save_path: # ホットキーからの場合など、パスが直接渡された場合
                    filename = save_path
                else: # ボタンからの場合など、保存ディレクトリを使う場合
                    timestamp = int(time.time())
                    filename = f"{self.save_directory}/screenshot_{timestamp}.png"

                mss.tools.to_png(sct_img.rgb, sct_img.size, output=filename)
                print(f"スクリーンショットを保存しました: {filename}")
                self.master.clipboard_clear()
                self.master.clipboard_append(filename) # 保存したファイル名をクリップボードにコピー
                print("ファイル名をクリップボードにコピーしました。")

                # 撮影した画像をプレビュー表示 (簡易版)
                # mssの画像をPILに変換し、tkinterで表示
                img = Image.frombytes("RGB", sct_img.size, sct_img.rgb)
                img.thumbnail((self.region["width"], self.region["height"])) # プレビューサイズに縮小
                photo = ImageTk.PhotoImage(image=img)
                self.preview_canvas.delete("all") # 古いプレビューを削除
                self.preview_canvas.create_image(0, 0, anchor=tk.NW, image=photo)
                self.preview_canvas.image = photo # ガベージコレクションされないように参照を保持
                self.preview_canvas.create_text(self.region["width"]/2, self.region["height"]/2, text=f"W:{self.region['width']} H:{self.region['height']}", fill="white", font=("Arial", 16))


        except mss.exception.ScreenShotError as e:
            print(f"スクリーンショットエラー: {e}")
            print("指定された範囲がディスプレイの範囲を超えている可能性があります。")
        except Exception as e:
            print(f"エラーが発生しました: {e}")

    def take_screenshot_button(self):
        self.take_screenshot()

    def take_screenshot_hotkey(self):
        # ホットキーからの場合、現在のタイムスタンプを使ってカレントディレクトリに保存
        # または、GUIで設定された保存ディレクトリがあればそちらに保存
        if self.save_directory:
            timestamp = int(time.time())
            filename = f"{self.save_directory}/screenshot_hotkey_{timestamp}.png"
            self.take_screenshot(save_path=filename)
        else:
            timestamp = int(time.time())
            filename = f"screenshot_hotkey_{timestamp}.png"
            self.take_screenshot(save_path=filename)


if __name__ == "__main__":
    root = tk.Tk()
    app = ScreenshotApp(root)
    root.mainloop()