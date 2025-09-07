import os
import re
import shutil
import chardet
from pathlib import Path

def detect_encoding(file_path):
    """检测文件编码"""
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        return result['encoding']

def read_file_with_encoding(file_path):
    """尝试用多种编码读取文件"""
    # 尝试检测编码
    try:
        encoding = detect_encoding(file_path)
        if encoding:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
    except:
        pass
    
    # 如果检测失败或读取失败，尝试常见编码
    encodings = ['utf-8', 'gbk', 'gb2312', 'big5', 'latin-1', 'cp1252']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"使用编码 {encoding} 读取文件时出错: {e}")
            continue
    
    # 如果所有编码都失败，尝试二进制读取并忽略错误
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception as e:
        print(f"即使使用错误忽略也无法读取文件: {e}")
        return ""

def process_novels():
    # 确保目录存在
    os.makedirs("novel", exist_ok=True)
    os.makedirs("novel_already", exist_ok=True)
    
    # 查找所有TXT文件
    txt_files = [f for f in os.listdir(".") if f.endswith(".txt")]
    
    if not txt_files:
        print("未找到TXT文件")
        return
    
    for txt_file in txt_files:
        print(f"处理文件: {txt_file}")
        
        # 提取小说名称（不含扩展名）
        novel_name = os.path.splitext(txt_file)[0]
        
        # 创建小说目录
        novel_dir = os.path.join("novel", novel_name)
        os.makedirs(novel_dir, exist_ok=True)
        
        # 读取文件内容
        content = read_file_with_encoding(txt_file)
        
        if not content:
            print(f"警告: 无法读取文件 {txt_file}，跳过处理")
            continue
        
        # 定义章节分割的正则表达式模式
        # 这个模式匹配常见的章节标题格式
        chapter_patterns = [
            r'第[零一二三四五六七八九十百千万\d]+章',
            r'第\d+章',
            r'CHAPTER\s+\d+',
            r'Chapter\s+\d+',
            r'\d+、',
            r'【.*?】',
            r'第.*?节',
            r'第.*?回'
        ]
        
        chapter_pattern = '|'.join(chapter_patterns)
        
        # 分割章节
        chapters = re.split(chapter_pattern, content)
        chapter_titles = re.findall(chapter_pattern, content)
        
        # 如果有找到章节标题
        if chapter_titles and len(chapters) > 1:
            # 第一个部分可能是前言或简介
            if chapters[0].strip():
                with open(os.path.join(novel_dir, "前言.txt"), 'w', encoding='utf-8') as f:
                    f.write(chapters[0].strip())
            
            # 处理每个章节
            for i, (title, content) in enumerate(zip(chapter_titles, chapters[1:]), 1):
                if content.strip():  # 确保章节内容不为空
                    # 清理文件名中的非法字符
                    safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
                    chapter_filename = f"{i:03d}_{safe_title}.txt"
                    
                    with open(os.path.join(novel_dir, chapter_filename), 'w', encoding='utf-8') as f:
                        f.write(f"{title}\n\n{content.strip()}")
            
            print(f"已分割 {len(chapter_titles)} 个章节")
        else:
            # 如果没有找到章节标题，将整个文件作为一个章节
            with open(os.path.join(novel_dir, "全文.txt"), 'w', encoding='utf-8') as f:
                f.write(content)
            print("未检测到章节标题，将整个文件保存为一个章节")
        
        # 移动已处理的文件到novel_already目录
        shutil.move(txt_file, os.path.join("novel_already", txt_file))
        print(f"已移动 {txt_file} 到 novel_already 目录")

if __name__ == "__main__":
    process_novels()        # 定义章节分割的正则表达式模式
        # 这个模式匹配常见的章节标题格式，如 "第一章", "第1章", "Chapter 1" 等
        chapter_pattern = r'(?:第[零一二三四五六七八九十百千万\d]+章|第\d+章|CHAPTER\s+\d+|Chapter\s+\d+|\d+、)'
        
        # 分割章节
        chapters = re.split(chapter_pattern, content)
        chapter_titles = re.findall(chapter_pattern, content)
        
        # 如果有找到章节标题
        if chapter_titles:
            # 第一个部分可能是前言或简介
            if chapters[0].strip():
                with open(os.path.join(novel_dir, "前言.txt"), 'w', encoding='utf-8') as f:
                    f.write(chapters[0].strip())
            
            # 处理每个章节
            for i, (title, content) in enumerate(zip(chapter_titles, chapters[1:]), 1):
                if content.strip():  # 确保章节内容不为空
                    # 清理文件名中的非法字符
                    safe_title = re.sub(r'[\\/*?:"<>|]', "", title)
                    chapter_filename = f"{i:03d}_{safe_title}.txt"
                    
                    with open(os.path.join(novel_dir, chapter_filename), 'w', encoding='utf-8') as f:
                        f.write(f"{title}\n\n{content.strip()}")
            
            print(f"已分割 {len(chapter_titles)} 个章节")
        else:
            # 如果没有找到章节标题，将整个文件作为一个章节
            with open(os.path.join(novel_dir, "全文.txt"), 'w', encoding='utf-8') as f:
                f.write(content)
            print("未检测到章节标题，将整个文件保存为一个章节")
        
        # 移动已处理的文件到novel_already目录
        shutil.move(txt_file, os.path.join("novel_already", txt_file))
        print(f"已移动 {txt_file} 到 novel_already 目录")

if __name__ == "__main__":
    process_novels()
