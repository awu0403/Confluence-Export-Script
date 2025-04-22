#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import logging
import argparse
import requests
import configparser
from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from atlassian import Confluence
from urllib3.exceptions import InsecureRequestWarning

# 禁用不安全请求警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# 配置日志
def setup_logger(log_level=logging.INFO):
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('confluence_export.log', encoding='utf-8')
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logger()

class ConfluenceExporter:
    def __init__(self, url, username, api_token, output_dir=None, max_workers=2, timeout=(30, 1800)):
        """
        初始化Confluence导出器
        
        参数:
            url: Confluence实例URL
            username: 用户名
            api_token: API令牌
            output_dir: 输出目录，默认为当前目录下的confluence_export文件夹
            max_workers: 最大并行工作线程数
            timeout: 请求超时设置，(连接超时, 读取超时)
        """
        self.url = url
        self.username = username
        self.api_token = api_token
        self.output_dir = Path(output_dir) if output_dir else Path('confluence_export')
        self.max_workers = max_workers
        self.timeout = timeout
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化Confluence客户端
        self.confluence = Confluence(
            url=self.url,
            username=self.username,
            password=self.api_token,
            verify_ssl=False
        )
        
        # 缓存文件
        self.cache_file = self.output_dir / 'export_cache.json'
        self.export_cache = self._load_cache()
    
    def _load_cache(self):
        """加载缓存数据"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"无法加载缓存文件: {e}")
        return {}
    
    def _save_cache(self):
        """保存缓存数据"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.export_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"无法保存缓存文件: {e}")
    
    def export_space(self, space):
        """
        导出单个空间
        
        参数:
            space: 空间信息字典
        
        返回:
            (成功标志, 空间键, 导出文件路径)
        """
        space_key = space['key']
        space_name = space.get('name', space_key)
        
        # 检查缓存
        cache_key = f"{space_key}_{int(time.time() / (3600 * 24))}"  # 使用空间键和当天日期作为缓存键
        if cache_key in self.export_cache:
            logger.info(f"从缓存中获取空间: {space_name} ({space_key})")
            return True, space_key, self.export_cache[cache_key]
        
        logger.info(f"开始导出空间: {space_name} ({space_key})")
        
        try:
            # 获取导出URL
            export_url = self.confluence.get_space_export(space_key, 'html')
            
            if not export_url:
                logger.error(f"无法获取空间 {space_name} ({space_key}) 的导出URL")
                return False, space_key, None
            
            # 准备输出文件路径
            safe_name = "".join([c if c.isalnum() or c in "._- " else "_" for c in space_name])
            output_file = self.output_dir / f"{space_key}_{safe_name}.html.zip"
            response = requests.get(export_url, timeout=(10, 300))
            # 下载导出文件
            with open(output_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # 更新缓存
            self.export_cache[cache_key] = str(output_file)
            self._save_cache()
            
            logger.info(f"成功导出空间: {space_name} ({space_key}) 到 {output_file}")
            return True, space_key, str(output_file)
                    
        except Exception as e:
            logger.error(f"导出空间 {space_name} ({space_key}) 失败: {str(e)}")
            return False, space_key, None
    
    def export_all_spaces(self, include_personal=False, include_archived=False, specific_spaces=None):
        """
        导出所有空间或指定空间
        
        参数:
            include_personal: 是否包含个人空间
            include_archived: 是否包含归档空间
            specific_spaces: 指定要导出的空间键列表
        
        返回:
            (成功导出数量, 失败空间列表)
        """
        # 获取所有空间
        all_spaces = []
        start = 0
        limit = 50
        
        while True:
            response = self.confluence.get_all_spaces(start=start, limit=limit, expand='description.plain')
            
            if not response or 'results' not in response:
                break
                
            spaces = response['results']
            if not spaces:
                break
                
            all_spaces.extend(spaces)
            
            if len(spaces) < limit:
                break
                
            start += limit
        
        total_spaces = len(all_spaces)
        logger.info(f"找到 {total_spaces} 个空间")
        
        # 过滤空间
        spaces_to_export = []
        
        if specific_spaces:
            # 只导出指定的空间
            specific_keys = set(specific_spaces)
            spaces_to_export = [s for s in all_spaces if s['key'] in specific_keys]
            logger.info(f"将导出 {len(spaces_to_export)}/{len(specific_keys)} 个指定空间")
        else:
            # 根据条件过滤
            for space in all_spaces:
                # 检查是否是个人空间
                is_personal = space['type'].lower() == 'personal'
                if is_personal and not include_personal:
                    continue
                    
                # 检查是否是归档空间
                is_archived = space.get('status', '').lower() == 'archived'
                if is_archived and not include_archived:
                    continue
                    
                spaces_to_export.append(space)
            
            logger.info(f"将导出 {len(spaces_to_export)}/{total_spaces} 个空间")
        
        if not spaces_to_export:
            logger.warning("没有找到要导出的空间")
            return 0, []
        
        # 使用线程池并行导出
        successful_exports = 0
        failed_spaces = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有导出任务
            future_to_space = {
                executor.submit(self.export_space, space): space
                for space in spaces_to_export
            }
            
            # 处理结果
            for future in tqdm(as_completed(future_to_space), total=len(future_to_space), desc="导出进度"):
                space = future_to_space[future]
                try:
                    success, space_key, file_path = future.result()
                    if success:
                        successful_exports += 1
                    else:
                        failed_spaces.append(space_key)
                except Exception as e:
                    logger.error(f"导出空间 {space['key']} 时发生异常: {str(e)}")
                    failed_spaces.append(space['key'])
        
        # 报告结果
        logger.info(f"导出完成! 成功: {successful_exports}, 失败: {len(failed_spaces)}")
        if failed_spaces:
            logger.error(f"导出失败的空间: {', '.join(failed_spaces)}")
        
        return successful_exports, failed_spaces

def load_config(config_file='config.ini'):
    """加载配置文件"""
    config = configparser.ConfigParser()
    
    # 默认配置
    config['DEFAULT'] = {
        'confluence_url': 'https://your-instance.atlassian.net',
        'username': 'your-email@example.com',
        'api_token': 'your-api-token',
        'output_dir': 'confluence_export',
        'max_workers': '2',
        'include_personal': 'false',
        'include_archived': 'false'
    }
    
    # 读取配置文件
    if os.path.exists(config_file):
        config.read(config_file)
    else:
        # 创建示例配置文件
        with open(config_file, 'w') as f:
            config.write(f)
        logger.info(f"已创建配置文件模板: {config_file}")
    
    return config

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='导出Confluence空间为HTML格式')
    
    parser.add_argument('--config', '-c', default='config.ini',
                        help='配置文件路径 (默认: config.ini)')
    
    parser.add_argument('--url', help='Confluence实例URL')
    parser.add_argument('--username', '-u', help='Confluence用户名/邮箱')
    parser.add_argument('--token', '-t', help='Confluence API令牌')
    
    parser.add_argument('--output', '-o', help='输出目录')
    parser.add_argument('--workers', '-w', type=int, help='最大并行工作线程数')
    
    parser.add_argument('--spaces', '-s', nargs='+', help='要导出的特定空间键列表')
    parser.add_argument('--all', '-a', action='store_true', help='导出所有空间')
    parser.add_argument('--personal', '-p', action='store_true', help='包含个人空间')
    parser.add_argument('--archived', action='store_true', help='包含归档空间')
    
    parser.add_argument('--debug', action='store_true', help='启用调试日志')
    
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_arguments()
    
    # 设置日志级别
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    # 加载配置
    config = load_config(args.config)
    
    # 优先使用命令行参数，其次使用配置文件
    confluence_url = args.url or config['DEFAULT']['confluence_url']
    username = args.username or config['DEFAULT']['username']
    api_token = args.token or config['DEFAULT']['api_token']
    output_dir = args.output or config['DEFAULT']['output_dir']
    max_workers = args.workers or int(config['DEFAULT']['max_workers'])
    
    include_personal = args.personal or config['DEFAULT'].getboolean('include_personal')
    include_archived = args.archived or config['DEFAULT'].getboolean('include_archived')
    
    # 检查必要参数
    if confluence_url == 'https://your-instance.atlassian.net' or username == 'your-email@example.com' or api_token == 'your-api-token':
        logger.error("请在配置文件或命令行中提供有效的Confluence URL、用户名和API令牌")
        return 1
    
    # 创建导出器
    exporter = ConfluenceExporter(
        url=confluence_url,
        username=username,
        api_token=api_token,
        output_dir=output_dir,
        max_workers=max_workers
    )
    
    # 导出空间
    if args.spaces:
        logger.info(f"将导出指定的 {len(args.spaces)} 个空间")
        successful, failed = exporter.export_all_spaces(specific_spaces=args.spaces)
    else:
        logger.info(f"将导出所有空间 (个人空间: {'包含' if include_personal else '排除'}, 归档空间: {'包含' if include_archived else '排除'})")
        successful, failed = exporter.export_all_spaces(
            include_personal=include_personal,
            include_archived=include_archived
        )
    
    return 0 if not failed else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.info("用户中断，退出程序")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"程序执行时发生错误: {e}")
        sys.exit(1)