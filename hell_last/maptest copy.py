import random


import csv

def load_map_cards(filename):
    maps = []
    with open(filename, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            maps.append({
                "name": row["地图名"],
                "description": row["描述"],
                "effect": row["地图效果"]
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
                "type": row["类型"],
                "effect": row["效果"]
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



MAP_CARDS = load_map_cards("mapcard.csv")
EVENT_CARDS = load_event_cards("eventcard.csv")
PASSAGE_CARDS = load_passage_cards("passagecard.csv")


import csv
import random

# 洗牌
random.shuffle(MAP_CARDS)
random.shuffle(PASSAGE_CARDS)
random.shuffle(EVENT_CARDS)

# ========= 地图节点类 =========
class MapNode:
    def __init__(self, map_card):
        self.map = map_card
        self.passages = {}      # direction -> Passage
        self.events_drawn = False
        self.previous = None    # 上一节点

class Passage:
    def __init__(self, passage_card, next_node):
        self.card = passage_card
        self.next = next_node
        self.known = False  # 初始状态：未知



# ========= 初始化 =========
map_deck = MAP_CARDS.copy()
passage_deck = PASSAGE_CARDS.copy()
event_deck = EVENT_CARDS.copy()

visited_maps = []

start_node = MapNode(map_deck.pop())
current_node = start_node
visited_maps.append(current_node)

print("🎲 游戏开始")

# ========= 核心函数 =========
def enter_map(node):
    print(f"\n🗺️ 进入地图：{node.map['name']}")
    print(f"📜 描述：{node.map['description']}")
    print(f"⚠️ 地图效果：{node.map['effect']}")

    # 第一次进入才生成通道
    if not node.passages:
        num_passages = random.randint(1, 3)
        for i in range(num_passages):
            if not passage_deck or not map_deck:
                break
            passage_card = passage_deck.pop()
            next_map = map_deck.pop()
            next_node = MapNode(next_map)
            node.passages[i + 1] = Passage(passage_card, next_node)

    # 第一次进入才抽事件
    if not node.events_drawn and event_deck:
        event = event_deck.pop()
        print(f"🎴 事件：{event['name']}")
        print(f"📜 描述：{event['description']}")
        print(f"类型：{event['type']}  效果：{event['effect']}")
        node.events_drawn = True

def show_passages(node):
    """
    显示当前地图节点的通道列表。
    未知通道只显示“未知”，已知通道显示完整信息
    """
    print("\n可用通道：")
    # 0 回到上一地图
    if node.previous:
        print("0. 回到上一地图")

    for i, passage in node.passages.items():
        if passage.known:
            # 已知通道显示具体内容
            print(f"{i}. 名称：{passage.card['name']}, 描述：{passage.card['description']}, 效果：{passage.card['effect']}")
        else:
            # 未知通道只显示“未知”
            print(f"{i}. 未知")


def choose_passage(node):
    show_passages(node)  # 显示通道列表

    while True:
        choice = input("选择通道编号：")
        if choice.isdigit():
            choice = int(choice)
            # 回到上一地图
            if choice == 0 and node.previous:
                return node.previous
            elif choice in node.passages:
                passage = node.passages[choice]
                # 第一次踏入 → 标记已知
                if not passage.known:
                    passage.known = True
                # 显示已知通道信息
                print(f"\n你选择了通道 {choice}：")
                print(f"名称：{passage.card['name']}")
                print(f"描述：{passage.card['description']}")
                print(f"效果：{passage.card['effect']}\n")
                # 设置下一节点的 previous
                passage.next.previous = node
                return passage.next
        print("❌ 输入无效，请重新选择")

# ========= 游戏主循环 =========
while True:
    enter_map(current_node)
    if not current_node.passages:
        print("前方没有通道了，游戏结束")
        break
    current_node = choose_passage(current_node)
    visited_maps.append(current_node)
