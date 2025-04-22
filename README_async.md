# Confluence空间异步导出工具

这是一个使用异步协程技术导出Confluence空间为HTML格式的Python工具。相比于线程池实现，异步协程可以更高效地利用网络IO等待时间，显著提高导出效率。

## 功能特点

- **高效的异步IO处理**：使用Python的`asyncio`和`aiohttp`库，高效处理网络IO等待
- **并发控制**：通过信号量控制最大并发请求数
- **智能重试**：自动重试失败的下载，包含指数退避策略
- **断点续传**：支持下载中断后从断点处继续
- **分批处理**：支持大量空间的分批导出，避免内存溢出
- **连接池优化**：优化TCP连接池，提高网络利用率
- **缓存机制**：避免重复导出相同空间
- **完整的错误处理**：详细记录失败原因，便于排查
- **可配置性**：丰富的配置选项，适应不同场景

## 与线程池版本的比较

| 特性 | 异步协程版本 | 线程池版本 |
|------|------------|----------|
| 资源占用 | 低 | 中-高 |
| 并发效率 | 高 | 中 |
| 适用场景 | 大量IO操作 | 小-中等量任务 |
| 最大并发数 | 可支持更高 | 受线程开销限制 |
| 断点续传 | 支持 | 不支持 |
| 分批处理 | 支持 | 不支持 |
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

# 基本导出选项
output_dir = confluence_export
max_concurrent = 5  # 最大并发请求数
timeout = 300       # 请求超时时间(秒)

# 高级优化参数
chunk_size = 262144  # 下载数据块大小(字节), 256KB
tcp_limit = 100      # TCP连接池大小
batch_size = 0       # 每批处理空间数量, 0表示一次处理所有

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
python export_confluence_html_async.py --spaces SPACE1 SPACE2 SPACE3    #（SPACE是空间的key）
```

### 调整并发数量

```bash
python export_confluence_html_async.py --concurrent 10
```

### 调整超时时间

```bash
python export_confluence_html_async.py --timeout 600
```

### 高级优化

#### 设置批处理大小

对于大量空间，建议使用批处理来避免内存压力：

```bash
python export_confluence_html_async.py --batch-size 10
```

#### 优化下载块大小

较大的块大小通常能提高下载速度，但可能增加内存占用：

```bash
python export_confluence_html_async.py --chunk-size 524288  # 512KB
```

#### 调整TCP连接池

增加连接池大小可能提高并发效率：

```bash
python export_confluence_html_async.py --tcp-limit 150
```

## 完整的命令行参数

```
usage: export_confluence_html_async.py [-h] [--config CONFIG] [--url URL]
                                     [--username USERNAME] [--token TOKEN]
                                     [--output OUTPUT] [--concurrent CONCURRENT]
                                     [--timeout TIMEOUT]
                                     [--spaces SPACES [SPACES ...]] [--all]
                                     [--personal] [--archived] 
                                     [--chunk-size CHUNK_SIZE]
                                     [--tcp-limit TCP_LIMIT]
                                     [--batch-size BATCH_SIZE]
                                     [--debug]

异步导出Confluence空间为HTML格式

基本配置:
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

空间选择:
  --spaces SPACES [SPACES ...], -s SPACES [SPACES ...]
                        要导出的特定空间键列表
  --all, -a             导出所有空间
  --personal, -p        包含个人空间
  --archived            包含归档空间

高级配置:
  --chunk-size CHUNK_SIZE
                        下载数据块大小(字节)
  --tcp-limit TCP_LIMIT
                        TCP连接池大小
  --batch-size BATCH_SIZE
                        每批处理的空间数量

其他:
  --debug               启用调试日志
  -h, --help            显示帮助信息并退出
```

## 调优建议

1. **根据网络情况调整参数**：
   - 对于稳定、高速的网络：增大并发数和块大小
   - 对于不稳定的网络：减小并发数，开启分批处理

2. **不同的空间数量情况**:
   - 少量空间（<10）: 无需批处理，`--max-concurrent 5`
   - 中等数量（10-50）: `--batch-size 10 --max-concurrent 5`
   - 大量空间（>50）: `--batch-size 20 --max-concurrent 3`

3. **内存使用优化**:
   - 增加批处理大小可减少总内存使用
   - 减小块大小可减少单次下载的内存峰值

4. **超时设置**：对于大型空间（>100MB），建议增加超时设置：
   ```bash
   python export_confluence_html_async.py --timeout 600
   ```

5. **断点续传**：工具支持断点续传，如果下载中断，重新运行命令会从断点处继续

## 故障排除

1. **SSL错误**：如果遇到SSL相关错误，可能需要更新Python的SSL证书。

2. **内存使用过高**：
   - 减少并发数量：`--concurrent 3`
   - 开启批处理：`--batch-size 5`
   - 减小块大小：`--chunk-size 131072`

3. **导出失败**：
   - 查看日志文件`confluence_export.log`了解详细错误信息
   - 使用`--debug`选项获取更详细的日志
   - 尝试增加超时时间：`--timeout 600`

4. **导出速度慢**：
   - 增加并发数：`--concurrent 10`
   - 增大块大小：`--chunk-size 524288`
   - 增加TCP连接数：`--tcp-limit 150`

5. **部分空间导出失败**：导出完成后，可以使用`--spaces`参数单独重试失败的空间：
   ```bash
   python export_confluence_html_async.py --spaces FAILED_SPACE1 FAILED_SPACE2
   ``` 