# Confluence空间异步导出工具

这是一个使用异步协程技术导出Confluence空间为HTML格式的Python工具。相比于线程池实现，异步协程可以更高效地利用网络IO等待时间，显著提高导出效率。

## 功能特点

- **高效的异步IO处理**：使用Python的`asyncio`和`aiohttp`库，高效处理网络IO等待
- **并发控制**：通过信号量控制最大并发请求数
- **智能重试**：自动重试失败的下载，包含指数退避策略
- **下载进度反馈**：实时显示总体进度和单个下载进度
- **缓存机制**：避免重复导出相同空间
- **完整的错误处理**：详细记录失败原因，便于排查
- **可配置性**：支持配置文件和命令行参数

## 与线程池版本的比较

| 特性 | 异步协程版本 | 线程池版本 |
|------|------------|----------|
| 资源占用 | 低 | 中-高 |
| 并发效率 | 高 | 中 |
| 适用场景 | 大量IO操作 | 小-中等量任务 |
| 最大并发数 | 可支持更高 | 受线程开销限制 |
| 代码复杂度 | 较高 | 中等 |

## 安装依赖

比普通版本多需要安装`aiohttp`库：

```bash
pip install aiohttp asyncio tqdm atlassian-python-api
```

## 配置

你可以通过两种方式配置工具：

### 1. 配置文件（推荐）

编辑`config_async.ini`文件：

```ini
[DEFAULT]
# Confluence服务器URL
confluence_url = https://your-instance.atlassian.net

# 用户认证信息
username = your-email@example.com
api_token = your-api-token

# 导出选项
output_dir = confluence_export
max_concurrent = 5
timeout = 300

# 空间过滤选项
include_personal = false
include_archived = false
```

### 2. 命令行参数

```bash
python export_confluence_html_async.py --url https://your-instance.atlassian.net --username your-email@example.com --token your-api-token
```

## 使用方法

### 导出所有空间

```bash
python export_confluence_html_async.py --config config_async.ini
```

### 导出指定空间

```bash
python export_confluence_html_async.py --spaces SPACE1 SPACE2 SPACE3
```

### 调整并发数量

```bash
python export_confluence_html_async.py --concurrent 10
```

### 调整超时时间

```bash
python export_confluence_html_async.py --timeout 600
```

## 完整的命令行参数

```
usage: export_confluence_html_async.py [-h] [--config CONFIG] [--url URL]
                                     [--username USERNAME] [--token TOKEN]
                                     [--output OUTPUT] [--concurrent CONCURRENT]
                                     [--timeout TIMEOUT]
                                     [--spaces SPACES [SPACES ...]] [--all]
                                     [--personal] [--archived] [--debug]

异步导出Confluence空间为HTML格式

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
  --concurrent CONCURRENT, -n CONCURRENT
                        最大并发请求数
  --timeout TIMEOUT     请求超时时间(秒)
  --spaces SPACES [SPACES ...], -s SPACES [SPACES ...]
                        要导出的特定空间键列表
  --all, -a             导出所有空间
  --personal, -p        包含个人空间
  --archived            包含归档空间
  --debug               启用调试日志
```

## 调优建议

1. **调整并发数**：默认的并发数是5，可以根据网络条件和API限制调整。增加并发数可以提高总体导出速度，但过高可能触发API限制。
   
2. **超时设置**：默认超时为300秒。对于大型空间，可能需要增加此值：
   ```bash
   python export_confluence_html_async.py --timeout 600
   ```

3. **分批导出**：对于大量空间，可以考虑分批导出，以避免长时间运行导致的问题：
   ```bash
   python export_confluence_html_async.py --spaces SPACE1 SPACE2 SPACE3
   python export_confluence_html_async.py --spaces SPACE4 SPACE5 SPACE6
   ```

## 故障排除

1. **SSL错误**：如果遇到SSL相关错误，可能需要更新Python的SSL证书或使用`--no-verify-ssl`选项（未实现，需要修改代码）。

2. **内存使用过高**：减少并发数量。异步操作虽然比线程轻量，但大量并发下载仍会消耗大量内存。

3. **导出失败**：查看日志文件`confluence_export.log`了解详细错误信息。使用`--debug`选项获取更详细的日志。

4. **导出的文件不完整**：脚本会自动验证下载完整性，如果发现不完整会重试。如果仍然失败，可以尝试增加超时时间。 