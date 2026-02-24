import csv
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
# ========= 卡牌池 =========

print("🎲 游戏开始")

# 1 放置开始地图
current_map = random.choice(MAP_CARDS)
print(f"1️⃣ 起始地图卡：{current_map}")

round_count = 1
game_over = False

while not game_over:
    print(f"\n=== 第 {round_count} 轮 ===")

    # 2 roll d3
    num_passages = random.randint(1, 3)
    print(f"2️⃣ 投 d3 = {num_passages}，放置 {num_passages} 张通道卡")

    # 3 放置通道卡 & 地图卡（倒扣）
    passages = random.sample(PASSAGE_CARDS, num_passages)
    hidden_maps = random.choices(MAP_CARDS, k=num_passages)

    print("3️⃣ 你面前有以下通道：")
    for i in range(num_passages):
        print(f"   通道 {i + 1}（未知）")

    # 4 玩家选择方向
    while True:
        choice = input(f"4️⃣ 选择你要进入的通道（1-{num_passages}）：")
        if choice.isdigit():
            choice = int(choice)
            if 1 <= choice <= num_passages:
                break
        print("❌ 输入无效，请重新输入")

    index = choice - 1

    # 5 翻开通道卡
    passage = passages[index]
    print(f"5️⃣ 翻开通道卡：{passage}")

    # 6 通道卡事件
    if passage == "陷阱通道":
        print("6️⃣ 你触发了陷阱，前进代价增加")
    elif passage == "诅咒通道":
        print("6️⃣ 你被诅咒，空气变得沉重")
    else:
        print("6️⃣ 通道安全")

    # 7 进入下一个地图，抽事件卡
    current_map = hidden_maps[index]
    print(f"7️⃣ 你进入地图：{current_map}")

    event = random.choice(EVENT_CARDS)
    print(f"   抽取事件卡：{event}")

    # 8 / 9 游戏结束判断
    if "完成任务" in event:
        print("🏁 游戏结束：你完成了特定事件")
        game_over = True
    elif "玩家死亡" in event:
        print("💀 游戏结束：你死了")
        game_over = True
    else:
        print("➡️ 游戏继续，回到步骤 2")
        round_count += 1

print("\n🎮 游戏结束")

