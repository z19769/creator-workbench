#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, json, base64, datetime, requests, random

GH_TOKEN = os.environ.get("GH_TOKEN", "")
GIST_ID = os.environ.get("GIST_ID", "ae7b610eadb34a38e0cd76a28bb3360f")
AI_API_KEY = os.environ.get("AI_API_KEY", "")
TRACK_KEYWORDS = os.environ.get("TRACK_KEYWORDS", "家居,家居好物,家居改造,收纳,软装,家居博主")
REPO = "z19769/creator-workbench"
TODAY = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y-%m-%d")

def collect_hot():
    items = []
    sources = [("https://tenapi.cn/v2/weibohot","name","hot"),("https://tenapi.cn/v2/douyinhot","name","hot")]
    for url,nk,hk in sources:
        try:
            r=requests.get(url,timeout=8)
            if r.ok:
                for it in (r.json().get("data") or [])[:20]:
                    items.append({"title":it.get(nk,""),"hot":str(it.get(hk,""))})
        except: pass
    seen=set(); uniq=[]
    for it in items:
        if it["title"] and it["title"] not in seen:
            seen.add(it["title"]); uniq.append(it)
    return uniq[:30]

def ai_rewrite(hot, kw):
    inspire=[]; viral=[]
    if AI_API_KEY:
        try:
            p="我是家居博主赛道创作者。今日热点："+json.dumps([i["title"] for i in hot[:10]],ensure_ascii=False)+"请生成10条选题灵感和10条二创角度，返回JSON:{inspire:[{title,tag,desc}],viral:[{title,angle,hot}]}"
            r=requests.post("https://api.openai.com/v1/chat/completions",headers={"Authorization":"Bearer "+AI_API_KEY},json={"model":"gpt-4o-mini","messages":[{"role":"user","content":p}],"temperature":0.8},timeout=30)
            if r.ok:
                c=r.json()["choices"][0]["message"]["content"]; s=c.find("{"); e=c.rfind("}")+1
                if s>=0 and e>s:
                    d=json.loads(c[s:e]); inspire=d.get("inspire",[])[:10]; viral=d.get("viral",[])[:10]
        except Exception as ex: print("AI err:",ex)
    if not inspire:
        kws=[k.strip() for k in kw.split(",") if k.strip()]
        pool=hot[:10] if hot else [{"title":"家居热点"+str(i+1)} for i in range(10)]
        for i,h in enumerate(pool):
            kw1=kws[i%len(kws)] if kws else "家居"
            t=h.get("title","今日热点"+str(i+1))
            inspire.append({"title":kw1+"视角："+t,"tag":"选题","desc":"从"+kw1+"角度解读「"+t+"」"})
    if not viral:
        pool=hot[:10] if hot else [{"title":"家居热点"+str(i+1)} for i in range(10)]
        for i,h in enumerate(pool):
            t=h.get("title","今日热点"+str(i+1))
            viral.append({"title":t,"tag":"热点","hot":h.get("hot","热度上升"),"angle":"普通人视角复刻"})
    return inspire[:10], viral[:10]

def gen_teardown(kw):
    return [
        {"title":"沉浸式回家vlog","hook":"开门暖光亮起ASMR3秒治愈","structure":"钩子→空间→好物→收尾","highlights":"第一人称+柔光","reuse":"回家仪式感模板"},
        {"title":"500元爆改出租屋","hook":"改造前昏暗制造反差","structure":"痛点→清单→过程→对比","highlights":"前后对比强烈","reuse":"低成本改造模板"},
        {"title":"小户型收纳TOP10","hook":"住了5年越住越大","structure":"痛点→10件→对比→总结","highlights":"场景化展示","reuse":"TOP10模板"},
        {"title":"独居女生安全感好物","hook":"一个人住这些救了我","structure":"情感→场景→好物→对比","highlights":"情绪价值高","reuse":"独居好物模板"},
        {"title":"租房改造前后对比","hook":"房东不让动引发好奇","structure":"痛点→限制→方案→对比","highlights":"强调不破坏原装","reuse":"无损改造模板"}
    ]

def gen_quote():
    pool = [
        {"text":"你只管努力，剩下的交给时间","source":"网络"},
        {"text":"明天的你会感谢今天拼命的自己","source":"网络"},
        {"text":"家是平凡生活里的光，是每一天的期待","source":"家居博主金句"},
        {"text":"不负时光，不负自己，人生没有白走的路","source":"网络"},
        {"text":"将来的你一定会感谢现在咬牙坚持的自己","source":"网络"},
        {"text":"生活的美好从不是等来的，而是一点一滴营造的","source":"家居博主金句"},
        {"text":"人生没有重来，但可以重新出发","source":"网络"},
        {"text":"每个认真生活的人都值得被认真对待","source":"网络"},
        {"text":"世界很大，但家是唯一的底色","source":"家居博主金句"},
        {"text":"你不负光芒，光芒自会为你亮","source":"网络"},
        {"text":"努力不是为了超越别人，而是为了遇见更好的自己","source":"网络"},
        {"text":"把每一天过成作品，而不是任务","source":"网络"},
        {"text":"生活的质感从不在于价格，而在于用心","source":"家居博主金句"},
        {"text":"别让明天的烦恼浪费今天的美好","source":"网络"},
        {"text":"坚持是最难的，但也是最值得的","source":"网络"},
        {"text":"你的生活就是你的作品，认真的人最美","source":"网络"},
        {"text":"所有的美好都是从一点一滴的累积开始的","source":"家居博主金句"},
        {"text":"人生最大的成就就是让自己活成想要的样子","source":"网络"},
        {"text":"不管多难的日子，请记得给自己一束光","source":"网络"},
        {"text":"生活不是等风晋，而是自己去造风","source":"家居博主金句"},
    ]
    random.shuffle(pool)
    return pool[:10]

def gen_english():
    pool = [
        {"text":"practice makes perfect","note":"熟能生巧 — 反复练习是精通的关键"},
        {"text":"home is where the heart is","note":"心在哪里，家就在哪里 — 家的温暖在于心"},
        {"text":"less is more","note":"少即是多 — 极简生活哲学"},
        {"text":"make yourself at home","note":"别客气，当自己家 — 待客常用语"},
        {"text":"home sweet home","note":"金窝银窝不如自己的草窝 — 表达对家的思念"},
        {"text":"a place for everything and everything in its place","note":"物各其位 — 收纳整理的经典格言"},
        {"text":"keep going, never give up","note":"继续前进，永不放弃 — 励志常用句"},
        {"text":"every day is a new beginning","note":"每天都是新的开始 — 積极生活态度"},
        {"text":"slow and steady wins the race","note":"稳打稳赢得比赛 — 坚持的力量"},
        {"text":"the best is yet to come","note":"最好的还在后头 — 充满希望的话"},
        {"text":"dream big, start small","note":"梦想要大，从小做起 — 行动力格言"},
        {"text":"where there is a will, there is a way","note":"有志者事竟成 — 经典谚语"},
        {"text":"be the change you wish to see","note":"成为你想看到的改变 — 自我成长金句"},
        {"text":"light up your life","note":"点亮你的生活 — 家居照明相关"},
        {"text":"cozy and warm","note":"温馆舒适 — 家居常用形容词"},
        {"text":"declutter your space, declutter your mind","note":"整理空间，清理心灵 — 收纳的哲学"},
        {"text":"stay positive, work hard, make it happen","note":"保持积极，努力工作，让它成真 — 励志短句"},
        {"text":"detail makes difference","note":"细节决定成败 — 家居设计格言"},
        {"text":"a tidy home, a tidy mind","note":"整洁的家，清晰的心智 — 收纳理念"},
        {"text":"turn your house into a home","note":"把房子变成家 — 软装理念"},
    ]
    random.shuffle(pool)
    return pool[:10]

def make_payload(ins,vir,td,qe,en):
    return json.dumps({"date":TODAY,"inspire":ins,"viral":vir,"teardown":td,"quote":qe,"english":en},ensure_ascii=False,indent=2)

def push_gist(c):
    if not GH_TOKEN: return False
    r=requests.patch("https://api.github.com/gists/"+GIST_ID,headers={"Authorization":"token "+GH_TOKEN},json={"files":{"daily.json":{"content":c}}},timeout=15)
    print("Gist:",r.status_code); return r.ok

def push_repo(c):
    if not GH_TOKEN: return False
    h={"Authorization":"token "+GH_TOKEN}
    sha=None
    try:
        r=requests.get("https://api.github.com/repos/"+REPO+"/contents/daily.json",headers=h,timeout=10)
        if r.ok: sha=r.json().get("sha")
    except: pass
    b={"message":"update "+TODAY,"content":base64.b64encode(c.encode()).decode(),"branch":"main"}
    if sha: b["sha"]=sha
    r=requests.put("https://api.github.com/repos/"+REPO+"/contents/daily.json",headers=h,json=b,timeout=15)
    print("repo:",r.status_code); return r.ok

def main():
    print("=== "+TODAY+" ===")
    hot=collect_hot(); print("hot:",len(hot))
    ins,vir=ai_rewrite(hot,TRACK_KEYWORDS)
    td=gen_teardown(TRACK_KEYWORDS)
    qe=gen_quote()
    en=gen_english()
    print("ins:",len(ins),"vir:",len(vir),"td:",len(td),"quote:",len(qe),"english:",len(en))
    c=make_payload(ins,vir,td,qe,en)
    push_gist(c); push_repo(c)
    print("=== done ===")

if __name__=="__main__": main()
