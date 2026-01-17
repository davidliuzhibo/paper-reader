#!/usr/bin/env python3
"""
Skills 同步工具
在本地项目和全局 .claude 目录之间同步 skills
"""

import os
import shutil
from pathlib import Path

# 定义路径
LOCAL_SKILLS = Path(r"C:\Private\Trae\CC_20260108\skills")
GLOBAL_SKILLS = Path(r"C:\Users\david\.claude\skills")

def sync_to_global(skill_name=None):
    """将本地 skills 同步到全局目录"""
    if skill_name:
        # 同步特定 skill
        src = LOCAL_SKILLS / skill_name
        dst = GLOBAL_SKILLS / skill_name
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print(f"✓ 已同步 {skill_name} 到全局目录")
        else:
            print(f"✗ 本地不存在 {skill_name}")
    else:
        # 同步所有 skills
        for skill_dir in LOCAL_SKILLS.iterdir():
            if skill_dir.is_dir() and not skill_dir.name.startswith('.'):
                dst = GLOBAL_SKILLS / skill_dir.name
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(skill_dir, dst)
                print(f"✓ 已同步 {skill_dir.name}")

def sync_from_global(skill_name=None):
    """将全局 skills 同步到本地目录"""
    if skill_name:
        # 同步特定 skill
        src = GLOBAL_SKILLS / skill_name
        dst = LOCAL_SKILLS / skill_name
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print(f"✓ 已同步 {skill_name} 到本地目录")
        else:
            print(f"✗ 全局不存在 {skill_name}")
    else:
        # 同步所有 skills
        for skill_dir in GLOBAL_SKILLS.iterdir():
            if skill_dir.is_dir() and not skill_dir.name.startswith('.'):
                dst = LOCAL_SKILLS / skill_dir.name
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(skill_dir, dst)
                print(f"✓ 已同步 {skill_dir.name}")

def list_skills():
    """列出所有 skills"""
    print("\n本地 Skills:")
    print("-" * 50)
    if LOCAL_SKILLS.exists():
        local_skills = [d.name for d in LOCAL_SKILLS.iterdir() if d.is_dir() and not d.name.startswith('.')]
        if local_skills:
            for skill in sorted(local_skills):
                print(f"  - {skill}")
        else:
            print("  (空)")
    else:
        print("  (目录不存在)")

    print("\n全局 Skills:")
    print("-" * 50)
    if GLOBAL_SKILLS.exists():
        global_skills = [d.name for d in GLOBAL_SKILLS.iterdir() if d.is_dir() and not d.name.startswith('.')]
        if global_skills:
            for skill in sorted(global_skills):
                print(f"  - {skill}")
        else:
            print("  (空)")
    else:
        print("  (目录不存在)")
    print()

def create_skill_in_both(skill_name):
    """在本地和全局同时创建新 skill"""
    # 创建本地 skill
    local_path = LOCAL_SKILLS / skill_name
    global_path = GLOBAL_SKILLS / skill_name

    local_path.mkdir(parents=True, exist_ok=True)
    global_path.mkdir(parents=True, exist_ok=True)

    # 创建 SKILL.md 模板
    template = f"""---
name: {skill_name}
description: "描述这个 skill 的功能和使用场景"
---

# {skill_name.replace('-', ' ').title()}

## 概述

这个 skill 的作用是...

## 何时使用

当用户需要：
- 功能1
- 功能2
- 功能3

## 使用说明

### 步骤1
说明...

### 步骤2
说明...

## 示例

```
示例代码或用法
```

## 限制

- 限制1
- 限制2
"""

    # 写入两个位置
    (local_path / "SKILL.md").write_text(template, encoding='utf-8')
    (global_path / "SKILL.md").write_text(template, encoding='utf-8')

    print(f"✓ 已在本地和全局创建 skill: {skill_name}")
    print(f"  本地: {local_path}")
    print(f"  全局: {global_path}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Skills 同步工具")
        print("=" * 50)
        print("\n用法:")
        print("  python sync_skills.py list                    # 列出所有 skills")
        print("  python sync_skills.py to-global [skill]       # 同步到全局")
        print("  python sync_skills.py from-global [skill]     # 从全局同步")
        print("  python sync_skills.py create <skill-name>     # 创建新 skill")
        print("\n示例:")
        print("  python sync_skills.py list")
        print("  python sync_skills.py to-global")
        print("  python sync_skills.py to-global example-skill")
        print("  python sync_skills.py create my-new-skill")
        sys.exit(0)

    command = sys.argv[1]

    if command == "list":
        list_skills()

    elif command == "to-global":
        skill_name = sys.argv[2] if len(sys.argv) > 2 else None
        sync_to_global(skill_name)

    elif command == "from-global":
        skill_name = sys.argv[2] if len(sys.argv) > 2 else None
        sync_from_global(skill_name)

    elif command == "create":
        if len(sys.argv) < 3:
            print("✗ 请提供 skill 名称")
            sys.exit(1)
        skill_name = sys.argv[2]
        create_skill_in_both(skill_name)

    else:
        print(f"✗ 未知命令: {command}")
        sys.exit(1)
