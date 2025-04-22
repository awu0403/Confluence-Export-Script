# Confluence空间导出工具

这是一个用于批量导出Confluence空间为HTML格式的Python工具。它支持导出指定空间或按条件过滤的所有空间，并提供进度显示和缓存功能，提高导出效率。

## 功能特点

- 支持导出为HTML格式（ZIP压缩包）
- 支持导出指定空间或所有空间
- 可过滤个人空间和归档空间
- 单线程或多线程导出，支持可配置的导出间隔
- 缓存机制避免重复导出
- 完整的进度显示和日志记录
- 支持配置文件和命令行参数
- 错误处理和重试机制

## 注意事项

**关于多线程导出**：多线程导出可能会因为Confluence API限制导致部分导出失败。如果遇到导出失败的情况，建议：

1. 使用单线程模式导出 (`max_workers = 1`)
2. 增加导出间隔时间 (`export_interval = 3` 或更高)
3. 使用较低的并发数 (`max_workers = 2`)

单线程模式虽然速度较慢，但可以确保更高的成功率。

## 安装

1. 克隆或下载此仓库
2. 安装依赖包：

```bash
pip install -r requirements.txt
```

## 配置

你可以通过两种方式配置工具：

### 1. 配置文件（推荐）

编辑`config.ini`文件：

```ini
[DEFAULT]
# Confluence服务器URL
confluence_url = https://your-instance.atlassian.net

# 用户认证信息
username = your-email@example.com
api_token = your-api-token

# 导出选项
output_dir = confluence_export
max_workers = 1
export_interval = 3

# 空间过滤选项
include_personal = false
include_archived = false
```

### 2. 命令行参数

```bash
python export_confluence_html.py --url https://your-instance.atlassian.net --username your-email@example.com --token your-api-token
```

## 使用方法

### 导出所有空间（排除个人空间和归档空间）

```bash
python export_confluence_html.py
```

### 导出指定空间

```bash
python export_confluence_html.py --spaces SPACE1 SPACE2 SPACE3
```

### 导出所有空间，包括个人空间

```bash
python export_confluence_html.py --personal
```

### 单线程模式（推荐用于稳定性）

```bash
python export_confluence_html.py --workers 1
```

### 多线程模式（设置导出间隔）

```bash
python export_confluence_html.py --workers 2 --interval 5
```

### 导出到自定义目录

```bash
python export_confluence_html.py --output /path/to/output/dir
```

## 完整的命令行参数

```
usage: export_confluence_html.py [-h] [--config CONFIG] [--url URL]
                               [--username USERNAME] [--token TOKEN]
                               [--output OUTPUT] [--workers WORKERS]
                               [--interval INTERVAL]
                               [--spaces SPACES [SPACES ...]] [--all]
                               [--personal] [--archived] [--debug]

导出Confluence空间为HTML格式

optional arguments:
  -h, --help            显示帮助信息并退出
  --config CONFIG, -c CONFIG
                        配置文件路径 (默认: config.ini)
  --url URL             Confluence实例URL
  --username USERNAME, -u USERNAME
                        Confluence用户名/邮箱
  --token TOKEN, -t TOKEN
                        Confluence API令牌
  --output OUTPUT, -o OUTPUT
                        输出目录
  --workers WORKERS, -w WORKERS
                        最大并行工作线程数
  --interval INTERVAL, -i INTERVAL
                        导出间隔时间(秒)
  --spaces SPACES [SPACES ...], -s SPACES [SPACES ...]
                        要导出的特定空间键列表
  --all, -a             导出所有空间
  --personal, -p        包含个人空间
  --archived            包含归档空间
  --debug               启用调试日志
```

## 获取Confluence API令牌

1. 登录到 Atlassian 账户: https://id.atlassian.com/manage-profile/security/api-tokens
2. 点击"创建API令牌"
3. 为令牌输入一个标签(例如"Confluence导出")，然后点击"创建"
4. 复制生成的令牌并将其保存在安全的地方
5. 在配置文件或命令行中使用此令牌

## 高级使用技巧

### 重试失败的空间导出

如果某些空间导出失败，你可以使用`--spaces`参数单独导出它们：

```bash
python export_confluence_html.py --spaces FAILED_SPACE1 FAILED_SPACE2
```

### 对于大型空间的建议

- 对于非常大的空间，增加超时设置
- 确保有足够的磁盘空间来存储导出的文件
- 使用单线程模式导出，避免资源竞争