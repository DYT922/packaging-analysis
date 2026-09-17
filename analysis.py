"""
包装成本分析
------------
目标:比较不同包装材料的综合成本(运费 + 破损损失),给出可执行的优化建议。
数据:data/packages.csv(15 条模拟快递包裹记录)
运行:python analysis.py
"""

import pandas as pd
import matplotlib.pyplot as plt

# 让图表正常显示中文,避免出现方块
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

# 各类商品的假设货值(元/件),破损时按此计算损失
VALUE_MAP = {"electronics": 100, "glass": 150, "ceramics": 100, "clothing": 30}


def load_data(path="data/packages.csv"):
    """读取数据,并派生分析所需的列。"""
    df = pd.read_csv(path)
    df["value"] = df["category"].map(VALUE_MAP)                        # 货值
    df["volume"] = df["length_cm"] * df["width_cm"] * df["height_cm"]  # 体积(cm3)
    df["unit_freight"] = df["freight_cost"] / df["weight_kg"]          # 单位运费(元/kg)
    return df


def cost_summary(df):
    """按包装材料汇总成本:总成本 = 平均运费 + 破损率 × 平均货值。"""
    freight = df.groupby("material")["freight_cost"].mean()
    rate = df.groupby("material")["damaged"].mean()
    value = df.groupby("material")["value"].mean()
    loss = rate * value
    total = freight + loss
    return pd.DataFrame(
        {
            "平均运费": freight,
            "破损率": rate,
            "平均货值": value,
            "破损损失": loss,
            "总成本": total,
        }
    )


def plot_cost_compare(summary, path="charts/cost_compare.png"):
    """总成本对比柱状图。"""
    plt.figure(figsize=(7, 4))
    plt.bar(summary.index, summary["总成本"], color=["#4C9F70", "#3B82C4", "#C4623B"])
    plt.title("三种包装材料的平均总成本对比")
    plt.xlabel("包装材料")
    plt.ylabel("成本(元/件)")
    for x, y in zip(summary.index, summary["总成本"]):
        plt.text(x, y + 2, f"{y:.2f}", ha="center")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def plot_cost_stack(summary, path="charts/cost_stack.png"):
    """成本构成堆叠柱状图:运费 + 破损损失。"""
    plt.figure(figsize=(7, 4))
    plt.bar(summary.index, summary["平均运费"], label="运费", color="#3B82C4")
    plt.bar(
        summary.index,
        summary["破损损失"],
        bottom=summary["平均运费"],
        label="破损损失",
        color="#C4623B",
    )
    plt.title("三种包装材料的成本构成对比")
    plt.xlabel("包装材料")
    plt.ylabel("成本(元/件)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def main():
    df = load_data()
    summary = cost_summary(df)

    print("=" * 44)
    print("一、数据概览")
    print("=" * 44)
    print(f"订单总数:{len(df)}")
    print(f"破损订单:{int(df['damaged'].sum())} 件")
    print(df.groupby("material").size().rename("订单数").to_frame().T)

    print()
    print("=" * 44)
    print("二、各包装材料成本对比(元/件)")
    print("=" * 44)
    print(summary.round(2))

    plot_cost_compare(summary)
    plot_cost_stack(summary)

    # 换料测算:木箱换成纸箱,省下的运费能覆盖多少新增破损
    freight_wood = summary.loc["wood", "平均运费"]
    freight_cardboard = summary.loc["cardboard", "平均运费"]
    avg_value_glass = df[df["category"] == "glass"]["value"].mean()
    saving = freight_wood - freight_cardboard
    threshold = saving / avg_value_glass

    total_wood = summary.loc["wood", "总成本"]
    total_cardboard = summary.loc["cardboard", "总成本"]
    loss_ratio = summary.loc["wood", "破损损失"] / total_wood * 100

    print()
    print("=" * 44)
    print("三、结论与建议")
    print("=" * 44)
    print(
        f"1. 木箱平均总成本 {total_wood:.2f} 元/件,"
        f"是纸箱({total_cardboard:.2f} 元/件)的 {total_wood / total_cardboard:.1f} 倍。"
    )
    print(f"2. 木箱成本中破损损失占 {loss_ratio:.0f}%,说明破损而非运费才是主要矛盾。")
    print(
        f"3. 换用纸箱每件可省运费 {saving:.2f} 元;按玻璃平均货值 "
        f"{avg_value_glass:.0f} 元计算,纸箱破损率上升不超过 "
        f"{threshold * 100:.1f} 个百分点时,换料才划算。"
    )
    print("4. 建议先小批量试运『纸箱 + 缓冲材料』包装玻璃陶瓷,采集实际破损数据后再决定是否全面更换。")
    print()
    print("图表已保存到 charts/ 目录。")
    print("注:本数据为教学用模拟数据,实际快递破损率通常在 1%-3%。")


if __name__ == "__main__":
    main()
