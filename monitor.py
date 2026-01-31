import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import time

# --- 配置区 ---
# 填写你企业微信机器人的 Webhook 地址
WECOM_WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=52b3dac7-fbdd-4f79-85c9-cec274b6151d"

# 监控源：苹果开发者新闻 和 谷歌安卓开发者博客
SOURCES = {
    "Apple Developer News": "https://developer.apple.com/news/rss/news.rss",
    "Google Play Policy": "https://android-developers.googleblog.com/feeds/posts/default"
}

def get_news(url, platform_name):
    headers = {'User-Agent': 'Mozilla/5.0'}
    items = []
    try:
        response = requests.get(url, headers=headers, timeout=15)
        root = ET.fromstring(response.content)
        
        # 解析 RSS 格式
        for item in root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry'):
            # 兼容不同格式的标题、链接和时间
            title = (item.find('title').text if item.find('title') is not None else "无标题").strip()
            link = (item.find('link').text if item.find('link') is not None else 
                    item.find('{http://www.w3.org/2005/Atom}link').attrib.get('href', ""))
            
            # 处理时间：获取发布时间并转为日期对象
            pub_date_str = ""
            if item.find('pubDate') is not None:
                pub_date_str = item.find('pubDate').text # Apple 格式
            elif item.find('{http://www.w3.org/2005/Atom}published') is not None:
                pub_date_str = item.find('{http://www.w3.org/2005/Atom}published').text # Google 格式

            # 简单的时间过滤逻辑：收集最近30天
            # (注：由于GitHub环境时区和解析复杂度，这里简化为获取前5条，你可以根据需要过滤pub_date)
            items.append({
                "platform": platform_name,
                "title": title,
                "link": link,
                "date": pub_date_str[:16] if pub_date_str else "未知时间"
            })
            if len(items) >= 3: break # 每个平台取最新的3条，避免消息过长
    except Exception as e:
        print(f"解析 {platform_name} 出错: {e}")
    return items

def send_to_wecom(news_list):
    if not news_list:
        return

    for news in news_list:
        content = (
            f"**平台名称**：{news['platform']}\n"
            f"**政策内容**：{news['title']}\n"
            f"**更新时间**：{news['date']}\n"
            f"**具体链接**：[点击查看]({news['link']})"
        )
        
        data = {
            "msgtype": "markdown",
            "markdown": {"content": content}
        }
        requests.post(WECOM_WEBHOOK_URL, json=data)
        time.sleep(1) # 防止发送过快被限流

if __name__ == "__main__":
    all_news = []
    for name, url in SOURCES.items():
        all_news.extend(get_news(url, name))
    
    if all_news:
        send_to_wecom(all_news)
    else:
        print("未抓取到新政策")
