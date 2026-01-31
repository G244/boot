import requests
import xml.etree.ElementTree as ET
import os
import json

# 配置
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WECOM_WEBHOOK_URL = os.getenv("WECOM_WEBHOOK_URL")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

SOURCES = {
    "Apple Developer News": "https://developer.apple.com/news/rss/news.rss",
    "Google Play Policy": "https://android-developers.googleblog.com/feeds/posts/default"
}

def get_ai_summary(text):
    """带日志诊断的 Gemini 总结函数"""
    headers = {'Content-Type': 'application/json'}
    prompt = f"你是一个App政策分析专家。请简洁总结下文的政策变动和对App开发者的风险影响（100字内）：\n\n{text}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    try:
        response = requests.post(GEMINI_URL, json=payload, headers=headers, timeout=20)
        res_json = response.json()
        
        # 诊断日志：如果出错，可以在 GitHub Actions 的日志里看到具体原因
        if response.status_code != 200:
            print(f"API报错详情: {res_json}")
            return "（AI接口响应异常）"

        return res_json['candidates'][0]['content']['parts'][0]['text'].strip()
    except Exception as e:
        print(f"解析过程出错: {e}")
        return "（总结失败，请阅读原文）"

def monitor():
    headers = {'User-Agent': 'Mozilla/5.0'}
    for platform, url in SOURCES.items():
        try:
            res = requests.get(url, headers=headers, timeout=15)
            root = ET.fromstring(res.content)
            # 找到最新一条更新
            item = root.findall('.//item')[0] if root.findall('.//item') else root.findall('.//{http://www.w3.org/2005/Atom}entry')[0]
            
            title = item.find('title').text.strip()
            link = (item.find('link').text if item.find('link') is not None else 
                    item.find('{http://www.w3.org/2005/Atom}link').attrib.get('href', ""))
            
            # AI 总结
            summary = get_ai_summary(title)
            
            # 推送消息
            message = {
                "msgtype": "markdown",
                "markdown": {
                    "content": f"### 🛡️ 跨境政策风险预警\n"
                               f"**【{platform}】**\n"
                               f"**内容**：{title}\n"
                               f"**AI 风险分析**：<font color=\"warning\">{summary}</font>\n\n"
                               f"[查看政策详情]({link})"
                }
            }
            requests.post(WECOM_WEBHOOK_URL, json=message)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    monitor()
