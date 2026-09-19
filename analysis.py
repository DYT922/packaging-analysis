"""
包装成本分析 v2
---------------
数据:data/packages_clean.csv(由 clean_data.py 清洗得到)
分析:整体成本对比 + 易碎品分层分析 + 破损率时间趋势
运行:python analysis.py
"""

import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

CLEAN_PATH = "data/packages_clean.csv"
MATERIAL_CN = {"bubble": "气泡袋", "cardboard": "纸箱", "wood": "木箱"}
COLORS = {"bubble": "#4C9F70", "cardboard": "#3B82C4", "wood": "#C4623B"}


def load_data(path=CLEAN_PATH):
    return pd.read_csv(path, parse_dates=["order_date"])


def cost_summary(df):
    """总成本 = 平均运费 + 破损率 × 平均货值。"""
    freight = df.groupby("material")["freight_cost"].mean()
    rate = df.groupby("material")["damaged"].mean()
    value = df.groupby("material")["value"].mean()
    loss = rate * value
    return pd.DataFrame(
        {
            "平均运费": freight,
            "破损率": rate,
            "平均货值": value,
            "破损损失": loss,
            "总成本": freight + loss,
        }
    )


def plot_total_cost(summary, path="charts/cost_compare.png"):
    labels = [MATERIAL_CN.get(m, m) for m in summary.index]
    colors = [COLORS.get(m, "#888888") for m in summary.index]
    plt.figure(figsize=(7, 4))
    plt.bar(labels, summary["总成本"], color=colors)
    plt.title("各包装材料的平均总成本对比")
    plt.xlabel("包装材料")
    plt.ylabel("成本(元/件)")
    for x, y in zip(range(len(summary)), summary["总成本"]):
        plt.text(x, y + 0.5, f"{y:.2f}", ha="center")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def plot_cost_stack(summary, title, path):
    labels = [MATERIAL_CN.get(m, m) for m in summary.index]
    plt.figure(figsize=(7, 4))
    plt.bar(labels, summary["平均运费"], label="运费", color="#3B82C4")
    plt.bar(
        labels,
        summary["破损损失"],
        bottom=summary["平均运费"],
        label="破损损失",
        color="#C4623B",
    )
    plt.title(title)
    plt.xlabel("包装材料")
    plt.ylabel("成本(元/件)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def plot_monthly(df, path="charts/monthly_damage.png"):
    monthly = df.groupby("month")["damaged"].mean()
    plt.figure(figsize=(7, 4))
    plt.plot(monthly.index, monthly.values, marker="o", color="#C4623B")
    plt.title("破损率月度趋势")
    plt.xlabel("月份")
    plt.ylabel("破损率")
    plt.gca().yaxis.set_major_formatter(lambda v, _: f"{v:.1%}")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    return monthly


def main():
    df = load_data()

    print("=" * 48)
    print("一、数据概览")
    print("=" * 48)
    print(f"订单总数:{len(df)}")
    print(f"时间范围:{df['order_date'].min():%Y-%m-%d} ~ {df['order_date'].max():%Y-%m-%d}")
    print(f"城市数量:{df['city'].nunique()}")
    print(f"整体破损率:{df['damaged'].mean():.2%}")
    print(df.groupby("material").size().rename("订单数").to_frame().T)

    summary = cost_summary(df)
    print()
    print("=" * 48)
    print("二、各包装材料综合成本(元/件)")
    print("=" * 48)
    print(summary.round(2))

    fragile_df = df[df["fragile"] == 1]
    fragile_summary = cost_summary(fragile_df)
    print()
    print("=" * 48)
    print(f"三、易碎商品分层分析(共 {len(fragile_df)} 单)")
    print("=" * 48)
    print(fragile_summary.round(2))

    print()
    print("非易碎商品参考:")
    print(cost_summary(df[df["fragile"] == 0]).round(2))

    monthly = plot_monthly(df)
    plot_total_cost(summary)
    plot_cost_stack(summary, "成本构成:运费 + 破损损失", "charts/cost_stack.png")
    plot_cost_stack(fragile_summary, "易碎商品:各包装材料的成本构成对比", "charts/cost_fragile.png")

    best = fragile_summary["总成本"].idxmin()
    worst = fragile_summary["总成本"].idxmax()
    gap = fragile_summary.loc[worst, "总成本"] - fragile_summary.loc[best, "总成本"]
    worst_loss_ratio = (
        fragile_summary.loc[worst, "破损损失"] / fragile_summary.loc[worst, "总成本"]
    )

    print()
    print("=" * 48)
    print("四、结论与建议")
    print("=" * 48)
    print(
        f"1. 易碎商品中,{MATERIAL_CN[best]}综合成本最低"
        f"({fragile_summary.loc[best, '总成本']:.2f} 元/件),"
        f"{MATERIAL_CN[worst]}最高({fragile_summary.loc[worst, '总成本']:.2f} 元/件),"
        f"每件相差 {gap:.2f} 元。"
    )
    print(
        f"2. {MATERIAL_CN[worst]}在易碎品上的破损率为 "
        f"{fragile_summary.loc[worst, '破损率']:.2%},破损损失 "
        f"{fragile_summary.loc[worst, '破损损失']:.2f} 元/件,"
        f"占其总成本的 {worst_loss_ratio:.0%}。"
    )
    print(
        f"3. 破损率月度波动区间 "
        f"{monthly.min():.2%} ~ {monthly.max():.2%},可据此进一步排查旺季或特定线路的问题。"
    )
    print("4. 建议:易碎品优先选择防护更好的材料,并通过小批量试运验证换料后的破损率变化。")
    print()
    print("图表已保存到 charts/。")


if __name__ == "__main__":
    main()
