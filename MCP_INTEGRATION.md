# MCP 接入说明（MCP_INTEGRATION.md）

本文件说明「麦门年度人格报告」技能实际使用的麦当劳 MCP Server、Tool、调用流程与业务价值，满足大赛参赛要求。

## 1. 接入的 MCP Server

| 项 | 值 |
|---|---|
| Server 名称 | `mcd-mcp` |
| 传输方式 | `streamablehttp` |
| 服务地址 | `https://mcp.mcd.cn` |
| 鉴权方式 | `Authorization: Bearer <TOKEN>`（Token 由参赛者在麦当劳 MCP 控制台申请） |
| 配置样例 | 见仓库 `mcp-config.example.json`（仅占位符，不含真实凭证） |

## 2. 实际调用的 Tool

| Tool | 是否核心 | 用途 |
|---|---|---|
| `order-list` | ✅ 核心 | 拉取历史**餐饮**订单 `data.list[]`，含订单时间、渠道、门店、状态、商品明细与金额，是人格报告唯一主数据源 |
| `query-my-account` | 降级 | 查询积分账户；当 `order-list` 无数据时，回退展示积分维度，避免空卡 |
| `query-my-prizes` | 降级 | 查询抽奖记录；无订单时的次选填充维度 |
| `query-my-coupons` | 可选 | 查询我的券；用于扩展「优惠敏感度」次级维度（当前为可选增强） |
| `now-time-info` | 可选 | 提供时间基准，用于文案中的「当前年度」标注 |

> 说明：`order-list` **不含商城订单**（商城订单由 `mall-*` 接口提供）。本技能聚焦「餐饮订单」以刻画「吃麦当劳的人格」，定位更聚焦、传播更利。

## 3. order-list 字段 → 年报指标 映射

`order-list` 返回 `data.list[]`，单条订单结构（已实测确认）：

| 字段 | 含义 | 用于计算的年报指标 |
|---|---|---|
| `orderId` | 订单编码 | 脱敏对象（不展示） |
| `orderType` | 订单类型 / 渠道 | 渠道分布（到店 / 外送 / 得来速） |
| `createTime` | 下单时间 | 主力时段画像（深夜 / 早安 / 正午 / 午后 / 黄昏） |
| `beType` / `beCode` | 门店类型 / BE 编码 | 脱敏对象（不展示） |
| `storeCode` / `storeName` | 门店编码 / 名称 | 脱敏对象；本地聚合「常去门店」后仅展示匿名标签 |
| `orderStatus` | 订单状态 | 仅统计已完成订单 |
| `orderProductList[].productName` / `.quantity` | 商品名称 / 数量 | 最爱单品（按数量聚合）、品类原型判定 |
| `realTotalAmount` | 总金额（字符串） | 总花费、平均客单 |

> 单次 `order-list` 调用即可获得上述全部字段，**无需 `query-order` 二次查询**。

## 4. 调用流程

```
用户发起「生成我的麦门年报」
        │
        ▼
Agent 通过 mcd-mcp 连接器调用 order-list
        │  （工具全名通常为 mcp__mcd-mcp__order-list）
        ▼
取得 data.list[] → 写入本地临时 JSON（仅本次会话，不留存凭证）
        │
        ▼
python src/build.py orders.json -o card.svg
   ├─ analyze.py：脱敏 + 计算指标 + 确定性人格分类
   └─ render_card.py：国潮风 SVG 卡片合成
        │
        ▼
预览 / 导出 PNG（Pillow 可选）并回传用户
```

## 5. 降级策略（数据为空）

- 若 `order-list` 返回 `data.list` 为空（账号无历史订单）：
  1. 尝试 `query-my-account` 获取积分，渲染「积分版」简卡；
  2. 仍不足则直接渲染「麦门萌新」默认卡（段位 Lv.1），并提示用户先下单一笔。
- 全程不抛未捕获异常，保证「有网即出卡」。

## 6. 业务价值

将冷冰冰的订单流水，转化为**可分享、有梗、带品牌识别度**的「年度人格报告」：
- 强化用户与麦当劳品牌的情感连接与社交传播（用户自发晒卡 = 免费曝光）；
- 国潮视觉 + 确定性人格，降低生成随机性、提升可复现与可审阅性；
- 隐私脱敏设计契合数据安全合规要求，便于公开传播。

## 7. 隐私与安全

- 不写入/不提交任何真实 Token、密钥、账号凭证（配置仅占位符）；
- 渲染前对订单号、门店编码、BE 编码、门店名称做脱敏；
- 中间数据仅存在于本次本地会话，不落盘敏感信息。
