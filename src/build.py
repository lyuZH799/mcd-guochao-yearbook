#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py —— 麦门年度人格报告 · 一键生成

输入：order-list 原始订单 JSON
输出：国潮风 SVG 卡片

用法：
    python src/build.py orders.json -o card.svg
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyze import load_orders, build_metrics
from render_card import build_svg


def main():
    ap = argparse.ArgumentParser(description="麦门年报 · 订单 JSON -> 国潮 SVG 卡片")
    ap.add_argument("input", help="订单 JSON 文件路径")
    ap.add_argument("-o", "--out", default="card.svg", help="输出 SVG 路径（默认 card.svg）")
    ap.add_argument("--metrics-out", help="顺便导出中间 metrics JSON 的路径（可选）")
    args = ap.parse_args()

    orders = load_orders(args.input)
    metrics = build_metrics(orders)

    if args.metrics_out:
        with open(args.metrics_out, "w", encoding="utf-8") as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)

    svg = build_svg(metrics)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(svg)

    print("[build] 订单数={} 人格='{}' 段位={} 进度={}% -> {}".format(
        metrics["total_orders"], metrics["persona_title"],
        metrics["tier_name"], metrics["progress"], args.out))


if __name__ == "__main__":
    main()
