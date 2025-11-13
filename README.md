# 💰 个人记账本 - Ledger

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)](https://pypi.org/project/PyQt5/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/your-username/ledger.svg)](https://github.com/cioutn/CannotRun-Ledger)

> 🚀 现代化个人财务管理工具，基于 PyQt5 + Fluent Design，支持 AI 智能录入和可视化分析

## ✨ 项目特色

### 🎨 现代化界面
- **Fluent Design**: 采用微软 Fluent Design 设计语言，界面美观现代
- **响应式布局**: 支持高 DPI 显示，适配不同屏幕尺寸
- **深色/浅色主题**: 自动适配系统主题，提供舒适的视觉体验

### 🤖 AI 智能功能
- **自然语言录入**: 支持中文自然语言指令，如"今天中午吃饭花了36.5元，标签餐饮"
- **智能标签**: 自动为交易添加合适标签，支持规则引擎 + LLM 增强
- **批量操作**: 一条指令即可添加/修改/删除多笔交易

### 📊 数据可视化
- **实时统计**: 收入/支出/余额统计卡片
- **图表分析**: 柱状图和饼图展示月度/标签统计
- **CSV 导出**: 一键导出分析数据

### 🔧 技术栈
- **UI 框架**: PyQt5 + PyQt-Fluent-Widgets + PyQtChart
- **AI 支持**: OpenAI 兼容接口，支持多种模型
- **数据存储**: JSON 文件存储，支持扩展到数据库
- **配置管理**: 环境变量配置，灵活部署

## 🚀 快速开始

### 📋 系统要求

- **Python**: 3.10 或更高版本
- **操作系统**: Windows 10+ / macOS 10.15+ / Linux
- **内存**: 至少 512MB RAM
- **存储**: 至少 100MB 可用空间

### 🛠️ 环境配置

#### 1. 克隆项目
```bash
git clone https://github.com/your-username/ledger.git
cd ledger
```

#### 2. 创建 Python 环境（推荐）
```bash
# 使用 conda
conda create -n ledger python=3.12 -y
conda activate ledger

# 或使用 venv
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

#### 3. 安装依赖
```bash
pip install -r requirements.txt
```

**依赖说明**:
- `PyQt5`: GUI 框架核心
- `PyQt-Fluent-Widgets`: 现代化 UI 组件库
- `PyQtChart`: 图表可视化
- `python-dotenv`: 环境变量管理
- `openai`: AI 功能支持（可选）

### ⚙️ 配置说明

#### 环境变量配置

复制 `.env.example` 到 `.env` 并根据需要修改：

```bash
cp .env.example .env
```

**核心配置项**:

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `DATABASE_PATH` | `ledger/data/transactions.json` | 交易数据存储路径 |
| `AI_ENABLED` | `false` | 是否启用 AI 功能 |
| `AI_AUTO_TAG` | `true` | 是否启用自动标签 |
| `AI_AUTO_TAG_WITH_LLM` | `false` | 是否使用 LLM 增强标签 |
| `OPENAI_BASE_URL` | 空 | OpenAI 兼容 API 地址 |
| `OPENAI_API_KEY` | 空 | API 密钥 |
| `OPENAI_MODEL` | 空 | 使用的模型名称 |

#### AI 配置示例

```bash
# 启用 AI 功能
AI_ENABLED=true
AI_AUTO_TAG=true
AI_AUTO_TAG_WITH_LLM=false

# OpenAI 兼容配置（例如使用 DeepSeek 或其他服务）
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=deepseek-chat
```

### 🎯 启动应用

#### 方法一：模块启动（推荐）
```bash
python -m ledger
```

#### 方法二：直接运行
```bash
python ledger/app.py
```

#### 方法三：使用主脚本
```bash
python ledger/main.py
```

启动后将显示现代化界面，包含仪表盘和统计分析两个主要页面。

## 🏗️ 项目架构

```
ledger/
├── app.py                 # 主应用入口，日志配置，窗口初始化
├── main.py                # 传统启动脚本
├── __main__.py            # 模块启动支持
├── config/
│   └── settings.py        # 配置管理，环境变量加载
├── models/
│   └── transaction.py     # 交易数据模型
├── services/
│   ├── transaction_service.py    # 交易 CRUD 服务
│   ├── analytics_service.py      # 数据分析服务
│   ├── ai_service.py              # AI 指令解析服务
│   └── tagging_service.py         # 自动标签服务
├── ui/
│   ├── main_window.py     # 主窗口，导航管理
│   ├── dialogs.py         # 对话框组件
│   ├── analytics_view.py  # 统计分析界面
│   ├── ai_dialog.py       # AI 录入对话框
│   └── theme.py           # UI 主题配置
└── utils/                 # 工具函数（预留）
```

### 核心组件说明

- **服务层 (Services)**: 业务逻辑封装，数据持久化，AI 处理
- **UI 层**: 基于 PyQt5 的现代化界面，Fluent Design 风格
- **配置层**: 环境变量驱动的配置管理，支持灵活部署
- **模型层**: 数据结构定义，支持 JSON 序列化

## 📖 使用指南

### 基本操作

1. **添加交易**: 点击"添加交易"按钮，填写金额、类型、日期、描述
2. **编辑交易**: 在表格中点击"编辑"按钮修改现有交易
3. **删除交易**: 点击"删除"按钮确认删除
4. **搜索筛选**: 使用搜索框和筛选条件快速找到交易

### AI 智能录入

在主界面点击"AI记账"按钮，输入自然语言指令：

```
今天中午吃饭花了36.5元，标签餐饮；把昨天的星巴克支出改为45元；删除上周三的兼职收入
```

系统将自动解析并执行相应操作。

### 统计分析

切换到"统计分析"页面查看：
- 月度收入支出趋势图
- 标签分类饼图
- 汇总统计数据
- CSV 数据导出

## 🔧 高级配置

### 自定义主题

修改 `ledger/ui/theme.py` 中的颜色常量来自定义界面主题。

### 数据迁移

项目支持从 JSON 格式迁移到其他存储方式，只需修改 `config/settings.py` 中的 `DATA_FORMAT`。

### 日志配置

通过环境变量控制日志级别和输出位置：

```bash
LOG_LEVEL=DEBUG
LOG_FILE=ledger/logs/app.log
```

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发环境设置

1. Fork 本项目
2. 创建特性分支: `git checkout -b feature/amazing-feature`
3. 提交更改: `git commit -m 'Add amazing feature'`
4. 推送分支: `git push origin feature/amazing-feature`
5. 创建 Pull Request

### 代码规范

- 使用 `pylint` 检查代码质量
- 遵循 PEP 8 编码规范
- 为新功能添加单元测试

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [PyQt5](https://pypi.org/project/PyQt5/) - 强大的 GUI 框架
- [PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets) - 现代化 UI 组件
- [OpenAI](https://openai.com/) - AI 能力支持

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给它一个星标！**

[🐛 报告问题](https://github.com/cioutn/CannotRun-Ledger/issues) • [💡 功能请求](https://github.com/cioutn/CannotRun-Ledger/issues) • [🔀 提交PR](https://github.com/cioutn/CannotRun-Ledger/pulls)

</div>
