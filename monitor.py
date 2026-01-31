import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import os
import json

# 配置
KIMI_API_KEY = os.getenv("KIMI_API_KEY")
WECOM_WEBHOOK_URL = os.getenv("WECOM_WEBHOOK_URL")
KIMI_URL = "https://api.moonshot.cn/v1/chat/completions"

def get_kimi_summary(platform, title, detail):
    """调用 Kimi AI 进行合规风险分析"""
    headers = {"Authorization": f"Bearer {KIMI_API_KEY}", "Content-Type": "application/json"}
    prompt = (
        f"你是项目管理专员。请分析 {platform} 的最新动态：\n"
        f"标题：{title}\n详情：{detail[:800]}\n\n"
        "请回答：1.政策/技术核心变动；2.对产品的潜在风险；3.建议行动。100字内。"
    )
    payload = {
        "model": "moonshot-v1-8k",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }
    try:
        res = requests.post(KIMI_URL, json=payload, headers=headers, timeout=30)
        return res.json()['choices'][0]['message']['content'].strip()
    except:
        return "（AI总结失败，请查阅原文）"

def send_wecom(platform, title, summary, link, color):
    """推送至企业微信"""
    message = {
        "msgtype": "markdown",
        "markdown": {
            "content": f"# <font color=\"{color}\">{platform}</font>\n**【标题】**：{title}\n\n**【AI风险解析】**：\n{summary}\n\n[查看详情链接]({link})"
        }
    }
    requests.post(WECOM_WEBHOOK_URL, json=message)

def monitor_apple():
    """1. 监控 iOS / Apple Store 新闻 (RSS)"""
    url = "https://developer.apple.com/news/rss/news.rss"
    try:
        res = requests.get(url, timeout=15)
        root = ET.fromstring(res.content)
        item = root.findall('.//item')[0]
        title = item.find('title').text
        link = item.find('link').text
        desc = item.find('description').text if item.find('description') is not None else title
        summary = get_kimi_summary("iOS / Apple", title, desc)
        send_wecom("🍏 iOS / Apple Store", title, summary, link, "info")
    except Exception as e: print(f"Apple Error: {e}")

def monitor_android_blog():
    """2. 监控 Android 官方博客 (Atom Feed)"""
    url = "https://android-developers.googleblog.com/feeds/posts/default"
    try:
        res = requests.get(url, timeout=15)
        root = ET.fromstring(res.content)
        # Atom 格式使用 entry 标签
        entry = root.find('{http://www.w3.org/2005/Atom}entry')
        title = entry.find('{http://www.w3.org/2005/Atom}title').text
        link = entry.find('{http://www.w3.org/2005/Atom}link').attrib.get('href', "")
        summary_text = entry.find('{http://www.w3.org/2005/Atom}content').text or title
        
        summary = get_kimi_summary("Android Blog", title, summary_text)
        send_wecom("🤖 Android Developer Blog", title, summary, link, "warning")
    except Exception as e: print(f"Android Blog Error: {e}")

if __name__ == "__main__":
    monitor_apple()
    monitor_android_blog()
