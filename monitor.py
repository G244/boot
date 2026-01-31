import requests
import xml.etree.ElementTree as ET
import os
import json

# 配置
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WECOM_WEBHOOK_URL = os.getenv("WECOM_WEBHOOK_URL")

# 根据 2026 官方文档更新的路径和模型名
# 注意：v1beta 路径支持最新的 preview 模型
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={GEMINI_API_KEY}"

SOURCES = {
    "Apple Developer News": "https://developer.apple.com/news/rss/news.rss",
    "Google Play Policy": "https://android-developers.googleblog.com/feeds/posts/default"
}

def get_ai_summary(text):
    """使用 Gemini 3 接口进行总结"""
    headers = {'Content-Type': 'application/json'}
    # 提示词优化，针对政策合规
    prompt = f"你是一名App合规专家。请对下文进行风险总结。提取对开发者影响最大的变动（100字内）：\n\n{text}"
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    try:
        response = requests.post(GEMINI_URL, json=payload, headers=headers, timeout=20)
        res_json = response.json()
        
        # 调试：如果报错，则输出完整日志到 Action
        if response.status_code != 200:
            print(f"API Error: {res_json}")
            return "（AI接口异常，请阅读原文）"

        # 解析 Gemini 3 返回的文本
        summary = res_json['candidates'][0]['content']['parts'][0]['text']
        return summary.strip()
    except Exception as e:
        print(f"Error calling AI: {e}")
        return "（总结暂不可用，请查看详情）"

def monitor():
    headers = {'User-Agent': 'Mozilla/5.0'}
    for platform, url in SOURCES.items():
        try:
            res = requests.get(url, headers=headers, timeout=15)
            # 解析 XML
            root = ET.fromstring(res.content)
            
            # 兼容不同平台的 RSS/Atom 节点
            items = root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry')
            if not items:
                continue
                
            latest_item = items[0]
            title = latest_item.find('title').text.strip()
            
            # 兼容链接提取
            link_node = latest_item.find('link')
            link = link_node.text if link_node is not None and link_node.text else link_node.attrib.get('href', "")
            
            # 获取 AI 总结
            summary = get_ai_summary(title)
            
            # 推送企业微信
            message = {
                "msgtype": "markdown",
                "markdown": {
                    "content": (
                        f"### 🛡️ 政策预警\n"
                        f"**【{platform}】**\n"
                        f"**标题**：{title}\n"
                        f"**风险分析**：<font color=\"warning\">{summary}</font>\n\n"
                        f"[查看政策详情]({link})"
                    )
                }
            }
            requests.post(WECOM_WEBHOOK_URL, json=message)
            
        except Exception as e:
            print(f"处理 {platform} 时出错: {e}")

if __name__ == "__main__":
    monitor()
