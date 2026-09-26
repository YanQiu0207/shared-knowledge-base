---
status: provisional
source: wechat-article-exporter 官方仓库及停更公告；qiye45/wechatDownload、zyw-Wayne/wechat-article-down 官方 README；易微信 Chrome 扩展商店说明
source_version: accessed 2026-09-26
applies_to: 微信公众号文章的个人备份、已知文章链接保存与工具选型
excludes: 未经实测的批量抓取成功率、绕过平台限制、版权授权判断、特定项目的部署配置与数据
---

# 微信公众号文章归档：停用工具与替代路径

## 结论

- `wechat-article-exporter` 曾提供公众号搜索、历史文章同步和 HTML、Markdown、Word 等格式导出，支持 Docker 私有化部署。但作者于 2026-07-30 公告：依赖的微信上游核心接口已关闭，**开箱即用的一键同步历史文章不再可用**；已同步到本地的文章仍可保留和导出。容器仍运行或页面能打开，不等于同步功能仍可用。[项目仓库](https://github.com/wechat-article/wechat-article-exporter)、[停更公告](https://github.com/wechat-article/wechat-article-exporter/issues/200)
- 先分清需求：**抓取某个公众号的历史文章列表**与**保存手头已有链接的文章**不是同一能力。前者受上游接口关闭影响更大；后者可尝试基于浏览器已打开页面的提取工具。以下替代品仅核对了官方项目说明，**尚未做目标文章的端到端实测，不能保证当前可用**。

## 替代候选

| 场景 | 候选 | 官方说明与限制 |
| --- | --- | --- |
| 批量下载、合集、评论、多格式导出 | [qiye45/wechatDownload](https://github.com/qiye45/wechatDownload) | Windows / macOS 桌面工具。README 称支持历史消息、HTML / MHTML / Markdown / PDF / DOCX / CSV；操作需要目标公众号的一篇文章链接，并在微信内置浏览器打开链接以获取密钥。2026-09-26 未做实际下载验证。其 README 声明仅供学习交流、下载后 24 小时内删除，因此不应直接视为长期归档方案。 |
| 浏览器中保存已打开的单篇文章 | [易微信](https://chromewebstore.google.com/detail/aocfodmfemoeolhgnajngignebdhimja) | Chrome 扩展商店说明称可将已打开文章导出为 Markdown、HTML、PDF，Markdown ZIP 可连图片打包；未验证导出质量与扩展权限，不保证批量发现历史文章。 |
| 已知链接的单篇或多篇 Markdown 归档 | [zyw-Wayne/wechat-article-down](https://github.com/zyw-Wayne/wechat-article-down) | Claude Code Skill，经浏览器打开文章、提取已渲染正文并下载媒体；支持多个已知文章链接，不提供按公众号发现完整历史列表的保证。依赖 Node.js 和 `chrome-devtools` MCP；2026-09-26 未做实际下载验证。 |

## 选型与验证

1. 有已知文章链接时，先用单篇做试验，检查正文、图片、音视频、格式和本地文件是否完整；再考虑批量处理。
2. 需要某个公众号的历史文章时，优先小范围试用 `wechatDownload`，确认文章列表是否能取回；不要仅根据 README 或软件启动成功判断可用。
3. 涉及微信登录、密钥或浏览器会话的工具，先审查来源与权限，不向第三方提交凭据；仅归档有权保存的内容。
4. `wechat-article-exporter` 的[旧版操作教程](https://docs.mptext.top/get-started/usage.html)仍可用于理解界面或导出已缓存数据，但其中的「搜索公众号 → 同步历史文章」流程已被官方停更公告否定。
