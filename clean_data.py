"""
数据清洗
--------
读取 data/packages_raw.csv,处理重复行、缺失值、异常值、单位错误和城市写法不一致,
输出可直接分析的 data/packages_clean.csv。

运行:python clean_data.py
"""

import pandas as pd

CITY_FIX = {
    "北京市": "北京",
    "北京 ": "北京",
    " 上海": "上海",
    "SHANGHAI": "上海",
    "广州市": "广州",
    "SHENZHEN": "深圳",
    "杭州市": "杭州",
    "成都市": "成都",
    "武汉市": "武汉",
    "西安市": "西安",
}

NUMERIC_COLS = ["weight_kg", "length_cm", "width_cm", "height_cm", "value"]


def quality_report(df, title):
    """打印数据质量体检报告。"""
    print(f"\n===== {title} =====")
    print(f"行数:{len(df)}  列数:{df.shape[1]}")
    print(f"重复行数:{df.duplicated().sum()}")
    missing = df.isna().sum()
    missing = missing[missing > 0]
    if len(missing):
        print("缺失值:")
        for col, n in missing.items():
            print(f"  {col}: {n} 个")
    else:
        print("缺失值:无")
    if "weight_kg" in df.columns:
        print(f"重量最大值:{df['weight_kg'].max()}")


def clean(df):
    """执行清洗流程。"""
    df = df.copy()

    # 1. 去掉完全重复的行
    df = df.drop_duplicates()

    # 2. 城市写法统一(去空格 + 替换别名)
    df["city"] = df["city"].astype(str).str.strip().replace(CITY_FIX)

    # 3. 修正单位错误:大于 100 的重量按"克"处理,换算成千克
    unit_error = df["weight_kg"] > 100
    df.loc[unit_error, "weight_kg"] = df.loc[unit_error, "weight_kg"] / 1000

    # 4. 超出合理范围的重量(<=0 或 >50kg)视为无效,置为缺失
    df.loc[(df["weight_kg"] <= 0) | (df["weight_kg"] > 50), "weight_kg"] = None

    # 5. 数值列缺失值用"同类别中位数"填补
    for col in NUMERIC_COLS:
        df[col] = df.groupby("category")[col].transform(lambda s: s.fillna(s.median()))

    # 6. 破损状态缺失的行无法分析,直接删除
    df = df.dropna(subset=["damaged"])

    # 6.5 注意:用中位数填补缺失值后,可能让原本不同的行变得完全相同,
    #     所以填补之后要再查一次重复行并去掉。
    df = df.drop_duplicates()

    # 7. 派生分析所需的新列
    df["volume"] = df["length_cm"] * df["width_cm"] * df["height_cm"]
    df["unit_freight"] = df["freight_cost"] / df["weight_kg"]
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["month"] = df["order_date"].dt.to_period("M").astype(str)

    return df.reset_index(drop=True)


def main():
    raw = pd.read_csv("data/packages_raw.csv")
    quality_report(raw, "清洗前")

    cleaned = clean(raw)
    quality_report(cleaned, "清洗后")

    cleaned.to_csv("data/packages_clean.csv", index=False)
    print(f"\n清洗完成,已保存 {len(cleaned)} 行 → data/packages_clean.csv")


if __name__ == "__main__":
    main()
