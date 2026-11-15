---
status: provisional
source: Tencent、Tencent-Hunyuan、TencentARC、TencentCloud、WeChatCV 官方 GitHub 仓库说明及 README
source_version: accessed 2026-11-15；仓库创建窗口 2026-08-15 至 2026-11-15
applies_to: 跨项目发现腾讯 AI 开源工具、Agent 运行时、记忆、知识库及多模态研究项目
excludes: 穷尽腾讯关联组织、认定首次公开日期、许可证法律判断、生产可用性或性能验收
---

# 腾讯 AI 开源项目发现与选型

## 结论

检索腾讯开源项目时，不能只查 `Tencent` 主组织。已核对组织主页的独立入口还包括 [Tencent-Hunyuan](https://github.com/Tencent-Hunyuan)、[TencentARC](https://github.com/TencentARC)、[TencentCloud](https://github.com/TencentCloud) 和 [WeChatCV](https://github.com/WeChatCV)。前三者分别链接腾讯混元、腾讯 ARC 和腾讯云官网；WeChatCV 标注为微信计算机视觉团队。

下面是 2026-11-15 的发现快照，不是腾讯全部开源项目清单。仓库创建日期不等于首次开源日期，也不等于最近版本发布日期；现有项目的重要更新应单列，避免漏掉 WeKnora 这类项目。

## Agent 工程优先入口

| 项目 | 定位 | 官方来源 |
| --- | --- | --- |
| octop-harness | 基于 Harness Engineering 思路的 Agent 运行时 | [TencentCloud/octop-harness](https://github.com/TencentCloud/octop-harness) |
| Hy-Memory / MemHub | 聊天、工作和编码记忆；跨 AI 应用的本地优先记忆管理 | [Tencent-Hunyuan/Hy-Memory](https://github.com/Tencent-Hunyuan/Hy-Memory) |
| octop-memory | 跨会话、跨 Agent 的偏好和上下文记忆 | [TencentCloud/octop-memory](https://github.com/TencentCloud/octop-memory) |
| ContextPilot | 通过强化学习训练 Agent 主动管理上下文 | [Tencent/ContextPilot](https://github.com/Tencent/ContextPilot) |
| page-harness | 在实际网页上点选元素，与编码 Agent 协作修改页面 | [Tencent/page-harness](https://github.com/Tencent/page-harness) |
| IterSynth | 角色解耦的深度搜索 Agent 与强化学习训练代码 | [Tencent/IterSynth](https://github.com/Tencent/IterSynth) |
| VideoHarness-RSI | 固定视频模型，由编码 Agent 优化外围上下文构建程序 | [Tencent/VideoHarness-RSI](https://github.com/Tencent/VideoHarness-RSI) |
| octop-browser | 直接基于 CDP 的 Agent 浏览器自动化 | [TencentCloud/octop-browser](https://github.com/TencentCloud/octop-browser) |
| octop-gateway | 面向 Agent 的多平台即时通信桥接 | [TencentCloud/octop-gateway](https://github.com/TencentCloud/octop-gateway) |
| aigate | 自托管 LLM 网关，支持 OpenAI / Anthropic 协议、路由和配额 | [TencentCloud/aigate](https://github.com/TencentCloud/aigate) |

以上用途来自官方描述或 README，未运行验证。Hy-Memory 的 README 明确记录 2026 年 10 月开源 monorepo 及 MemHub，其余项目不要仅凭创建时间认定首次开源时间。

## 其他 AI 项目发现索引

下列名称对应组织内同名仓库，具体能力、权重和代码开放范围应在选型时重新核读。

| 组织 | 方向 | 仓库名 |
| --- | --- | --- |
| [Tencent](https://github.com/Tencent) | 多模态、文档、视频 | WeMM-Embedding、EVIE、WeVisDoc、WeVisOne-VL、WeVisCut |
| Tencent | Agent、推理与评测 | Game-Creation-Agents、KnowGPO、DSpine、ElephantBench、GroupAssistBench、NarrativeSteward |
| Tencent | 科学与机器人 | DynaHelix、legged_rl_gym |
| [Tencent-Hunyuan](https://github.com/Tencent-Hunyuan) | 模型、生成与训练优化 | AuK、Hy4-preview、Prism、Hy-Nomas、Hy-SimulMT、Simple-Attention-Sparsification、HYDRA、FlashTopK、EmoReward |
| Tencent-Hunyuan | 评测及数据研究 | ExplorationBench、DiagSafe、OmniCapBench、HyperLogic、ORAV-Bench、AppCIF-Bench、evolve-scaler |
| [TencentARC](https://github.com/TencentARC) | 世界模型、游戏与 3D | WorldCrafter、GAE-GeometricAutoEncoder、GameHorizon、Player-1、Multics、Looking-Ahead、OREO-RenderingEdittingOptimization |
| [WeChatCV](https://github.com/WeChatCV) | 视频及视觉文字生成 | Loopy、SyncReward、Wan-Alpha_PlusPlus、TextDART-SCANNER |

## 现有项目的重要更新

[WeKnora](https://github.com/Tencent/WeKnora) 不应因不满足新建仓库筛选而被忽略。官方 README 记录 v0.8.2（2026-09-24）、v0.8.3（2026-10-14）和 v0.9.0（2026-10-29）；它属于 RAG + Agent + Wiki 知识平台，详见 [已有选型条目](weknora-tencent-knowledge-platform.md)。本轮未独立核实首次公开日期。

## 检索边界与复用方法

1. 明确统计的是首次公开、新建仓库，还是已有项目的新版本；分别列证据。
2. 先从腾讯主组织和已确认归属的独立组织检索，再用官方公告补首次公开时间。
3. GitHub 搜索可用 `org:Tencent created:2026-08-15..2026-11-15 fork:false`，替换组织名逐一查询；此条件只限定创建时间。
4. 不把所有合作实验室、作者个人组织或名字含 Tencent 的账号自动算成腾讯旗下。
5. 本轮 API 随后限流，优图、腾讯音乐等未完成核查；不能声称已穷尽。
6. 未逐项审核许可证，也未安装或做性能、质量测试。公开代码或模型不代表无条件商用。
