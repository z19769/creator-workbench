#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日采集与生成脚本（家居博主赛道）
- 抓取抖音/全网热榜
- 用 AI 改写成贴合赛道的选题灵感(10条) + 二创角度(10条)
- 推送到 GitHub Gist + 仓库 daily.json（同域访问不被墙）
"""
import os
import json
import base64
import datetime
import requests

GH_TOKEN = os.environ.get('GH_TOKEN', '')
GIST_ID = os.environ.get('GIST_ID', 'ae7b610eadb34a38e0cd76a28bb3360f')
AI_API_KEY = os.environ.get('AI_API_KEY', '')
TRACK_KEYWORDS = os.environ.get('TRACK_KEYWORDS', '家居,家居好物,家居改造,收纳,软装,家居博主')
REPO = 'z19769/creator-workbench'

TODAY = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y-%m-%d')


def collect_hot():
    """抓取全网热榜（多源聚合，失败则用占位）"""
    items = []
    sources = [
        ('https://tenapi.cn/v2/weibohot', 'name', 'hot'),
        ('https://tenapi.cn/v2/douyinhot', 'name', 'hot'),
    ]
    for url, name_key, hot_key in sources:
        try:
            r = requests.get(url, timeout=8)
            if r.ok:
                data = r.json()
                for it in (data.get('data') or [])[:20]:
                    items.append({'title': it.get(name_key, ''), 'hot': str(it.get(hot_key, ''))})
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
    """用 AI 把热点改写成选题灵感 + 二创角度。无 AI_API_KEY 时用规则模板。"""
    inspire = []
    viral = []

    if AI_API_KEY:
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
        pool = hot_items[:10] if hot_items else [{'title': f'家居热点{i+1}'} for i in range(10)]
        for i, h in enumerate(pool):
            kw = kws[i % len(kws)] if kws else '家居'
            title = h.get('title', f'今日热点{i+1}')
            inspire.append({
                'title': f'{kw}视角：{title}',
                'tag': '选题',
                'desc': f'从{kw}角度解读「{title}」，结合个人经历输出观点。'
            })
    if not viral:
        pool = hot_items[:10] if hot_items else [{'title': f'家居热点{i+1}'} for i in range(10)]
        for i, h in enumerate(pool):
            title = h.get('title', f'今日热点{i+1}')
            viral.append({
                'title': title,
                'tag': '热点',
                'hot': h.get('hot', '热度上升'),
                'angle': '普通人视角复刻，加入反差与个人观点。'
            })

    return inspire[:10], viral[:10]


def make_payload(inspire, viral):
    return json.dumps({'date': TODAY, 'inspire': inspire, 'viral': viral}, ensure_ascii=False, indent=2)


def push_gist(content):
    """推送到 Gist"""
    if not GH_TOKEN:
        print('未配置 GH_TOKEN，跳过 Gist')
        return False
    payload = {
        'description': '创作工作台每日数据',
        'files': {'daily.json': {'content': content}}
    }
    r = requests.patch(
        f'https://api.github.com/gists/{GIST_ID}',
        headers={'Authorization': f'token {GH_TOKEN}', 'Accept': 'application/vnd.github+json'},
        json=payload, timeout=15
    )
    print('Gist 更新:', r.status_code)
    return r.ok


def push_repo_json(content):
    """更新仓库里的 daily.json（同域访问，手机不被墙）"""
    if not GH_TOKEN:
        print('未配置 GH_TOKEN，跳过仓库更新')
        return False
    headers = {'Authorization': f'token {GH_TOKEN}', 'Accept': 'application/vnd.github+json'}
    # 获取现有文件 sha（若存在）
    sha = None
    try:
        r = requests.get(f'https://api.github.com/repos/{REPO}/contents/daily.json', headers=headers, timeout=10)
        if r.ok:
            sha = r.json().get('sha')
    except Exception:
        pass
    body = {'message': f'chore: 更新每日数据 {TODAY}', 'content': base64.b64encode(content.encode()).decode(), 'branch': 'main'}
    if sha:
        body['sha'] = sha
    r = requests.put(f'https://api.github.com/repos/{REPO}/contents/daily.json', headers=headers, json=body, timeout=15)
    print('仓库 daily.json 更新:', r.status_code)
    return r.ok


def main():
    print(f'=== {TODAY} 采集任务开始 ===')
    print('赛道关键词:', TRACK_KEYWORDS)
    hot = collect_hot()
    print(f'采集到热点 {len(hot)} 条')
    inspire, viral = ai_rewrite(hot, TRACK_KEYWORDS)
    print(f'生成灵感 {len(inspire)} 条, 二创 {len(viral)} 条')
    content = make_payload(inspire, viral)
    push_gist(content)
    push_repo_json(content)
    print('=== 采集任务完成 ===')


if __name__ == '__main__':
    main()
