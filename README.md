# 校园活动管理系统 V1.0

课程：软件工程 实验一 —— 基于工程意图的软件迭代开发

为校园活动的组织与学生参与提供信息化支持。V1.0 聚焦一个能成立的最小业务闭环：
教师发布活动 → 学生浏览并报名 → 教师管理报名名单。

## 技术栈

- 后端：Python + Flask
- 数据库：SQLite（零配置，随仓库提供 `schema.sql` 描述结构）
- 前端：Jinja2 模板 + 原生 CSS
- 版本管理：Git

## 目录结构

```
campus-activity-system/
├── docs/               # 工程文档：需求、工程意图、设计、验证
├── app/                # 应用源码
├── tests/              # 验证用例
├── schema.sql          # 数据库结构定义
├── requirements.txt    # 依赖清单
└── .gitignore
```

## 运行

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python run.py
```

## 开发流程

本仓库按实验要求记录软件逐步形成的过程，提交顺序遵循：

需求分析 → 工程意图 → 软件设计 → 分模块实现 → 软件验证

各阶段产物放在 `docs/`，实现代码放在 `app/`，验证用例放在 `tests/`。
每次提交信息说明本次修改内容，并在需要时注明对应的需求编号（如 REQ-03）。
