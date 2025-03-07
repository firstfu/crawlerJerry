import json
import os

from yt_dlp import YoutubeDL


def load_video_data(json_file='youtube_links.json'):
    """載入 JSON 檔案中的影片資訊"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"讀取 JSON 檔案時發生錯誤: {e}")
        return None

def download_video(video_info):
    """下載單一影片"""
    url = video_info['url']
    resolution = video_info['resolution']
    filename = video_info['filename']
    target_height = int(resolution[:-1])  # 將 "720p" 轉換為 720

    # 設定 yt-dlp 的選項
    ydl_opts = {
        'format': f'best[ext=mp4][height={target_height}]/best[height={target_height}]/best[ext=mp4][height<={target_height}]',
        'outtmpl': filename,
        'quiet': False,
        'no_warnings': False,
        'verbose': True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            # 先獲取影片資訊
            info = ydl.extract_info(url, download=False)
            print(f"\n可用的格式：")
            formats_info = []
            for f in info['formats']:
                if 'height' in f and f['height'] is not None:
                    format_info = {
                        'format_id': f['format_id'],
                        'ext': f.get('ext', 'N/A'),
                        'height': f['height'],
                        'vcodec': f.get('vcodec', 'N/A'),
                        'acodec': f.get('acodec', 'N/A'),
                    }
                    formats_info.append(format_info)
                    print(f"格式：{f['format_id']}, 類型：{f.get('ext', 'N/A')}, "
                          f"解析度：{f['height']}p, 影像編碼：{f.get('vcodec', 'N/A')}, "
                          f"音訊編碼：{f.get('acodec', 'N/A')}")

            # 下載影片
            print(f"\n目標解析度：{target_height}p")
            print(f"開始下載影片...")
            ydl.download([url])
        print(f"成功下載: {filename}")
        return True
    except Exception as e:
        print(f"下載 {filename} 時發生錯誤: {e}")
        return False

def main():
    # 載入影片資料
    data = load_video_data()
    if not data:
        return

    # 建立下載目錄
    os.makedirs('downloads', exist_ok=True)
    os.chdir('downloads')

    # 遍歷所有類別和影片
    for category_name, category_data in data['categories'].items():
        print(f"\n開始下載類別: {category_name}")

        # 建立類別目錄
        os.makedirs(category_name, exist_ok=True)
        os.chdir(category_name)

        for video in category_data['videos']:
            print(f"\n正在處理: {video['title']}")
            download_video(video)

        os.chdir('..')  # 回到上層目錄

if __name__ == "__main__":
    main()
