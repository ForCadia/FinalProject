import tkinter as tk
from tkinter import ttk, messagebox
import csv
import random
import sys
import math
import os  # 新增：处理路径

# ===================== 核心修复：绝对路径处理 =====================
def get_script_dir():
    """获取当前代码文件所在的绝对目录"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def safe_path(filename):
    """拼接绝对路径"""
    return os.path.join(get_script_dir(), filename)

# ===================== 全局变量（探索相关）=====================
PLAYER_BATTLE_PARAMS = None  # 存储已购卡牌等核心参数
PLAYER_STATUS = {            # 新增：存储玩家状态（血量/属性），同步战斗结果
    "current_hp": 0,
    "max_hp": 0,
    "attributes": {}
}

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

# UI控件（全局，供main.py调用）
root = None
canvas = None     # 绘图画布（树状小地图）
detail_frame = None# 地图下方详情栏
detail_text = None# 详情栏文本框
tip_label = None  # 中间红色提示标签
stat_label = None # 顶部探索统计标签
hp_label = None   # 新增：玩家血量显示标签

# 图形ID映射（画布ID -> 游戏对象）
id_to_node = {}    # 画布ID -> MapNode对象
id_to_passage = {} # 画布ID -> Passage对象

# ===================== 卡牌加载函数（修复路径） =====================
def load_map_cards(filename):
    maps = []
    file_path = safe_path(filename)  # 转绝对路径
    try:
        with open(file_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                maps.append({
                    "name": row["地图名"],
                    "description": row["描述"],
                    "effect": row["地图效果"],
                    "event": None  # 存储该节点触发的事件
                })
        print(f"✅ 成功加载 {len(maps)} 张地图卡")
        return maps
    except FileNotFoundError:
        messagebox.showerror("文件错误", f"未找到地图文件：{file_path}")
        sys.exit()
    except KeyError as e:
        messagebox.showerror("格式错误", f"地图CSV缺少列名：{e}")
        sys.exit()

def load_event_cards(filename):
    events = []
    file_path = safe_path(filename)  # 转绝对路径
    try:
        with open(file_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                events.append({
                    "name": row["事件名"],
                    "description": row["描述"],
                    "type": row.get("类型", ""),
                    "effect": row["效果"],
                    "关键词": row["关键词"],  # 战斗触发关键词
                    "角色": row.get("角色", ""),
                    "数量": row.get("数量", ""),
                    "completed": False
                })
        print(f"✅ 成功加载 {len(events)} 张事件卡")
        return events
    except FileNotFoundError:
        messagebox.showerror("文件错误", f"未找到事件文件：{file_path}")
        sys.exit()
    except KeyError as e:
        messagebox.showerror("格式错误", f"事件CSV缺少列名：{e}")
        sys.exit()

def load_passage_cards(filename):
    passage = []
    file_path = safe_path(filename)  # 转绝对路径
    try:
        with open(file_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                passage.append({
                    "name": row["通道名"],
                    "description": row["描述"],
                    "effect": row["效果"]
                })
        print(f"✅ 成功加载 {len(passage)} 张通道卡")
        return passage
    except FileNotFoundError:
        messagebox.showerror("文件错误", f"未找到通道文件：{file_path}")
        sys.exit()
    except KeyError as e:
        messagebox.showerror("格式错误", f"通道CSV缺少列名：{e}")
        sys.exit()

# ===================== 游戏类定义 ======================
class MapNode:
    def __init__(self, map_card, x, y, depth):
        self.map = map_card          # 地图卡信息
        self.passages = []           # 通道列表
        self.children = []           # 子节点列表
        self.parent = None           # 父节点
        self.is_generated = False    # 子节点是否已生成
        # 图形属性
        self.x = x
        self.y = y
        self.depth = depth
        self.radius = 25
        self.graph_id = None

class Passage:
    def __init__(self, passage_card, start_node, end_node):
        self.card = passage_card
        self.start = start_node
        self.end = end_node
        # 图形属性
        self.graph_id = None
        self.x1, self.y1 = 0, 0
        self.x2, self.y2 = 0, 0
        self.mid_x, self.mid_y = 0, 0

# ===================== UI提示与详情更新函数 =====================
def show_tip(text, color="#ff0000", delay=3000):
    """在画布中间显示提示文本"""
    tip_label.config(text=text, fg=color, font=("微软雅黑", 14, "bold"))
    tip_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    root.after(delay, lambda: tip_label.place_forget())

def update_detail_text():
    """更新地图下方详情栏"""
    detail_text.config(state=tk.NORMAL)
    detail_text.delete(1.0, tk.END)
    content = "【当前位置】\n未开始探索，请从初始地图开始点击相邻通道探索！\n\n【操作规则】\n1. 禁止直接点击相邻地图，必须先点通道\n2. 遵循「地图→通道→地图」的移动逻辑\n3. 首次探索地图触发专属事件，再次进入标为已完成"
    
    if isinstance(game_current_pos, MapNode):
        node = game_current_pos
        content = f"【地图名称】{node.map['name']}\n\n【地图描述】{node.map['description']}\n\n【地图效果】{node.map['effect']}\n\n"
        if node.map['event']:
            event = node.map['event']
            if node in game_visited_nodes and game_visited_nodes.count(node) >= 2:
                event_title = "【触发事件-已完成】"
            else:
                event_title = "【触发事件】"
            content += f"{event_title} {event['name']}\n\n【事件描述】{event['description']}\n\n【事件类型】{event['type']}\n\n【事件效果】{event['effect']}"
        else:
            content += "【触发事件】暂无专属事件"
    elif isinstance(game_current_pos, Passage):
        passage = game_current_pos
        content = f"【通道名称】{passage.card['name']}\n\n【通道描述】{passage.card['description']}\n\n【通道效果】{passage.card['effect']}\n\n【操作提示】可点击该通道连接的另一地图节点完成移动"
    
    detail_text.insert(tk.END, content)
    detail_text.config(state=tk.DISABLED)
    update_stat()

def update_stat():
    """更新顶部探索统计（新增血量显示）"""
    visited_num = len(set(game_visited_nodes))
    draw_num = len(game_all_nodes)
    remain_map = len(game_map_deck) if game_map_deck else 0
    remain_event = len([e for e in game_event_deck if not e['completed']]) if game_event_deck else 0
    
    # 玩家血量信息
    hp_text = f"💖 血量：{PLAYER_STATUS['current_hp']}/{PLAYER_STATUS['max_hp']}" if PLAYER_STATUS['max_hp'] > 0 else ""
    
    stat_label.config(
        text=f"探索统计：已探索地图{visited_num}个 | 已绘制地图{draw_num}个 | 剩余地图{remain_map}张 | 剩余事件{remain_event}个 | {hp_text}"
    )

# ===================== 图形绘制核心函数 =====================
def check_collision(x, y):
    """碰撞检测"""
    for node in game_all_nodes:
        distance = math.hypot(node.x - x, node.y - y)
        if distance < COLLISION_THRESHOLD:
            return node
    return None

def draw_map_node(node):
    """绘制地图节点"""
    circle_id = canvas.create_oval(
        node.x - node.radius, node.y - node.radius,
        node.x + node.radius, node.y + node.radius,
        outline="#0066FF", fill="white", width=3, tags=f"node_{node.depth}"
    )
    name_id = canvas.create_text(
        node.x, node.y,
        text=node.map["name"], font=("微软雅黑", 9, "bold"), fill="#000000", width=node.radius*2
    )
    node.graph_id = (circle_id, name_id)
    for gid in node.graph_id:
        id_to_node[gid] = node
        canvas.tag_bind(gid, "<Button-1>", lambda e, n=node: click_node(n))
        canvas.tag_bind(gid, "<Enter>", lambda e, c=circle_id: canvas.itemconfig(c, fill="#E6F7FF"))
        canvas.tag_bind(gid, "<Leave>", lambda e, c=circle_id: canvas.itemconfig(c, fill="white"))
    game_all_nodes.append(node)
    update_canvas_scroll()

def draw_passage(passage):
    """绘制通道"""
    passage.x1 = passage.start.x + NODE_RADIUS
    passage.y1 = passage.start.y
    passage.x2 = passage.end.x - NODE_RADIUS
    passage.y2 = passage.end.y
    passage.mid_x = (passage.x1 + passage.x2) / 2
    passage.mid_y = (passage.y1 + passage.y2) / 2
    
    line_id = canvas.create_line(
        passage.x1, passage.y1, passage.x2, passage.y2,
        fill="#000000", width=2, arrow=tk.LAST, arrowshape=(8, 10, 3)
    )
    name_id = canvas.create_text(
        passage.mid_x, passage.mid_y - 10,
        text=passage.card["name"], font=("微软雅黑", 9, "bold"), fill="#FF6600", width=80
    )
    passage.graph_id = (line_id, name_id)
    for gid in passage.graph_id:
        id_to_passage[gid] = passage
        canvas.tag_bind(gid, "<Button-1>", lambda e, p=passage: click_passage(p))
        canvas.tag_bind(gid, "<Enter>", lambda e, l=line_id: canvas.itemconfig(l, width=4, fill="#FF6600"))
        canvas.tag_bind(gid, "<Leave>", lambda e, l=line_id: canvas.itemconfig(l, width=2, fill="#000000"))
    game_all_passages.append(passage)
    update_canvas_scroll()

def draw_player_token():
    """绘制玩家Token"""
    for gid in canvas.find_withtag("player_token"):
        canvas.delete(gid)
    if game_current_pos is None:
        return
    
    if isinstance(game_current_pos, MapNode):
        x, y = game_current_pos.x, game_current_pos.y
        radius = TOKEN_RADIUS + 2
    elif isinstance(game_current_pos, Passage):
        x, y = game_current_pos.mid_x, game_current_pos.mid_y
        radius = TOKEN_RADIUS
    
    token_id = canvas.create_oval(
        x - radius, y - radius,
        x + radius, y + radius,
        fill="#FF3333", outline="black", width=2, tags="player_token"
    )
    canvas.tag_raise(token_id)
    update_canvas_scroll()
    update_detail_text()

def update_canvas_scroll():
    """更新画布滚动区域"""
    all_coords = canvas.bbox("all")
    if all_coords:
        canvas.config(scrollregion=all_coords)
    if game_current_pos:
        if isinstance(game_current_pos, MapNode):
            x, y = game_current_pos.x, game_current_pos.y
        else:
            x, y = game_current_pos.mid_x, game_current_pos.mid_y
        canvas.xview_moveto(max(0, (x - 700) / (all_coords[2] if all_coords else 1600)))
        canvas.yview_moveto(max(0, (y - 300) / (all_coords[3] if all_coords else 600)))

# ===================== 树状节点生成 =====================
def generate_child_nodes(parent_node):
    """动态生成子节点"""
    if parent_node.is_generated or not game_map_deck or not game_passage_deck:
        return
    parent_node.is_generated = True

    base_num = random.randint(1, 3)
    if parent_node.map["name"] == "迷雾森林" and base_num > 1:
        num_passages = 1
        show_tip("🌫️ 迷雾森林效果：仅生成1条通道！", "#0099ff", 2500)
    elif parent_node.map["name"] == "水晶洞穴" and base_num < 3:
        num_passages = base_num + 1
        show_tip("💎 水晶洞穴效果：通道数+1！", "#0099ff", 2500)
    else:
        num_passages = base_num

    y_offsets = []
    if num_passages == 1:
        y_offsets = [0]
    elif num_passages == 2:
        y_offsets = [-BRANCH_STEP//2, BRANCH_STEP//2]
    elif num_passages >= 3:
        y_offsets = [-BRANCH_STEP, 0, BRANCH_STEP][:num_passages]

    for i, y_offset in enumerate(y_offsets):
        if not game_passage_deck:
            show_tip("🚫 通道牌库为空，停止生成！", "#ff9900", 3000)
            break
        child_x = parent_node.x + DEPTH_STEP
        child_y = parent_node.y + y_offset
        child_depth = parent_node.depth + 1
        
        collision_node = check_collision(child_x, child_y)
        passage_card = game_passage_deck.pop()
        
        if collision_node:
            show_tip(f"📍 坐标重合，连接{parent_node.map['name']}与{collision_node.map['name']}", "#0099ff", 2500)
            new_node = collision_node
        else:
            if not game_map_deck:
                show_tip("🚫 地图牌库为空，无法生成新节点！", "#ff9900", 3000)
                break
            map_card = game_map_deck.pop()
            new_node = MapNode(map_card, child_x, child_y, child_depth)
            new_node.parent = parent_node
            parent_node.children.append(new_node)
            draw_map_node(new_node)
        
        passage = Passage(passage_card, parent_node, new_node)
        parent_node.passages.append(passage)
        draw_passage(passage)

# ===================== 核心交互逻辑 =====================
def click_node(target_node):
    """点击地图节点逻辑"""
    global game_current_pos
    if game_current_pos is None:
        game_current_pos = target_node
        game_visited_nodes.append(target_node)
        draw_player_token()
        explore_node(target_node)
        return
    
    if target_node == game_current_pos:
        show_tip(f"你已在{target_node.map['name']}，无需重复点击！")
        return
    
    if isinstance(game_current_pos, Passage):
        if game_current_pos.start == target_node or game_current_pos.end == target_node:
            game_current_pos = target_node
            game_visited_nodes.append(target_node)
            draw_player_token()
            if game_visited_nodes.count(target_node) == 1:
                explore_node(target_node)
                show_tip(f"🔍 首次探索{target_node.map['name']}，触发专属事件！", "#0099ff", 2500)
            else:
                if target_node.map['event']:
                    target_node.map['event']['completed'] = True
                show_tip(f"移动成功！再次到达{target_node.map['name']}", "#00cc00", 2500)
            return
        else:
            show_tip("该节点与当前通道无连接，无法移动！")
            return
    
    if isinstance(game_current_pos, MapNode):
        show_tip("禁止直接点击地图！必须先点击相邻通道再移动！")
        return

def click_passage(target_passage):
    """点击通道逻辑"""
    global game_current_pos
    if game_current_pos is None:
        show_tip("请先从初始地图开始探索，再点击通道！")
        return
    
    if isinstance(game_current_pos, MapNode):
        if target_passage.start == game_current_pos or target_passage.end == game_current_pos:
            game_current_pos = target_passage
            draw_player_token()
            show_tip(f"进入通道{target_passage.card['name']}，可点击连接的另一地图移动", "#00cc00", 2500)
            return
        else:
            show_tip("该通道与当前地图无连接，无法进入！")
            return
    
    if isinstance(game_current_pos, Passage):
        if target_passage == game_current_pos:
            show_tip(f"已在{target_passage.card['name']}，请点击通道连接的另一地图！")
            return
        else:
            show_tip("请先从当前通道移动到地图，再进入其他通道！")
            return
        
def explore_node(node):
    """探索节点（最终修复版：先延伸地图+变量名避重名+传递卡牌参数）"""
    show_tip(f"🔍 正在探索{node.map['name']}，生成通道并触发事件...", "#0099ff", 5000)
    
    # 第一步：先生成子节点（延伸地图），再处理事件
    generate_child_nodes(node)
    
    # 第二步：处理事件（变量名改为game_event，避免和tkinter.Event冲突）
    if game_event_deck and not node.map['event']:
        game_event = game_event_deck.pop()
        node.map['event'] = game_event
        show_tip(f"🎴 触发专属事件：{game_event['name']}", "#ffcc00", 2500)
        
        # 触发战斗（传递game_event而非event，同步玩家状态）
        if "战斗" in game_event["关键词"] or "怪物" in game_event["关键词"] or "敌人" in game_event["关键词"]:
            show_tip(f"⚔️ 触发战斗事件：{game_event['name']}，准备使用已购卡牌！", "#ff0000", 3000)
            try:
                import battle_core as bc
                # 传递战斗参数 + 同步玩家状态
                bc.trigger_battle(game_event, root, PLAYER_BATTLE_PARAMS)
                
                # 战斗结束后更新玩家血量
                if hasattr(bc, 'PLAYER') and bc.PLAYER.get('current_hp'):
                    PLAYER_STATUS['current_hp'] = bc.PLAYER['current_hp']
                    PLAYER_STATUS['max_hp'] = bc.PLAYER['max_hp']
                    update_stat()  # 刷新血量显示
                    
                    # 血量为0时结束游戏
                    if PLAYER_STATUS['current_hp'] <= 0:
                        show_tip(f"💀 玩家血量为0，探索失败！", "#ff0000", 5000)
                        root.after(5000, root.destroy)
            except ImportError:
                show_tip("⚠️ 未找到战斗模块battle_core.py", "#ff9900", 3000)
            except Exception as e:
                show_tip(f"⚠️ 战斗启动失败：{str(e)}\n错误类型：{type(e).__name__}", "#ff9900", 5000)
        
        update_detail_text()
    elif not node.map['event']:
        show_tip("📭 该地图无专属事件，直接生成通道！", "#0099ff", 2500)
    
    # 游戏结束判断
    if not game_map_deck and len(set(game_visited_nodes)) == len(game_all_nodes):
        show_tip(f"🎮 游戏结束！已探索所有{len(set(game_visited_nodes))}个地图！", "#ff00ff", 5000)

# ===================== 游戏UI构建 =====================
def create_game_ui():
    """创建探索UI（主窗口）"""
    global root, canvas, detail_frame, detail_text, tip_label, stat_label, hp_label
    root = tk.Tk()
    root.title("树状地图探索游戏 - 模块化版")
    root.geometry("1400x800")
    root.resizable(True, True)
    root.config(bg="#f5f5f5")

    # 修复ttk.LabelFrame字体
    style = ttk.Style(root)
    style.configure('Custom.TLabelframe.Label', font=("微软雅黑", 14, "bold"))

    # 顶部统计栏
    stat_label = tk.Label(
        root, text="探索统计：已探索地图0个 | 已绘制地图0个 | 剩余地图0张 | 剩余事件0个",
        font=("微软雅黑", 12, "bold"), bg="#ffffff", fg="#333333", pady=10, padx=20
    )
    stat_label.pack(fill=tk.X, padx=20, pady=(10, 0))

    # 中间画布容器
    canvas_container = ttk.Frame(root, width=1360, height=450)
    canvas_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    canvas_xscroll = ttk.Scrollbar(canvas_container, orient=tk.HORIZONTAL)
    canvas_xscroll.pack(side=tk.BOTTOM, fill=tk.X)
    canvas_yscroll = ttk.Scrollbar(canvas_container, orient=tk.VERTICAL)
    canvas_yscroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    canvas = tk.Canvas(
        canvas_container, bg="#ffffff",
        xscrollcommand=canvas_xscroll.set, yscrollcommand=canvas_yscroll.set
    )
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    canvas_xscroll.config(command=canvas.xview)
    canvas_yscroll.config(command=canvas.yview)

    # 提示标签
    tip_label = tk.Label(canvas, bg="#ffffff", bd=0)
    tip_label.place_forget()

    # 下方详情栏
    detail_frame = ttk.LabelFrame(root, text="当前位置详情", style='Custom.TLabelframe', labelanchor=tk.N)
    detail_frame.pack(fill=tk.BOTH, expand=False, padx=20, pady=(0, 10))
    
    detail_text = tk.Text(
        detail_frame, font=("Consolas", 11), bg="#f8f8f8", fg="#000000",
        wrap=tk.WORD, state=tk.DISABLED, spacing1=5, spacing3=5
    )
    detail_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # 初始化游戏
    init_game()
    
    # 同步玩家初始状态（从battle_core读取）
    try:
        import battle_core as bc
        if bc.PLAYER.get('current_hp'):
            PLAYER_STATUS['current_hp'] = bc.PLAYER['current_hp']
            PLAYER_STATUS['max_hp'] = bc.PLAYER['max_hp']
            PLAYER_STATUS['attributes'] = bc.PLAYER['attributes']
            update_stat()
    except:
        pass
    
    return root

def init_game():
    """初始化探索游戏（修复路径）"""
    global game_current_pos, game_visited_nodes, game_all_nodes, game_all_passages
    global game_map_deck, game_passage_deck, game_event_deck

    # 加载卡牌（使用绝对路径）
    try:
        game_map_deck = load_map_cards("mapcard.csv")
        game_passage_deck = load_passage_cards("passagecard.csv")
        game_event_deck = load_event_cards("eventcard.csv")
    except FileNotFoundError as e:
        messagebox.showerror("文件错误", f"未找到卡牌文件：{e.filename}")
        sys.exit()
    except KeyError as e:
        messagebox.showerror("格式错误", f"CSV文件缺少列名：{e}")
        sys.exit()

    # 洗牌
    random.shuffle(game_map_deck)
    random.shuffle(game_passage_deck)
    random.shuffle(game_event_deck)

    # 初始化变量
    game_visited_nodes = []
    game_all_nodes = []
    game_all_passages = []
    game_current_pos = None

    # 创建根节点
    if not game_map_deck:
        show_tip("❌ 地图牌库为空，无法开始游戏！", "#ff0000", 5000)
        return
    root_map = game_map_deck.pop()
    root_node = MapNode(root_map, ROOT_X, ROOT_Y, depth=0)
    root_node.is_generated = False
    draw_map_node(root_node)

    update_detail_text()
    update_stat()
    show_tip(f"🎉 游戏开始！初始地图：{root_node.map['name']}", "#00cc00", 5000)