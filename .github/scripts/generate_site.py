import os
import json
import shutil
from pathlib import Path
import re

class NovelSiteGenerator:
    def __init__(self):
        self.novels_dir = "novel"
        self.dist_dir = "dist"
        self.template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'SimSun', '宋体', serif; 
            line-height: 1.8;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
            max-width: 800px;
            margin: 0 auto;
        }
        .header { 
            text-align: center; 
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #ddd;
        }
        .novel-title { 
            font-size: 2em; 
            color: #2c3e50;
            margin-bottom: 10px;
        }
        .chapter-title { 
            font-size: 1.5em; 
            color: #34495e;
            margin: 30px 0 20px 0;
            text-align: center;
        }
        .content { 
            font-size: 1.1em;
            text-indent: 2em;
            margin-bottom: 20px;
        }
        .nav { 
            display: flex;
            justify-content: space-between;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
        }
        .nav a {
            text-decoration: none;
            color: #3498db;
            padding: 8px 16px;
            border: 1px solid #3498db;
            border-radius: 4px;
        }
        .nav a:hover {
            background: #3498db;
            color: white;
        }
        .catalog {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .catalog h2 {
            margin-bottom: 20px;
            color: #2c3e50;
        }
        .chapter-list {
            list-style: none;
        }
        .chapter-list li {
            margin-bottom: 10px;
            padding: 10px;
            border-bottom: 1px solid #eee;
        }
        .chapter-list a {
            text-decoration: none;
            color: #34495e;
            display: block;
        }
        .chapter-list a:hover {
            color: #3498db;
            background: #f8f9fa;
        }
        .back-to-top {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #3498db;
            color: white;
            padding: 10px 15px;
            border-radius: 50%;
            text-decoration: none;
            display: none;
        }
    </style>
</head>
<body>
    {content}
    <a href="#" class="back-to-top">↑</a>
    <script>
        // 返回顶部按钮
        window.addEventListener('scroll', function() {
            var backToTop = document.querySelector('.back-to-top');
            if (window.pageYOffset > 300) {
                backToTop.style.display = 'block';
            } else {
                backToTop.style.display = 'none';
            }
        });
        
        document.querySelector('.back-to-top').addEventListener('click', function(e) {
            e.preventDefault();
            window.scrollTo({top: 0, behavior: 'smooth'});
        });
    </script>
</body>
</html>
        """
    
    def clean_filename(self, filename):
        """清理文件名，移除非法字符"""
        return re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    def get_novel_list(self):
        """获取小说列表"""
        novels = []
        for item in os.listdir(self.novels_dir):
            novel_path = os.path.join(self.novels_dir, item)
            if os.path.isdir(novel_path) and item != "already":
                novels.append({
                    'name': item,
                    'path': novel_path,
                    'chapters': self.get_chapters(novel_path)
                })
        return novels
    
    def get_chapters(self, novel_path):
        """获取小说的章节列表"""
        chapters = []
        for file in os.listdir(novel_path):
            if file.endswith('.txt') and file != 'metadata.txt' and file != 'split_stats.txt':
                chapters.append({
                    'name': file.replace('.txt', ''),
                    'file': file
                })
        # 按文件名排序
        chapters.sort(key=lambda x: x['file'])
        return chapters
    
    def read_chapter_content(self, file_path):
        """读取章节内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    return f.read()
            except:
                return "无法读取文件内容"
    
    def generate_chapter_html(self, novel_name, chapter, prev_chapter=None, next_chapter=None):
        """生成章节HTML页面"""
        chapter_path = os.path.join(self.novels_dir, novel_name, chapter['file'])
        content = self.read_chapter_content(chapter_path)
        
        nav_html = '<div class="nav">'
        if prev_chapter:
            prev_url = f"{self.clean_filename(prev_chapter['name'])}.html"
            nav_html += f'<a href="{prev_url}">上一章：{prev_chapter["name"]}</a>'
        else:
            nav_html += '<a href="index.html">返回目录</a>'
            
        nav_html += '<a href="index.html">目录</a>'
        
        if next_chapter:
            next_url = f"{self.clean_filename(next_chapter['name'])}.html"
            nav_html += f'<a href="{next_url}">下一章：{next_chapter["name"]}</a>'
        else:
            nav_html += '<a href="index.html">返回目录</a>'
        nav_html += '</div>'
        
        content_html = f"""
        <div class="header">
            <h1 class="novel-title">{novel_name}</h1>
        </div>
        <div class="chapter-title">{chapter['name']}</div>
        <div class="content">{content.replace(chr(10), '<br>').replace('    ', '&nbsp;&nbsp;&nbsp;&nbsp;')}</div>
        {nav_html}
        """
        
        return self.template.format(
            title=f"{chapter['name']} - {novel_name}",
            content=content_html
        )
    
    def generate_index_html(self, novels):
        """生成首页"""
        novels_html = ""
        for novel in novels:
            chapters_html = ""
            for i, chapter in enumerate(novel['chapters']):
                chapter_url = f"{novel['name']}/{self.clean_filename(chapter['name'])}.html"
                chapters_html += f'<li><a href="{chapter_url}">{chapter["name"]}</a></li>'
            
            novels_html += f"""
            <div class="catalog">
                <h2>{novel['name']}</h2>
                <ul class="chapter-list">
                    {chapters_html}
                </ul>
            </div>
            """
        
        index_html = f"""
        <div class="header">
            <h1 class="novel-title">小说阅读站</h1>
            <p>共 {len(novels)} 部小说</p>
        </div>
        {novels_html}
        """
        
        return self.template.format(
            title="小说阅读站",
            content=index_html
        )
    
    def generate_site(self):
        """生成整个站点"""
        # 清理并创建dist目录
        if os.path.exists(self.dist_dir):
            shutil.rmtree(self.dist_dir)
        os.makedirs(self.dist_dir)
        
        novels = self.get_novel_list()
        
        # 生成首页
        index_html = self.generate_index_html(novels)
        with open(os.path.join(self.dist_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(index_html)
        
        # 为每部小说生成章节页面
        for novel in novels:
            novel_dist_dir = os.path.join(self.dist_dir, novel['name'])
            os.makedirs(novel_dist_dir, exist_ok=True)
            
            # 生成每个章节的HTML
            for i, chapter in enumerate(novel['chapters']):
                prev_chapter = novel['chapters'][i-1] if i > 0 else None
                next_chapter = novel['chapters'][i+1] if i < len(novel['chapters'])-1 else None
                
                chapter_html = self.generate_chapter_html(
                    novel['name'], chapter, prev_chapter, next_chapter
                )
                
                chapter_filename = f"{self.clean_filename(chapter['name'])}.html"
                with open(os.path.join(novel_dist_dir, chapter_filename), 'w', encoding='utf-8') as f:
                    f.write(chapter_html)
        
        print(f"站点生成完成！共生成 {len(novels)} 部小说")
        total_chapters = sum(len(novel['chapters']) for novel in novels)
        print(f"总章节数: {total_chapters}")

def main():
    generator = NovelSiteGenerator()
    generator.generate_site()

if __name__ == "__main__":
    main()
