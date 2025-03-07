# YouTube 影片爬蟲系統

這是一個兩階段的 YouTube 影片爬蟲系統，可以從 HTML 檔案中提取 YouTube 連結，並以最高品質下載影片。

## 系統架構

系統分為兩個獨立的腳本：

1. **crawler01.py** - 從 HTML 檔案中提取 YouTube 連結，並將連結資訊儲存為 JSON 檔案
2. **crawler02.py** - 讀取 JSON 檔案，並下載其中所列的所有 YouTube 影片

這種分離式設計具有以下優點：

- 連結提取和影片下載過程分開，便於獨立維護
- JSON 作為中間格式，方便檢視和編輯要下載的影片清單
- 如果下載過程中斷，不需要重新爬取頁面

## 功能

- 自動從 HTML 檔案中提取 YouTube 影片連結
- 使用 yt-dlp 下載最高品質的影片
- 自動處理檔案命名，使用 HTML 中的標題作為檔名
- 建立專屬資料夾存放下載的影片
- 支援斷點續傳，避免重複下載
- 提供詳細日誌記錄，方便追蹤進度

## 安裝步驟

1. 安裝所需的 Python 套件：

```bash
pip install -r requirements.txt
```

2. 確保您的系統已安裝 Python 3.6+ 版本

## 使用方法

### 步驟 1：提取 YouTube 連結

```bash
python crawler01.py
```

這個命令會從 `reference/r1.html` 提取所有 YouTube 連結，並將資訊儲存為 `youtube_links.json` 檔案。

### 步驟 2：下載 YouTube 影片

```bash
python crawler02.py
```

這個命令會讀取 `youtube_links.json` 檔案，並將其中列出的所有 YouTube 影片下載到 `youtube` 資料夾。

### 一次執行兩個程式

如果您想一次執行兩個腳本，可以使用以下命令：

```bash
python crawler01.py && python crawler02.py
```

## 注意事項

- 下載大量影片可能需要一段時間
- 可以隨時中斷 crawler02.py 的執行，下次執行時會自動跳過已下載的影片
- 可以在兩次執行之間編輯 youtube_links.json 檔案，以便自訂要下載的影片
- crawler02.py 會自動檢查並安裝 yt-dlp（如果尚未安裝）
- 確保您有足夠的儲存空間
- 請遵守 YouTube 的使用條款

## 依賴套件

- beautifulsoup4: 用於解析 HTML
- yt-dlp: 用於下載 YouTube 影片
- pathlib: 用於處理檔案路徑
