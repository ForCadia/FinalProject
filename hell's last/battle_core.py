import random
import csv
import tkinter as tk
from tkinter import messagebox, Toplevel, Frame, Button, Label, Listbox, Scrollbar, END, Text
import time
import os  # 新增：检查文件是否存在
import sys # 新增：处理绝对路径
import player_data as pd  
import weapon_data as wd

# ===================== 全局速度控制 =====================
GLOBAL_DELAY = 1500
# =============================================================================

ENEMY_DATA = {}
PLAYER_DECK = []
PLAYER_HAND = []
PLAYER_DISCARD = []
INITIAL_DECK = []

PLAYER_ATTR = {
    "weapon": "基础长剑",
    "base_damage": 2,
    "hit_check": "3+",
    "dodge_check": "3+",  # 装备基础闪避阈值
    "block_check": "3+",  # 装备基础格挡阈值
    "extra_attack_times": 0,  # 兼容保留（已不再使用）
    "extra_defense_times": 0, # 兼容保留（已不再使用）
    "extra_attack_str": "0",  # 装备额外攻击次数原始值（如d6/2d6）
    "extra_defense_str": "0"  # 装备额外防御次数原始值（如d6/2d6）
}

# ===================== 核心修复：绝对路径处理（和explore_core统一） =====================
def get_script_dir():
    """获取当前代码文件所在的绝对目录"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def safe_path(filename):
    """拼接绝对路径"""
    return os.path.join(get_script_dir(), filename)

def safe_int(v, default=0):
    try:
        return int(str(v).strip())
    except:
        return default

def safe_str(v, default=""):
    return str(v).strip() if v else default

def parse_check_condition(s):
    s = safe_str(s)
    if "+" in s:
        return safe_int(s.replace("+", ""), 3)
    return safe_int(s, 3)

# ===================== 骰子解析函数（核心修复） =====================
def roll_dice(value):
    """
    解析骰子格式并掷骰：
    - 支持 d6/D6 → 随机1-6
    - 支持 2d6 → 随机2-12（2个6面骰）
    - 普通数字 → 直接返回数字
    - 其他格式 → 返回0
    修复：每次掷骰刷新随机种子，解决"老是出3"的问题
    """
    # 关键修复：每次掷骰都刷新随机种子，确保真随机
    random.seed(time.time() + random.randint(1, 1000000))
    
    value = safe_str(value).lower().strip()
    # 处理纯骰子（如 d6、d4、d8）
    if value.startswith('d') and len(value) == 2 and value[1].isdigit():
        dice_sides = int(value[1])
        roll_result = random.randint(1, dice_sides)
        return roll_result
    # 处理多骰子（如 2d6、3d4）
    elif 'd' in value:
        parts = value.split('d')
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            dice_num = int(parts[0])
            dice_sides = int(parts[1])
            roll_result = sum(random.randint(1, dice_sides) for _ in range(dice_num))
            return roll_result
    # 普通数字
    elif value.isdigit():
        return int(value)
    # 其他情况返回0
    else:
        return 0

# ===================== 闪避阈值（装备+敏捷） =====================
def get_dodge_threshold_str():
    """
    闪避阈值计算逻辑：
    最终阈值 = 装备基础闪避阈值 - (角色敏捷 // 2)
    限制范围：2+ ~ 6+
    """
    # 1. 获取装备基础闪避阈值
    equip_dodge = parse_check_condition(PLAYER_ATTR["dodge_check"])
    
    # 2. 获取角色敏捷属性
    agility = safe_int(pd.PLAYER["attributes"].get("Agility", 6))
    
    # 3. 计算最终阈值
    final_threshold = equip_dodge - (agility // 2)
    
    # 4. 限制范围：最低2+，最高6+
    final_threshold = max(2, min(6, final_threshold))
    
    return f"{final_threshold}+"

# ===================== 格挡阈值（装备+力量） =====================
def get_block_threshold_str():
    """
    格挡阈值计算逻辑：
    最终阈值 = 装备基础格挡阈值 - (角色力量 // 2)
    限制范围：2+ ~ 6+
    """
    # 1. 获取装备基础格挡阈值
    equip_block = parse_check_condition(PLAYER_ATTR["block_check"])
    
    # 2. 获取角色力量属性
    strength = safe_int(pd.PLAYER["attributes"].get("Strength", 6))
    
    # 3. 计算最终阈值
    final_threshold = equip_block - (strength // 2)
    
    # 4. 限制范围：最低2+，最高6+
    final_threshold = max(2, min(6, final_threshold))
    
    return f"{final_threshold}+"

def load_enemy_data(filename="enemycharacter.csv"):
    """
    加载敌人数据（修复版）：
    1. 检查文件是否存在（绝对路径）
    2. 兼容中英文字段名（name/名称, HP/生命值, Damage/伤害值 等）
    3. 输出详细加载日志，方便排查问题
    """
    global ENEMY_DATA
    ENEMY_DATA = {}
    
    # 关键修改：使用绝对路径
    file_path = safe_path(filename)
    
    # 第一步：检查文件是否存在
    if not os.path.exists(file_path):
        print(f"❌ 敌人数据文件 {file_path} 不存在！将使用默认敌人数据")
        # 添加默认敌人
        ENEMY_DATA["purplemaze"] = {
            "number": 1,
            "hp": 5,
            "damage": 1,
            "hit_check": "3+",
            "block_check": "3+",
            "base_attack_times": 1
        }
        return
    
    encodings = ["utf-8-sig", "gbk", "utf-8"]
    rows = []
    field_mapping = {  # 字段名映射：兼容中英文
        "name": ["name", "名称", "敌人名称"],
        "number": ["number", "编号", "序号"],
        "hp": ["HP", "hp", "生命值", "生命"],
        "damage": ["Damage", "damage", "伤害值", "伤害"],
        "hit_check": ["Hit", "hit", "命中", "命中判定"],
        "block_check": ["doge", "dodge", "block", "格挡", "闪避", "格挡判定"]
    }
    
    # 第二步：读取CSV文件
    for enc in encodings:
        try:
            with open(file_path, encoding=enc) as f:
                reader = csv.DictReader(f)
                # 检查表头是否有效
                if not reader.fieldnames:
                    print(f"⚠️ 编码{enc}读取到空表头")
                    continue
                # 读取所有行
                for row in reader:
                    clean_row = {k.strip(): str(v).strip() for k, v in row.items()}
                    rows.append(clean_row)
            print(f"✅ 使用编码 {enc} 成功读取 {filename}，共 {len(rows)} 行数据")
            break
        except Exception as e:
            print(f"⚠️ 编码{enc}读取失败：{e}")
            continue
    
    if not rows:
        print(f"❌ 无法读取 {filename} 中的有效数据！将使用默认敌人")
        ENEMY_DATA["purplemaze"] = {
            "number": 1,
            "hp": 5,
            "damage": 1,
            "hit_check": "3+",
            "block_check": "3+",
            "base_attack_times": 1
        }
        return
    
    # 第三步：解析每行数据（兼容多字段名）
    for idx, r in enumerate(rows):
        # 查找敌人名称（核心字段）
        enemy_name = None
        for possible_name in field_mapping["name"]:
            if possible_name in r and r[possible_name].strip():
                enemy_name = r[possible_name].strip()
                break
        if not enemy_name:
            print(f"⚠️ 第{idx+1}行数据缺少敌人名称，跳过")
            continue
        
        # 解析其他字段（兼容多字段名）
        def get_field_value(field_key):
            for possible_field in field_mapping[field_key]:
                if possible_field in r:
                    return r[possible_field].strip()
            return ""
        
        # 组装敌人数据
        ENEMY_DATA[enemy_name] = {
            "number": safe_int(get_field_value("number"), 1),
            "hp": safe_int(get_field_value("hp"), 5),
            "damage": safe_int(get_field_value("damage"), 1),
            "hit_check": safe_str(get_field_value("hit_check"), "3+"),
            "block_check": safe_str(get_field_value("block_check"), "3+"),
            "base_attack_times": 1
        }
    
    # 输出加载结果
    print(f"✅ 成功加载 {len(ENEMY_DATA)} 个NPC数据：{list(ENEMY_DATA.keys())}")
    if not ENEMY_DATA:
        # 兜底：确保至少有一个默认敌人
        ENEMY_DATA["purplemaze"] = {
            "number": 1,
            "hp": 5,
            "damage": 1,
            "hit_check": "3+",
            "block_check": "3+",
            "base_attack_times": 1
        }

def init_player_deck(battle_params):
    global PLAYER_DECK, PLAYER_HAND, PLAYER_DISCARD, INITIAL_DECK
    PLAYER_DECK = []
    PLAYER_HAND = []
    PLAYER_DISCARD = []
    INITIAL_DECK = []

    purchased_cards = []
    if battle_params and "已购卡牌" in battle_params:
        purchased_cards = battle_params.get("已购卡牌", [])
    elif battle_params and "已购卡牌详情" in battle_params:
        purchased = battle_params.get("已购卡牌详情", {})
        for cid, info in purchased.items():
            n = info.get("持有数量", 1)
            for _ in range(n):
                purchased_cards.append(info.copy())

    total = 0

    if not purchased_cards:
        default_cards = [
            {"编号":1,"卡名":"步行","卡牌类型":"移动","能量消耗":0,"移动值":1,"伤害值":0,"防御值":0,"能量增益":0,"持有数量":4,"描述":"基础移动卡","价格":2},
            {"编号":5,"卡名":"轻击","卡牌类型":"伤害","能量消耗":0,"移动值":0,"伤害值":1,"防御值":0,"能量增益":0,"持有数量":4,"描述":"基础伤害卡","价格":2},
            {"编号":9,"卡名":"木盾","卡牌类型":"防御","能量消耗":0,"移动值":0,"伤害值":0,"防御值":1,"能量增益":0,"持有数量":4,"描述":"基础防御卡","价格":2},
            {"编号":13,"卡名":"小型魔力源","卡牌类型":"能量","能量消耗":1,"移动值":0,"伤害值":0,"防御值":0,"能量增益":1,"持有数量":4,"描述":"基础能量卡","价格":2},
        ]
        for card in default_cards:
            n = card.get("持有数量", 1)
            for _ in range(n):
                if total >=16: break
                PLAYER_DECK.append(card.copy())
                INITIAL_DECK.append(card.copy())
                total +=1
    else:
        card_count = {}
        for card in purchased_cards:
            card_id = card.get("编号")
            if card_id not in card_count:
                card_count[card_id] = {
                    "card": card,
                    "count": 0
                }
            card_count[card_id]["count"] += 1

        for cid, info in card_count.items():
            card = info["card"]
            n = info["count"]
            for _ in range(n):
                if total >=16: break
                card_copy = card.copy()
                PLAYER_DECK.append(card_copy)
                INITIAL_DECK.append(card_copy)
                total +=1

    need = 16 - len(PLAYER_DECK)
    if need > 0:
        basic_attack = {"编号":5,"卡名":"轻击","卡牌类型":"伤害","能量消耗":0,"移动值":0,"伤害值":1,"防御值":0,"能量增益":0,"持有数量":1,"描述":"基础伤害卡","价格":2}
        for _ in range(need):
            PLAYER_DECK.append(basic_attack.copy())
            INITIAL_DECK.append(basic_attack.copy())

    if len(PLAYER_DECK) > 16:
        PLAYER_DECK = PLAYER_DECK[:16]
        INITIAL_DECK = INITIAL_DECK[:16]

    random.shuffle(PLAYER_DECK)

    # ========== 加载装备属性（仅存储原始字符串，不再开局固定掷骰） ==========
    weapon_name = pd.PLAYER["attributes"].get("装备1")

    for w in wd.WEAPONS:
        if w["武器名"] == weapon_name:
            PLAYER_ATTR["weapon"] = w["武器名"]
            PLAYER_ATTR["base_damage"] = w["伤害"]
            PLAYER_ATTR["hit_check"] = w["命中"]
            PLAYER_ATTR["block_check"] = w["格挡"]
            PLAYER_ATTR["dodge_check"] = w.get("闪避", "3+")
            
            # 仅读取并存储骰子原始字符串，不做开局固定掷骰
            extra_atk_str = w.get("额外攻击次数", "0")
            extra_def_str = w.get("额外防御次数", "0")
            
            # 存入全局 PLAYER_ATTR
            PLAYER_ATTR["extra_attack_str"] = extra_atk_str
            PLAYER_ATTR["extra_defense_str"] = extra_def_str
            
            # 日志
            print(f"装备【{weapon_name}】额外攻击次数：{extra_atk_str}（战斗中实时掷骰）")
            print(f"装备【{weapon_name}】额外防御次数：{extra_def_str}（战斗中实时掷骰）")
            break

    # ========== 计算最终的闪避/格挡阈值 ==========
    PLAYER_ATTR["dodge_check"] = get_dodge_threshold_str()
    PLAYER_ATTR["block_check"] = get_block_threshold_str()

def draw_cards():
    global PLAYER_HAND, PLAYER_DECK, PLAYER_DISCARD, INITIAL_DECK
    PLAYER_HAND = []
    draw = 0

    while draw < 4:
        if not PLAYER_DECK:
            PLAYER_DECK = [card.copy() for card in INITIAL_DECK]
            random.shuffle(PLAYER_DECK)
            PLAYER_DISCARD = []

        PLAYER_HAND.append(PLAYER_DECK.pop(0))
        draw += 1

    while len(PLAYER_HAND) < 4:
        PLAYER_HAND.append({"编号":5,"卡名":"轻击","卡牌类型":"伤害","能量消耗":0,"移动值":0,"伤害值":1,"防御值":0,"能量增益":0,"持有数量":1,"描述":"基础伤害卡","价格":2})

def apply_card_effect(card, player_energy):
    msg = []
    energy_cost = safe_int(card.get("能量消耗", 0))
    card_type = safe_str(card.get("卡牌类型"))

    move_value    = safe_int(card.get("移动值", 0))
    damage_value  = safe_int(card.get("伤害值", 0))
    defense_value = safe_int(card.get("防御值", 0))
    energy_gain   = safe_int(card.get("能量增益", 0))

    is_energy = (card_type == "能量")
    is_attack = (card_type == "伤害")
    is_block  = (card_type == "防御")
    is_dodge  = (card_type == "移动")

    times_bonus = 0
    if is_attack:
        times_bonus = damage_value
    elif is_block:
        times_bonus = defense_value
    elif is_dodge:
        times_bonus = move_value
    elif is_energy:
        times_bonus = energy_gain

    if energy_cost > player_energy:
        msg.append(f"能量不足！需要{energy_cost}，当前{player_energy}")
        return 0, 0, 1, "; ".join(msg), player_energy, False, True, is_attack, is_block, is_dodge, times_bonus

    player_energy -= energy_cost
    msg.append(f"消耗{energy_cost}能量（剩余：{player_energy}）")

    if is_energy:
        multiply = energy_gain if energy_gain > 0 else 1
        return 0, 0, multiply, "; ".join(msg), player_energy, is_energy, False, is_attack, is_block, is_dodge, times_bonus

    actual_bonus = 0
    if is_dodge:
        threshold = parse_check_condition(PLAYER_ATTR["dodge_check"])
        dodge_logs = []
        for idx in range(1, times_bonus + 1):
            roll = random.randint(1, 6)
            success = roll >= threshold
            dodge_logs.append(f"闪避{idx}次：掷骰{roll} | 需要{threshold}+ → {'成功' if success else '失败'}")
            if success:
                actual_bonus += 1
        msg.append(" | ".join(dodge_logs))
        msg.append(f"最终生效闪避次数：{actual_bonus}")

    elif is_block:
        threshold = parse_check_condition(PLAYER_ATTR["block_check"])
        block_logs = []
        for idx in range(1, times_bonus + 1):
            roll = random.randint(1, 6)
            success = roll >= threshold
            block_logs.append(f"格挡{idx}次：掷骰{roll} | 需要{threshold}+ → {'成功' if success else '失败'}")
            if success:
                actual_bonus += 1
        msg.append(" | ".join(block_logs))
        msg.append(f"最终生效格挡次数：{actual_bonus}")

    elif is_attack:
        actual_bonus = times_bonus
        msg.append(f"攻击次数 +{actual_bonus}")

    times_bonus = actual_bonus

    return 0, 0, 1, "; ".join(msg), player_energy, is_energy, False, is_attack, is_block, is_dodge, times_bonus

def create_battle_ui(main_root, game_event, battle_params):
    if not ENEMY_DATA:
        load_enemy_data()

    init_player_deck(battle_params)

    event_name = safe_str(game_event.get("name", "事件"))
    enemy_name = safe_str(game_event.get("角色", "purplemaze"))
    cnt = safe_int(game_event.get("数量", 1))

    # ========== 修复：敌人名称匹配优化 ==========
    # 1. 先精确匹配
    if enemy_name not in ENEMY_DATA:
        # 2. 模糊匹配（忽略大小写、空格）
        target_name = enemy_name.lower().replace(" ", "")
        matched_name = None
        for name in ENEMY_DATA.keys():
            if name.lower().replace(" ", "") == target_name:
                matched_name = name
                break
        # 3. 仍未匹配则用第一个敌人或默认
        if matched_name:
            enemy_name = matched_name
            print(f"✅ 模糊匹配到敌人：{enemy_name}（原始输入：{game_event.get('角色')}）")
        else:
            # 取第一个加载的敌人，没有则用默认
            enemy_name = next(iter(ENEMY_DATA.keys())) if ENEMY_DATA else "purplemaze"
            print(f"⚠️ 未找到敌人 {game_event.get('角色')}，使用默认：{enemy_name}")
    
    npc_data = ENEMY_DATA.get(enemy_name, {
        "hp":5, "damage":1, "hit_check":"3+", "block_check":"3+", "base_attack_times":1
    })

    npc_hp_single = safe_int(npc_data.get("hp", 5))
    npc_damage_per_hit = safe_int(npc_data.get("damage", 1))
    npc_hit_check = safe_str(npc_data.get("hit_check", "3+"))
    npc_block_check = safe_str(npc_data.get("block_check", "3+"))
    total_npc_hp = npc_hp_single * cnt

    # ========== 读取角色坚韧属性计算生命值 ==========
    toughness = safe_int(pd.PLAYER["attributes"].get("Toughness", 0))
    player_hp = pd.PLAYER["current_hp"]
    player_energy = 10
    next_attack_multiply = 1  # 下一回合攻击倍数
    current_defense_multiply = 1  # 本回合防御倍数
    energy_used_in_phase = False

    current_attack_times = 0
    current_block_times = 0
    current_dodge_times = 0

    round_num = 1
    battle_over = False
    player_turn = True
    react_phase = False
    played_react_card = False
    npc_actual_hit = 0

    battle_win = Toplevel(main_root)
    battle_win.title(f"第{round_num}回合 - {enemy_name} × {cnt} | 玩家：{pd.PLAYER['name']}")
    battle_win.geometry("1400x850")
    battle_win.configure(bg="#f5f5f5")
    battle_win.transient(main_root)
    battle_win.grab_set()

    top_frame = Frame(battle_win, bg="#2c3e50")
    top_frame.pack(fill="x", padx=10, pady=10)

    def update_status():
        # 实时计算最新阈值
        dodge_threshold = parse_check_condition(get_dodge_threshold_str())
        block_threshold = parse_check_condition(get_block_threshold_str())
        
        player_status_text = (
            f"👤 玩家: {pd.PLAYER['name']} | 💖 生命: {player_hp} | ⚡ 能量: {player_energy} | 🗡️ 装备: {PLAYER_ATTR['weapon']} "
            f"| 🎯 单次伤害: {PLAYER_ATTR['base_damage']} | ⚔️ 攻击次数: {current_attack_times} "
            f"| 🛡️ 格挡次数: {current_block_times} (阈值{block_threshold}+) | ✨ 闪避次数: {current_dodge_times} (阈值{dodge_threshold}+)"
            f"| 🔋 下回合攻击倍数: ×{next_attack_multiply} | 🛡️ 本回合防御倍数: ×{current_defense_multiply}"
            f"| 🚫 本阶段能量卡已用: {'是' if energy_used_in_phase else '否'}"
            f"| 📌 装备加成: 攻击({PLAYER_ATTR['extra_attack_str']}) 格挡({PLAYER_ATTR['extra_defense_str']})（实时掷骰）"
        )

        npc_status_text = (
            f"👹 {enemy_name} × {cnt} | ❤️ 总生命: {max(total_npc_hp, 0)} | ⚔️ 单次伤害: {npc_damage_per_hit} "
            f"| 🎯 命中判定: {npc_hit_check} | 🛡️ 格挡判定: {npc_block_check}"
        )

        player_status.config(text=player_status_text, wraplength=800)
        enemy_status.config(text=npc_status_text, wraplength=600)
        battle_win.update()

    player_status = Label(
        top_frame, text="", font=("微软雅黑", 12),
        bg="#2c3e50", fg="white", anchor="w"
    )
    player_status.pack(side="left", padx=20, fill="x", expand=True)

    enemy_status = Label(
        top_frame, text="", font=("微软雅黑", 12),
        bg="#2c3e50", fg="white", anchor="e"
    )
    enemy_status.pack(side="right", padx=20, fill="x", expand=True)

    # ===================== 按钮 =====================
    button_frame = Frame(battle_win, bg="#f5f5f5")
    button_frame.pack(fill="x", padx=10, pady=5)

    def skip_play_phase():
        nonlocal player_turn
        if not player_turn or react_phase or battle_over:
            add_log("❌ 当前无法跳过出牌阶段！")
            return
        player_turn = False
        add_log("📢 玩家跳过出牌阶段，进入攻击判定！")
        skip_play_btn.config(state="disabled")
        player_attack_phase()

    def skip_react_phase():
        nonlocal react_phase, played_react_card
        if not react_phase or battle_over or played_react_card:
            add_log("❌ 当前无法跳过反应阶段！")
            return
        react_phase = False
        played_react_card = True
        react_label.config(text="")
        skip_react_btn.config(state="disabled")
        add_log("📢 玩家跳过反应阶段，进入伤害结算！")
        calculate_damage()

    skip_play_btn = Button(button_frame, text="跳过出牌阶段", command=skip_play_phase,
                          font=("微软雅黑", 11), bg="#3498db", fg="white", padx=20, pady=5, state="disabled")
    skip_play_btn.pack(side="left", padx=5)

    skip_react_btn = Button(button_frame, text="跳过反应阶段", command=skip_react_phase,
                           font=("微软雅黑", 11), bg="#e74c3c", fg="white", padx=20, pady=5, state="disabled")
    skip_react_btn.pack(side="left", padx=5)

    # ===================== 日志 =====================
    log_queue = []
    log_frame = Frame(battle_win, bg="white", bd=1, relief="solid")
    log_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

    Label(log_frame, text="战斗日志", font=("黑体", 16, "bold"), bg="white").pack(pady=5)
    report_text = Text(log_frame, font=("微软雅黑", 12), state="disabled", height=35)
    report_text.pack(fill="both", expand=True, padx=10, pady=5)

    def add_log(line):
        log_queue.append(line)
        if len(log_queue) == 1:
            show_next_log()

    def show_next_log():
        if not log_queue or battle_over:
            return
        line = log_queue.pop(0)
        report_text.config(state="normal")
        report_text.insert(END, f"【第{round_num}回合】{line}\n")
        report_text.see(END)
        report_text.config(state="disabled")
        battle_win.after(GLOBAL_DELAY, show_next_log)

    # ===================== 手牌 =====================
    hand_frame = Frame(battle_win, bg="white", bd=1, relief="solid")
    hand_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10, ipadx=10)

    Label(hand_frame, text="手牌", font=("黑体", 16, "bold"), bg="white").pack(pady=5)
    react_label = Label(hand_frame, text="", font=("微软雅黑", 11, "bold"), bg="white", fg="orange")
    react_label.pack(pady=5)
    card_container = Frame(hand_frame, bg="white")
    card_container.pack(fill="both", expand=True)

    scroll = Scrollbar(card_container)
    card_listbox = Listbox(card_container, font=("微软雅黑", 11), yscrollcommand=scroll.set, height=20)
    scroll.config(command=card_listbox.yview)
    card_listbox.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    def refresh_hand():
        card_listbox.delete(0, END)
        for i, card in enumerate(PLAYER_HAND, 1):
            name = safe_str(card.get("卡名"))
            card_type = safe_str(card.get("卡牌类型"))
            cost = safe_int(card.get("能量消耗"))
            desc = safe_str(card.get("描述", ""))

            bonus_type = ""
            bonus_value = 0
            if card_type == "伤害":
                bonus_type = "攻击次数"
                bonus_value = safe_int(card.get("伤害值", 0))
            elif card_type == "防御":
                bonus_type = "格挡次数"
                bonus_value = safe_int(card.get("防御值", 0))
            elif card_type == "移动":
                bonus_type = "闪避次数"
                bonus_value = safe_int(card.get("移动值", 0))
            elif card_type == "能量":
                bonus_type = "倍数"
                bonus_value = safe_int(card.get("能量增益", 0))

            display_text = f"{i}.【{name}】| 类型:{card_type} | 耗:{cost} | {bonus_type}+{bonus_value} | {desc}"
            card_listbox.insert(END, display_text)

    def reset_player_times():
        nonlocal current_attack_times, current_block_times, current_dodge_times, react_phase, played_react_card, npc_actual_hit, energy_used_in_phase
        current_attack_times = 0
        current_block_times = 0
        current_dodge_times = 0
        react_phase = False
        played_react_card = False
        npc_actual_hit = 0
        energy_used_in_phase = False

    def player_attack_phase():
        nonlocal total_npc_hp, current_attack_times, battle_over, next_attack_multiply

        if battle_over: return
        
        # ===================== 装备额外攻击次数加成（每次攻击实时掷骰） =====================
        extra_atk_str = PLAYER_ATTR.get("extra_attack_str", "0")
        extra_atk = roll_dice(extra_atk_str)  # 每次攻击都重新roll
        if extra_atk > 0:
            current_attack_times += extra_atk
            add_log(f"⚔️ 装备【{PLAYER_ATTR['weapon']}】额外攻击 +{extra_atk} 次（{extra_atk_str} 本次掷骰结果）！当前总攻击次数: {current_attack_times}")
        
        if current_attack_times <= 0:
            add_log("⚠️ 玩家无攻击次数，跳过攻击")
            npc_counter_attack()
            return

        add_log(f"===== 玩家攻击阶段 ===== | 总攻击次数: {current_attack_times} | 攻击倍数: ×{next_attack_multiply}")

        hit_threshold = parse_check_condition(PLAYER_ATTR["hit_check"])
        actual_hit_times = 0

        for attack_idx in range(1, current_attack_times + 1):
            roll = random.randint(1, 6)
            hit = roll >= hit_threshold
            add_log(f"攻击{attack_idx}次：掷骰{roll} | 命中判定{PLAYER_ATTR['hit_check']} → {'命中' if hit else '未命中'}")
            if hit:
                actual_hit_times += 1

        if actual_hit_times == 0:
            add_log("❌ 所有攻击均未命中！")
            battle_win.after(GLOBAL_DELAY, lambda: npc_block_phase(actual_hit_times))
            return

        add_log(f"✅ 成功命中 {actual_hit_times} 次！进入NPC格挡判定")
        battle_win.after(GLOBAL_DELAY, lambda: npc_block_phase(actual_hit_times))

    def npc_block_phase(player_hit_times):
        nonlocal total_npc_hp, battle_over, next_attack_multiply

        if battle_over: return

        block_threshold = parse_check_condition(npc_block_check)
        npc_block_success = 0

        for block_idx in range(1, player_hit_times + 1):
            roll = random.randint(1, 6)
            block = roll >= block_threshold
            add_log(f"NPC格挡{block_idx}次：掷骰{roll} | 格挡判定{npc_block_check} → {'格挡成功' if block else '失败'}")
            if block:
                npc_block_success += 1

        damage_times = max(0, player_hit_times - npc_block_success)
        total_damage = damage_times * PLAYER_ATTR['base_damage'] * next_attack_multiply

        if damage_times > 0:
            total_npc_hp -= total_damage
            add_log(f"💥 NPC被击中 {damage_times} 次！造成 {total_damage} 点伤害（×{next_attack_multiply}倍） | 剩余生命: {max(total_npc_hp, 0)}")
        else:
            add_log("🛡️ NPC成功格挡所有攻击！")

        # 重置攻击倍数
        next_attack_multiply = 1
        add_log(f"🔋 攻击倍数已重置为 ×{next_attack_multiply}（攻击阶段结束）")

        if total_npc_hp <= 0:
            add_log("🎉 所有敌人已被击败！战斗胜利！")
            battle_over = True
            # 关键修复：战斗胜利后同步玩家血量到全局
            pd.PLAYER["current_hp"] = player_hp
            battle_win.after(GLOBAL_DELAY, battle_win.destroy)
            return

        battle_win.after(GLOBAL_DELAY, npc_counter_attack)

    # ========== 反应阶段函数 ==========
    def on_play_react_card(event):
        nonlocal current_block_times, current_dodge_times, player_energy, played_react_card, battle_over, next_attack_multiply, current_defense_multiply, energy_used_in_phase

        if not react_phase or played_react_card or battle_over:
            return

        idx = card_listbox.curselection()
        if not idx: return
        idx = idx[0]
        if idx >= len(PLAYER_HAND): return

        # 先读取卡牌做前置校验
        card = PLAYER_HAND[idx]
        card_type = safe_str(card.get("卡牌类型"))

        # 1. 反应阶段能量卡重复使用校验
        if card_type == "能量" and energy_used_in_phase:
            add_log(f"❌ 本阶段已使用能量卡，禁止再次使用！卡牌已退回")
            refresh_hand()
            return

        # 2. 反应阶段禁止使用攻击卡
        if card_type == "伤害":
            add_log(f"❌ 反应阶段禁止使用攻击牌！卡牌已退回")
            refresh_hand()
            return

        # 3. 反应阶段仅允许防御/移动/能量卡
        if card_type not in ["防御", "移动", "能量"]:
            add_log(f"❌ 反应阶段仅可使用防御/闪避/能量卡！卡牌已退回")
            refresh_hand()
            return

        # 所有校验通过，正式弹出卡牌
        card = PLAYER_HAND.pop(idx)
        PLAYER_DISCARD.append(card)
        played_react_card = True

        def process_react_card():
            nonlocal player_energy, current_block_times, current_dodge_times, next_attack_multiply, current_defense_multiply, energy_used_in_phase

            if battle_over: return

            # 应用卡牌效果
            _, _, mul, emsg, new_energy, is_energy, no_enough, is_attack, is_block, is_dodge, times_bonus = apply_card_effect(card, player_energy)

            # 能量不足：退回卡牌
            if no_enough:
                add_log(f"❌ {emsg}！卡牌已退回")
                PLAYER_HAND.insert(idx, card)
                PLAYER_DISCARD.pop()
                played_react_card = False
                refresh_hand()
                update_status()
                return

            # 正常处理卡牌逻辑
            player_energy = new_energy
            add_log(f"✅ 反应阶段使用：【{safe_str(card.get('卡名'))}】")
            add_log(f"🎯 卡牌效果：{emsg}")

            if is_energy:
                next_attack_multiply = mul
                energy_used_in_phase = True
                add_log(f"🔋 能量牌生效！下一回合攻击阶段次数加成 ×{mul} 倍（仅单次生效）")
            elif is_block:
                actual_bonus = times_bonus * current_defense_multiply
                if actual_bonus > 0:
                    current_block_times += actual_bonus
                    add_log(f"🛡️ 反应格挡次数增加 {actual_bonus} 次（×{current_defense_multiply}倍） | 当前格挡次数: {current_block_times}")
            elif is_dodge:
                actual_bonus = times_bonus * current_defense_multiply
                if actual_bonus > 0:
                    current_dodge_times += actual_bonus
                    add_log(f"✨ 反应闪避次数增加 {actual_bonus} 次（×{current_defense_multiply}倍） | 当前闪避次数: {current_dodge_times}")

            # 更新界面状态
            update_status()
            refresh_hand()
            react_label.config(text="")
            skip_react_btn.config(state="disabled")
            add_log("----- 反应阶段结束 -----")
            battle_win.after(GLOBAL_DELAY, calculate_damage)

        process_react_card()

    def calculate_damage():
        nonlocal player_hp, battle_over, npc_actual_hit, current_defense_multiply

        if battle_over: return

        total_defense = current_dodge_times + current_block_times
        defense_success = min(total_defense, npc_actual_hit)
        damage_times = max(0, npc_actual_hit - defense_success)

        add_log(f"🛡️ 玩家最终防御：闪避{current_dodge_times} + 格挡{current_block_times} = {total_defense} 次")

        if defense_success > 0:
            add_log(f"✅ 玩家成功防御 {defense_success} 次")

        if damage_times > 0:
            total_damage = damage_times * npc_damage_per_hit
            player_hp -= total_damage
            add_log(f"💥 玩家被击中 {damage_times} 次！受到 {total_damage} 点伤害 | 剩余生命: {player_hp}")
            # 同步玩家血量到全局
            pd.PLAYER["current_hp"] = player_hp
        else:
            add_log("✨ 玩家成功防御所有攻击！无伤")

        # 重置防御倍数
        current_defense_multiply = 1
        add_log(f"🔋 防御倍数已重置为 ×{current_defense_multiply}（反应结算完成）")

        if player_hp <= 0:
            add_log("💀 玩家生命值为0！战斗失败！")
            battle_over = True
            battle_win.after(GLOBAL_DELAY, battle_win.destroy)
            return

        check_battle_result()

    def npc_counter_attack():
        nonlocal player_hp, current_block_times, current_dodge_times, battle_over, react_phase, npc_actual_hit

        if battle_over: return

        add_log(f"===== NPC反击阶段 =====")
        npc_attack_times = random.randint(1, 6)
        add_log(f"👹 {enemy_name} 发起 {npc_attack_times} 次攻击！")

        hit_threshold = parse_check_condition(npc_hit_check)
        npc_actual_hit = 0

        for attack_idx in range(1, npc_attack_times + 1):
            roll = random.randint(1, 6)
            hit = roll >= hit_threshold
            add_log(f"NPC攻击{attack_idx}次：掷骰{roll} | 命中判定{npc_hit_check} → {'命中' if hit else '未命中'}")
            if hit:
                npc_actual_hit += 1

        add_log(f"⚠️ 进入玩家反应阶段（NPC实际命中 {npc_actual_hit} 次）")
        react_phase = True
        played_react_card = False
        
        # ===================== 装备额外防御次数（每次反击实时掷骰） =====================
        extra_def_str = PLAYER_ATTR.get("extra_defense_str", "0")
        extra_def = roll_dice(extra_def_str)  # 每次反击都重新roll
        if extra_def > 0:
            current_block_times += extra_def
            add_log(f"🛡️ 装备【{PLAYER_ATTR['weapon']}】额外格挡 +{extra_def} 次（{extra_def_str} 本次掷骰结果）！当前总格挡次数: {current_block_times}")
        
        react_label.config(text="📢 反应阶段：可打出1张闪避/格挡/能量卡！")
        card_listbox.unbind("<<ListboxSelect>>")
        card_listbox.bind("<<ListboxSelect>>", on_play_react_card)
        refresh_hand()
        update_status()
        skip_react_btn.config(state="normal")

        has_react_card = any(safe_str(c.get("卡牌类型")) in ["防御", "移动", "能量"] for c in PLAYER_HAND)
        if not has_react_card:
            add_log("⚠️ 无可用的防御/闪避/能量卡！请点击跳过反应阶段")
            return

        add_log("🟡 请打出1张反应卡，或点击「跳过反应阶段」")

    def check_battle_result():
        nonlocal battle_over

        if total_npc_hp <= 0:
            pd.PLAYER["current_hp"] = player_hp
            add_log("🎉 所有敌人已被击败！战斗胜利！")
            battle_over = True
            battle_win.after(GLOBAL_DELAY, battle_win.destroy)
            return

        next_round()

    def next_round():
        nonlocal round_num, player_turn, current_defense_multiply, battle_over, react_phase, played_react_card

        if battle_over: return

        round_num += 1
        battle_win.title(f"第{round_num}回合 - {enemy_name} × {cnt} | 玩家：{pd.PLAYER['name']}")

        reset_player_times()
        draw_cards()
        refresh_hand()

        # 每回合重新计算阈值
        PLAYER_ATTR["dodge_check"] = get_dodge_threshold_str()
        PLAYER_ATTR["block_check"] = get_block_threshold_str()

        player_turn = True
        react_phase = False
        played_react_card = False
        card_listbox.unbind("<<ListboxSelect>>")
        card_listbox.bind("<<ListboxSelect>>", on_play_card)

        skip_play_btn.config(state="normal")
        skip_react_btn.config(state="disabled")

        add_log(f"===== 第{round_num}回合开始 =====")
        add_log(f"🔋 初始状态 - 下回合攻击倍数: ×{next_attack_multiply} | 本回合防御倍数: ×{current_defense_multiply}")
        add_log(f"🎲 本回合阈值 - 闪避{PLAYER_ATTR['dodge_check']} | 格挡{PLAYER_ATTR['block_check']}")
        add_log(f"📌 装备加成：攻击({PLAYER_ATTR['extra_attack_str']}) 格挡({PLAYER_ATTR['extra_defense_str']})（实时掷骰）")
        add_log("📢 请选择卡牌使用，或点击「跳过出牌阶段」")
        update_status()

    def end_battle():
        nonlocal battle_over
        battle_over = True
        battle_win.after(GLOBAL_DELAY, battle_win.destroy)

    def on_play_card(event):
        nonlocal player_turn, current_attack_times, player_energy, battle_over, energy_used_in_phase, current_defense_multiply

        if not player_turn or battle_over or react_phase:
            return

        idx = card_listbox.curselection()
        if not idx: return
        idx = idx[0]
        if idx >= len(PLAYER_HAND): return

        card = PLAYER_HAND.pop(idx)
        card_type = safe_str(card.get("卡牌类型"))

        # 统一的卡牌退回重置函数
        def restore_play_card():
            PLAYER_HAND.insert(idx, card)
            player_turn = True
            skip_play_btn.config(state="normal")
            card_listbox.unbind("<<ListboxSelect>>")
            card_listbox.bind("<<ListboxSelect>>", on_play_card)
            refresh_hand()
            update_status()
            return

        # 1. 能量卡重复使用校验
        if card_type == "能量" and energy_used_in_phase:
            add_log(f"❌ 本阶段已使用能量卡，禁止再次使用！卡牌已退回")
            restore_play_card()
            return

        # 2. 出牌阶段禁止使用防御/移动卡
        if card_type in ["防御", "移动"]:
            add_log(f"❌ 出牌阶段禁止使用防御/闪避牌！卡牌已退回")
            restore_play_card()
            return

        PLAYER_DISCARD.append(card)

        def process_card():
            nonlocal player_energy, current_attack_times, player_turn, energy_used_in_phase, current_defense_multiply

            if battle_over: return

            _, _, mul, emsg, new_energy, is_energy, no_enough, _, _, _, times_bonus = apply_card_effect(card, player_energy)

            player_energy = new_energy
            add_log(f"✅ 使用卡牌：【{safe_str(card.get('卡名'))}】")
            add_log(f"🎯 卡牌效果：{emsg}")

            if no_enough:
                PLAYER_HAND.insert(idx, card)
                PLAYER_DISCARD.pop()
                restore_play_card()
                return

            if is_energy:
                current_defense_multiply = mul
                energy_used_in_phase = True
                add_log(f"🔋 能量牌生效！本回合防御加成 ×{mul} 倍")
            elif card_type == "伤害":
                actual_bonus = times_bonus * next_attack_multiply
                if actual_bonus > 0:
                    current_attack_times += actual_bonus
                    add_log(f"⚔️ 攻击次数 +{actual_bonus}（×{next_attack_multiply}倍） | 当前：{current_attack_times}")

            update_status()
            refresh_hand()
            skip_play_btn.config(state="disabled")
            add_log("----- 出牌结束 -----")
            player_turn = False
            battle_win.after(GLOBAL_DELAY, player_attack_phase)

        process_card()

    # 初始绑定出牌事件
    card_listbox.bind("<<ListboxSelect>>", on_play_card)

    # 初始化战斗信息
    dodge_threshold = parse_check_condition(PLAYER_ATTR["dodge_check"])
    block_threshold = parse_check_condition(PLAYER_ATTR["block_check"])
    add_log(f"🔥 战斗开始！对手：{cnt}个{enemy_name} | NPC总生命：{total_npc_hp}")
    add_log(f"🎮 玩家：{pd.PLAYER['name']} | 生命{player_hp} | 能量{player_energy}")
    add_log(f"⚔️ 装备：{PLAYER_ATTR['weapon']} | 单次伤害{PLAYER_ATTR['base_damage']}")
    add_log(f"🎲 攻击判定{PLAYER_ATTR['hit_check']} | 闪避{dodge_threshold}+ | 格挡{block_threshold}+")
    add_log(f"📌 装备加成：攻击({PLAYER_ATTR['extra_attack_str']}) 格挡({PLAYER_ATTR['extra_defense_str']})（战斗中实时掷骰）")
    add_log(f"🔋 攻击倍数×{next_attack_multiply} | 防御倍数×{current_defense_multiply}")
    add_log("📢 请选择卡牌使用，或点击「跳过出牌阶段」")

    draw_cards()
    refresh_hand()
    reset_player_times()
    skip_play_btn.config(state="normal")
    update_status()
    battle_win.mainloop()

def trigger_battle(game_event, main_root, battle_params=None):
    if battle_params is None:
        battle_params = pd.get_battle_params()
        if battle_params is None:
            return
    try:
        create_battle_ui(main_root, game_event, battle_params)
    except Exception as e:
        print(f"战斗错误：{e}")
        import traceback
        traceback.print_exc()

if not ENEMY_DATA:
    load_enemy_data()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    # 测试：可以修改这里的角色名称来测试不同敌人
    test_event = {"name": "测试战斗", "角色": "purplemaze", "数量": 1}
    trigger_battle(test_event, root)
    root.mainloop()