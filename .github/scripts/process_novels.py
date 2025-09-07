import os
import re
import shutil
from pathlib import Path

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
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            with open(txt_file, 'r', encoding='gbk') as f:
                content = f.read()
        
        # 定义章节分割的正则表达式模式
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
