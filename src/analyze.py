#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze.py —— 麦门年度人格报告 · 指标计算与确定性人格分类

输入：order-list 返回的原始订单 JSON（支持多种结构形态）
输出：metrics（JSON），包含核心指标 + 确定性人格分类结果

设计原则：纯标准库、确定性、可复现、隐私脱敏。
"""

import json
import sys
import re
from datetime import datetime
from collections import Counter


# ----------------------------- 数据加载与归一化 -----------------------------

def load_orders(path):
    """读取订单 JSON 并归一化为订单列表 list[dict]。

    兼容以下形态：
      - {"success":..., "data": {"list": [...]}}
      - {"data": {"list": [...]}}
      - {"list": [...]}
      - [...]  (直接是列表)
    """
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        data = raw.get("data")
        if isinstance(data, dict) and "list" in data:
            return data.get("list") or []
        if "list" in raw:
            return raw.get("list") or []
    return []


# ----------------------------- 脱敏辅助 -----------------------------

def anon_store_labels(store_counter):
    """把门店名称映射为匿名标签 店A / 店B / ..."""
    labels = {}
    for i, (store, _cnt) in enumerate(store_counter.most_common()):
        labels[store] = "店" + chr(ord("A") + i)
    return labels


# ----------------------------- 解析辅助 -----------------------------

def parse_hour(create_time):
    """从 createTime 字符串中提取小时（0-23）。失败返回 -1。"""
    if not create_time:
        return -1
    m = re.search(r"(\d{1,2}):\d{2}", str(create_time))
    if m:
        return int(m.group(1))
    # 退而求其次：尝试 ISO 日期中的 T 后小时
    m = re.search(r"T(\d{1,2}):", str(create_time))
    if m:
        return int(m.group(1))
    return -1


def parse_date(create_time):
    """提取 YYYY-MM-DD 日期字符串，失败返回空。"""
    if not create_time:
        return ""
    m = re.search(r"(\d{4}-\d{2}-\d{2})", str(create_time))
    return m.group(1) if m else ""


def to_float(amount):
    """realTotalAmount 多为字符串，转为 float；失败返回 0.0。"""
    if amount is None:
        return 0.0
    try:
        return float(str(amount).replace(",", "").strip())
    except ValueError:
        return 0.0


# ----------------------------- 分类规则（确定性） -----------------------------

def hour_bucket(h):
    if h == -1:
        return "未知"
    if 22 <= h or h < 5:
        return "深夜"
    if 5 <= h < 11:
        return "早安"
    if 11 <= h < 14:
        return "正午"
    if 14 <= h < 17:
        return "午后"
    return "黄昏"


# 品类原型判定：顺序即优先级
ARCHETYPE_RULES = [
    (["薯条", "薯", "条"], "薯条哲学家"),
    (["辣"], "无辣不欢者"),
    (["鸡", "翅", "腿", "块", "鸡米"], "炸鸡鉴赏家"),
    (["堡", "巨无霸", "板烧", "汉堡"], "汉堡指挥官"),
    (["咖啡", "美式", "拿铁", "卡布", "麦咖啡"], "续命咖啡因"),
    (["派", "圣代", "新地", "甜", "圆筒", "麦旋"], "甜品收藏家"),
    (["早餐", "猪柳", "蛋", "粥", "麦满分"], "晨型人"),
]


def archetype_of(name):
    n = str(name or "")
    for keys, label in ARCHETYPE_RULES:
        if any(k in n for k in keys):
            return label
    return "麦门探索者"


SLOGAN_MAP = {
    "薯条哲学家": "月亮不睡你不睡，麦辣薯条配工位",
    "炸鸡鉴赏家": "金黄酥脆，是治愈一周的真理",
    "汉堡指挥官": "一口巨无霸，掌控小宇宙",
    "无辣不欢者": "辣，是成年人最后的任性",
    "续命咖啡因": "冰美式续命，打工人的图腾",
    "甜品收藏家": "生活很苦，麦麦甜一点",
    "晨型人": "早起的人，先尝到麦香",
    "麦门探索者": "每一次点单，都是新的冒险",
    "麦门萌新": "故事才刚开始，下单一杯开启麦门",
}


def tier_of(n):
    """返回 (段位名, 等级, 当前值, 下一门槛)。进度 = 当前值/下一门槛。"""
    if n <= 0:
        return ("麦门萌新", "Lv.1", 0, 1)
    if n < 10:
        return ("见习门徒", "Lv.2", n, 10)
    if n < 25:
        return ("资深门徒", "Lv.3", n, 25)
    if n < 50:
        return ("黄金门徒", "Lv.4", n, 50)
    if n < 100:
        return ("钻石门徒", "Lv.5", n, 100)
    return ("麦门传奇", "Lv.6", 100, 100)


# ----------------------------- 指标计算 -----------------------------

def compute_metrics(orders):
    if not orders:
        return _novice_metrics()

    total_orders = len(orders)
    total_spend = 0.0
    item_counter = Counter()          # 商品名 -> 总数量
    hour_counter = Counter()          # 时段 -> 订单数
    channel_counter = Counter()       # 渠道 -> 订单数
    store_counter = Counter()         # 门店名 -> 订单数（仅本地聚合，渲染前脱敏）
    dates = []

    for o in orders:
        total_spend += to_float(o.get("realTotalAmount"))
        h = parse_hour(o.get("createTime"))
        hour_counter[hour_bucket(h)] += 1
        ot = o.get("orderType") or "未知"
        channel_counter[ot] += 1
        sn = o.get("storeName") or "未知门店"
        store_counter[sn] += 1
        d = parse_date(o.get("createTime"))
        if d:
            dates.append(d)
        for p in (o.get("orderProductList") or []):
            nm = p.get("productName")
            qty = p.get("quantity") or 0
            try:
                qty = int(qty)
            except (TypeError, ValueError):
                qty = 0
            if nm:
                item_counter[nm] += qty

    # 最爱单品
    if item_counter:
        favorite_item, favorite_count = item_counter.most_common(1)[0]
    else:
        favorite_item, favorite_count = "—", 0

    # 主力时段
    time_label = hour_counter.most_common(1)[0][0] if hour_counter else "未知"

    # 常去门店（匿名）
    store_labels = anon_store_labels(store_counter)
    top_store_name = store_counter.most_common(1)[0][0] if store_counter else "—"
    top_store_label = store_labels.get(top_store_name, "—")

    # 渠道
    channel_dominant = channel_counter.most_common(1)[0][0] if channel_counter else "—"

    avg_order = (total_spend / total_orders) if total_orders else 0.0

    # 人格分类
    archetype = archetype_of(favorite_item)
    tier_name, level, cur, nxt = tier_of(total_orders)
    progress = min(100, round(cur / nxt * 100)) if nxt else 100
    persona_title = "麦门萌新" if total_orders == 0 else (time_label + archetype)
    slogan = SLOGAN_MAP.get(archetype if total_orders else "麦门萌新", SLOGAN_MAP["麦门探索者"])

    return {
        "mode": "full",
        "total_orders": total_orders,
        "total_spend": round(total_spend, 2),
        "avg_order": round(avg_order, 2),
        "favorite_item": favorite_item,
        "favorite_count": favorite_count,
        "time_label": time_label,
        "time_dist": dict(hour_counter),
        "channel_dist": dict(channel_counter),
        "top_store_label": top_store_label,
        "first_order": min(dates) if dates else "",
        "last_order": max(dates) if dates else "",
        "persona_title": persona_title,
        "archetype": archetype,
        "tier_name": tier_name,
        "level": level,
        "progress": progress,
        "slogan": slogan,
    }


def _novice_metrics():
    return {
        "mode": "novice",
        "total_orders": 0,
        "total_spend": 0.0,
        "avg_order": 0.0,
        "favorite_item": "—",
        "favorite_count": 0,
        "time_label": "—",
        "time_dist": {},
        "channel_dist": {},
        "top_store_label": "—",
        "first_order": "",
        "last_order": "",
        "persona_title": "麦门萌新",
        "archetype": "麦门萌新",
        "tier_name": "麦门萌新",
        "level": "Lv.1",
        "progress": 0,
        "slogan": SLOGAN_MAP["麦门萌新"],
    }


def build_metrics(orders):
    """对外入口：订单列表 -> metrics。"""
    return compute_metrics(orders)


# ----------------------------- CLI -----------------------------

def main():
    import argparse
    ap = argparse.ArgumentParser(description="麦门年报 · 订单指标与人格分类")
    ap.add_argument("input", help="订单 JSON 文件路径")
    ap.add_argument("--out", help="输出 metrics JSON 路径（默认 stdout）")
    args = ap.parse_args()

    orders = load_orders(args.input)
    metrics = build_metrics(orders)
    text = json.dumps(metrics, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"[analyze] 已写入 metrics -> {args.out}（订单数={metrics['total_orders']}）")
    else:
        print(text)


if __name__ == "__main__":
    main()
