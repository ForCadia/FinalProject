# game_start.py - 新增已购卡牌明细展示
import tkinter as tk
from tkinter import messagebox, ttk
import player_data as pd
import os
import sys

# 全局变量
root = None
card_list = []

# ===================== 检查文件 =====================
def check_file(filename):
    if os.path.exists(filename):
        return True
    current_dir = os.getcwd()
    files = os.listdir(current_dir)
    messagebox.showerror(
        "文件缺失",
        f"未找到{filename}！\n当前目录：{current_dir}\n目录内文件：\n{', '.join(files)}"
    )
    return False

# ===================== 角色选择界面 =====================
def show_character_select():
    global root
    root = tk.Tk()
    root.title("游戏开局 - 选择角色")
    root.geometry("600x400")
    root.configure(bg="#f5f5f5")
    root.resizable(False, False)

    # 标题
    title = tk.Label(
        root, text="⚔️ 选择你的角色",
        font=("微软雅黑", 22, "bold"), bg="#f5f5f5", fg="#333"
    )
    title.pack(pady=40)

    # 选择William
    def select_william():
        if check_file("William.csv") and pd.load_character("William.csv"):
            root.destroy()
            show_card_shop()

    # 选择Bard
    def select_bard():
        if check_file("Bard.csv") and pd.load_character("Bard.csv"):
            root.destroy()
            show_card_shop()

    # 角色按钮
    btn_william = tk.Button(
        root, text="WilliamZhu\n力量5 | 敏捷1 | 坚韧4",
        font=("微软雅黑", 14, "bold"), width=18, height=4,
        bg="#4CAF50", fg="white", command=select_william
    )
    btn_william.pack(pady=10)

    btn_bard = tk.Button(
        root, text="Bard\n敏捷5 | 影响力6 | 智力6",
        font=("微软雅黑", 14, "bold"), width=18, height=4,
        bg="#2196F3", fg="white", command=select_bard
    )
    btn_bard.pack(pady=10)

    root.mainloop()

# ===================== 卡牌购买界面（新增已购卡牌展示） =====================
def show_card_shop():
    global root, card_list
    root = tk.Tk()
    root.title(f"卡牌商店 - {pd.PLAYER['name']}")
    root.geometry("1000x700")  # 加宽窗口，容纳已购卡牌展示
    root.configure(bg="#f5f5f5")

    # 加载卡牌
    if not check_file("action_card.csv"):
        root.destroy()
        return
    card_list = pd.load_action_cards("action_card.csv")

    # 顶部信息（分左右）
    top_frame = tk.Frame(root, bg="#f5f5f5")
    top_frame.pack(fill="x", padx=20, pady=10)

    # 左侧：金币信息
    gold_label = tk.Label(
        top_frame, text=f"当前金币：{pd.PLAYER['gold']}",
        font=("微软雅黑", 16, "bold"), bg="#f5f5f5", fg="#e67e22"
    )
    gold_label.pack(side="left")

    # 右侧：已购卡牌数量
    card_count_label = tk.Label(
        top_frame, text=f"已购卡牌：{len(pd.PLAYER['cards'])}",
        font=("微软雅黑", 14), bg="#f5f5f5", fg="#666"
    )
    card_count_label.pack(side="right")

    # 中间区域：分左右两栏（可购买卡牌 + 已购卡牌）
    main_frame = tk.Frame(root, bg="#f5f5f5")
    main_frame.pack(fill="both", expand=True, padx=20, pady=10)

    # -------------------- 左侧：可购买卡牌列表 --------------------
    left_frame = tk.Frame(main_frame, bg="#fff", relief="solid", bd=1)
    left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

    # 左侧标题
    left_title = tk.Label(
        left_frame, text="可购买卡牌",
        font=("微软雅黑", 14, "bold"), bg="#fff", fg="#333"
    )
    left_title.pack(pady=5)

    # 可购买卡牌列表+滚动条
    scrollbar1 = tk.Scrollbar(left_frame)
    scrollbar1.pack(side="right", fill="y")

    card_listbox = tk.Listbox(
        left_frame, font=("微软雅黑", 11),
        width=60, height=25, yscrollcommand=scrollbar1.set
    )
    card_listbox.pack(side="left", fill="both", expand=True)
    scrollbar1.config(command=card_listbox.yview)

    # 填充可购买卡牌数据
    for idx, card in enumerate(card_list):
        card_info = (
            f"[{card['卡牌类型']}] {card['卡名']} "
            f"| 价格：{card['价格']}金币 "
            f"| 效果：{card['描述']} "
            f"| 移动：{card['移动值']} 伤害：{card['伤害值']} 防御：{card['防御值']}"
        )
        card_listbox.insert(tk.END, card_info)

    # -------------------- 右侧：已购卡牌明细（核心新增） --------------------
    right_frame = tk.Frame(main_frame, bg="#fff", relief="solid", bd=1)
    right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))

    # 右侧标题
    right_title = tk.Label(
        right_frame, text="已购卡牌（战斗可用）",
        font=("微软雅黑", 14, "bold"), bg="#fff", fg="#27ae60"
    )
    right_title.pack(pady=5)

    # 已购卡牌列表+滚动条
    scrollbar2 = tk.Scrollbar(right_frame)
    scrollbar2.pack(side="right", fill="y")

    bought_card_listbox = tk.Listbox(
        right_frame, font=("微软雅黑", 12),
        width=50, height=25, yscrollcommand=scrollbar2.set, fg="#27ae60"
    )
    bought_card_listbox.pack(side="left", fill="both", expand=True)
    scrollbar2.config(command=bought_card_listbox.yview)

    # 初始化已购卡牌列表（首次加载）
    def refresh_bought_cards():
        """刷新已购卡牌展示"""
        bought_card_listbox.delete(0, tk.END)  # 清空原有内容
        if not pd.PLAYER["cards"]:
            bought_card_listbox.insert(tk.END, "暂无已购卡牌")
            return
        # 逐条展示已购卡牌的完整信息（战斗参数）
        for idx, card in enumerate(pd.PLAYER["cards"], 1):
            bought_info = (
                f"{idx}. {card['卡名']} "
                f"| 类型：{card['卡牌类型']} "
                f"| 效果：{card['描述']} "
                f"| 伤害：{card['伤害值']} 防御：{card['防御值']}"
            )
            bought_card_listbox.insert(tk.END, bought_info)
    
    # 首次刷新
    refresh_bought_cards()

    # -------------------- 按钮区域 --------------------
    btn_frame = tk.Frame(root, bg="#f5f5f5")
    btn_frame.pack(fill="x", padx=20, pady=10)

    # 购买选中卡牌（新增刷新已购列表）
    def buy_selected():
        selected = card_listbox.curselection()
        if not selected:
            messagebox.showwarning("提示", "请先选中一张卡牌！")
            return
        idx = selected[0]
        card = card_list[idx]
        if pd.buy_card(card):
            # 更新显示
            gold_label.config(text=f"当前金币：{pd.PLAYER['gold']}")
            card_count_label.config(text=f"已购卡牌：{len(pd.PLAYER['cards'])}")
            refresh_bought_cards()  # 刷新已购卡牌列表

    # 重置购买（新增清空已购列表）
    def reset_buy():
        if messagebox.askyesno("确认", "是否重置购买记录？（恢复50金币，清空已购卡牌）"):
            pd.reset_cards()  # 调用重置函数
            # 更新显示
            gold_label.config(text=f"当前金币：{pd.PLAYER['gold']}")
            card_count_label.config(text=f"已购卡牌：{len(pd.PLAYER['cards'])}")
            refresh_bought_cards()  # 刷新已购卡牌列表
            messagebox.showinfo("重置成功", "已恢复初始状态！")

    # 开始游戏（传递战斗参数）
    def start_game():
        # 获取战斗核心参数
        battle_params = pd.get_battle_params()
        if not battle_params:
            return
        
        # 打印战斗参数（供战斗系统调用，可注释/保留）
        print("\n===== 战斗核心参数 =====")
        for key, value in battle_params.items():
            print(f"{key}：{value}")
        print("========================\n")
        
        messagebox.showinfo(
            "开始游戏",
            f"已进入战斗！\n角色：{battle_params['角色名']}\n已购卡牌：{battle_params['卡牌数量']}张"
        )
        root.destroy()
        # 此处可添加调用战斗系统的代码：
        # import battle_core as bc
        # bc.start_battle(battle_params)

    # 按钮样式
    buy_btn = tk.Button(
        btn_frame, text="购买选中卡牌", font=("微软雅黑", 12, "bold"),
        width=15, bg="#27ae60", fg="white", command=buy_selected
    )
    buy_btn.pack(side="left", padx=5)

    reset_btn = tk.Button(
        btn_frame, text="重置购买", font=("微软雅黑", 10),
        width=10, bg="#e74c3c", fg="white", command=reset_buy
    )
    reset_btn.pack(side="left", padx=5)

    start_btn = tk.Button(
        btn_frame, text="开始游戏", font=("微软雅黑", 12, "bold"),
        width=15, bg="#3498db", fg="white", command=start_game
    )
    start_btn.pack(side="right", padx=5)

    root.mainloop()

# ===================== 启动游戏 =====================
if __name__ == "__main__":
    show_character_select()