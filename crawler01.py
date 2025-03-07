#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import os
import re
import sys
from pathlib import Path

import yt_dlp
from bs4 import BeautifulSoup

# 設定日誌記錄
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_video_info(url):
    """獲取 YouTube 影片的資訊，包括最高解析度"""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'best'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])
            # 篩選出有高度資訊的格式
            video_formats = [f for f in formats if f.get('height')]
            if video_formats:
                # 根據高度排序，獲取最高解析度
                max_height = max(f.get('height', 0) for f in video_formats)
                return f"{max_height}p"
            return "unknown"
    except Exception as e:
        logger.error(f"獲取影片資訊失敗 {url}: {e}")
        return "unknown"

def sanitize_filename(filename):
    """清理檔案名稱，移除非法字元"""
    # 移除不能用於檔名的字元
    sanitized = re.sub(r'[\\/*?:"<>|]', "", filename)
    # 移除前後空格
    sanitized = sanitized.strip()
    # 確保檔名不為空
    if not sanitized:
        sanitized = "unnamed_video"
    return sanitized

def extract_youtube_links(html_file):
    """從 HTML 文件中提取 YouTube 連結和標題，並依類別分類"""
    try:
        with open(html_file, 'r', encoding='utf-8') as file:
            content = file.read()
    except Exception as e:
        logger.error(f"讀取 HTML 文件時出錯: {e}")
        return {}

    soup = BeautifulSoup(content, 'html.parser')
    categorized_data = {
        "護理常規紀錄": [],
        "品質監測紀錄": []
    }

    # 尋找所有 h3 標題和其後的 ul 列表
    for h3 in soup.find_all('h3'):
        category_title = h3.get_text().strip()
        if '護理組 -' in category_title:
            # 取得類別名稱
            category_name = category_title.split('-')[-1].strip()
            # 找到下一個 ul 元素
            ul = h3.find_next('ul')
            if ul:
                # 處理該類別下的所有連結
                for link in ul.find_all('a', href=re.compile(r'youtu\.be')):
                    url = link.get('href')
                    title = link.get_text().strip()
                    if url and title:
                        safe_title = sanitize_filename(title)
                        # 獲取影片解析度
                        resolution = get_video_info(url)
                        video_data = {
                            'url': url,
                            'title': title,
                            'safe_title': safe_title,
                            'resolution': resolution,
                            'filename': f"{safe_title}_{resolution}.mp4"
                        }
                        if category_name in categorized_data:
                            categorized_data[category_name].append(video_data)
                            logger.info(f"已獲取影片資訊: {title} ({resolution})")

    # 記錄每個類別找到的連結數量
    for category, videos in categorized_data.items():
        logger.info(f"類別 '{category}' 中找到 {len(videos)} 個 YouTube 連結")

    return categorized_data

def save_to_json(data, output_file):
    """將資料儲存為 JSON 檔案"""
    try:
        with open(output_file, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        logger.info(f"已成功儲存資料到 {output_file}")
        return True
    except Exception as e:
        logger.error(f"儲存 JSON 檔案時出錯: {e}")
        return False

def main():
    """主程式功能：提取連結並儲存為 JSON"""
    # HTML 文件路徑
    html_file = "reference/r1.html"

    # 確認 HTML 文件存在
    if not os.path.exists(html_file):
        logger.error(f"HTML 文件不存在: {html_file}")
        return

    # 提取 YouTube 連結
    categorized_links = extract_youtube_links(html_file)

    if not any(categorized_links.values()):
        logger.warning("未找到任何 YouTube 連結")
        return

    # 準備要儲存的資料
    output_data = {
        "source": html_file,
        "extraction_time": str(Path(html_file).stat().st_mtime),
        "categories": {}
    }

    # 為每個類別添加統計資訊
    for category, videos in categorized_links.items():
        output_data["categories"][category] = {
            "total_videos": len(videos),
            "videos": videos
        }

    # 儲存為 JSON 檔案
    output_file = "youtube_links.json"
    save_to_json(output_data, output_file)

if __name__ == "__main__":
    try:
        main()
        logger.info("YouTube 連結提取完成，已儲存為 JSON 檔案")
    except Exception as e:
        logger.error(f"程式執行期間發生錯誤: {e}")
