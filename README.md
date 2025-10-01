# 小说章节自动分割工具

这是一个用于自动分割小说章节的工具项目，包含 GitHub Actions 工作流和 Python 脚本。当新的小说文本文件被添加到仓库根目录时，系统会自动将其分割成独立的章节文件，并按小说名称组织到各自的文件夹中。

## 🚀 功能特点

- **自动触发**: 当根目录有新的txt文件时自动运行
- **手动触发**: 支持在GitHub Actions页面手动运行
- **智能组织**: 每本小说一个独立的输出文件夹
- **文件管理**: 处理后的原文件自动移动到`already`文件夹
- **智能识别**: 基于正则表达式模式匹配，支持多种中文数字章节格式
- **批量处理**: 支持单文件处理和批量处理模式

## 📁 目录结构

```
├── novel_小说名/     # 每本小说分割后的章节文件夹
├── already/         # 已处理完成的小说原文件
├── .github/
│   ├── scripts/
│   │   └── fenli.py          # 核心分割脚本
│   └── workflows/
│       └── split-novels.yml  # GitHub Actions 工作流配置
└── README.md
```

## 📖 使用方法

### 克隆仓库
点击fork按钮

### 设置环境变量
在 GitHub 仓库中需要设置以下 Secrets：

1. 进入仓库的 **Settings** → **Secrets and variables** → **Actions**
2. 点击 **New repository secret** 添加以下两个 secret：
   - `GIT_EMAIL`：你的邮箱地址（例如：zzk6780051@gmail.com）
   - `GIT_NAME`：你的用户名（例如：zzk6780051）

### 自动处理
当 `.txt` 文件被推送到仓库根目录时，GitHub Actions 会自动运行并处理这些文件。

### 手动处理
1. 前往仓库的 **Actions** 页面
2. 选择 **Split Novel Chapters** 工作流
3. 点击 **Run workflow** 按钮

### 本地运行
```bash
# 处理单个文件
python .github/scripts/fenli.py novel.txt

# 批量处理当前目录所有txt文件
python .github/scripts/fenli.py -a

# 指定输出目录
python .github/scripts/fenli.py novel.txt -o output_directory
```

## 🔧 开发说明

该项目使用 Python 编写，核心逻辑在 `.github/scripts/fenli.py` 文件中。章节识别基于正则表达式模式匹配，支持多种中文数字章节格式。

### 主要类和方法

- `NovelSplitter` 类：负责小说分割逻辑
- `split_novel()` 方法：分割指定小说文件
- `detect_chapter_pattern()` 方法：自动检测章节模式
- `is_valid_chapter_title()` 方法：验证章节标题有效性

### 支持的章节格式

- `第X章 标题`
- `## 第X章 标题`
- `第X回 标题`
- 支持中文数字（一、二、三...）和阿拉伯数字

## 📝 注意事项

- 确保小说文件使用 UTF-8 编码
- 章节标题应包含"章"、"卷"或"回"等关键词
- 处理后的原文件会自动移动到 `already` 文件夹进行归档
- 每本小说的章节会保存在独立的 `小说名` 文件夹中