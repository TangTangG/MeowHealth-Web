# MeowHealth Web

"猫咪健康守护" 网页版，一个支持桌面和移动端的私有化单用户猫咪健康管理系统。

## 当前状态
- [x] 项目初始化
- [x] 需求说明书 (PRD) 与技术设计文档 (SystemDesign) 起草
- [x] AI 化验单与 Dashboard 交互设计规范确认
- [x] 生成交互设计 Mockup (`mockup/dashboard.html` + `mockup/index.html`)
- [ ] 后端基础框架搭建
- [ ] 前端基础框架搭建
- [ ] 核心 API 实现

## 文档导航
- 需求文档：`docs/PRD.md`
- 技术设计：`docs/SystemDesign.md`
- 交互设计规范：`docs/superpowers/specs/2026-04-09-ai-report-analysis-design.md`
- 交互原型：`mockup/dashboard.html` (Dashboard 概览) | `mockup/index.html` (报告详情)

## 设计亮点
- **Dashboard 概览页**：整合待办提醒 (iOS UNNotificationManager 映射)、体重趋势图 (SwiftCharts 映射)、近期健康事件流水与 AI 报告摘要。
- **AI 化验单分析**：采用「卡片仪表盘主展示 + 悬浮对话助手辅助答疑」的融合交互方案。
- **上传入口**：独立的拖拽多文件上传区 (支持 PDF/JPG/PNG)。
- **多猫支持**：侧边栏嵌入猫咪切换器，方便多猫家庭使用。
