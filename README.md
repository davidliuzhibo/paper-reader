# 论文解读 Skill 项目 (Paper Reader)

## 项目概述

本项目创建了一个名为 `lunwen` 的 Claude Skill，用于自动读取和解释学术论文。**v3.0 版本已支持 GitHub Actions 云端自动化执行。**

### 核心功能
- 📄 读取 PDF 文件或 URL 链接的学术论文
- 🎯 提取并分析论文核心内容
- ✍️ 用"黄叔风格"生成通俗易懂的中文解读
- 🖼️ 自动生成信息图表（Gemini 3 Pro Image）
- 📝 输出 Markdown + HTML + PDF 三种格式
- ☁️ GitHub Actions 云端定时/手动执行

### 设计理念
- **零打断自动化**：静默执行模式，无需用户确认
- **智能降级**：遇到错误时自动降级处理，确保总能输出结果
- **黄叔风格**：个人化叙事、通俗化表达、故事化结构

---

## 🚀 快速开始（GitHub Actions 云端版）

### 仓库地址
**GitHub**: https://github.com/davidliuzhibo/paper-reader

### 使用方式

#### 方式 1: 手动触发（推荐）
1. 打开 https://github.com/davidliuzhibo/paper-reader/actions
2. 点击 "Paper Reader - 论文解读自动化"
3. 点击 "Run workflow"
4. 输入论文 PDF 的 URL
5. 点击运行，等待 2-3 分钟

#### 方式 2: 定时自动执行
Workflow 每天北京时间 09:00 自动运行，处理 `papers/` 目录下最新的 PDF。

#### 方式 3: 推送触发
```bash
cp ~/Downloads/new-paper.pdf papers/
git add papers/new-paper.pdf
git commit -m "Add new paper"
git push
```

### 输出结果
运行完成后，`outputs/` 目录将包含：
- `paper-explanation-*.md` - Markdown 源文件
- `paper-explanation-*.html` - 精美网页版
- `paper-explanation-*.pdf` - 中文 PDF（含配图）
- `image_*.png` - Gemini 生成的信息图表

---

## 项目结构

```
paper-reader/
├── .github/
│   └── workflows/
│       └── paper-reader.yml      # GitHub Actions 工作流
├── scripts/
│   └── cloud_paper_reader.py     # 云端执行脚本
├── papers/                        # 存放待处理的 PDF 文件
├── outputs/                       # 生成的解读文件
├── skills/
│   └── lunwen/
│       └── SKILL.md              # 原始 Skill 定义
├── FINAL_REPORT.md               # 完整报告
├── GITHUB_ACTIONS_DEPLOYMENT.md  # 部署指南
└── README.md                     # 本文档
```

---

## 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions Workflow                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   触发: 定时 / 手动 / 推送                                    │
│                                                              │
│   PDF解析 ──> Claude API ──> 输出 (MD/HTML/PDF)              │
│      │         (yunwu.ai)                                    │
│      v                                                       │
│   图像生成: Gemini 3 Pro (优先) / 通义万相 (备用)              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## GitHub Secrets 配置（共 9 个）

| 类别 | Secret 名称 | 用途 |
|------|------------|------|
| Claude | `ANTHROPIC_API_KEY` | API 密钥 |
| Claude | `ANTHROPIC_BASE_URL` | yunwu.ai 代理地址 |
| Claude | `ANTHROPIC_MODEL` | 模型名称 |
| Gemini | `GEMINI_API_KEY` | API 密钥 |
| Gemini | `GEMINI_BASE_URL` | yunwu.ai 代理地址 |
| Gemini | `GEMINI_MODEL` | gemini-3-pro-image-preview |
| DashScope | `DASHSCOPE_API_KEY` | 通义万相 API 密钥 |
| DashScope | `DASHSCOPE_BASE_URL` | DashScope API 地址 |
| DashScope | `DASHSCOPE_MODEL` | wanx2.1-t2i-turbo |

---

## 本地使用（斜杠命令）

如果你在本地安装了 Claude Code，也可以使用斜杠命令：

```bash
/lunwen https://arxiv.org/pdf/1706.03762.pdf
```

或自然语言触发：
```
帮我读这篇论文：https://arxiv.org/pdf/2103.14030.pdf
```

---

## 版本历史

### v3.0 (2026-01-17) - GitHub Actions 云端部署
- ✅ 新增：GitHub Actions 自动化工作流
- ✅ 新增：Gemini 3 Pro Image 图像生成
- ✅ 新增：WeasyPrint PDF 中文支持
- ✅ 新增：多服务商智能降级
- ✅ 新增：定时/手动/推送三种触发方式

### v2.0 (2026-01-14) - 多格式输出
- ✅ 新增：HTML 格式输出
- ✅ 新增：PDF 格式输出
- ✅ 新增：阿里通义万相 API 集成

### v1.0 (2026-01-14) - 初始版本
- ✅ Markdown 格式输出
- ✅ "黄叔风格"论文解读

---

## 参考资料

### "黄叔风格"特征
- 个人化叙事（第一人称视角）
- 通俗化表达（避免术语堆砌）
- 故事化结构（场景引入）
- 真实与反思（诚实指出局限）
- 长文深度（3000-5000字）

---

## 许可说明

- 本工具使用的 API 服务遵循各自的服务条款
- 生成的解读内容仅供学习交流使用
- 原论文版权归原作者所有

---

*文档更新时间：2026-01-17*
