# fenli.py
import re
import os
import argparse
import sys
import glob
import logging
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime
import hashlib
import zipfile
import shutil

class EnhancedNovelSplitter:
    def __init__(self, log_file: Optional[str] = None):
        # 增强章节检测模式
        self.chapter_patterns = [
            # 中文章节格式
            r'^## 第[零一二三四五六七八九十百千两万千亿\d]+章[\s\S]*$',
            r'^第[零一二三四五六七八九十百千两万千亿\d]+章[\s\S]*$',
            r'^## [上下卷]?第[零一二三四五六七八九十百千两万千亿\d]+[章节回][\s\S]*$',
            r'^第[零一二三四五六七八九十百千\d]+[章节回][\s\S]*$',
            r'^[上下卷]第[零一二三四五六七八九十百千\d]+[章节回][\s\S]*$',
            
            # 英文章节格式
            r'^Chapter\s+\d+[\s\S]*$',
            r'^CHAPTER\s+\d+[\s\S]*$',
            r'^##\s+Chapter\s+\d+[\s\S]*$',
            
            # 其他格式
            r'^【第[零一二三四五六七八九十百千\d]+章】[\s\S]*$',
            r'^\[第[零一二三四五六七八九十百千\d]+章\][\s\S]*$',
        ]
        
        # 设置日志
        self.setup_logging(log_file)
        
        # 统计信息
        self.stats = {
            'total_files': 0,
            'successful_splits': 0,
            'total_chapters': 0,
            'failed_files': 0,
            'zip_files_created': 0
        }
    
    def setup_logging(self, log_file: Optional[str] = None):
        """设置日志记录"""
        self.logger = logging.getLogger('NovelSplitter')
        self.logger.setLevel(logging.INFO)
        
        # 清除已有的处理器
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 文件处理器（如果提供了日志文件）
        if log_file:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def detect_encoding(self, file_path: str) -> str:
        """检测文件编码"""
        encodings = ['utf-8', 'gbk', 'gb18030', 'big5', 'utf-16']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    f.read(1024)  # 读取前1024个字符测试
                return encoding
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        self.logger.warning(f"无法检测 {file_path} 的编码，使用utf-8")
        return 'utf-8'
    
    def detect_chapter_pattern(self, lines: List[str]) -> str:
        """检测小说使用的章节模式"""
        pattern_scores: Dict[str, int] = {pattern: 0 for pattern in self.chapter_patterns}
        
        for i, line in enumerate(lines):
            if i > 500:  # 检查前500行
                break
            line = line.strip()
            if not line or len(line) < 2:
                continue
                
            for pattern in self.chapter_patterns:
                if re.match(pattern, line):
                    pattern_scores[pattern] += 1
                    # 记录第一个匹配的模式作为示例
                    if pattern_scores[pattern] == 1:
                        self.logger.info(f"匹配到模式: {pattern} -> {line}")
        
        # 选择得分最高的模式
        if pattern_scores:
            best_pattern = max(pattern_scores.keys(), key=lambda k: pattern_scores[k])
            if pattern_scores[best_pattern] > 0:
                self.logger.info(f"选择模式: {best_pattern} (得分: {pattern_scores[best_pattern]})")
                return best_pattern
        
        # 如果没有匹配到，使用最宽松的模式
        fallback_pattern = r'^第[零一二三四五六七八九十百千\d]+章[\s\S]*$'
        self.logger.warning(f"未找到匹配的章节模式，使用备用模式: {fallback_pattern}")
        return fallback_pattern
    
    def extract_metadata(self, lines: List[str]) -> Dict[str, str]:
        """提取小说元数据（标题、作者等）"""
        metadata: Dict[str, str] = {}
        
        for i, line in enumerate(lines[:50]):  # 检查前50行
            line = line.strip()
            
            # 检测标题
            if not metadata.get('title') and len(line) < 100 and len(line) > 2:
                if any(keyword in line for keyword in ['书名', '标题', '小说', '《']):
                    metadata['title'] = line
                elif i < 10 and not any(char in line for char in ['第', '章', '回']):
                    metadata['title'] = line
            
            # 检测作者
            if not metadata.get('author') and any(keyword in line for keyword in ['作者', '著', '文']):
                metadata['author'] = line
        
        return metadata
    
    def generate_chapter_filename(self, title: str, index: int, metadata: Dict[str, str]) -> str:
        """生成章节文件名"""
        # 清理标题
        clean_title = re.sub(r'^##\s*', '', title)
        clean_title = re.sub(r'[<>:"/\\|?*]', '_', clean_title)
        clean_title = clean_title.replace('\n', ' ').replace('\r', ' ').strip('. ')
        
        if not clean_title.strip():
            clean_title = f"第{index}章"
        
        # 限制文件名长度
        if len(clean_title) > 80:
            clean_title = clean_title[:80]
        
        # 修改：直接使用章节标题作为文件名，去掉序号前缀
        filename = f"{clean_title}.txt"
        
        return filename
    
    def calculate_file_hash(self, content: str) -> str:
        """计算文件内容的哈希值"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def create_zip_archive(self, source_dir: str, zip_filename: str) -> bool:
        """创建ZIP压缩包"""
        try:
            # 确保zip目录存在
            zip_dir = "zip"
            os.makedirs(zip_dir, exist_ok=True)
            
            zip_path = os.path.join(zip_dir, zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(source_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # 在ZIP文件中创建相对路径
                        arcname = os.path.relpath(file_path, os.path.dirname(source_dir))
                        zipf.write(file_path, arcname)
            
            self.logger.info(f"已创建ZIP压缩包: {zip_path}")
            return True
        except Exception as e:
            self.logger.error(f"创建ZIP压缩包失败: {e}")
            return False
    
    def split_novel(self, input_file: str, output_dir: str = "chapters") -> Dict[str, Any]:
        """分割小说文件"""
        self.stats['total_files'] += 1
        
        # 检查文件是否存在
        if not os.path.exists(input_file):
            self.logger.error(f"文件 {input_file} 不存在")
            self.stats['failed_files'] += 1
            return {"total_chapters": 0, "success": False, "error": "文件不存在"}
        
        # 检测编码并读取文件
        encoding = self.detect_encoding(input_file)
        try:
            with open(input_file, 'r', encoding=encoding) as f:
                content = f.read()
        except Exception as e:
            self.logger.error(f"无法读取文件 {input_file}: {e}")
            self.stats['failed_files'] += 1
            return {"total_chapters": 0, "success": False, "error": str(e)}
        
        lines = content.split('\n')
        
        # 提取元数据
        metadata = self.extract_metadata(lines)
        self.logger.info(f"提取的元数据: {metadata}")
        
        # 检测章节模式
        pattern = self.detect_chapter_pattern(lines)
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存元数据
        if metadata:
            with open(os.path.join(output_dir, "metadata.txt"), 'w', encoding='utf-8') as f:
                for key, value in metadata.items():
                    f.write(f"{key}: {value}\n")
        
        # 查找所有章节起始位置
        chapter_starts: List[Tuple[int, str]] = []
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if re.match(pattern, line_stripped):
                if self.is_valid_chapter_title(line_stripped, i, lines):
                    chapter_starts.append((i, line_stripped))
        
        if not chapter_starts:
            self.logger.warning("未找到任何章节，尝试备用模式")
            # 尝试更宽松的匹配
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                if any(keyword in line_stripped for keyword in ['第', '章', 'Chapter', 'CHAPTER']):
                    if self.is_valid_chapter_title(line_stripped, i, lines):
                        chapter_starts.append((i, line_stripped))
        
        if not chapter_starts:
            self.logger.error("未找到任何章节")
            self.stats['failed_files'] += 1
            return {"total_chapters": 0, "success": False, "error": "未找到章节"}
        
        self.logger.info(f"找到 {len(chapter_starts)} 个章节")
        
        # 分割章节
        total_chapters = len(chapter_starts)
        success_count = 0
        chapter_hashes = set()  # 用于去重
        
        for idx, (start_line, title) in enumerate(chapter_starts):
            try:
                # 计算章节结束位置
                end_line = chapter_starts[idx + 1][0] if idx + 1 < total_chapters else len(lines)
                
                # 提取章节内容
                chapter_lines = lines[start_line:end_line]
                chapter_content = '\n'.join(chapter_lines)
                
                # 检查重复内容
                chapter_hash = self.calculate_file_hash(chapter_content)
                if chapter_hash in chapter_hashes:
                    self.logger.warning(f"跳过重复章节: {title}")
                    continue
                chapter_hashes.add(chapter_hash)
                
                # 生成文件名
                filename = self.generate_chapter_filename(title, idx + 1, metadata)
                filepath = os.path.join(output_dir, filename)
                
                # 处理重复文件名
                counter = 1
                original_filepath = filepath
                while os.path.exists(filepath):
                    name, ext = os.path.splitext(original_filepath)
                    filepath = f"{name}_{counter}{ext}"
                    counter += 1
                
                # 写入文件
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(chapter_content)
                
                self.logger.info(f"已保存: {filename}")
                success_count += 1
                
            except Exception as e:
                self.logger.error(f"处理章节 {title} 时出错: {e}")
        
        # 生成统计文件
        stats_content = f"""处理统计:
- 总章节数: {total_chapters}
- 成功分割: {success_count}
- 重复章节: {total_chapters - success_count}
- 处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 原文件: {input_file}
"""
        with open(os.path.join(output_dir, "split_stats.txt"), 'w', encoding='utf-8') as f:
            f.write(stats_content)
        
        # 创建ZIP压缩包
        zip_filename = f"{output_dir}.zip"
        zip_success = self.create_zip_archive(output_dir, zip_filename)
        
        result: Dict[str, Any] = {
            "total_chapters": total_chapters,
            "success_count": success_count,
            "success": success_count > 0,
            "metadata": metadata,
            "zip_created": zip_success,
            "zip_filename": zip_filename if zip_success else None
        }
        
        if success_count > 0:
            self.stats['successful_splits'] += 1
            self.stats['total_chapters'] += success_count
        
        if zip_success:
            self.stats['zip_files_created'] += 1
        
        return result
    
    def is_valid_chapter_title(self, line: str, line_num: int, all_lines: List[str]) -> bool:
        """检查是否是有效的章节标题"""
        if len(line) > 200:
            return False
            
        # 检查是否包含常见章节关键词
        chapter_keywords = ['章', '卷', '回', 'Chapter', 'CHAPTER']
        if not any(keyword in line for keyword in chapter_keywords):
            return False
            
        # 检查上下文，避免误判
        if line_num > 0:
            prev_line = all_lines[line_num - 1].strip()
            if len(prev_line) == 0 and line_num < len(all_lines) - 1:
                next_line = all_lines[line_num + 1].strip()
                if len(next_line) == 0:
                    return True
        
        return True
    
    def batch_process_with_progress(self, file_pattern: str = "*.txt") -> Dict[str, Any]:
        """批量处理文件并显示进度"""
        txt_files = glob.glob(file_pattern)
        
        if not txt_files:
            self.logger.warning("未找到任何txt文件")
            return self.stats
        
        self.logger.info(f"找到 {len(txt_files)} 个txt文件")
        
        for i, file in enumerate(txt_files):
            self.logger.info(f"处理进度: {i+1}/{len(txt_files)} - {file}")
            filename = os.path.splitext(file)[0]
            # 修改：直接使用原文件名作为输出目录，不加前缀
            output_dir = f"{filename}"
            
            result = self.split_novel(file, output_dir)
            
            if result['success']:
                self.logger.info(f"成功分割 {file}，共 {result['success_count']} 个章节")
                if result.get('zip_created'):
                    self.logger.info(f"已创建ZIP文件: {result['zip_filename']}")
                # 移动原文件到already文件夹
                os.makedirs("already", exist_ok=True)
                os.rename(file, os.path.join("already", file))
                self.logger.info(f"已移动 {file} 到 already/ 目录")
            else:
                self.logger.error(f"分割 {file} 失败: {result.get('error', '未知错误')}")
                # 移动失败文件到failed文件夹
                os.makedirs("failed", exist_ok=True)
                os.rename(file, os.path.join("failed", file))
        
        return self.stats

def process_all_novels(log_file: Optional[str] = None):
    """处理所有小说文件的函数，用于手动运行"""
    splitter = EnhancedNovelSplitter(log_file)
    
    stats = splitter.batch_process_with_progress()
    
    print(f"\n=== 批量处理完成 ===")
    print(f"总文件数: {stats['total_files']}")
    print(f"成功分割: {stats['successful_splits']}")
    print(f"失败文件: {stats['failed_files']}")
    print(f"总章节数: {stats['total_chapters']}")
    print(f"ZIP文件数: {stats['zip_files_created']}")
    print(f"===================")

def main():
    parser = argparse.ArgumentParser(description='增强版小说章节分割工具')
    parser.add_argument('input_file', nargs='?', help='输入小说文件路径')
    parser.add_argument('-o', '--output', default='chapters', help='输出目录')
    parser.add_argument('-a', '--auto', action='store_true', help='自动处理所有小说文件')
    parser.add_argument('--log', help='日志文件路径')
    parser.add_argument('--pattern', default='*.txt', help='文件匹配模式')
    
    args = parser.parse_args()
    
    splitter = EnhancedNovelSplitter(args.log)
    
    if args.auto:
        process_all_novels(args.log)
        return
    
    if not args.input_file:
        print("请提供输入文件或使用 -a 参数自动处理所有文件")
        return
    
    result = splitter.split_novel(args.input_file, args.output)
    
    if result['success']:
        print(f"处理完成! 共分割 {result['success_count']} 个章节")
        if result.get('metadata'):
            print(f"提取的元数据: {result['metadata']}")
        if result.get('zip_created'):
            print(f"已创建ZIP文件: {result['zip_filename']}")
    else:
        print(f"处理失败! 错误: {result.get('error', '未知错误')}")

if __name__ == "__main__":
    main()
