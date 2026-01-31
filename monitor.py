import requests
import xml.etree.ElementTree as ET
import os
import json

# 配置
KIMI_API_KEY = os.getenv("KIMI_API_KEY")
WECOM_WEBHOOK_URL = os.getenv("WECOM_WEBHOOK_URL")
KIMI_URL = "https://api.moonshot.cn/v1/chat/completions"

# 监控源分类
SOURCES = {
    "iOS / Apple Store": {
        "url": "https://developer.apple.com/news/rss/news.rss",
        "color": "info"  # 蓝色
    },
    "Android / Google Play": {
        "url": "https://android-developers.googleblog.com/feeds/posts/default",
        "color": "warning"  # 橙色
    }
}

def get_kimi_summary(platform, title, description):
    """调用 Kimi AI 进行深度分类总结"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {KIMI_API_KEY}"
    }
    
    # 强化提示词：要求 AI 从项目管理角度分析
    prompt = (
        f"你是一名跨境 App 项目管理专员，专注于 {platform} 平台的政策合规。\n"
        f"标题：{title}\n"
        f"详情：{description[:500]}\n\n"
        "请从以下三个维度简要总结（150字内）：\n"
        "1. 政策核心变动；\n"
        "2. 对公司产品的潜在风险（如：需更新 SDK、隐私申明、强制停用等）；\n"
        "3. 建议采取的行动。"
    )
    
    payload = {
        "model": "moonshot-v1-8k",
        "messages": [
            {"role": "system", "content": "你是一个专业的 App 审核政策分析助手。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }
    
    try:
        res = requests.post(KIMI_URL, json=payload, headers=headers, timeout=30)
        return res.json()['choices'][0]['message']['content'].strip()
    except:
        return "（总结失败，请核对原文）"

def monitor():
    headers = {'User-Agent': 'Mozilla/5.0'}
    for platform, info in SOURCES.items():
        try:
            res = requests.get(info['url'], headers=headers, timeout=15)
            root = ET.fromstring(res.content)
            
            # 解析不同格式的条目
            items = root.findall('.//item') or root.findall('.//{http://www.w3.org/2005/Atom}entry')
            
            # 我们获取最近的两条，确保不遗漏
            for item in items[:2]:
                title = item.find('title').text.strip()
                # 尝试获取描述或内容以供 AI 分析
                desc_node = item.find('description') or item.find('{http://www.w3.org/2005/Atom}summary')
                description = desc_node.text if desc_node is not None else title
                
                link_node = item.find('link')
                link = link_node.text if link_node is not None and link_node.text else link_node.attrib.get('href', "")

                # AI 总结
                summary = get_kimi_summary(platform, title, description)
                
                # 企业微信分平台推送
                color = info['color']
                message = {
                    "msgtype": "markdown",
                    "markdown": {
                        "content": (
                            f"# <font color=\"{color}\">{platform} 政策更新</font>\n"
                            f"**【标题】**：{title}\n\n"
                            f"**【AI 深度解析】**：\n{summary}\n\n"
                            f"**【原文链接】**：[点击跳转查看]({link})"
                        )
                    }
                }
                requests.post(WECOM_WEBHOOK_URL, json=message)
        except Exception as e:
            print(f"解析 {platform} 失败: {e}")

if __name__ == "__main__":
    monitor()
