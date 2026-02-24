import csv
import sys
import os  # 新增：导入os模块处理路径
from tkinter import messagebox

# ===================== 核心修复：路径处理 =====================
def get_script_dir():
    """获取当前py文件所在的绝对目录（不管程序在哪运行）"""
    if getattr(sys, 'frozen', False):
        # 打包成exe时的目录
        return os.path.dirname(sys.executable)
    else:
        # 普通py文件的目录
        return os.path.dirname(os.path.abspath(__file__))

def safe_path(filename):
    """拼接出文件的绝对路径（当前py文件所在文件夹 + 文件名）"""
    return os.path.join(get_script_dir(), filename)

# ===================== 玩家数据存储 =====================
PLAYER = {
    "name": "",
    "attributes": {
        "Strength": 0,
        "Agility": 0,
        "Toughness": 0,
        "Influence": 0,
        "Willpower": 0,
        "Intelligence": 0,
        "装备1": "",
        "装备2": "",
        "护甲": ""
    },
    "gold": 50,
    "cards": [],          # 已购卡牌数据（传给explore_core/battle_core）
    "card_names": [],
    "battle_ready": False,
    "max_hp": 0,         # 补充：之前漏了这个字段
    "current_hp": 0      # 补充：之前漏了这个字段
}

# ===================== 角色加载（修复路径） =====================
def load_character(filename):
    # 核心修改：把文件名转成绝对路径
    file_path = safe_path(filename)
    try:
        with open(file_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                PLAYER["name"] = row["角色名称"].strip()
                PLAYER["attributes"] = {
                    "Strength": int(row["Strength"]),
                    "Agility": int(row["Agility"]),
                    "Toughness": int(row["Toughness"]),
                    "Influence": int(row["Influence"]),
                    "Willpower": int(row["Willpower"]),
                    "Intelligence": int(row["Intelligence"]),
                    "装备1": row["装备1"].strip(),
                    "装备2": row["装备2"].strip(),
                    "护甲": row["护甲"].strip()
                }
        toughness = PLAYER["attributes"].get("Toughness", 0)
        PLAYER["max_hp"] = 50 + toughness * 2
        PLAYER["current_hp"] = PLAYER["max_hp"]
        PLAYER["battle_ready"] = True
        messagebox.showinfo("成功", f"加载角色：{PLAYER['name']}")
        return True
    except FileNotFoundError:
        messagebox.showerror("错误", f"找不到角色文件：{file_path}\n请确认文件在当前文件夹！")
        return False
    except Exception as e:
        messagebox.showerror("错误", f"读取角色失败：{str(e)}\n文件路径：{file_path}")
        return False

# ===================== 卡牌加载（修复路径） =====================
def load_action_cards(filename):
    # 核心修改：把文件名转成绝对路径
    file_path = safe_path(filename)
    cards = []
    try:
        with open(file_path, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cards.append({
                    "编号": int(row["编号"]),
                    "卡名": row["卡名"].strip(),
                    "卡牌类型": row["卡牌类型"].strip(),
                    "能量消耗": int(row["能量消耗"]),
                    "移动值": int(row["移动值"]),
                    "伤害值": int(row["伤害值"]),
                    "防御值": int(row["防御值"]),
                    "能量增益": int(row["能量增益"]),
                    "持有数量": int(row["持有数量"]),
                    "描述": row["描述"].strip(),
                    "价格": int(row["价格"])
                })
        return cards
    except FileNotFoundError:
        messagebox.showerror("错误", f"找不到卡牌文件：{file_path}\n请确认文件在当前文件夹！")
        sys.exit()
    except Exception as e:
        messagebox.showerror("错误", f"读取卡牌失败：{str(e)}\n文件路径：{file_path}")
        sys.exit()

# ===================== 卡牌购买/重置 =====================
def buy_card(card):
    if PLAYER["gold"] < card["价格"]:
        messagebox.showwarning("金币不足", f"需要{card['价格']}金币，当前只有{PLAYER['gold']}")
        return False
    PLAYER["gold"] -= card["价格"]
    PLAYER["cards"].append(card)
    PLAYER["card_names"].append(card["卡名"])
    messagebox.showinfo("购买成功", f"已购买【{card['卡名']}】，剩余金币：{PLAYER['gold']}")
    return True

def reset_cards():
    PLAYER["gold"] = 50
    PLAYER["cards"] = []
    PLAYER["card_names"] = []
    return True

def get_battle_params():
    """仅返回参数，供explore_core/battle_core调用"""
    if not PLAYER["battle_ready"]:
        messagebox.showerror("错误", "未选择角色，无法进入探索/战斗！")
        return None
    return {
        "角色名": PLAYER["name"],
        "基础属性": PLAYER["attributes"],
        "剩余金币": PLAYER["gold"],
        "已购卡牌": PLAYER["cards"],          # 核心：传递已购卡牌数据
        "卡牌数量": len(PLAYER["cards"])
    }