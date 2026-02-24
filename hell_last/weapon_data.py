import csv
import os
import sys  # 新增：导入sys模块处理打包/普通运行场景

WEAPONS = []

# ===================== 核心修复：绝对路径处理 =====================
def get_script_dir():
    """
    获取当前代码文件所在的绝对目录
    - 普通运行：返回py文件所在目录
    - 打包成exe：返回exe所在目录
    """
    if getattr(sys, 'frozen', False):
        # 打包为exe时的目录
        return os.path.dirname(sys.executable)
    else:
        # 普通py文件运行时的目录
        return os.path.dirname(os.path.abspath(__file__))

def safe_path(filename):
    """拼接出「代码所在目录 + 文件名」的绝对路径"""
    script_dir = get_script_dir()
    full_path = os.path.join(script_dir, filename)
    print(f"拼接后的绝对路径：{full_path}")  # 调试：打印最终路径
    return full_path

# ===================== 武器加载（保留原有功能 + 绝对路径） =====================
def load_weapons(filename="weapon.csv"):
    global WEAPONS
    WEAPONS = []
    
    # 核心修改：转成绝对路径
    full_path = safe_path(filename)
    
    # 打印调试信息（增强版）
    print("="*50)
    print(f"【武器加载调试】")
    print(f"目标文件名：{filename}")
    print(f"绝对路径：{full_path}")
    print(f"当前工作目录：{os.getcwd()}")
    print(f"代码所在目录：{get_script_dir()}")
    print(f"文件是否存在：{os.path.exists(full_path)}")
    print("="*50)
    
    # 尝试多种编码读取
    encodings = ["utf-8-sig", "gbk", "utf-8"]
    for encoding in encodings:
        try:
            with open(full_path, encoding=encoding) as f:  # 用绝对路径读取
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                print(f"\nCSV表头（编码{encoding}）：{headers}")
                
                # 修复：清理表头的BOM头和空格（解决\ufeff编号问题）
                clean_headers = []
                for h in headers:
                    clean_h = h.strip().replace("\ufeff", "")  # 去掉BOM头和空格
                    clean_headers.append(clean_h)
                reader.fieldnames = clean_headers  # 替换为清理后的表头
                
                # 读取每一行数据
                for row in reader:
                    # 核心：字段名和CSV表头完全匹配（额外防御次数 N）
                    WEAPONS.append({
                        "编号": int(row["编号"]),
                        "武器名": row["武器名"],
                        "额外攻击次数": row["额外攻击次数"],
                        "命中": row["命中 H"],          # CSV里是"命中 H"
                        "伤害": int(row["伤害 D"]),     # CSV里是"伤害 D"
                        "额外防御次数": row["额外防御次数 N"],  # 关键修复：CSV里是"额外防御次数 N"
                        "格挡": row["格挡 E"],          # CSV里是"格挡 E"
                        "描述": row["描述"],
                        "特性": row["特性"]
                    })
            print(f"✅ 成功加载 {len(WEAPONS)} 条武器数据（编码：{encoding}）")
            break
        except FileNotFoundError:
            print(f"❌ 未找到文件：{full_path}")
            break
        except KeyError as e:
            print(f"❌ 字段不匹配（编码{encoding}）：缺少字段 {e}")
            continue
        except Exception as e:
            print(f"❌ 读取失败（编码{encoding}）：{str(e)}")
            continue

# 初始化加载（程序启动时自动加载）
load_weapons()

# 测试加载
if __name__ == "__main__":
    load_weapons()
    print("\n最终武器列表：")
    for weapon in WEAPONS:
        print(weapon)