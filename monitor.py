import requests
import xml.etree.ElementTree as ET
import os
import json

# 配置从 GitHub Secrets 读取
KIMI_API_KEY = os.getenv("KIMI_API_KEY")
WECOM_WEBHOOK_URL = os.getenv("WECOM_WEBHOOK_URL")

# Kimi API 官方地址
KIMI_URL = "https://api.moonshot.cn/v1/chat/completions"

SOURCES = {
    "Apple Developer News": "https://developer.apple.com/news/rss/news.rss",
    "Google Play Policy": "https://android-developers.googleblog.com/feeds/posts/default"
}

def get_kimi_summary(text):
    """调用 Kimi AI 进行中文政策风险深度总结"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {KIMI_API_KEY}"
    }
    
    # 针对项目管理专员优化的提示词
    prompt = (
        "你是一名资深的 App 合规专家。请分析下述政策标题，"
        "简要说明该政策对公司 App 产品线可能存在的风险或影响（如：下架风险、需要更新 SDK、隐私协议变更等）。"
        "请用 80 字以内中文回答。\n\n内容如下：" + text
    )
    
    payload = {
        "model": "moonshot-v1-8k",  # Kimi 的标准模型
        "messages": [
            {"role": "system", "content": "你是一个专业的合规分析助手。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }
    
    try:
        response = requests.post(KIMI_URL, json=payload, headers=headers, timeout=30)
        res_json = response.json()
        if response.status_code == 200:
            return res_json['choices'][0]['message']['content'].strip()
        else:
            print(f"Kimi API 报错: {res_json}")
            return "（AI 总结失败，请查阅原文）"
    except Exception as e:
        print(f"请求 Kimi 出错: {e}")
        return "（服务连接异常）"

def monitor():
    headers = {'User-Agent': 'Mozilla/5.0'}
    for platform, url in SOURCES.items():
        try:
            res = requests.get(url, headers=headers, timeout=15)
            root = ET.fromstring(res.content)
            
            items = root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry')
            if not items: continue
            
            # 获取最新的一条政策
            latest_item = items[0]
            title = latest_item.find('title').text.strip()
            
            # 兼容链接
            link_node = latest_item.find('link')
            link = link_node.text if link_node is not None and link_node.text else link_node.attrib.get('href', "")
            
            # 关键步骤：调用 Kimi 总结
            summary = get_kimi_summary(title)
            
            # 企业微信推送格式
            message = {
                "msgtype": "markdown",
                "markdown": {
                    "content": (
                        f"### 🛡️ Kimi 政策风险日报\n"
                        f"**【{platform}】**\n"
                        f"**变动标题**：{title}\n"
                        f"**Kimi 专家分析**：<font color=\"info\">{summary}</font>\n\n"
                        f"[查看详细政策指南]({link})"
                    )
                }
            }
            requests.post(WECOM_WEBHOOK_URL, json=message)
            
        except Exception as e:
            print(f"处理 {platform} 失败: {e}")

if __name__ == "__main__":
    monitor()
