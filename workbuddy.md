# WorkBuddy 开发上下文（workbuddy.md）

> 本文件记录本项目使用 WorkBuddy 进行创意构思、开发与调试的关键上下文，用于核验是否符合麦当劳 × WorkBuddy 联动活动奖励条件。

## 项目由来

参赛方向从 6 个候选中筛选产生：D1 抽奖概率精算、D2 性价比价值密度、D3 个性化营养、D4 社交年报/人格卡、D5 价格监控、D6 企业团餐精算。综合「传播性、差异化、可行性、红海程度」后选定 **D4 麦门年报/人格卡** 作为主攻方向。

## 关键设计决策（在 WorkBuddy 中迭代完成）

1. **三段论架构**：取数交给 MCP、算术交给代码、表达交给 Agent。核心计算与渲染全部落在 `src/*.py`，Agent 仅做编排，保证结果确定性、可复现、可审阅。
2. **确定性人格分类**：时段 / 品类 / 客单 / 渠道多维规则，输出稳定称号 + 段位 + slogon，避免 LLM 随机生成导致同一用户每次结果不同。
3. **预置图片问题**：明确**不预置位图**，改用 SVG 矢量模板 + 代码合成（离线可复现、可版本化、可审阅），人格图标用 SVG 形状绘制，PNG 导出仅作可选 Pillow 分支。
4. **隐私脱敏**：分享卡片必须剥离订单号、门店、手机号等敏感字段。
5. **视觉增强**：检索平台内设计专家与图像能力后，确定以**国潮风**（朱红 + 鎏金 + 宣纸、楷体/宋体）作为差异化视觉，并加入麦当劳金色拱门「M」徽章与「我就喜欢 · I'M LOVIN' IT」标识；明确技能内不调用外部图像连接器，以维持离线/零依赖。

## 关键技术验证（由 WorkBuddy 执行）

- 配置并连通麦当劳 MCP（`mcd-mcp`），实测暴露 35 个工具。
- **实测确认 `order-list` 返回字段**：`orderId / orderType / createTime / beType / beCode / storeCode / storeName / orderStatus / orderProductList[]{productCode,productName,quantity,comboItemList} / realTotalAmount`，确认单次调用即可支撑全部年报指标，**无需 `query-order` 二次查询**。
- 发现测试账号 `data` 为空 → 据此在技能中内置**空数据降级**与**脱敏离线样例数据**，保证任何人在无订单时也能跑出完整卡片。

## 产出物

- 国潮风人格卡示例（`examples/sample_card.svg`）；
- 完整可安装的 WorkBuddy 技能（`SKILL.md` + `src/`）；
- 符合大赛要求的参赛文件套件（README / CONTEST_DECLARATION / MCP_INTEGRATION / mcp-config.example.json / 本文件）。

## 开发方式说明

全程在 WorkBuddy Agent 模式下，以「先诊断确认、再动手实现、迭代修改」的方式推进：先核对官方参赛规则与必交文件清单，再搭建骨架，最后用离线样例做渲染验证。
