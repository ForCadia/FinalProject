import tkinter as tk
from tkinter import messagebox

# 初始化游戏窗口（UI主容器）
root = tk.Tk()
root.title("简易游戏UI")
root.geometry("400x300")  # 窗口大小，自己调
root.resizable(False, False)  # 固定窗口，不让缩放

# 1. 游戏标题（纯手写文字样式）
title_label = tk.Label(root, text="我的小游戏", font=("Arial", 20, "bold"), fg="#FF6347")
title_label.pack(pady=20)

# 2. 关卡/状态显示（游戏UI必备）
level_label = tk.Label(root, text="当前关卡：1 | 分数：0", font=("Arial", 12))
level_label.pack(pady=10)

# 3. 按钮交互（游戏核心操作）
def start_game():
    messagebox.showinfo("游戏开始", "进入关卡1！祝通关～")
    # 后续可加简单逻辑，比如分数变化、关卡切换
def quit_game():
    root.quit()

start_btn = tk.Button(root, text="开始游戏", font=("Arial", 12), width=10, command=start_game, bg="#90EE90")
start_btn.pack(pady=5)
quit_btn = tk.Button(root, text="退出游戏", font=("Arial", 12), width=10, command=quit_game, bg="#FFB6C1")
quit_btn.pack(pady=5)

# 运行UI
root.mainloop()