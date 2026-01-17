# 论文解读 Skill 云端部署指南

将 `lunwen` skill 迁移到 GitHub Actions 实现云端定时执行。

---

## 技术可行性分析

### ✅ 可行

| 需求 | GitHub Actions 支持情况 |
|------|-------------------------|
| Python 运行环境 | ✅ 原生支持 Python 3.11 |
| Claude Agent SDK | ✅ 可通过 pip 安装，支持自定义 Base URL |
| PDF 文件处理 | ✅ PyPDF2 等库支持 |
| 外部 API 调用 | ✅ 支持 HTTPS 出站请求 |
| 定时触发 | ✅ cron 表达式支持 |
| Secrets 管理 | ✅ 加密存储敏感信息 |
| 文件存储 | ✅ Artifacts + Git 提交 |

---

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions Workflow                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   触发方式:                                                   │
│   ├── 定时 (cron): 每天北京时间 09:00                          │
│   ├── 手动 (workflow_dispatch): 传入 URL 或文件路径            │
│   └── 推送 (push): papers/*.pdf 有新文件时                    │
│                                                              │
│   ┌─────────────┐    ┌──────────────────┐    ┌────────────┐ │
│   │  Download   │ -> │  Claude Agent    │ -> │   Save     │ │
│   │  PDF File   │    │  SDK (yunwu.ai)  │    │   Output   │ │
│   └─────────────┘    └──────────────────┘    └────────────┘ │
│                              │                              │
│                              v                              │
│                    ┌──────────────────┐                     │
│                    │   阿里通义万相    │                     │
│                    │   (图片生成)      │                     │
│                    └──────────────────┘                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 需要配置的 GitHub Secrets

共需要配置 **4 个** Secrets：

### Claude API 配置（通过 yunwu.ai 代理）

| Secret 名称 | 用途 | 值 |
|------------|------|-----|
| `ANTHROPIC_API_KEY` | API 认证密钥 | `sk-GFAAGFNIHon8fFSLYvNZ8q4I1rE4NdkPYc5CNmP0LwTOmmN0` |
| `ANTHROPIC_BASE_URL` | API 端点地址 | `https://yunwu.ai` |
| `ANTHROPIC_MODEL` | 模型名称 | `claude-opus-4-5-20251101` |

### 阿里通义万相配置

| Secret 名称 | 用途 | 值 |
|------------|------|-----|
| `DASHSCOPE_API_KEY` | 通义万相 API 密钥 | `sk-d044f39d8be848e898a81df4c5182444` |

---

## 文件结构

```
paper-reader/
├── .github/
│   └── workflows/
│       └── paper-reader.yml      # GitHub Actions 工作流
├── scripts/
│   └── cloud_paper_reader.py     # 云端执行脚本（Claude Agent SDK + 通义万相）
├── papers/                        # 存放待处理的 PDF 文件
│   └── .gitkeep
├── outputs/                       # 生成的解读文件
│   └── .gitkeep
└── skills/
    └── lunwen/
        └── SKILL.md              # 原始 Skill 定义
```

---

## 一步步配置流程

### 步骤 1: 推送代码到 GitHub

```bash
git add -A
git commit -m "Update: Claude Agent SDK + 通义万相"
git push origin master
```

### 步骤 2: 配置 GitHub Secrets

1. 打开仓库页面: https://github.com/davidliuzhibo/paper-reader
2. 点击 **Settings** (设置)
3. 在左侧菜单选择 **Secrets and variables** → **Actions**
4. 点击 **New repository secret**
5. 依次添加以下 4 个 Secrets:

#### Secret 1: ANTHROPIC_API_KEY

- **Name**: `ANTHROPIC_API_KEY`
- **Secret**: `sk-GFAAGFNIHon8fFSLYvNZ8q4I1rE4NdkPYc5CNmP0LwTOmmN0`

#### Secret 2: ANTHROPIC_BASE_URL

- **Name**: `ANTHROPIC_BASE_URL`
- **Secret**: `https://yunwu.ai`

#### Secret 3: ANTHROPIC_MODEL

- **Name**: `ANTHROPIC_MODEL`
- **Secret**: `claude-opus-4-5-20251101`

#### Secret 4: DASHSCOPE_API_KEY

- **Name**: `DASHSCOPE_API_KEY`
- **Secret**: `sk-d044f39d8be848e898a81df4c5182444`

### 步骤 3: 验证 Workflow

1. 进入仓库的 **Actions** 标签页
2. 找到 "Paper Reader - 论文解读自动化" workflow
3. 点击 **Run workflow** 手动触发测试

---

## 使用方式

### 方式 A: 定时自动执行

Workflow 会在每天北京时间 09:00 自动运行，处理 `papers/` 目录下最新的 PDF 文件。

### 方式 B: 手动触发 (传入 URL)

1. 进入 Actions → Paper Reader
2. 点击 **Run workflow**
3. 在 `paper_url` 输入框填入论文 PDF 的 URL
4. 点击 **Run workflow**

### 方式 C: 手动触发 (仓库内文件)

1. 进入 Actions → Paper Reader
2. 点击 **Run workflow**
3. 在 `paper_path` 输入框填入仓库内的文件路径，如 `papers/example.pdf`
4. 点击 **Run workflow**

### 方式 D: 推送触发

将 PDF 文件推送到 `papers/` 目录，workflow 会自动触发：

```bash
cp ~/Downloads/new-paper.pdf papers/
git add papers/new-paper.pdf
git commit -m "Add new paper for processing"
git push
```

---

## 查看结果

1. **GitHub Actions 日志**: 在 Actions 标签页查看执行日志
2. **Artifacts 下载**: 每次运行会生成可下载的 artifacts
3. **仓库 outputs/ 目录**: 解读文件会自动提交到仓库

---

## 环境变量说明

这些环境变量在 GitHub Actions 运行时自动注入：

| 环境变量 | 来源 | 说明 |
|---------|------|------|
| `ANTHROPIC_API_KEY` | GitHub Secrets | Claude Agent SDK 自动读取此变量进行认证 |
| `ANTHROPIC_BASE_URL` | GitHub Secrets | Claude Agent SDK 自动读取此变量作为 API 端点 |
| `ANTHROPIC_MODEL` | GitHub Secrets | 脚本读取此变量指定模型 |
| `DASHSCOPE_API_KEY` | GitHub Secrets | 通义万相图片生成 API 密钥 |
| `PAPER_PATH` | Workflow 设置 | 待处理的论文文件路径 |

> 💡 **注意**: 这些变量只需要在 GitHub Secrets 中配置，不需要在你的本地电脑上设置。

---

## 故障排除

### 问题: ANTHROPIC_API_KEY 无效

```
[ERROR] ANTHROPIC_API_KEY environment variable is not set
```

**解决**: 检查 Secrets 是否正确配置，名称是否拼写正确。

### 问题: Claude API 返回错误

```
[ERROR] API returned status 401
```

**解决**:
1. 检查 `ANTHROPIC_API_KEY` 是否正确
2. 检查 `ANTHROPIC_BASE_URL` 是否为 `https://yunwu.ai`
3. 确认 yunwu.ai 账户额度是否充足

### 问题: 图片生成失败

```
[WARN] DashScope API returned status 401
```

**解决**: 检查 `DASHSCOPE_API_KEY` 是否正确，或阿里云账户是否有余额。

### 问题: PDF 提取失败

```
[ERROR] PDF extraction failed
```

**解决**: 确认 PDF 文件不是扫描版或加密版。

---

## 成本估算

| 资源 | 免费额度 | 预计消耗 |
|------|----------|----------|
| GitHub Actions | 2000分钟/月 | ~5分钟/次 |
| yunwu.ai Claude API | 按量付费 | 取决于套餐 |
| 阿里通义万相 | 按量付费 | ~2张/篇 |

---

## 参考资料

- [Claude Agent SDK Python](https://github.com/anthropics/claude-agent-sdk-python)
- [阿里通义万相 API 文档](https://help.aliyun.com/zh/model-studio/developer-reference/tongyi-wanxiang-api)
- [GitHub Actions 文档](https://docs.github.com/en/actions)
