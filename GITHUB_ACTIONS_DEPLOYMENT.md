# 论文解读 Skill 云端部署指南

将 `lunwen` skill 迁移到 GitHub Actions 实现云端定时执行。

---

## 技术可行性分析

### ✅ 可行

| 需求 | GitHub Actions 支持情况 |
|------|-------------------------|
| Python 运行环境 | ✅ 原生支持 Python 3.11 |
| Claude Agent SDK | ✅ 可通过 pip 安装 |
| PDF 文件处理 | ✅ PyPDF2 等库支持 |
| 外部 API 调用 | ✅ 支持 HTTPS 出站请求 |
| 定时触发 | ✅ cron 表达式支持 |
| Secrets 管理 | ✅ 加密存储敏感信息 |
| 文件存储 | ✅ Artifacts + Git 提交 |

### ⚠️ 注意事项

1. **运行时限制**: GitHub Actions 免费版每个 job 最长运行 6 小时
2. **并发限制**: 免费账户最多 20 个并发 job
3. **存储限制**: Artifacts 默认保留 90 天
4. **网络限制**: 某些地区可能无法访问特定 API

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
│   │  PDF File   │    │  SDK Processing  │    │   Output   │ │
│   └─────────────┘    └──────────────────┘    └────────────┘ │
│                              │                              │
│                              v                              │
│                    ┌──────────────────┐                     │
│                    │   Yunwu API      │                     │
│                    │   (Image Gen)    │                     │
│                    └──────────────────┘                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 需要配置的 GitHub Secrets

从 `skills/lunwen/SKILL.md` 中提取的敏感信息：

| Secret 名称 | 来源 | 用途 |
|------------|------|------|
| `ANTHROPIC_API_KEY` | [Anthropic Console](https://console.anthropic.com/) | Claude Agent SDK 认证 |
| `YUNWU_API_KEY` | SKILL.md 中的 API Key | 图片生成 API 认证 |

### 当前 SKILL.md 中的 API 信息

```
端点: https://yunwu.ai/v1beta/models/gemini-3-pro-image-preview:generateContent
API密钥: sk-vnGbZHjawACCghqzVzekqy8OPEa42UPnmL2rMKTmAbvZPywV
```

> ⚠️ **安全提醒**: 上述密钥已在 SKILL.md 中公开，建议尽快更换并仅存储在 GitHub Secrets 中。

---

## 文件结构

```
paper-reader/
├── .github/
│   └── workflows/
│       └── paper-reader.yml      # GitHub Actions 工作流
├── scripts/
│   └── cloud_paper_reader.py     # 云端执行脚本
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
# 添加新文件
git add .github/workflows/paper-reader.yml
git add scripts/cloud_paper_reader.py
git add papers/.gitkeep
git add outputs/.gitkeep
git add GITHUB_ACTIONS_DEPLOYMENT.md

# 提交
git commit -m "Add GitHub Actions workflow for paper reader

- Add paper-reader.yml workflow with schedule, manual, and push triggers
- Add cloud_paper_reader.py script using Claude Agent SDK
- Add papers/ and outputs/ directories

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"

# 推送
git push origin master
```

### 步骤 2: 配置 GitHub Secrets

1. 打开仓库页面: https://github.com/davidliuzhibo/paper-reader
2. 点击 **Settings** (设置)
3. 在左侧菜单选择 **Secrets and variables** → **Actions**
4. 点击 **New repository secret**
5. 添加以下 Secrets:

#### Secret 1: ANTHROPIC_API_KEY

- **Name**: `ANTHROPIC_API_KEY`
- **Secret**: 你的 Anthropic API 密钥
- 获取地址: https://console.anthropic.com/settings/keys

#### Secret 2: YUNWU_API_KEY

- **Name**: `YUNWU_API_KEY`
- **Secret**: `sk-vnGbZHjawACCghqzVzekqy8OPEa42UPnmL2rMKTmAbvZPywV`
- 注意: 这是 SKILL.md 中的密钥，建议更换为新密钥

### 步骤 3: 验证 Workflow

1. 进入仓库的 **Actions** 标签页
2. 找到 "Paper Reader - 论文解读自动化" workflow
3. 点击 **Run workflow** 手动触发测试

### 步骤 4: 使用方式

#### 方式 A: 定时自动执行

Workflow 会在每天北京时间 09:00 自动运行，处理 `papers/` 目录下最新的 PDF 文件。

#### 方式 B: 手动触发 (传入 URL)

1. 进入 Actions → Paper Reader
2. 点击 **Run workflow**
3. 在 `paper_url` 输入框填入论文 PDF 的 URL
4. 点击 **Run workflow**

#### 方式 C: 手动触发 (仓库内文件)

1. 进入 Actions → Paper Reader
2. 点击 **Run workflow**
3. 在 `paper_path` 输入框填入仓库内的文件路径，如 `papers/example.pdf`
4. 点击 **Run workflow**

#### 方式 D: 推送触发

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

## 故障排除

### 问题: ANTHROPIC_API_KEY 无效

```
[ERROR] ANTHROPIC_API_KEY environment variable is not set
```

**解决**: 检查 Secrets 是否正确配置，名称是否拼写正确。

### 问题: 图片生成失败

```
[WARN] Image API returned status 401
```

**解决**: 检查 YUNWU_API_KEY 是否正确，或 API 额度是否用尽。

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
| Claude API | 按量付费 | ~$0.05-0.15/篇 |
| Yunwu 图片 API | 取决于套餐 | ~2-3张/篇 |

---

## 参考资料

- [Claude Agent SDK Python](https://github.com/anthropics/claude-agent-sdk-python)
- [Agent SDK 文档](https://docs.anthropic.com/en/docs/claude-code/sdk)
- [GitHub Actions 文档](https://docs.github.com/en/actions)
