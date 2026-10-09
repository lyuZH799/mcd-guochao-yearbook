#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_card.py —— 麦门年度人格报告 · 国潮风 SVG 卡片生成

输入：analyze.py 输出的 metrics（JSON）
输出：国潮风矢量 SVG 卡片（viewBox 0 0 680 960）

设计：朱红 #B22222 + 鎏金 #C9A227 + 宣纸 #F7F1E3；楷体标题 / 宋体正文；
内含麦当劳金色拱门「M」徽章与「我就喜欢 · I'M LOVIN' IT」标识。
纯矢量、零依赖、可离线复现。
"""

import json
import sys


# ----------------------------- 数值格式化 -----------------------------

def fmt_money(v):
    if v is None:
        return "¥0"
    v = float(v)
    if abs(v - round(v)) < 1e-6:
        return "¥{:,.0f}".format(round(v))
    return "¥{:,.1f}".format(v)


def esc(s):
    """转义 SVG 文本中的特殊字符。"""
    if s is None:
        return ""
    s = str(s)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ----------------------------- SVG 构建 -----------------------------

def build_svg(m):
    total_orders = m.get("total_orders", 0)
    total_spend = fmt_money(m.get("total_spend", 0))
    avg_order = fmt_money(m.get("avg_order", 0))
    favorite = esc(m.get("favorite_item", "—"))
    title = esc(m.get("persona_title", "麦门萌新"))
    tier = esc("{} · {}".format(m.get("tier_name", "麦门萌新"), m.get("level", "Lv.1")))
    slogan = esc(m.get("slogan", ""))
    time_label = esc(m.get("time_label", "—"))
    top_store = esc(m.get("top_store_label", "—"))
    channel = m.get("channel_dist", {})
    # 渠道取最高频
    if isinstance(channel, dict) and channel:
        channel = esc(sorted(channel.items(), key=lambda kv: -kv[1])[0][0])
    else:
        channel = "—"
    progress = int(m.get("progress", 0))

    # 段位进度条填充宽度（总宽 540）
    bar_w = max(0, min(540, round(540 * progress / 100.0)))

    svg = []
    svg.append('<svg viewBox="0 0 680 960" xmlns="http://www.w3.org/2000/svg">')

    # 外框 + 内描边
    svg.append('<rect x="20" y="20" width="640" height="920" rx="20" fill="#F7F1E3" stroke="#B22222" stroke-width="4"/>')
    svg.append('<rect x="32" y="32" width="616" height="896" rx="14" fill="none" stroke="#C9A227" stroke-width="1.5"/>')

    # 顶部红色标题带（仅上方圆角）
    svg.append('<path d="M20 150 L20 40 Q20 20 40 20 L640 20 Q660 20 660 40 L660 150 Z" fill="#B22222"/>')
    # 祥云装饰线
    svg.append('<path d="M60 120 q18 -14 36 0 t36 0 t36 0 t36 0 t36 0 t36 0 t36 0 t36 0 t36 0 t36 0 t36 0 t36 0 t36 0" fill="none" stroke="#E7C66B" stroke-width="1.5"/>')

    # 左上：麦当劳金色拱门 M 徽章
    svg.append('<rect x="56" y="36" width="50" height="50" rx="11" fill="#FFC72C"/>')
    svg.append('<path d="M68 64 Q74.5 47 81 64" fill="none" stroke="#DA291C" stroke-width="4" stroke-linecap="round"/>')
    svg.append('<path d="M81 64 Q87.5 47 94 64" fill="none" stroke="#DA291C" stroke-width="4" stroke-linecap="round"/>')

    # 标题
    svg.append('<text x="360" y="74" text-anchor="middle" font-family="KaiTi, STKaiti, serif" font-size="32" font-weight="500" fill="#F2D98C">我的麦门年报</text>')
    svg.append('<text x="360" y="108" text-anchor="middle" font-family="SimSun, serif" font-size="13" fill="#F2D98C" letter-spacing="3">MCD YEAR IN REVIEW</text>')

    # 右上：門 印章
    svg.append('<rect x="588" y="36" width="56" height="56" rx="8" fill="#B22222" stroke="#E7C66B" stroke-width="1.5"/>')
    svg.append('<text x="616" y="80" text-anchor="middle" font-family="KaiTi, STKaiti, serif" font-size="30" font-weight="500" fill="#F7F1E3">門</text>')

    # 人格徽章：薯条吉祥物（矢量）
    svg.append('<circle cx="340" cy="250" r="58" fill="#F7F1E3" stroke="#C9A227" stroke-width="3"/>')
    svg.append('<path d="M322 290 L358 290 L353 256 L327 256 Z" fill="#DA291C"/>')
    svg.append('<rect x="328" y="222" width="5" height="64" rx="2.5" fill="#C9A227"/>')
    svg.append('<rect x="337" y="216" width="5" height="70" rx="2.5" fill="#C9A227"/>')
    svg.append('<rect x="346" y="224" width="5" height="62" rx="2.5" fill="#C9A227"/>')

    # 人格称号 + 段位 + slogon
    svg.append('<text x="340" y="362" text-anchor="middle" font-family="KaiTi, STKaiti, serif" font-size="26" font-weight="500" fill="#B22222">' + title + '</text>')
    svg.append('<text x="340" y="394" text-anchor="middle" font-family="SimSun, serif" font-size="15" fill="#C9A227">' + tier + '</text>')
    svg.append('<text x="340" y="422" text-anchor="middle" font-family="SimSun, serif" font-size="13" fill="#5A4A3A">' + slogan + '</text>')

    # 四宫格分隔线
    svg.append('<line x1="70" y1="446" x2="610" y2="446" stroke="#C9A227" stroke-width="1"/>')
    svg.append('<line x1="340" y1="470" x2="340" y2="692" stroke="#C9A227" stroke-width="1"/>')
    svg.append('<line x1="70" y1="581" x2="610" y2="581" stroke="#C9A227" stroke-width="1"/>')

    # 四宫格数据
    svg.append('<text x="178" y="502" text-anchor="middle" font-family="SimSun, serif" font-size="12" fill="#8A7A5A">总订单</text>')
    svg.append('<text x="178" y="534" text-anchor="middle" font-family="SimSun, serif" font-size="26" font-weight="500" fill="#1A1A1A">' + str(total_orders) + '</text>')
    svg.append('<text x="502" y="502" text-anchor="middle" font-family="SimSun, serif" font-size="12" fill="#8A7A5A">总花费</text>')
    svg.append('<text x="502" y="534" text-anchor="middle" font-family="SimSun, serif" font-size="26" font-weight="500" fill="#1A1A1A">' + total_spend + '</text>')
    svg.append('<text x="178" y="613" text-anchor="middle" font-family="SimSun, serif" font-size="12" fill="#8A7A5A">最爱单品</text>')
    svg.append('<text x="178" y="645" text-anchor="middle" font-family="SimSun, serif" font-size="17" font-weight="500" fill="#1A1A1A">' + favorite + '</text>')
    svg.append('<text x="502" y="613" text-anchor="middle" font-family="SimSun, serif" font-size="12" fill="#8A7A5A">平均客单</text>')
    svg.append('<text x="502" y="645" text-anchor="middle" font-family="SimSun, serif" font-size="18" font-weight="500" fill="#1A1A1A">' + avg_order + '</text>')

    # 数据画像（三列）
    svg.append('<text x="70" y="712" font-family="SimSun, serif" font-size="12" fill="#8A7A5A">数据画像</text>')
    svg.append('<line x1="245" y1="726" x2="245" y2="778" stroke="#C9A227" stroke-width="1"/>')
    svg.append('<line x1="435" y1="726" x2="435" y2="778" stroke="#C9A227" stroke-width="1"/>')
    svg.append('<text x="150" y="738" text-anchor="middle" font-family="SimSun, serif" font-size="12" fill="#8A7A5A">主力时段</text>')
    svg.append('<text x="150" y="766" text-anchor="middle" font-family="SimSun, serif" font-size="16" font-weight="500" fill="#1A1A1A">' + time_label + '</text>')
    svg.append('<text x="340" y="738" text-anchor="middle" font-family="SimSun, serif" font-size="12" fill="#8A7A5A">常去门店</text>')
    svg.append('<text x="340" y="766" text-anchor="middle" font-family="SimSun, serif" font-size="16" font-weight="500" fill="#1A1A1A">' + top_store + '</text>')
    svg.append('<text x="530" y="738" text-anchor="middle" font-family="SimSun, serif" font-size="12" fill="#8A7A5A">下单渠道</text>')
    svg.append('<text x="530" y="766" text-anchor="middle" font-family="SimSun, serif" font-size="16" font-weight="500" fill="#1A1A1A">' + channel + '</text>')

    # 段位进度条
    svg.append('<text x="70" y="800" font-family="SimSun, serif" font-size="12" fill="#8A7A5A">麦门段位进度</text>')
    svg.append('<rect x="70" y="812" width="540" height="12" rx="6" fill="#E5D9BC"/>')
    svg.append('<rect x="70" y="812" width="' + str(bar_w) + '" height="12" rx="6" fill="#C9A227"/>')
    svg.append('<text x="610" y="823" text-anchor="end" font-family="SimSun, serif" font-size="11" fill="#8A7A5A">' + str(progress) + '%</text>')

    # 麦当劳 slogon 胶囊
    svg.append('<rect x="200" y="842" width="280" height="34" rx="17" fill="#FFC72C"/>')
    svg.append('<text x="340" y="865" text-anchor="middle" font-family="KaiTi, STKaiti, serif" font-size="15" font-weight="500" fill="#DA291C">我就喜欢 · I\'M LOVIN\' IT</text>')

    # 脱敏页脚
    svg.append('<text x="340" y="904" text-anchor="middle" font-family="SimSun, serif" font-size="12" fill="#8A7A5A">用 WorkBuddy + 麦当劳 MCP 生成</text>')
    svg.append('<text x="340" y="928" text-anchor="middle" font-family="SimSun, serif" font-size="12" fill="#B22222">github.com/lyuZH799/mcd-guochao-yearbook</text>')

    svg.append('</svg>')
    return "\n".join(svg)


# ----------------------------- CLI -----------------------------

def main():
    import argparse
    ap = argparse.ArgumentParser(description="麦门年报 · 国潮风 SVG 卡片生成")
    ap.add_argument("input", help="metrics JSON 文件路径")
    ap.add_argument("-o", "--out", help="输出 SVG 路径（默认 stdout）")
    args = ap.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        m = json.load(f)
    svg = build_svg(m)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"[render] 已生成卡片 -> {args.out}")
    else:
        print(svg)


if __name__ == "__main__":
    main()
