# Skills 管理指南

## 目录结构

你现在有两个 skills 目录：

1. **全局 Skills** (推荐): `C:\Users\david\.claude\skills\`
   - 在所有项目中可用
   - 适合通用工具和个人工作流

2. **项目本地 Skills**: `C:\Private\Trae\CC_20260108\skills\`
   - 仅在当前项目中可用
   - 适合项目特定功能

## 使用同步工具

### 查看所有 skills
```bash
python sync_skills.py list
```

### 创建新 skill（同时在两个位置创建）
```bash
python sync_skills.py create my-skill-name
```

这会在两个位置创建包含模板的新 skill。

### 同步到全局目录
```bash
# 同步所有 skills
python sync_skills.py to-global

# 同步特定 skill
python sync_skills.py to-global my-skill-name
```

### 从全局目录同步到本地
```bash
# 同步所有 skills
python sync_skills.py from-global

# 同步特定 skill
python sync_skills.py from-global my-skill-name
```

## 创建 Skill 的步骤

### 方法1: 使用同步工具（推荐）
```bash
python sync_skills.py create my-new-skill
```

然后编辑生成的 SKILL.md 文件。

### 方法2: 手动创建
1. 在两个 skills 目录中创建新文件夹
2. 在文件夹中创建 SKILL.md 文件
3. 按照以下结构编写

## SKILL.md 文件结构

```markdown
---
name: skill-name
description: "清晰描述何时使用这个 skill"
---

# Skill 标题

## 概述
简要说明这个 skill 的作用

## 何时使用
- 场景1
- 场景2
- 场景3

## 使用说明
详细的执行步骤

## 示例
具体的使用示例

## 限制
说明不能做什么
```

## 重要提示

1. **name**: 使用小写字母和连字符（如 `pdf-editor`）
2. **description**: 最关键的部分，决定 skill 何时被触发
3. **同步策略**: 在本地创建/修改后，使用 `to-global` 同步到全局

## 工作流程建议

1. 在本地项目中创建和测试新 skill
2. 确认工作正常后，同步到全局目录
3. 这样其他项目也能使用这个 skill
