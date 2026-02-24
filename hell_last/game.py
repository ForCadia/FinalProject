import tkinter as tk
from tkinter import ttk, messagebox
import csv
import random
import sys
import math

# ===================== 卡牌加载函数 =====================
def load_map_cards(filename):
    maps = []
    with open(filename, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            maps.append({
                "name": row["地图名"],
                "description": row["描述"],
                "effect": row["地图效果"],
                "event": None  # 存储该节点触发的事件
            })
    return maps

def load_event_cards(filename):
    events = []
    with open(filename, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            events.append({
                "name": row["事件名"],
                "description": row["描述"],
                "type": row.get("类型", ""),  # 保留原type列，不影响其他功能
                "effect": row["效果"],
                "关键词": row["关键词"],  # 核心：读取关键词列
                "角色": row.get("角色", ""),  # 战斗专属：敌人角色
                "数量": row.get("数量", ""),  # 战斗专属：敌人数量
                "completed": False  # 仅二次访问地图时设为True
            })
    return events

def load_passage_cards(filename):
    passage = []
    with open(filename, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            passage.append({
                "name": row["通道名"],
                "description": row["描述"],
                "effect": row["效果"]
            })
    return passage

def load_enemy_cards(filename):
    """加载敌人卡（enemycharacter.csv），返回字典：{name: 敌人属性}"""
    enemies = {}
    with open(filename, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            enemies[row["name"]] = {
              #  "number": int(row["number"]),
                "HP": int(row["HP"]),
                "Damage": int(row["Damage"]),
                "Hit": row["Hit"],
                "doge": row["doge"],
                "current_HP": int(row["HP"])  # 新增当前血量，战斗中实时修改
            }
    return enemies

# 新增敌人卡全局加载（和地图/事件/通道卡同级别）
try:
    ENEMY_CARDS = load_enemy_cards("enemycharacter.csv")
except FileNotFoundError as e:
    messagebox.showerror("文件错误", f"未找到敌人卡文件：{e.filename}\n请确保enemycharacter.csv和py文件在同一目录！")
    sys.exit()
except KeyError as e:
    messagebox.showerror("格式错误", f"enemycharacter.csv缺少列名：{e}\n请按指定列名创建！")
    sys.exit()

# 加载卡牌（异常处理，防止文件缺失/列名错误）
try:
    MAP_CARDS = load_map_cards("mapcard.csv")
    EVENT_CARDS = load_event_cards("eventcard.csv")
    PASSAGE_CARDS = load_passage_cards("passagecard.csv")
except FileNotFoundError as e:
    messagebox.showerror("文件错误", f"未找到卡牌文件：{e.filename}\n请确保CSV文件和py文件在同一目录！")
    sys.exit()
except KeyError as e:
    messagebox.showerror("格式错误", f"CSV文件缺少列名：{e}\n请按指定列名创建CSV文件！")
    sys.exit()

# 洗牌：随机打乱卡牌顺序，保证每次探索不同
random.shuffle(MAP_CARDS)
random.shuffle(PASSAGE_CARDS)
random.shuffle(EVENT_CARDS)

# ===================== 游戏类定义（封装节点/通道属性）=====================
class MapNode:
    def __init__(self, map_card, x, y, depth):
        self.map = map_card          # 地图卡信息（名/描述/效果/绑定事件）
        self.passages = []           # 通道列表：[Passage对象]
        self.children = []           # 子节点列表：[MapNode对象]
        self.parent = None           # 父节点：MapNode对象
        self.is_generated = False    # 子节点是否已生成（核心：动态生成）
        # 图形属性
        self.x = x                   # 节点x坐标
        self.y = y                   # 节点y坐标
        self.depth = depth           # 节点深度（用于树状布局）
        self.radius = 25             # 圆圈半径
        self.graph_id = None         # 节点对应的画布图形ID（仅圆圈+名称）

class Passage:
    def __init__(self, passage_card, start_node, end_node):
        self.card = passage_card     # 通道卡信息（名/描述/效果）
        self.start = start_node      # 起点节点
        self.end = end_node          # 终点节点
        # 图形属性
        self.graph_id = None         # 通道对应的画布图形ID（仅线条+名称）
        self.x1, self.y1 = 0, 0      # 线条起点坐标
        self.x2, self.y2 = 0, 0      # 线条终点坐标
        self.mid_x, self.mid_y = 0, 0# 线条中间坐标（Token定位用）

# ===================== 全局变量（游戏+UI）=====================
# 游戏核心参数
game_current_pos = None       # 当前玩家位置：MapNode/Passage对象
game_visited_nodes = []       # 已访问节点列表（用于判断是否二次进图）
game_all_nodes = []           # 所有已绘制节点列表（用于防重合检测）
game_all_passages = []        # 所有已绘制通道列表
game_map_deck = None          # 地图牌库
game_passage_deck = None      # 通道牌库
game_event_deck = None        # 事件牌库

# 树状布局参数（可微调）
ROOT_X = 200               # 根节点x坐标
ROOT_Y = 300               # 根节点y坐标
DEPTH_STEP = 220           # 深度间距（左右）：控制树状横向展开
BRANCH_STEP = 160          # 分支间距（上下）：控制树状纵向分支
NODE_RADIUS = 25           # 节点圆圈半径
COLLISION_THRESHOLD = 50   # 碰撞检测阈值：小于该值判定为重合
TOKEN_RADIUS = 8           # 玩家Token半径（通道中显示更小更精准）

# UI控件
root = None
canvas = None     # 绘图画布（树状小地图）
detail_frame = None# 地图下方详情栏
detail_text = None# 详情栏文本框
tip_label = None  # 中间红色提示标签
stat_label = None # 顶部探索统计标签

# 图形ID映射（画布ID -> 游戏对象）
id_to_node = {}    # 画布ID -> MapNode对象
id_to_passage = {} # 画布ID -> Passage对象

# 战斗系统全局变量
battle_window = None  # 战斗主窗口（覆盖地图的顶级窗口）
battle_canvas = None  # 战斗绘图画布
player_placeholder = None  # 左下玩家占位ID
enemy_placeholders = []    # 右上敌人占位列表（存储ID和属性）
initative_placeholder = None  # 先攻区域占位ID
drawcard_placeholder = None   # 抽卡区域占位ID
current_battle_enemies = []   # 当前战斗敌人列表（角色名+数量）


# ===================== UI提示与详情更新函数 =====================
def show_tip(text, color="#ff0000", delay=3000):
    """
    在画布中间显示提示文本，指定颜色和延迟后淡出
    红色错误提示3秒（默认），成功/效果提示2.5秒，重要提示5秒
    """
    tip_label.config(text=text, fg=color, font=("微软雅黑", 14, "bold"))
    tip_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    # 延迟后隐藏提示
    root.after(delay, lambda: tip_label.place_forget())

def update_detail_text():
    """更新地图下方详情栏：首次进图显事件，二次进图标已完成，通道显详情"""
    detail_text.config(state=tk.NORMAL)
    detail_text.delete(1.0, tk.END)
    content = "【当前位置】\n未开始探索，请从初始地图开始点击相邻通道探索！\n\n【操作规则】\n1. 禁止直接点击相邻地图，必须先点通道\n2. 遵循「地图→通道→地图」的移动逻辑\n3. 首次探索地图触发专属事件，再次进入标为已完成"
    # Token在地图节点上
    if isinstance(game_current_pos, MapNode):
        node = game_current_pos
        # 地图基础信息
        content = f"【地图名称】{node.map['name']}\n\n【地图描述】{node.map['description']}\n\n【地图效果】{node.map['effect']}\n\n"
        # 核心修改：首次进图仅显事件，二次进图加[已完成]批注
        if node.map['event']:
            event = node.map['event']
            # 判断是否二次访问该地图：已在visited_nodes中则标完成
            if node in game_visited_nodes and game_visited_nodes.count(node) >= 2:
                event_title = "【触发事件-已完成】"
            else:
                event_title = "【触发事件】"
            content += f"{event_title} {event['name']}\n\n【事件描述】{event['description']}\n\n【事件类型】{event['type']}\n\n【事件效果】{event['effect']}"
        else:
            content += "【触发事件】暂无专属事件"
    # Token在通道上
    elif isinstance(game_current_pos, Passage):
        passage = game_current_pos
        content = f"【通道名称】{passage.card['name']}\n\n【通道描述】{passage.card['description']}\n\n【通道效果】{passage.card['effect']}\n\n【操作提示】可点击该通道连接的另一地图节点完成移动"
    detail_text.insert(tk.END, content)
    detail_text.config(state=tk.DISABLED)
    # 更新统计信息
    update_stat()

def update_stat():
    """更新顶部探索统计"""
    visited_num = len(set(game_visited_nodes))  # 去重：统计不同地图数量
    draw_num = len(game_all_nodes)
    remain_map = len(game_map_deck)
    remain_event = len([e for e in game_event_deck if not e['completed']]) if game_event_deck else 0
    stat_label.config(
        text=f"探索统计：已探索地图{visited_num}个 | 已绘制地图{draw_num}个 | 剩余地图{remain_map}张 | 剩余事件{remain_event}个"
    )

# ===================== 图形绘制核心函数 =====================
def check_collision(x, y):
    """碰撞检测：检测新坐标是否与已知节点重合，返回重合节点/None"""
    for node in game_all_nodes:
        distance = math.hypot(node.x - x, node.y - y)
        if distance < COLLISION_THRESHOLD:
            return node
    return None

def draw_map_node(node):
    """绘制地图节点（仅圆圈+名称），绑定点击/悬停事件"""
    # 1. 绘制节点圆圈：蓝色边框+白色填充
    circle_id = canvas.create_oval(
        node.x - node.radius, node.y - node.radius,
        node.x + node.radius, node.y + node.radius,
        outline="#0066FF", fill="white", width=3, tags=f"node_{node.depth}"
    )
    # 2. 绘制节点名称（圆圈正中间）
    name_id = canvas.create_text(
        node.x, node.y,
        text=node.map["name"], font=("微软雅黑", 9, "bold"), fill="#000000", width=node.radius*2
    )
    # 保存图形ID
    node.graph_id = (circle_id, name_id)
    # 3. 绑定交互事件
    for gid in node.graph_id:
        id_to_node[gid] = node
        canvas.tag_bind(gid, "<Button-1>", lambda e, n=node: click_node(n))
        # 悬停高亮：圆圈变浅蓝
        canvas.tag_bind(gid, "<Enter>", lambda e, c=circle_id: canvas.itemconfig(c, fill="#E6F7FF"))
        canvas.tag_bind(gid, "<Leave>", lambda e, c=circle_id: canvas.itemconfig(c, fill="white"))
    # 将节点加入已绘制列表
    game_all_nodes.append(node)
    update_canvas_scroll()

def draw_passage(passage):
    """绘制通道（仅线条+名称），计算中间坐标，绑定点击/悬停事件"""
    # 计算线条坐标：起点节点右侧 → 终点节点左侧（避开圆圈）
    passage.x1 = passage.start.x + NODE_RADIUS
    passage.y1 = passage.start.y
    passage.x2 = passage.end.x - NODE_RADIUS
    passage.y2 = passage.end.y
    # 计算通道中间坐标（Token定位核心）
    passage.mid_x = (passage.x1 + passage.x2) / 2
    passage.mid_y = (passage.y1 + passage.y2) / 2
    # 1. 绘制通道线条：黑色+箭头+宽度2
    line_id = canvas.create_line(
        passage.x1, passage.y1, passage.x2, passage.y2,
        fill="#000000", width=2, arrow=tk.LAST, arrowshape=(8, 10, 3)
    )
    # 2. 绘制通道名称（线条中间上方）
    name_id = canvas.create_text(
        passage.mid_x, passage.mid_y - 10,
        text=passage.card["name"], font=("微软雅黑", 9, "bold"), fill="#FF6600", width=80
    )
    # 保存图形ID
    passage.graph_id = (line_id, name_id)
    # 3. 绑定交互事件
    for gid in passage.graph_id:
        id_to_passage[gid] = passage
        canvas.tag_bind(gid, "<Button-1>", lambda e, p=passage: click_passage(p))
        # 悬停高亮：线条变粗+橙红
        canvas.tag_bind(gid, "<Enter>", lambda e, l=line_id: canvas.itemconfig(l, width=4, fill="#FF6600"))
        canvas.tag_bind(gid, "<Leave>", lambda e, l=line_id: canvas.itemconfig(l, width=2, fill="#000000"))
    # 将通道加入已绘制列表
    game_all_passages.append(passage)
    update_canvas_scroll()

def draw_player_token():
    """绘制玩家Token：在节点显示中心，在通道显示中间，精准定位"""
    # 删除旧Token
    for gid in canvas.find_withtag("player_token"):
        canvas.delete(gid)
    if game_current_pos is None:
        return
    # Token在地图节点：中心位置，常规大小
    if isinstance(game_current_pos, MapNode):
        x, y = game_current_pos.x, game_current_pos.y
        radius = TOKEN_RADIUS + 2
    # Token在通道：中间位置，更小更精准
    elif isinstance(game_current_pos, Passage):
        x, y = game_current_pos.mid_x, game_current_pos.mid_y
        radius = TOKEN_RADIUS
    # 绘制Token（红色实心圆，置顶）
    token_id = canvas.create_oval(
        x - radius, y - radius,
        x + radius, y + radius,
        fill="#FF3333", outline="black", width=2, tags="player_token"
    )
    canvas.tag_raise(token_id)  # Token置顶，不被遮挡
    update_canvas_scroll()
    # 绘制Token后自动更新详情
    update_detail_text()

def update_canvas_scroll():
    """更新画布滚动区域，适配树状地图的无限展开"""
    all_coords = canvas.bbox("all")  # 获取所有图形的边界框
    if all_coords:
        canvas.config(scrollregion=all_coords)
    # 自动滚动到当前Token位置
    if game_current_pos:
        if isinstance(game_current_pos, MapNode):
            x, y = game_current_pos.x, game_current_pos.y
        else:
            x, y = game_current_pos.mid_x, game_current_pos.mid_y
        canvas.xview_moveto(max(0, (x - 700) / (all_coords[2] if all_coords else 1600)))
        canvas.yview_moveto(max(0, (y - 300) / (all_coords[3] if all_coords else 600)))

def create_battle_interface(enemy_list):
    """
    创建战斗界面：覆盖地图的顶级窗口，优化分区布局（无拥挤），
    严格按数量显示所有敌人，支持任意数量的敌人呈现
    enemy_list: 战斗敌人列表，格式[(敌人名, 数量), ...]
    """
    global battle_window, battle_canvas, player_placeholder, enemy_placeholders
    global initative_placeholder, drawcard_placeholder, current_battle_enemies
    current_battle_enemies = enemy_list
    
    # 关闭已有战斗窗口（防止重复打开）
    if battle_window:
        battle_window.destroy()
    
    # 创建战斗顶级窗口：全屏覆盖主地图，置顶
    battle_window = tk.Toplevel(root)
    battle_window.title("战斗界面")
    battle_window.geometry(f"{root.winfo_width()}x{root.winfo_height()}")
    battle_window.transient(root)  # 依附主窗口
    battle_window.grab_set()       # 独占焦点，无法操作地图
    battle_window.configure(bg="#1a1a1a")  # 暗黑战斗背景
    
    # 创建战斗画布（占满整个战斗窗口）
    battle_canvas = tk.Canvas(battle_window, bg="#1a1a1a", highlightthickness=0)
    battle_canvas.pack(fill=tk.BOTH, expand=True)
    
    # 初始化占位列表
    enemy_placeholders = []
    # ========== 1. 战斗开始动画：屏幕中心红色闪烁的"战斗开始！" ==========
    battle_start_text = battle_canvas.create_text(
        battle_window.winfo_width()//2, battle_window.winfo_height()//2,
        text="战斗开始！", font=("微软雅黑", 36, "bold"), fill="#ff0000", tags="battle_anim"
    )
    # 闪烁动画函数（动画结束自动删除）
    def flash_anim(alpha=1, step=-0.1):
        if alpha <= 0:
            step = 0.1
        elif alpha >= 1:
            step = -0.1
        color = f"#{int(255*alpha):02x}0000"
        battle_canvas.itemconfig(battle_start_text, fill=color)
        alpha += step
        if alpha > 0:
            battle_window.after(100, lambda: flash_anim(alpha, step))
        else:
            battle_canvas.delete("battle_anim")
    flash_anim()

    # ========== 全局尺寸配置（统一控制，方便修改） ==========
    frame_w = 70     # 敌人/玩家占位框宽度（缩小更适配多数量）
    frame_h = 70     # 敌人/玩家占位框高度
    top_pad = 30     # 顶部边距
    side_pad = 50    # 左右侧边距
    enemy_gap_y = 90 # 不同类型敌人的纵向间距
    enemy_gap_x = 80 # 同类型敌人的横向间距（适配多数量）
    info_font = 10   # 属性文字字号
    name_font = 11   # 名称文字字号（缩小适配多数量）

    # ========== 2. 顶部信息区：左-抽卡区  右-先攻区 ==========
    # 2.1 抽卡区：顶部左侧
    drawcard_x = side_pad + 100
    drawcard_y = top_pad
    drawcard_placeholder = battle_canvas.create_rectangle(
        drawcard_x - 120, drawcard_y - 15, drawcard_x + 120, drawcard_y + 15,
        outline="#8800ff", fill="#26004d", width=2, tags="drawcard"
    )
    battle_canvas.create_text(
        drawcard_x, drawcard_y, text="抽卡区 [预留] | 玩家手牌: 0 | 敌人手牌: 0",
        font=("微软雅黑", 12, "bold"), fill="#8800ff", tags="drawcard"
    )
    # 2.2 先攻区：顶部右侧
    initative_x = battle_window.winfo_width() - (side_pad + 100)
    initative_y = top_pad
    initative_placeholder = battle_canvas.create_rectangle(
        initative_x - 120, initative_y - 15, initative_x + 120, initative_y + 15,
        outline="#ffff00", fill="#333300", width=2, tags="initative"
    )
    battle_canvas.create_text(
        initative_x, initative_y, text="先攻判定 [预留] | 玩家: ? | 敌人: ?",
        font=("微软雅黑", 12, "bold"), fill="#ffff00", tags="initative"
    )

    # ========== 3. 左侧玩家区：中下位置 ==========
    player_x = side_pad + frame_w//2
    player_y = battle_window.winfo_height() - (side_pad + frame_h//2)
    player_placeholder = battle_canvas.create_rectangle(
        player_x - frame_w//2, player_y - frame_h//2,
        player_x + frame_w//2, player_y + frame_h//2,
        outline="#00ffff", fill="#001a33", width=3, tags="player"
    )
    # 玩家名称
    battle_canvas.create_text(
        player_x, player_y - 10, text="玩家", font=("微软雅黑", 14, "bold"),
        fill="#00ffff", tags="player"
    )
    # 玩家属性（预留）
    battle_canvas.create_text(
        player_x, player_y + 15, text=f"HP: ??? | 攻击: ???",
        font=("微软雅黑", info_font), fill="#ffffff", tags="player"
    )

    # ========== 4. 右侧敌人区：严格按数量绘制所有敌人（核心修复） ==========
    enemy_base_x = battle_window.winfo_width() - (side_pad + frame_w//2)  # 敌人基础X坐标
    enemy_start_y = top_pad + 60  # 敌人开始Y坐标（避开顶部信息区）
    
    # 遍历每个敌人类型（解决多类型+多数量显示问题）
    for enemy_type_idx, (enemy_name, count) in enumerate(enemy_list):
        if enemy_name not in ENEMY_CARDS:
            messagebox.showwarning("战斗警告", f"敌人{enemy_name}未在enemycharacter.csv中找到！")
            continue
        enemy_attr = ENEMY_CARDS[enemy_name]
        
        # 计算当前类型敌人的基础Y坐标（不同类型纵向分行）
        current_type_y = enemy_start_y + enemy_type_idx * enemy_gap_y
        
        # ========== 核心修复：循环count次，绘制指定数量的所有敌人 ==========
        for enemy_idx in range(count):
            # 同类型敌人横向偏移（数量越多，越往左排，无重叠）
            enemy_x = enemy_base_x - (enemy_idx * enemy_gap_x)
            enemy_y = current_type_y  # 同类型敌人纵向对齐
            
            # 绘制单个敌人占位框（1:1对应数量）
            enemy_id = battle_canvas.create_rectangle(
                enemy_x - frame_w//2, enemy_y - frame_h//2,
                enemy_x + frame_w//2, enemy_y + frame_h//2,
                outline="#ff4444", fill="#330000", width=2, tags=f"enemy_{enemy_name}_{enemy_idx}"
            )
            # 敌人名称（适配小尺寸）
            battle_canvas.create_text(
                enemy_x, enemy_y - 8, text=enemy_name[:6],  # 名称截断防溢出（如dogmanwithwings→dogman）
                font=("微软雅黑", name_font, "bold"), fill="#ff4444", tags=f"enemy_{enemy_name}_{enemy_idx}"
            )
            # 敌人当前HP
            battle_canvas.create_text(
                enemy_x, enemy_y + 12, text=f"HP: {enemy_attr['current_HP']}",
                font=("微软雅黑", info_font), fill="#ffffff", tags=f"enemy_{enemy_name}_{enemy_idx}"
            )
            # 存储每个敌人的占位信息（精准对应每个绘制的敌人）
            enemy_placeholders.append({
                "id": enemy_id,
                "name": enemy_name,
                "attr": enemy_attr,
                "index": enemy_idx,  # 同类型敌人的索引
                "total_count": count  # 该类型敌人的总数量
            })
    
    # ========== 窗口大小变化时，战斗元素自适应 ==========
    def resize_battle(event):
        # 重新获取窗口尺寸
        w, h = event.width, event.height
        # 更新抽卡区位置
        battle_canvas.coords(drawcard_placeholder, side_pad + 100 - 120, top_pad -15, side_pad +100 +120, top_pad +15)
        battle_canvas.coords(battle_canvas.find_withtag("drawcard")[1], side_pad + 100, top_pad)
        # 更新先攻区位置
        battle_canvas.coords(initative_placeholder, w - (side_pad +100) -120, top_pad -15, w - (side_pad +100) +120, top_pad +15)
        battle_canvas.coords(battle_canvas.find_withtag("initative")[1], w - (side_pad + 100), top_pad)
        # 更新玩家区位置
        battle_canvas.coords(player_placeholder, side_pad, h - side_pad - frame_h, side_pad + frame_w, h - side_pad)
        battle_canvas.coords(battle_canvas.find_withtag("player")[1], side_pad + frame_w//2, h - side_pad - frame_h//2 -10)
        battle_canvas.coords(battle_canvas.find_withtag("player")[2], side_pad + frame_w//2, h - side_pad - frame_h//2 +15)
        # 更新敌人区位置（适配所有数量的敌人）
        enemy_base_x_new = w - (side_pad + frame_w//2)
        for enemy_type_idx, (enemy_name, count) in enumerate(enemy_list):
            current_type_y = enemy_start_y + enemy_type_idx * enemy_gap_y
            for enemy_idx in range(count):
                enemy_x = enemy_base_x_new - (enemy_idx * enemy_gap_x)
                enemy_y = current_type_y
                # 更新对应敌人框和文字坐标
                tag = f"enemy_{enemy_name}_{enemy_idx}"
                for item in battle_canvas.find_withtag(tag):
                    if battle_canvas.type(item) == "rectangle":
                        battle_canvas.coords(item, enemy_x - frame_w//2, enemy_y - frame_h//2,
                                            enemy_x + frame_w//2, enemy_y + frame_h//2)
                    elif battle_canvas.type(item) == "text":
                        if "HP:" in battle_canvas.itemcget(item, "text"):
                            battle_canvas.coords(item, enemy_x, enemy_y + 12)
                        else:
                            battle_canvas.coords(item, enemy_x, enemy_y - 8)
    # 绑定窗口缩放事件
    battle_window.bind("<Configure>", resize_battle)

    
def trigger_battle(event_card):
    """
    触发战斗：解析eventcard的角色和数量列，调用战斗界面
    event_card: 触发的事件卡字典
    """
    try:
        # 解析角色和数量：按格式"角色1,角色2|数量1,数量2"（事件卡中需按此填写）
        enemy_names = event_card["角色"].split(",")  # 角色列：purplemaze,claws
        enemy_counts = list(map(int, event_card["数量"].split(",")))  # 数量列：2,1
        enemy_list = list(zip(enemy_names, enemy_counts))
        # 校验角色和数量长度一致
        if len(enemy_names) != len(enemy_counts):
            messagebox.showerror("战斗错误", "事件卡中角色和数量列数量不匹配！")
            return
        # 校验敌人是否存在
        for enemy_name, _ in enemy_list:
            if enemy_name not in ENEMY_CARDS:
                messagebox.showerror("战斗错误", f"敌人{enemy_name}未在enemycharacter.csv中找到！")
                return
        # 创建战斗界面
        create_battle_interface(enemy_list)
        show_tip(f"触发战斗！遭遇{enemy_list}", "#ff0000", 5000)
    except KeyError as e:
        messagebox.showerror("战斗错误", f"事件卡缺少列名：{e}（需包含角色/数量列）")
    except Exception as e:
        messagebox.showerror("战斗错误", f"解析战斗信息失败：{str(e)}\n请检查事件卡角色/数量列格式（例：purplemaze|2）")

# ===================== 树状节点生成（防重合）=====================
def generate_child_nodes(parent_node):
    """动态生成子节点：防重合检测，重合则直接连已知节点，不消耗新卡"""
    if parent_node.is_generated or not game_map_deck or not game_passage_deck:
        return  # 已生成/牌库空则不生成
    parent_node.is_generated = True  # 标记为已生成，防止重复生成

    # 处理地图效果：修改生成的通道数
    base_num = random.randint(1, 3)
    if parent_node.map["name"] == "迷雾森林" and base_num > 1:
        num_passages = 1
        show_tip("🌫️ 迷雾森林效果：仅生成1条通道！", "#0099ff", 2500)
    elif parent_node.map["name"] == "水晶洞穴" and base_num < 3:
        num_passages = base_num + 1
        show_tip("💎 水晶洞穴效果：通道数+1！", "#0099ff", 2500)
    else:
        num_passages = base_num

    # 计算子节点的y坐标（树状分支：上下均分）
    y_offsets = []
    if num_passages == 1:
        y_offsets = [0]
    elif num_passages == 2:
        y_offsets = [-BRANCH_STEP//2, BRANCH_STEP//2]
    elif num_passages >= 3:
        y_offsets = [-BRANCH_STEP, 0, BRANCH_STEP][:num_passages]

    # 生成子节点和通道
    for i, y_offset in enumerate(y_offsets):
        if not game_passage_deck:
            show_tip("🚫 通道牌库为空，停止生成！", "#ff9900", 3000)
            break
        # 1. 计算子节点坐标
        child_x = parent_node.x + DEPTH_STEP
        child_y = parent_node.y + y_offset
        child_depth = parent_node.depth + 1
        # 2. 碰撞检测
        collision_node = check_collision(child_x, child_y)
        passage_card = game_passage_deck.pop()  # 消耗通道卡
        
        if collision_node:
            # 重合：不消耗地图卡，直接连接已知节点
            show_tip(f"📍 坐标重合，连接{parent_node.map['name']}与{collision_node.map['name']}", "#0099ff", 2500)
            new_node = collision_node
        else:
            # 不重合：消耗地图卡，创建新节点
            if not game_map_deck:
                show_tip("🚫 地图牌库为空，无法生成新节点！", "#ff9900", 3000)
                break
            map_card = game_map_deck.pop()
            new_node = MapNode(map_card, child_x, child_y, child_depth)
            new_node.parent = parent_node
            parent_node.children.append(new_node)
            draw_map_node(new_node)
        
        # 3. 创建并绘制通道
        passage = Passage(passage_card, parent_node, new_node)
        parent_node.passages.append(passage)
        draw_passage(passage)

# ===================== 核心交互逻辑（强制通道移动+事件状态控制）=====================
def click_node(target_node):
    """点击地图节点的逻辑：强制通道移动，记录访问次数（用于事件已完成判定）"""
    global game_current_pos
    # 情况1：当前位置是初始状态（未探索）
    if game_current_pos is None:
        game_current_pos = target_node
        game_visited_nodes.append(target_node)  # 首次访问，加入列表
        draw_player_token()
        explore_node(target_node)
        return
    # 情况2：当前位置是该节点本身
    if target_node == game_current_pos:
        show_tip(f"你已在{target_node.map['name']}，无需重复点击！")
        return
    # 情况3：当前位置是通道，且通道连接该节点 → 允许移动（通道→节点）
    if isinstance(game_current_pos, Passage):
        if game_current_pos.start == target_node or game_current_pos.end == target_node:
            game_current_pos = target_node
            game_visited_nodes.append(target_node)  # 记录每次访问，用于统计次数
            draw_player_token()
            # 首次访问该节点则探索（必触发事件）
            if game_visited_nodes.count(target_node) == 1:
                explore_node(target_node)
                show_tip(f"🔍 首次探索{target_node.map['name']}，触发专属事件！", "#0099ff", 2500)
            else:
                # 二次及以后访问，标事件为已完成
                if target_node.map['event']:
                    target_node.map['event']['completed'] = True
                show_tip(f"移动成功！再次到达{target_node.map['name']}", "#00cc00", 2500)
            return
        else:
            show_tip("该节点与当前通道无连接，无法移动！")
            return
    # 情况4：当前位置是节点，直接点击其他节点 → 禁止（强制先点通道）
    if isinstance(game_current_pos, MapNode):
        show_tip("禁止直接点击地图！必须先点击相邻通道再移动！")
        return

def click_passage(target_passage):
    """点击通道的逻辑：仅允许点击当前节点的相邻通道"""
    global game_current_pos
    # 情况1：当前位置是初始状态 → 提示先从初始节点开始
    if game_current_pos is None:
        show_tip("请先从初始地图开始探索，再点击通道！")
        return
    # 情况2：当前位置是节点，通道是该节点的相邻通道 → 允许进入通道（节点→通道）
    if isinstance(game_current_pos, MapNode):
        if target_passage.start == game_current_pos or target_passage.end == game_current_pos:
            game_current_pos = target_passage
            draw_player_token()
            show_tip(f"进入通道{target_passage.card['name']}，可点击连接的另一地图移动", "#00cc00", 2500)
            return
        else:
            show_tip("该通道与当前地图无连接，无法进入！")
            return
    # 情况3：当前位置是通道本身 → 提示点击连接的地图
    if isinstance(game_current_pos, Passage):
        if target_passage == game_current_pos:
            show_tip(f"已在{target_passage.card['name']}，请点击通道连接的另一地图！")
            return
        else:
            show_tip("请先从当前通道移动到地图，再进入其他通道！")
            return
        

def explore_node(node):
    """探索节点：仅首次到达时执行，抽事件卡+动态生成子节点（首次仅绑定事件，不标完成）"""
    show_tip(f"🔍 正在探索{node.map['name']}，生成通道并触发事件...", "#0099ff", 5000)
    # 抽事件卡（仅首次探索，强制触发，不标完成）
    if game_event_deck and not node.map['event']:
        event = game_event_deck.pop()
        node.map['event'] = event   # 绑定事件，completed保持False
        show_tip(f"🎴 触发专属事件：{event['name']}", "#ffcc00", 2500)
        
        # ========== 新增：战斗事件触发判断（核心代码） ==========
        # ========== 新增：战斗事件触发判断（核心代码：关键词含战斗则触发） ==========
        if "战斗" in event["关键词"]:
           trigger_battle(event)  # 调用战斗函数
# ======================================================
        # ======================================================
        
        # 立即更新详情栏，首次进图就能看到事件
        update_detail_text()
    elif not node.map['event']:
        show_tip("📭 该地图无专属事件，直接生成通道！", "#0099ff", 2500)
    # 动态生成子节点
    generate_child_nodes(node)
    # 游戏结束判定
    if not game_map_deck and len(set(game_visited_nodes)) == len(game_all_nodes):
        show_tip(f"🎮 游戏结束！已探索所有{len(set(game_visited_nodes))}个地图！", "#ff00ff", 5000)

# ===================== 游戏UI构建（精简版：顶部统计+中间地图+下方详情）=====================
def create_game_ui():
    """创建完整的游戏UI：顶部统计+中间地图（带提示）+下方详情，无日志栏"""
    global root, canvas, detail_frame, detail_text, tip_label, stat_label
    # 主窗口
    root = tk.Tk()
    root.title("树状地图探索游戏 - 强制通道移动版")
    root.geometry("1400x800")
    root.resizable(True, True)
    root.config(bg="#f5f5f5")

    # 修复核心：为ttk.LabelFrame设置字体样式
    style = ttk.Style(root)
    style.configure('Custom.TLabelframe.Label', font=("微软雅黑", 14, "bold"))

    # 顶部：探索统计栏
    stat_label = tk.Label(
        root, text="探索统计：已探索地图0个 | 已绘制地图0个 | 剩余地图0张 | 剩余事件0个",
        font=("微软雅黑", 12, "bold"), bg="#ffffff", fg="#333333", pady=10, padx=20
    )
    stat_label.pack(fill=tk.X, padx=20, pady=(10, 0))

    # 中间：地图画布容器（带滚动条+红色提示）
    canvas_container = ttk.Frame(root, width=1360, height=450)
    canvas_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    # 画布滚动条
    canvas_xscroll = ttk.Scrollbar(canvas_container, orient=tk.HORIZONTAL)
    canvas_xscroll.pack(side=tk.BOTTOM, fill=tk.X)
    canvas_yscroll = ttk.Scrollbar(canvas_container, orient=tk.VERTICAL)
    canvas_yscroll.pack(side=tk.RIGHT, fill=tk.Y)
    # 核心画布
    canvas = tk.Canvas(
        canvas_container, bg="#ffffff",
        xscrollcommand=canvas_xscroll.set, yscrollcommand=canvas_yscroll.set
    )
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    canvas_xscroll.config(command=canvas.xview)
    canvas_yscroll.config(command=canvas.yview)
    # 中间红色提示标签（初始隐藏）
    tip_label = tk.Label(canvas, bg="#ffffff", bd=0)
    tip_label.place_forget()

    # 下方：固定详情栏 - 使用自定义样式解决font参数错误
    detail_frame = ttk.LabelFrame(root, text="当前位置详情", style='Custom.TLabelframe', labelanchor=tk.N)
    detail_frame.pack(fill=tk.BOTH, expand=False, padx=20, pady=(0, 10))
    # 详情文本框
    detail_text = tk.Text(
        detail_frame, font=("Consolas", 11), bg="#f8f8f8", fg="#000000",
        wrap=tk.WORD, state=tk.DISABLED, spacing1=5, spacing3=5
    )
    detail_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # 初始化游戏
    init_game()

    # 运行UI主循环
    root.mainloop()

def init_game():
    """游戏初始化：创建根节点+初始化牌库+绘制初始界面"""
    global game_current_pos, game_visited_nodes, game_all_nodes, game_all_passages
    global game_map_deck, game_passage_deck, game_event_deck
    # 初始化牌库和列表
    game_map_deck = MAP_CARDS.copy()
    game_passage_deck = PASSAGE_CARDS.copy()
    game_event_deck = EVENT_CARDS.copy()
    game_visited_nodes = []
    game_all_nodes = []
    game_all_passages = []
    game_current_pos = None

    # 创建根节点（深度0，树状起点）
    if not game_map_deck:
        show_tip("❌ 地图牌库为空，无法开始游戏！", "#ff0000", 5000)
        return
    root_map = game_map_deck.pop()
    root_node = MapNode(root_map, ROOT_X, ROOT_Y, depth=0)
    root_node.is_generated = False
    # 绘制根节点
    draw_map_node(root_node)
    # 初始化详情和统计
    update_detail_text()
    update_stat()
    show_tip(f"🎉 游戏开始！初始地图：{root_node.map['name']}，请点击其相邻通道开始探索", "#00cc00", 5000)

# ===================== 程序入口 =====================
if __name__ == "__main__":
    create_game_ui()