"""
模拟数据生成器
--------------
生成 2000 条快递包裹记录,并故意注入常见的"脏数据",用于练习数据清洗。

运行:python generate_data.py
输出:data/packages_raw.csv
"""

import numpy as np
import pandas as pd

SEED = 42          # 固定随机种子,保证每次生成的数据一样(结果可复现)
N = 2000           # 订单数量

# 各类商品的货值、重量范围和易碎概率
CATEGORY_PROFILE = {
    "electronics": {"value": 100, "w_range": (0.5, 5.0), "fragile": 0.25, "p": 0.30},
    "glass": {"value": 150, "w_range": (0.8, 5.0), "fragile": 0.95, "p": 0.20},
    "ceramics": {"value": 100, "w_range": (0.8, 4.5), "fragile": 0.90, "p": 0.20},
    "clothing": {"value": 30, "w_range": (0.2, 1.5), "fragile": 0.05, "p": 0.20},
    "books": {"value": 40, "w_range": (0.3, 3.0), "fragile": 0.02, "p": 0.10},
}

# 包装材料的运费附加和破损概率(易碎品)
MATERIAL_SURCHARGE = {"bubble": 0.0, "cardboard": 2.0, "wood": 7.0}
MATERIAL_DAMAGE = {"bubble": 0.060, "cardboard": 0.025, "wood": 0.010}
DAMAGE_NON_FRAGILE = 0.006

CITIES = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安"]
CITY_VARIANTS = {
    "北京": ["北京市", "北京 "],
    "上海": [" 上海", "SHANGHAI"],
    "广州": ["广州市"],
    "深圳": ["SHENZHEN"],
    "杭州": ["杭州市"],
    "成都": ["成都市"],
    "武汉": ["武汉市"],
    "西安": ["西安市"],
}


def pick_material(rng, weight, fragile):
    """按重量和易碎程度,用带随机性的规则选择包装材料(所以同一类商品会混用材料)。"""
    if fragile and weight >= 2:
        probs = {"wood": 0.60, "cardboard": 0.35, "bubble": 0.05}
    elif fragile:
        probs = {"wood": 0.30, "cardboard": 0.50, "bubble": 0.20}
    elif weight >= 3:
        probs = {"wood": 0.15, "cardboard": 0.75, "bubble": 0.10}
    else:
        probs = {"wood": 0.03, "cardboard": 0.32, "bubble": 0.65}
    keys = list(probs)
    return str(rng.choice(keys, p=[probs[k] for k in keys]))


def build_clean_rows(rng):
    """先生成一份"干净"的数据。"""
    categories = list(CATEGORY_PROFILE)
    weights_p = [CATEGORY_PROFILE[c]["p"] for c in categories]
    rows = []

    for i in range(N):
        category = str(rng.choice(categories, p=weights_p))
        profile = CATEGORY_PROFILE[category]

        weight = round(float(rng.uniform(*profile["w_range"])), 2)
        fragile = 1 if rng.random() < profile["fragile"] else 0
        material = pick_material(rng, weight, bool(fragile))

        length = round(float(rng.uniform(15, 60)), 1)
        width = round(float(rng.uniform(10, 45)), 1)
        height = round(float(rng.uniform(5, 40)), 1)
        volume = length * width * height

        freight = (
            5
            + 1.6 * weight
            + 0.00005 * volume
            + MATERIAL_SURCHARGE[material]
            + float(rng.normal(0, 1.0))
        )

        damage_rate = (
            MATERIAL_DAMAGE[material] if fragile else DAMAGE_NON_FRAGILE
        ) * (1 + 0.15 * max(0.0, weight - 1))
        damaged = 1 if rng.random() < damage_rate else 0

        value = int(profile["value"] * rng.uniform(0.8, 1.4))
        date = pd.Timestamp("2026-01-01") + pd.Timedelta(days=int(rng.integers(0, 243)))

        rows.append(
            {
                "order_id": 100001 + i,
                "order_date": date.strftime("%Y-%m-%d"),
                "city": str(rng.choice(CITIES)),
                "category": category,
                "fragile": fragile,
                "weight_kg": weight,
                "length_cm": length,
                "width_cm": width,
                "height_cm": height,
                "material": material,
                "freight_cost": round(max(3.0, freight), 2),
                "value": value,
                "damaged": damaged,
            }
        )
    return pd.DataFrame(rows)


def inject_dirty_data(df, rng):
    """注入常见的脏数据:重复行、缺失值、异常值、单位错误、城市写法不统一。"""
    df = df.copy()

    # 1. 重复行(约 1.5%)
    dup_idx = rng.choice(df.index, size=int(N * 0.015), replace=False)
    df = pd.concat([df, df.loc[dup_idx]], ignore_index=True)

    # 2. 缺失值
    for col, frac in [
        ("weight_kg", 0.03),
        ("length_cm", 0.02),
        ("width_cm", 0.02),
        ("height_cm", 0.02),
        ("damaged", 0.02),
        ("value", 0.02),
    ]:
        idx = rng.choice(df.index, size=int(len(df) * frac), replace=False)
        df.loc[idx, col] = np.nan

    # 3. 异常值:重量 999(明显的录入错误)
    idx = rng.choice(df.index, size=int(N * 0.005), replace=False)
    df.loc[idx, "weight_kg"] = 999

    # 4. 单位错误:把"克"当成"千克"录入(数值放大 1000 倍)
    idx = rng.choice(df.index, size=int(N * 0.010), replace=False)
    valid = df.loc[idx, "weight_kg"].notna()
    df.loc[idx[valid], "weight_kg"] = df.loc[idx[valid], "weight_kg"] * 1000

    # 5. 城市写法不统一
    idx = rng.choice(df.index, size=int(N * 0.05), replace=False)
    for i in idx:
        city = df.at[i, "city"]
        if city in CITY_VARIANTS:
            df.at[i, "city"] = str(rng.choice(CITY_VARIANTS[city]))

    return df.sample(frac=1, random_state=SEED).reset_index(drop=True)


def main():
    rng = np.random.default_rng(SEED)
    clean = build_clean_rows(rng)
    dirty = inject_dirty_data(clean, rng)
    dirty.to_csv("data/packages_raw.csv", index=False)
    print(f"已生成 {len(dirty)} 行数据 → data/packages_raw.csv")
    print("其中包含:重复行、缺失值、异常值(999)、单位错误(克/千克)、城市写法不一致")


if __name__ == "__main__":
    main()
