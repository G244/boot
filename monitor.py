import requests
import json
import time

# --- 配置区 ---
# 填写你企业微信机器人的 Webhook 地址
WECOM_WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=52b3dac7-fbdd-4f79-85c9-cec274b6151d"

# 监控的目标 URL（示例：苹果开发者新闻）
TARGET_URLS = {
    "Apple Developer News": "https://developer.apple.com/news/rss/news.rss",
    "Google Play Policy": "https://android-developers.googleblog.com/feeds/posts/default"
}

def send_to_wecom(content):
    headers = {"Content-Type": "application/json"}
    data = {
        "msgtype": "markdown",
        "markdown": {
            "content": f"## 📢 外媒/政策更新提醒\n> 更新来源：{content['source']}\n\n**内容摘要**: {content['title']}\n\n[点击查看详情]({content['link']})"
        }
    }
    requests.post(WECOM_WEBHOOK_URL, json=data, headers=headers)

def monitor():
    # 实际生产中这里会增加“对比旧记录”的逻辑，此处为核心推送逻辑演示
    for name, url in TARGET_URLS.items():
        # 这里模拟抓取最新一条，实际建议配合 RSS 解析库
        print(f"Checking {name}...")
        # 演示推送
        sample_update = {
            "source": name,
            "title": "检测到政策页面有变动，请专员及时排查。",
            "link": url
        }
        send_to_wecom(sample_update)

if __name__ == "__main__":
    monitor()
