import tkinter as tk
from tkinter import ttk, messagebox
import player_data as pd
import explore_core as ec
import os
import sys

start_window = None
action_cards = []
listbox_cards = None

# ==========================
# 检查文件是否存在
# ==========================
def check_file_exists(filename):
    if os.path.exists(filename):
        return True
    current_dir = os.getcwd()
    all_files = os.listdir(current_dir)
    messagebox.showerror(
        "缺少文件",
        f"找不到：{filename}\n当前目录：{current_dir}\n文件：{', '.join(all_files)}"
    )
    return False

# ==========================
# 角色选择界面
# ==========================
def create_character_select_ui():
    global start_window
    start_window = tk.Tk()
    start_window.title("选择角色")
    start_window.geometry("700x500")
    start_window.config(bg="#eee")

    tk.Label(start_window, text="选择你的角色", font=("微软雅黑",20,"bold"), bg="#eee").pack(pady=30)

    def choose_william():
        if check_file_exists("William.csv"):
            pd.load_character("William.csv")
            start_window.destroy()
            open_card_shop()

    def choose_bard():
        if check_file_exists("Bard.csv"):
            pd.load_character("Bard.csv")
            start_window.destroy()
            open_card_shop()

    # 角色按钮
    tk.Button(
        start_window, text="WilliamZhu", font=("微软雅黑",14,"bold"),
        width=20, height=3, bg="#4CAF50", fg="white", command=choose_william
    ).pack(pady=10)

    tk.Button(
        start_window, text="Bard", font=("微软雅黑",14,"bold"),
        width=20, height=3, bg="#2196F3", fg="white", command=choose_bard
    ).pack(pady=10)

    start_window.mainloop()

# ==========================
# 卡牌商店（极简 Listbox 写法，绝对能看到）
# ==========================
def open_card_shop():
    global start_window, action_cards, listbox_cards

    if not check_file_exists("action_card.csv"):
        return
    action_cards = pd.load_action_cards("action_card.csv")

    # 窗口
    start_window = tk.Tk()
    start_window.title("卡牌商店")
    start_window.geometry("900x700")
    start_window.config(bg="#eee")

    # 顶部信息
    info_text = f"角色：{pd.PLAYER['name']}   金币：{pd.PLAYER['gold']}"
    info_label = tk.Label(start_window, text=info_text, font=("微软雅黑",14,"bold"), bg="#eee")
    info_label.pack(pady=10)

    # 框架
    frame = tk.Frame(start_window)
    frame.pack(fill="both", expand=True, padx=20, pady=10)

    # 列表框（超大、超清晰）
    listbox_cards = tk.Listbox(
        frame, font=("微软雅黑",13),
        width=80, height=20
    )
    listbox_cards.pack(side="left", fill="both", expand=True)

    # 滚动条
    scroll = tk.Scrollbar(frame, orient="vertical", command=listbox_cards.yview)
    scroll.pack(side="right", fill="y")
    listbox_cards.config(yscrollcommand=scroll.set)

    # 填入所有卡牌
    for i, c in enumerate(action_cards):
        show = f"[{c['卡牌类型']}] {c['卡名']} | 价格:{c['价格']} | {c['描述']}"
        listbox_cards.insert("end", show)

    # ==========================
    # 按钮区域
    # ==========================
    btn_frame = tk.Frame(start_window, bg="#eee")
    btn_frame.pack(pady=15)

    # 购买
    def buy_selected():
        sel = listbox_cards.curselection()
        if not sel:
            messagebox.showwarning("提示","先选一张卡")
            return
        idx = sel[0]
        card = action_cards[idx]
        if pd.buy_card(card):
            info_label.config(text=f"角色：{pd.PLAYER['name']}   金币：{pd.PLAYER['gold']}")

    # 重置
    def reset_all():
        pd.PLAYER["gold"] = 50
        pd.PLAYER["cards"] = []
        info_label.config(text=f"角色：{pd.PLAYER['name']}   金币：{pd.PLAYER['gold']}")
        messagebox.showinfo("重置","已重置金币和卡牌")

    # 开始游戏
    def start_game():
        start_window.destroy()
        ec.create_game_ui()

    # 按钮
    tk.Button(btn_frame, text="购买选中卡牌", font=("微软雅黑",12),
              command=buy_selected, width=18).grid(row=0,column=0,padx=5)

    tk.Button(btn_frame, text="重置购买", font=("微软雅黑",12),
              command=reset_all, width=12).grid(row=0,column=1,padx=5)

    tk.Button(btn_frame, text="开始游戏", font=("微软雅黑",12,"bold"), bg="#4CAF50", fg="white",
              command=start_game, width=18).grid(row=0,column=2,padx=5)

    start_window.mainloop()