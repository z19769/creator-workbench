#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日采集与生成脚本
- 抓取抖音/全网热榜
- 用 AI 改写成贴合赛道的选题灵感(10条) + 二创角度(10条)
- 推送到 GitHub Gist
"""
import os
import json
import datetime
import requests

GH_TOKEN = os.environ.get('GH_TOKEN', '')
GIST_ID = os.environ.get('GIST_ID', 'ae7b610eadb34a38e0cd76a28bb3360f')
AI_API_KEY = os.environ.get('AI_API_KEY', '')
TRACK_KEYWORDS = os.environ.get('TRACK_KEYWORDS', '家居,家居好物,家居改造,收纳,软装,家居博主')

TODAY = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y-%m-%d')


def collect_hot():
    """抓取全网热榜（多源聚合，失败则用占位）"""
    items = []
    # 源1: 微博热搜 (公开API，不稳定，做容错)
    try:
        r = requests.get('https://tenapi.cn/v2/weibohot', timeout=8)
        if r.ok:
            data = r.json()
            for it in (data.get('data') or [])[:20]:
                items.append({'title': it.get('name', ''), 'hot': it.get('hot', '')})
    except Exception:
        pass
    # 源2: 抖音热搜
    try:
        r = requests.get('https://tenapi.cn/v2/douyinhot', timeout=8)
        if r.ok:
            data = r.json()
            for it in (data.get('data') or [])[:20]:
                items.append({'title': it.get('name', ''), 'hot': it.get('hot', '')})
    except Exception:
        pass
    # 去重
    seen = set()
    uniq = []
    for it in items:
        if it['title'] and it['title'] not in seen:
            seen.add(it['title'])
            uniq.append(it)
    return uniq[:30]


def ai_rewrite(hot_items, keywords):
    """用 AI 把热点改写成选题灵感 + 二创角度。
    若无 AI_API_KEY，则用规则模板生成占位内容。"""
    inspire = []
    viral = []

    if AI_API_KEY:
        # 调用 AI API（兼容 OpenAI 格式）
        try:
            prompt = (
                f"我是做「{keywords}」赛道的短视频创作者（家居博主）。"
                f"以下是今日热点：{json.dumps([i['title'] for i in hot_items[:10]], ensure_ascii=False)}\n"
                "请基于这些热点，结合家居博主赛道，生成：\n"
                "1. 10条选题灵感（title+tag+desc，围绕家居/收纳/软装/改造/好物分享）\n"
                "2. 10条二创角度（title+angle，可跟拍可改编的热点）\n"
                "用 JSON 返回，格式：{\"inspire\":[{\"title\",\"tag\",\"desc\"}],\"viral\":[{\"title\",\"angle\",\"hot\"}]}"
            )
            r = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers={'Authorization': f'Bearer {AI_API_KEY}'},
                json={'model': 'gpt-4o-mini', 'messages': [{'role': 'user', 'content': prompt}], 'temperature': 0.8},
                timeout=30
            )
            if r.ok:
                content = r.json()['choices'][0]['message']['content']
                # 提取 JSON
                start = content.find('{')
                end = content.rfind('}') + 1
                if start >= 0 and end > start:
                    parsed = json.loads(content[start:end])
                    inspire = parsed.get('inspire', [])[:10]
                    viral = parsed.get('viral', [])[:10]
        except Exception as e:
            print('AI 调用失败:', e)

    # 兜底：规则模板生成
    if not inspire:
        kws = [k.strip() for k in keywords.split(',') if k.strip()]
        for i, h in enumerate(hot_items[:10] if hot_items else [{'title': '今日热点'}]):
            kw = kws[i % len(kws)] if kws else '成长'
            title = h.get('title', f'今日热点{i+1}')
            inspire.append({
                'title': f'{kw}视角：{title}',
                'tag': '选题',
                'desc': f'从{kw}角度解读「{title}」，结合个人经历输出观点。'
            })
    if not viral:
        for i, h in enumerate(hot_items[:10] if hot_items else [{'title': '今日热点'}]):
            title = h.get('title', f'今日热点{i+1}')
            viral.append({
                'title': title,
                'tag': '热点',
                'hot': h.get('hot', '热度上升'),
                'angle': f'普通人视角复刻，加入反差与个人观点。'
            })

    return inspire[:10], viral[:10]


def push_gist(inspire, viral):
    """推送到 Gist"""
    payload = {
        'description': '创作工作台每日数据',
        'files': {
            'daily.json': {
                'content': json.dumps({
                    'date': TODAY,
                    'inspire': inspire,
                    'viral': viral
                }, ensure_ascii=False, indent=2)
            }
        }
    }
    r = requests.patch(
        f'https://api.github.com/gists/{GIST_ID}',
        headers={'Authorization': f'token {GH_TOKEN}', 'Accept': 'application/vnd.github+json'},
        json=payload, timeout=15
    )
    print('Gist 更新:', r.status_code)
    return r.ok


def main():
    print(f'=== {TODAY} 采集任务开始 ===')
    print('赛道关键词:', TRACK_KEYWORDS)
    hot = collect_hot()
    print(f'采集到热点 {len(hot)} 条')
    inspire, viral = ai_rewrite(hot, TRACK_KEYWORDS)
    print(f'生成灵感 {len(inspire)} 条, 二创 {len(viral)} 条')
    if GH_TOKEN:
        ok = push_gist(inspire, viral)
        print('推送 Gist:', '成功' if ok else '失败')
    else:
        print('未配置 GH_TOKEN，跳过推送')


if __name__ == '__main__':
    main()
