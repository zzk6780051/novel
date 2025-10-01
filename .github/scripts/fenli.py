import re
import os
import argparse
import sys
from typing import List, Tuple
import glob

class NovelSplitter:
    def __init__(self):
        # 增强章节检测模式
        self.chapter_patterns = [
            r'^## 第[零一二三四五六七八九十百千两万千亿\d]+章[\s\S]*$',
            r'^第[零一二三四五六七八九十百千两万千亿\d]+章[\s\S]*$',
            r'^## [上下卷]?第[零一二三四五六七八九十百千两万千亿\d]+[章节回][\s\S]*$',
        ]
        
    def detect_chapter_pattern(self, lines: List[str]) -> str:
        """检测小说使用的章节模式"""
        for i, line in enumerate(lines):
            if i > 300:  # 增加检查行数
                break
            line = line.strip()
            if not line or len(line) < 2:
                continue
                
            for pattern in self.chapter_patterns:
                if re.match(pattern, line):
                    print(f"匹配到模式: {pattern} -> {line}")
                    return pattern
        
        # 如果没有匹配到，使用最宽松的模式
        return r'^第[零一二三四五六七八九十百千\d]+章[\s\S]*$'
    
    def split_novel(self, input_file: str, output_dir: str = "chapters") -> dict:
        """分割小说文件"""
        # 检查文件是否存在
        if not os.path.exists(input_file):
            print(f"错误: 文件 {input_file} 不存在")
            return {"total_chapters": 0, "success": False}
        
        # 读取文件
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(input_file, 'r', encoding='gbk') as f:
                    content = f.read()
            except:
                try:
                    with open(input_file, 'r', encoding='gb18030') as f:
                        content = f.read()
                except Exception as e:
                    print(f"无法读取文件 {input_file}: {e}")
                    return {"total_chapters": 0, "success": False}
        
        lines = content.split('\n')
        
        # 检测章节模式
        pattern = self.detect_chapter_pattern(lines)
        print(f"使用的章节模式: {pattern}")
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 查找所有章节起始位置
        chapter_starts = []
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if re.match(pattern, line_stripped):
                if self.is_valid_chapter_title(line_stripped, i, lines):
                    chapter_starts.append((i, line_stripped))
        
        if not chapter_starts:
            print("警告: 未找到任何章节，尝试备用模式")
            # 尝试更宽松的匹配
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                if '第' in line_stripped and '章' in line_stripped:
                    if self.is_valid_chapter_title(line_stripped, i, lines):
                        chapter_starts.append((i, line_stripped))
        
        if not chapter_starts:
            print("错误: 未找到任何章节")
            return {"total_chapters": 0, "success": False}
        
        print(f"找到 {len(chapter_starts)} 个章节")
        
        # 分割章节
        total_chapters = len(chapter_starts)
        success_count = 0
        
        for idx, (start_line, title) in enumerate(chapter_starts):
            try:
                # 计算章节结束位置
                end_line = chapter_starts[idx + 1][0] if idx + 1 < total_chapters else len(lines)
                
                # 提取章节内容
                chapter_lines = lines[start_line:end_line]
                chapter_content = '\n'.join(chapter_lines)
                
                # 生成文件名
                clean_title = re.sub(r'^##\s*', '', title)
                safe_title = self.sanitize_filename(clean_title)
                if len(safe_title) > 100:
                    safe_title = safe_title[:100]
                
                if not safe_title.strip():
                    safe_title = f"第{idx+1}章"
                
                filename = f"{safe_title}.txt"
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
                
                print(f"已保存: {filename}")
                success_count += 1
                
            except Exception as e:
                print(f"处理章节 {title} 时出错: {e}")
        
        return {
            "total_chapters": total_chapters,
            "success_count": success_count,
            "success": success_count > 0
        }
    
    def is_valid_chapter_title(self, line: str, line_num: int, all_lines: List[str]) -> bool:
        """检查是否是有效的章节标题"""
        if len(line) > 200:
            return False
            
        # 检查是否包含常见章节关键词
        chapter_keywords = ['章', '卷', '回']
        if not any(keyword in line for keyword in chapter_keywords):
            return False
            
        return True
    
    def sanitize_filename(self, filename: str) -> str:
        """清理文件名中的非法字符"""
        illegal_chars = r'[<>:"/\\|?*]'
        filename = re.sub(illegal_chars, '_', filename)
        filename = filename.replace('\n', ' ').replace('\r', ' ')
        filename = filename.strip('. ')
        
        if not filename:
            filename = "未知章节"
            
        return filename

def process_all_novels():
    """处理所有小说文件的函数，用于手动运行"""
    splitter = NovelSplitter()
    
    # 查找所有txt文件
    txt_files = glob.glob("*.txt")
    
    if not txt_files:
        print("未找到任何txt文件")
        return
    
    print(f"找到 {len(txt_files)} 个txt文件")
    
    for file in txt_files:
        print(f"\n处理文件: {file}")
        filename = os.path.splitext(file)[0]
        output_dir = f"novel_{filename}"
        
        result = splitter.split_novel(file, output_dir)
        
        if result['success']:
            print(f"成功分割 {file}，共 {result['success_count']} 个章节")
            # 移动原文件到already文件夹
            os.makedirs("already", exist_ok=True)
            os.rename(file, os.path.join("already", file))
            print(f"已移动 {file} 到 already/ 目录")
        else:
            print(f"分割 {file} 失败")

def main():
    parser = argparse.ArgumentParser(description='小说章节分割工具')
    parser.add_argument('input_file', nargs='?', help='输入小说文件路径')
    parser.add_argument('-o', '--output', default='chapters', help='输出目录')
    parser.add_argument('-a', '--auto', action='store_true', help='自动处理所有小说文件')
    
    args = parser.parse_args()
    
    splitter = NovelSplitter()
    
    if args.auto:
        process_all_novels()
        return
    
    if not args.input_file:
        print("请提供输入文件或使用 -a 参数自动处理所有文件")
        return
    
    result = splitter.split_novel(args.input_file, args.output)
    
    if result['success']:
        print(f"处理完成! 共分割 {result['success_count']} 个章节")
    else:
        print("处理失败!")

if __name__ == "__main__":
    main()