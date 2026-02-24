import tkinter as tk
from tkinter import messagebox
import player_data as pd
import explore_core as ec
import os
import sys
import weapon_data as wd
from typing import Optional, Callable
# ===================== 【核心修复】永远定位到当前代码所在文件夹 =====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def safe_path(filename):
    # 把文件名变成 → 当前文件夹里的绝对路径
    return os.path.join(BASE_DIR, filename)

# ===================== 全局变量 =====================
root = None
card_list = []
PURCHASED_CARDS = {}

# ===================== 武器商店 =====================
def show_weapon_shop(after_callback: Optional[Callable] = None) -> None:
    try:
        wd.load_weapons()
    except Exception as e:
        messagebox.showerror("加载失败", f"读取武器数据出错：{e}")
        if after_callback:
            after_callback()
        return
    
    shop_win = tk.Toplevel()
    shop_win.title("武器商店")
    shop_win.geometry("800x600")
    shop_win.configure(bg="#f5f5f5")
    shop_win.transient(root)
    shop_win.grab_set()
    
    title = tk.Label(
        shop_win,
        text="武器列表（选择后点击购买装备）",
        font=("微软雅黑", 16, "bold"),
        bg="#f5f5f5",
        fg="#2c3e50"
    )
    title.pack(pady=10)
    
    listbox: tk.Listbox = tk.Listbox(
        shop_win,
        font=("微软雅黑", 12),
        width=80,
        height=20
    )
    listbox.pack(fill="both", expand=True, padx=20, pady=10)
    
    if not wd.WEAPONS:
        listbox.insert(tk.END, "⚠️ 未加载到任何武器数据！")
    else:
        for w in wd.WEAPONS:
            text = (
                f"{w['编号']}. {w['武器名']} | 伤害:{w['伤害']} | 命中:{w['命中']} | "
                f"额外攻击:{w['额外攻击次数']} | 额外防御:{w['额外防御次数']} | "
                f"格挡:{w['格挡']} | 特性:{w['特性']} | 描述:{w['描述']}"
            )
            listbox.insert(tk.END, text)
    
    def buy_weapon() -> None:
        idx = listbox.curselection()
        if not idx:
            messagebox.showwarning("提示", "请先选择一把武器！")
            return
        
        if idx[0] >= len(wd.WEAPONS):
            messagebox.showwarning("提示", "选择的武器不存在！")
            return
        
        weapon = wd.WEAPONS[idx[0]]
        pd.PLAYER["attributes"]["装备1"] = weapon["武器名"]
        
        try:
            from battle_core import PLAYER_ATTR
            PLAYER_ATTR["weapon"] = weapon["武器名"]
            PLAYER_ATTR["base_damage"] = weapon["伤害"]
            PLAYER_ATTR["hit_check"] = weapon["命中"]
            PLAYER_ATTR["block_check"] = weapon["格挡"]
        except ImportError:
            pd.PLAYER["attributes"]["武器伤害"] = weapon["伤害"]
            pd.PLAYER["attributes"]["武器命中"] = weapon["命中"]
            pd.PLAYER["attributes"]["武器格挡"] = weapon["格挡"]
        
        messagebox.showinfo("装备成功", 
            f"已装备【{weapon['武器名']}】\n"
            f"伤害：{weapon['伤害']} | 命中：{weapon['命中']} | 格挡：{weapon['格挡']}\n"
            f"额外攻击：{weapon['额外攻击次数']} | 额外防御：{weapon['额外防御次数']}\n"
            f"特性：{weapon['特性']}"
        )
        shop_win.destroy()
        if after_callback:
            after_callback()
    
    def on_shop_close():
        shop_win.destroy()
        if after_callback:
            after_callback()
    
    shop_win.protocol("WM_DELETE_WINDOW", on_shop_close)
    
    buy_btn = tk.Button(
        shop_win,
        text="购买并装备",
        font=("微软雅黑", 14, "bold"),
        bg="#2196F3",
        fg="white",
        width=20,
        height=2,
        command=buy_weapon
    )
    buy_btn.pack(pady=20)

# ===================== 工具函数 =====================
def check_file(filename):
    # 【修复】永远从当前文件夹找
    path = safe_path(filename)
    if os.path.exists(path):
        return True
    current_dir = os.getcwd()
    messagebox.showerror("文件缺失", f"未找到{filename}！\n期望路径：{path}")
    return False

# ===================== 角色选择 =====================
def show_character_select():
    global root, PURCHASED_CARDS
    PURCHASED_CARDS = {}

    root = tk.Tk()
    root.title("Hell's Last")
    root.geometry("850x550")
    root.configure(bg="#f5f5f5")
    root.resizable(False, False)

    title = tk.Label(
        root,
        text="Choose your character",
        font=("微软雅黑", 26, "bold"),
        bg="#f5f5f5",
        fg="#222"
    )
    title.pack(pady=30)

    main_frame = tk.Frame(root, bg="#f5f5f5")
    main_frame.pack()

    def read_preview(filename):
        import csv
        # 【修复】
        path = safe_path(filename)
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                row = next(reader)
                return {
                    "name": row["角色名称"],
                    "Strength": row["Strength"],
                    "Agility": row["Agility"],
                    "Toughness": row["Toughness"],
                    "Influence": row["Influence"],
                    "Willpower": row["Willpower"],
                    "Intelligence": row["Intelligence"]
                }
        except:
            return None

    def create_panel(filename, color):
        data = read_preview(filename)
        if not data:
            return

        frame = tk.Frame(main_frame, bg="white", relief="solid", bd=2)
        frame.pack(side="left", padx=50, ipadx=30, ipady=20)

        tk.Label(
            frame,
            text=data["name"],
            font=("微软雅黑", 20, "bold"),
            fg=color,
            bg="white"
        ).pack(pady=10)

        attr_text = (
            f"力量: {data['Strength']}    敏捷: {data['Agility']}\n\n"
            f"坚韧: {data['Toughness']}    影响力: {data['Influence']}\n\n"
            f"意志: {data['Willpower']}    智力: {data['Intelligence']}"
        )

        tk.Label(
            frame,
            text=attr_text,
            font=("微软雅黑", 13),
            bg="white",
            justify="left"
        ).pack(pady=15)

        def select_character():
            if check_file(filename) and pd.load_character(filename):
                
                def after_weapon_shop():
                    root.destroy()
                    show_card_shop()
                
                show_weapon_shop(after_callback=after_weapon_shop)

        tk.Button(
            frame,
            text="选择角色",
            font=("微软雅黑", 12, "bold"),
            bg=color,
            fg="white",
            width=16,
            height=2,
            command=select_character
        ).pack(pady=10)

    create_panel("William.csv", "#4CAF50")
    create_panel("Bard.csv", "#2196F3")

    def exit_game():
        if messagebox.askyesno("退出", "确定退出游戏吗？"):
            root.destroy()
            sys.exit()

    tk.Button(
        root,
        text="退出游戏",
        font=("微软雅黑", 12),
        width=12,
        bg="#e74c3c",
        fg="white",
        command=exit_game
    ).pack(pady=30)

    root.mainloop()

# ===================== 卡牌商店 =====================
def show_card_shop():
    global root, card_list, PURCHASED_CARDS
    root = tk.Tk()
    root.title(f"卡牌商店 - {pd.PLAYER['name']}")
    root.geometry("1000x700")
    root.configure(bg="#f5f5f5")

    if not check_file("action_card.csv"):
        root.destroy()
        return
    
    # 【修复】
    card_list = pd.load_action_cards(safe_path("action_card.csv"))

    top_frame = tk.Frame(root, bg="#f5f5f5")
    top_frame.pack(fill="x", padx=20, pady=10)

    gold_label = tk.Label(top_frame, text=f"当前金币：{pd.PLAYER['gold']}", font=("微软雅黑",16,"bold"), bg="#f5f5f5", fg="#e67e22")
    gold_label.pack(side="left")

    def calc_total_cards():
        total = 0
        for v in PURCHASED_CARDS.values():
            total += v["购买数量"]
        return total

    card_count_label = tk.Label(top_frame, text=f"已购卡牌总数：{calc_total_cards()}", font=("微软雅黑",14), bg="#f5f5f5", fg="#666")
    card_count_label.pack(side="right")

    main_frame = tk.Frame(root, bg="#f5f5f5")
    main_frame.pack(fill="both", expand=True, padx=20, pady=10)

    left_frame = tk.Frame(main_frame, bg="#fff", relief="solid", bd=1)
    left_frame.pack(side="left", fill="both", expand=True, padx=(0,10))

    left_title = tk.Label(left_frame, text="可购买卡牌（双击直接购买）", font=("微软雅黑",14,"bold"), bg="#fff", fg="#e74c3c")
    left_title.pack(pady=5)

    scroll1 = tk.Scrollbar(left_frame)
    scroll1.pack(side="right", fill="y")
    card_listbox = tk.Listbox(left_frame, font=("微软雅黑",11), width=60, height=25, yscrollcommand=scroll1.set)
    card_listbox.pack(side="left", fill="both", expand=True)
    scroll1.config(command=card_listbox.yview)

    for card in card_list:
        info = f"[{card['卡牌类型']}] {card['卡名']} | 价格：{card['价格']} | 基础：{card['持有数量']} | {card['描述']}"
        card_listbox.insert(tk.END, info)

    right_frame = tk.Frame(main_frame, bg="#fff", relief="solid", bd=1)
    right_frame.pack(side="right", fill="both", expand=True, padx=(10,0))

    right_title = tk.Label(right_frame, text="已购卡牌", font=("微软雅黑",14,"bold"), bg="#fff", fg="#27ae60")
    right_title.pack(pady=5)

    scroll2 = tk.Scrollbar(right_frame)
    scroll2.pack(side="right", fill="y")
    bought_listbox = tk.Listbox(right_frame, font=("微软雅黑",12), width=50, height=25, yscrollcommand=scroll2.set, fg="#27ae60")
    bought_listbox.pack(side="left", fill="both", expand=True)
    scroll2.config(command=bought_listbox.yview)

    def refresh_bought():
        bought_listbox.delete(0, tk.END)
        if not PURCHASED_CARDS:
            bought_listbox.insert(tk.END, "暂无已购卡牌")
            return
        for i, (cid, info) in enumerate(PURCHASED_CARDS.items(), 1):
            line = f"{i}. {info['卡名']} | 类型：{info['卡牌类型']} | 已购：{info['购买数量']}张 | {info['描述']}"
            bought_listbox.insert(tk.END, line)

    refresh_bought()

    def buy_double(event):
        sel = card_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        c = card_list[idx]

        if pd.PLAYER["gold"] < c["价格"]:
            messagebox.showwarning("金币不足", f"购买【{c['卡名']}】需要{int(c['价格'])}金币，当前只有{pd.PLAYER['gold']}！")
            return

        pd.PLAYER["gold"] -= c["价格"]
        gold_label.config(text=f"当前金币：{pd.PLAYER['gold']}")

        cid = c["编号"]
        if cid in PURCHASED_CARDS:
            PURCHASED_CARDS[cid]["购买数量"] += 1
        else:
            cp = c.copy()
            cp["购买数量"] = 1
            PURCHASED_CARDS[cid] = cp

        card_count_label.config(text=f"已购卡牌总数：{calc_total_cards()}")
        refresh_bought()

    card_listbox.bind('<Double-Button-1>', buy_double)

    def reset_buy():
        if messagebox.askyesno("确认", "重置购买记录？"):
            global PURCHASED_CARDS
            pd.PLAYER["gold"] = 50
            PURCHASED_CARDS = {}
            gold_label.config(text=f"当前金币：{pd.PLAYER['gold']}")
            card_count_label.config(text=f"已购卡牌总数：{calc_total_cards()}")
            refresh_bought()

    def launch_explore():
        if not pd.PLAYER["battle_ready"]:
            return
        bp = {
            "角色名": pd.PLAYER["name"],
            "已购卡牌详情": PURCHASED_CARDS,
            "已购卡牌总数": calc_total_cards()
        }
        ec.PLAYER_BATTLE_PARAMS = bp
        root.destroy()
        try:
            er = ec.create_game_ui()
            er.mainloop()
        except:
            pass

    def back_to_char():
        if messagebox.askyesno("返回", "放弃当前购买？"):
            root.destroy()
            show_character_select()

    btn_frame = tk.Frame(root, bg="#f5f5f5")
    btn_frame.pack(fill="x", padx=20, pady=10)

    reset_btn = tk.Button(btn_frame, text="重置", width=10, command=reset_buy)
    reset_btn.pack(side="left", padx=5)
    back_btn = tk.Button(btn_frame, text="返回角色", width=10, command=back_to_char)
    back_btn.pack(side="left", padx=5)
    explore_btn = tk.Button(btn_frame, text="进入探索", width=15, bg="#3498db", fg="white", command=launch_explore)
    explore_btn.pack(side="right", padx=5)

    root.mainloop()

# ===================== 入口 =====================
if __name__ == "__main__":
    pd.PLAYER = {
        "name": "",
        "attributes": {"Strength":0,"Agility":0,"Toughness":0,"Influence":0,"Willpower":0,"Intelligence":0,"装备1":"","装备2":"","护甲":""},
        "max_hp": 0,
        "current_hp": 0,
        "gold": 50,
        "cards": [],
        "card_names": [],
        "battle_ready": False
    }

    show_character_select()
