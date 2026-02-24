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
        self.map = map_card          # 地图卡信息
        self.passages = {}           # direction(int) -> Passage对象
        self.events_drawn = False    # 是否已抽事件

class Passage:
    def __init__(self, passage_card, next_node):
        self.card = passage_card
        self.next = next_node

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

    # 第一次进入：生成通道
    if not node.passages:
        num_passages = random.randint(1, 3)
        for i in range(num_passages):
            if not passage_deck:
                print("通道牌库为空")
                break
            passage_card = passage_deck.pop()
            if not map_deck:
                print("地图牌库为空")
                break
            next_map = map_deck.pop()
            next_node = MapNode(next_map)

            node.passages[i + 1] = Passage(passage_card, next_node)

    # 第一次进入：抽事件
    if not node.events_drawn and event_deck:
        event = event_deck.pop()
        print(f"🎴 事件：{event['name']}")
        print(f"📜 描述：{event['description']}")
        print(f"类型：{event['type']}  效果：{event['effect']}")
        node.events_drawn = True

def choose_passage(node):
    print("\n可用通道：")
    for i, passage in node.passages.items():
        print(f"{i}. {passage.card['name']}")

    while True:
        choice = input("选择通道编号：")
        if choice.isdigit() and int(choice) in node.passages:
            return node.passages[int(choice)].next
        else:
            print("❌ 输入无效，请重新选择")

# ========= 游戏主循环 =========
while True:
    enter_map(current_node)
    if not current_node.passages:
        print("前方没有通道了，游戏结束")
        break
    current_node = choose_passage(current_node)
    visited_maps.append(current_node)
