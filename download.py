#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import hashlib
import json
import logging
import os
import random
import shutil
import time
from pathlib import Path

import yt_dlp

# 設置日誌
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", handlers=[logging.FileHandler("download_log.txt"), logging.StreamHandler()])
logger = logging.getLogger(__name__)

# 創建下載目錄
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# 已下載的視頻記錄文件
DOWNLOADED_FILE = Path("downloaded.json")


# 全局設置
class Config:
    force_best_quality = False


def load_json(file_path):
    """載入 JSON 文件"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"載入 JSON 文件時出錯: {e}")
        return None


def save_json(data, file_path):
    """保存 JSON 文件"""
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        logger.error(f"保存 JSON 文件時出錯: {e}")
        return False


def get_downloaded_urls():
    """獲取已下載的視頻 URL 列表"""
    if DOWNLOADED_FILE.exists():
        downloaded_data = load_json(DOWNLOADED_FILE)
        if downloaded_data and isinstance(downloaded_data, dict):
            return downloaded_data.get("downloaded_urls", [])
    return []


def add_downloaded_url(url):
    """添加已下載的視頻 URL"""
    downloaded_urls = get_downloaded_urls()
    if url not in downloaded_urls:
        downloaded_urls.append(url)
        save_json({"downloaded_urls": downloaded_urls}, DOWNLOADED_FILE)


def get_url_hash(url):
    """獲取 URL 的哈希值，用於檢查是否已下載"""
    return hashlib.md5(url.encode("utf-8")).hexdigest()


def download_video(video_info, category_dir, downloaded_urls):
    """下載單個視頻"""
    url = video_info.get("url")
    title = video_info.get("safe_title", video_info.get("title", ""))

    if not url or not title:
        logger.warning(f"缺少 URL 或標題: {video_info}")
        return False

    # 檢查是否已下載
    if url in downloaded_urls:
        logger.info(f"已下載過視頻: {title} - {url}")
        return True

    # 從 video_info 中獲取指定的解析度（如果有）
    preferred_resolution = video_info.get("resolution", "").lower()
    logger.info(f"JSON 中指定的解析度: {preferred_resolution}")

    # 如果設置了強制使用最高解析度，忽略 JSON 中指定的解析度
    if Config.force_best_quality:
        logger.info("已啟用強制最高解析度選項，將忽略 JSON 中指定的解析度")
        preferred_resolution = ""

    # 設置 yt-dlp 選項
    ydl_opts = {
        # 下載最高解析度的 mp4 文件
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": str(category_dir / f"{title}.%(ext)s"),
        "merge_output_format": "mp4",  # 強制合併為 mp4
        "noplaylist": True,
        "quiet": False,
        "no_warnings": False,
        "ignoreerrors": True,
        "writethumbnail": False,  # 不下載縮略圖
        # 防爬蟲設置
        "source_address": "0.0.0.0",  # 綁定到所有接口
        "sleep_interval": random.uniform(1, 3),  # 下載間隔
        "max_sleep_interval": 5,
        "cookiefile": "cookies.txt" if os.path.exists("cookies.txt") else None,  # 如果有 cookies 文件才使用
        # 重試設置
        "retries": 10,
        "fragment_retries": 10,
        "file_access_retries": 5,
        "extractor_retries": 5,
        # 使用者代理（隨機選擇一個 - 防爬蟲）
        "user-agent": random.choice(
            [
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
            ]
        ),
        # 其他設置
        "geo_bypass": True,  # 嘗試繞過地理限制
        "geo_bypass_country": "TW",  # 台灣
        "postprocessors": [
            {
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4",  # 確保轉換為 mp4
            }
        ],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"正在下載: {title} - {url}")
            info_dict = ydl.extract_info(url, download=False)
            available_formats = info_dict.get("formats", [])

            # 記錄可用解析度，幫助調試
            available_resolutions = set()
            for fmt in available_formats:
                if fmt.get("height"):
                    available_resolutions.add(f"{fmt.get('height')}p")

            if available_resolutions:
                available_resolutions_sorted = sorted(available_resolutions, key=lambda x: int(x[:-1]), reverse=True)
                logger.info(f"可用解析度: {', '.join(available_resolutions_sorted)}")
                highest_resolution = available_resolutions_sorted[0]
                logger.info(f"最高可用解析度: {highest_resolution}")

                # 確定要下載的解析度
                target_resolution = highest_resolution  # 預設使用最高解析度

                # 如果指定了偏好解析度且不是強制使用最高解析度，檢查是否可用
                if preferred_resolution and preferred_resolution in available_resolutions and not Config.force_best_quality:
                    target_resolution = preferred_resolution
                    logger.info(f"使用指定解析度: {target_resolution}")
                else:
                    logger.info(f"使用最高可用解析度: {target_resolution}")

                # 提取解析度數值並更新下載格式
                resolution_value = target_resolution.rstrip("p")
                if resolution_value.isdigit():
                    # 更新下載格式以精確匹配目標解析度
                    ydl_opts["format"] = f"bestvideo[height={resolution_value}][ext=mp4]+bestaudio[ext=m4a]/best[height={resolution_value}][ext=mp4]/best"
                    # 重新創建 YoutubeDL 實例以應用新設置
                    ydl = yt_dlp.YoutubeDL(ydl_opts)

            # 開始下載
            ydl.download([url])
            logger.info(f"成功下載: {title}")

            # 標記為已下載
            add_downloaded_url(url)
            return True

    except Exception as e:
        logger.error(f"下載失敗 {title} ({url}): {e}")
        return False


def clean_directory(directory):
    """清理目錄中的非 mp4 文件"""
    cleaned_count = 0
    try:
        for file_path in directory.glob("**/*"):
            if file_path.is_file() and file_path.suffix.lower() not in [".mp4", ".json", ".txt"]:
                logger.info(f"刪除多餘文件: {file_path}")
                file_path.unlink()
                cleaned_count += 1
    except Exception as e:
        logger.error(f"清理目錄時出錯: {e}")

    return cleaned_count


def check_download_integrity():
    """檢查下載完整性，修復問題下載"""
    logger.info("檢查已下載視頻的完整性...")

    fixed_count = 0
    # 載入 YouTube 鏈接
    json_file = "youtube_links.json"
    links_data = load_json(json_file)

    if not links_data:
        logger.error(f"無法載入 {json_file}")
        return fixed_count

    # 載入已下載的視頻 URL
    downloaded_urls = get_downloaded_urls()
    urls_to_remove = []

    # 檢查每個標記為已下載的 URL
    for url in downloaded_urls:
        found = False
        title = None
        category_dir = None

        # 尋找 URL 對應的視頻信息
        for category_name, category_data in links_data.get("categories", {}).items():
            videos = category_data.get("videos", [])
            for video in videos:
                if video.get("url") == url:
                    title = video.get("safe_title", video.get("title", ""))
                    category_dir = DOWNLOAD_DIR / category_name
                    found = True
                    break
            if found:
                break

        if not found or not title or not category_dir:
            logger.warning(f"找不到 URL 的相關信息: {url}, 將其標記為未下載")
            urls_to_remove.append(url)
            continue

        # 檢查是否有完整的 mp4 文件
        expected_file = category_dir / f"{title}.mp4"
        part_files = list(category_dir.glob(f"{title}.*part"))
        webp_files = list(category_dir.glob(f"{title}.webp"))
        m4a_files = list(category_dir.glob(f"{title}.*.m4a"))
        mp4_segments = list(category_dir.glob(f"{title}.f*.mp4"))

        # 檢查 mp4 文件是否存在且大小大於 1MB
        if not expected_file.exists() or expected_file.stat().st_size < 1024 * 1024:
            logger.warning(f"視頻文件不完整或不存在: {expected_file}")

            # 如果存在部分下載，刪除它們
            for part_file in part_files + webp_files + m4a_files + mp4_segments:
                logger.info(f"刪除部分下載: {part_file}")
                part_file.unlink(missing_ok=True)

            # 標記為未下載
            urls_to_remove.append(url)
            fixed_count += 1

    # 更新已下載列表
    if urls_to_remove:
        new_downloaded_urls = [url for url in downloaded_urls if url not in urls_to_remove]
        save_json({"downloaded_urls": new_downloaded_urls}, DOWNLOADED_FILE)
        logger.info(f"已從已下載列表中移除 {len(urls_to_remove)} 個問題視頻")

    return fixed_count


def main():
    """主函數"""
    # 清理下載目錄中的非 mp4 文件
    logger.info("清理下載目錄中的臨時文件和非 mp4 文件...")
    cleaned_count = clean_directory(DOWNLOAD_DIR)
    logger.info(f"已清理 {cleaned_count} 個多餘文件")

    # 檢查下載完整性
    fixed_count = check_download_integrity()
    logger.info(f"已修復 {fixed_count} 個問題下載")

    # 載入 YouTube 鏈接
    json_file = "youtube_links.json"
    links_data = load_json(json_file)

    if not links_data:
        logger.error(f"無法載入 {json_file}")
        return

    # 載入已下載的視頻 URL
    downloaded_urls = get_downloaded_urls()
    logger.info(f"已下載 {len(downloaded_urls)} 個視頻")

    # 下載計數器
    total_videos = 0
    success_count = 0
    failure_count = 0
    skip_count = 0

    # 遍歷各個分類及其視頻
    categories = links_data.get("categories", {})
    for category_name, category_data in categories.items():
        logger.info(f"處理分類: {category_name}")

        # 創建分類目錄
        category_dir = DOWNLOAD_DIR / category_name
        category_dir.mkdir(exist_ok=True)

        # 獲取視頻列表
        videos = category_data.get("videos", [])
        total_videos += len(videos)

        # 下載每個視頻
        for index, video in enumerate(videos):
            logger.info(f"處理視頻 {index + 1}/{len(videos)}: {video.get('title')}")

            # 檢查是否已下載
            if video.get("url") in downloaded_urls:
                logger.info(f"已下載過，跳過: {video.get('title')}")
                skip_count += 1
                continue

            # 下載視頻
            success = download_video(video, category_dir, downloaded_urls)
            if success:
                success_count += 1
            else:
                failure_count += 1

            # 每次下載後隨機等待，避免被防爬蟲機制檢測
            if index < len(videos) - 1:  # 如果不是最後一個視頻
                wait_time = random.uniform(5, 15)  # 隨機等待 5-15 秒
                logger.info(f"等待 {wait_time:.2f} 秒後繼續...")
                time.sleep(wait_time)

    # 清理下載目錄中的非 mp4 文件
    logger.info("清理下載目錄中的臨時文件和非 mp4 文件...")
    cleaned_count = clean_directory(DOWNLOAD_DIR)
    logger.info(f"已清理 {cleaned_count} 個多餘文件")

    # 顯示總結
    logger.info(f"下載完成! 總視頻數: {total_videos}, 成功: {success_count}, 失敗: {failure_count}, 跳過(已下載): {skip_count}")
    logger.info(f"所有視頻位於: {DOWNLOAD_DIR.absolute()}")


if __name__ == "__main__":
    try:
        # 解析命令行參數
        parser = argparse.ArgumentParser(description="下載 YouTube 視頻")
        parser.add_argument("--clean", action="store_true", help="僅清理下載目錄中的非 mp4 文件")
        parser.add_argument("--check", action="store_true", help="檢查下載完整性並修復問題")
        parser.add_argument("--best-quality", action="store_true", help="強制下載所有視頻的最高解析度版本")
        args = parser.parse_args()

        if args.clean:
            # 僅執行清理
            logger.info("執行清理操作...")
            cleaned_count = clean_directory(DOWNLOAD_DIR)
            logger.info(f"已清理 {cleaned_count} 個多餘文件")
        elif args.check:
            # 僅執行檢查和修復
            logger.info("執行檢查和修復操作...")
            cleaned_count = clean_directory(DOWNLOAD_DIR)
            logger.info(f"已清理 {cleaned_count} 個多餘文件")
            fixed_count = check_download_integrity()
            logger.info(f"已修復 {fixed_count} 個問題下載")
        else:
            # 正常執行下載過程
            if args.best_quality:
                logger.info("強制下載所有視頻的最高解析度版本")
                # 設置全局配置
                Config.force_best_quality = True
            main()
    except KeyboardInterrupt:
        logger.info("用戶中斷下載，程序退出。")
    except Exception as e:
        logger.error(f"程序執行時發生錯誤: {e}")
