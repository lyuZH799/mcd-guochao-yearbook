---
name: mcd-guochao-yearbook
description: 基于麦当劳 MCP 历史订单，生成国潮风「麦门年度人格报告」分享卡片的技能。自动拉取订单、确定性人格分类、离线矢量渲染、隐私脱敏。当用户想"生成我的麦门年报 / 人格卡 / 年度总结 / 看看我是什么麦门人 / 用麦当劳订单做一张分享卡"时使用。
version: 1.0.0
author: mcd-guochao-yearbook-contributor
license: MIT
---

# 麦门年度人格报告（mcd-guochao-yearbook）

## 概述

把用户在麦当劳的历史餐饮订单，变成一张**国潮风、可分享、带品牌识别度**的「年度人格报告」卡片。设计原则：

- **取数交给 MCP**：通过 `mcd-mcp` 连接器调用 `order-list` 拉取订单。
- **算术交给代码**：所有指标与人格分类由 `src/analyze.py` 的确定性函数计算，不靠 LLM 随机生成。
- **表达交给 Agent**：卡片版式由 `src/render_card.py` 的矢量模板合成，Agent 负责调用与呈现。

## 触发场景

用户表达类似意图时启用本技能：生成麦门年报 / 人格卡 / 年度总结 / 看看我是什么麦门人 / 用我的麦当劳订单做一张好看的分享卡。

## 前置条件

1. 已按 `mcp-config.example.json` 配置并**启用** `mcd-mcp` 连接器（Token 已替换为真实值）。
2. Python 3 可用（优先使用环境内的 `python3` / 托管 Python；无需任何第三方依赖，Pillow 仅用于可选的 PNG 导出）。

## 工作流（严格按顺序）

### 步骤 1 · 取数
通过 `mcd-mcp` 连接器调用 **`order-list`**（工具全名通常为 `mcp__mcd-mcp__order-list`），取得历史餐饮订单。
- 参数：无需传参（默认返回当前账号历史订单）。
- 关注返回结构：`result.content[].structuredContent.data.list[]`（若只拿到文本，解析其中 `data.list`）。
- 将 `data.list` 写入本地临时文件 `orders.json`（仅本次会话，不留存任何 Token / 账号凭证）。

### 步骤 2 · 计算与分类
运行：
```bash
python src/build.py orders.json -o card.svg
```
该命令内部依次：
1. `analyze.py`：脱敏 → 计算指标 → 确定性人格分类，输出中间 `metrics`（JSON）。
2. `render_card.py`：依 `metrics` 生成国潮风 SVG 写入 `card.svg`。

若需要分步调试，也可分别运行 `python src/analyze.py orders.json` 与 `python src/render_card.py metrics.json -o card.svg`。

### 步骤 3 · 呈现与导出
- 直接预览 `card.svg`（纯矢量，浏览器/WorkBuddy 均可渲染）。
- 如需 PNG：`python -c "from PIL import Image; ..."` 将 SVG 栅格化（可选，依赖 Pillow；缺失时跳过并提示用户）。

### 步骤 4 · 降级（仅当 order-list 为空时）
若 `data.list` 为空（账号无历史订单）：
1. 尝试调用 `query-my-account` 获取积分，渲染「积分版」简卡（在 `metrics` 中标记 `mode="points"`）；
2. 仍不足则直接渲染「麦门萌新」默认卡（`mode="novice"`，段位 Lv.1），并提示用户「先下单一笔，明年就能生成完整年报」。

## 数据字段（order-list 实测确认）

单条订单 `data.list[]` 字段：

| 字段 | 用途 |
|---|---|
| `orderId` | 脱敏，不展示 |
| `orderType` | 渠道分布（到店 / 外送 / 得来速） |
| `createTime` | 主力时段画像 |
| `beType` / `beCode` | 脱敏，不展示 |
| `storeCode` / `storeName` | 脱敏；本地聚合「常去门店」后仅展示匿名标签 |
| `orderStatus` | 仅统计已完成订单 |
| `orderProductList[].productName` / `.quantity` | 最爱单品、品类原型 |
| `realTotalAmount` | 总花费、平均客单（字符串，需转 float） |

> `order-list` 不含商城订单（商城由 `mall-*` 提供）；本技能聚焦餐饮订单。

## 指标与人格分类（确定性规则，详见 `src/analyze.py`）

**核心指标**：总订单数、总花费、平均客单、最爱单品（按 `quantity` 聚合）、时段分布、渠道分布、常去门店（匿名标签）、首/末单日期。

**时段分桶**（按 `createTime` 小时）：
- 深夜 22:00–04:59 / 早安 05:00–10:59 / 正午 11:00–13:59 / 午后 14:00–16:59 / 黄昏 17:00–21:59。取占比最高桶为「主力时段」。

**品类原型**（按最爱单品关键词）：薯条→薯条哲学家；炸鸡/鸡翅→炸鸡鉴赏家；汉堡/巨无霸→汉堡指挥官；辣→无辣不欢者；咖啡→续命咖啡因；甜品/派→甜品收藏家；早餐→晨型人；默认→麦门探索者。

**人格称号** = 主力时段前缀 + 品类原型，例如「深夜薯条哲学家」。

**段位（按累计订单数）**：
- 0 → 麦门萌新 · Lv.1
- 1–9 → 见习门徒 · Lv.2
- 10–24 → 资深门徒 · Lv.3
- 25–49 → 黄金门徒 · Lv.4
- 50–99 → 钻石门徒 · Lv.5
- ≥100 → 麦门传奇 · Lv.6

段位进度条按「当前订单数 / 下一门槛」计算百分比。

**专属 slogon**：按品类原型从 `SLOGAN_MAP` 取固定文案（如薯条哲学家→「月亮不睡你不睡，麦辣薯条配工位」）；萌新→「故事才刚开始，下单一杯开启麦门」。

## 视觉规范（国潮风，详见 `src/render_card.py`）

- **配色**：朱红 `#B22222`、鎏金 `#C9A227`、宣纸 `#F7F1E3`、金红点缀 `#DA291C` / `#FFC72C`。
- **字体**：标题用楷体 `KaiTi, STKaiti, serif`，正文用宋体 `SimSun, serif`；SVG 中不内嵌字体文件，由渲染环境系统字体承接。
- **麦当劳品牌标识（必须包含）**：左上金色拱门「M」徽章（黄底 `#FFC72C` + 双红 `#DA291C` 拱形曲线）；底部「我就喜欢 · I'M LOVIN' IT」黄色 slogon 胶囊（`#FFC72C` 底 + `#DA291C` 字）。
- **版式**：封面标题 → 人格徽章（SVG 薯条吉祥物）→ 称号 + 段位 + slogon → 四宫格数据（总订单/总花费/最爱单品/平均客单）→ 数据画像（主力时段/常去门店/下单渠道）→ 段位进度条 → 品牌 slogon 胶囊 → 脱敏页脚（含「用 WorkBuddy + 麦当劳 MCP 生成」与仓库链接）。
- **尺寸**：SVG `viewBox="0 0 680 960"`，单图单内容、扁平无渐变无阴影（契合 WorkBuddy 组件规范与国潮扁平审美）。

## 隐私脱敏（必须执行）

`src/analyze.py` 在解析后立即丢弃 `orderId / storeName / storeCode / beCode` 等原始敏感值；「常去门店」仅以「店A / 店B」匿名标签出现。卡片与任何中间产物**不得包含真实 Token、手机号、门店全称**。

## 输出物

- `card.svg`：国潮风人格报告卡片（主交付）。
- 可选 `card.png`：栅格化分享图。
- 中间 `metrics.json`：结构化指标，便于二次创作。

## 注意事项

- 本技能**不调用任何外部图像连接器 / 文生图 API**，全部为本地矢量生成，保证离线可复现、零依赖。
- 餐品信息、价格及供应状态以麦当劳官方渠道实时结果为准；本卡片仅供参考，不构成专业建议。
- 若用户尚未配置 MCP，先引导其按 `mcp-config.example.json` 配置并启用 `mcd-mcp`，再执行取数。
