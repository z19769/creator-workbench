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
            p="我是家居博主，刚装修完，专注全屋定制收纳柜、柜子收纳、角落改造、家电首测方向。今日热点："+json.dumps([i["title"] for i in hot[:10]],ensure_ascii=False)+"请结合这4个方向生成10条选题灵感和10条二创角度，返回JSON:{inspire:[{title,tag,desc}],viral:[{title,angle,hot}]}"
            r=requests.post("https://api.openai.com/v1/chat/completions",headers={"Authorization":"Bearer "+AI_API_KEY},json={"model":"gpt-4o-mini","messages":[{"role":"user","content":p}],"temperature":0.8},timeout=30)
            if r.ok:
                c=r.json()["choices"][0]["message"]["content"]; s=c.find("{"); e=c.rfind("}")+1
                if s>=0 and e>s:
                    d=json.loads(c[s:e]); inspire=d.get("inspire",[])[:10]; viral=d.get("viral",[])[:10]
        except Exception as ex: print("AI err:",ex)
    if not inspire:
        inspire=gen_inspire()
    if not viral:
        viral=gen_viral(hot)
    return inspire[:10], viral[:10]

def gen_inspire():
    pool=[
        {"title":"全屋定制收纳柜入坑指南：这些坑千万别踩","tag":"全屋定制","desc":"分享全屋定制收纳柜的常见坑和避坑方法"},
        {"title":"入墙收纳柜 vs 独立柜，到底怎么选","tag":"全屋定制","desc":"入墙柜和独立柜的优缺点对比，帮粉丝避坑"},
        {"title":"衣帽间定制柜子怎么做最实用","tag":"柜子收纳","desc":"衣帽间定制柜的尺寸、层板分配和细节设计"},
        {"title":"厨房抽屉收纳神器，拿来就能用","tag":"柜子收纳","desc":"厨房抽屉的收纳分区和常用物品归纳方案"},
        {"title":"玄关改造记：1平米角落变身小咖啡角","tag":"角落改造","desc":"玄关/走廊角落的改造思路和实操过程"},
        {"title":"阳台角落改造：从堆杂物到污心小苑","tag":"角落改造","desc":"阳台角落的改造方案和绿植搜索建议"},
        {"title":"洗衣机首次使用开箱测评","tag":"家电首测","desc":"新买洗衣机的开箱、安装、首次使用全过程"},
        {"title":"扫地机首测：入住新房第一台智能家电","tag":"家电首测","desc":"扫地机的开箱体验、实际清洁效果和使用感受"},
        {"title":"全屋定制柜子尺寸怎么算才不后悔","tag":"全屋定制","desc":"定制柜子前如何正确测量尺寸和规划布局"},
        {"title":"卧室衣柜收纳改造，拆了重做后太香了","tag":"柜子收纳","desc":"旧衣柜改造或重做的收纳方案，前后对比"},
        {"title":"卫生间角落改造：拉箱变身洗护区","tag":"角落改造","desc":"卫生间角落的收纳改造和空间利用"},
        {"title":"烤箱首次用，新手烘焙入门指南","tag":"家电首测","desc":"烤箱开箱、首次使用、第一次烘焙的完整体验"},
        {"title":"定制柜子板材怎么选：颗粒板 vs 克能板","tag":"全屋定制","desc":"定制柜子常见板材的优缺点对比和选购建议"},
        {"title":"床底收纳柜，小户型必须安排","tag":"柜子收纳","desc":"床底收纳柜的定制方案和收纳技巧"},
        {"title":"楼梯下角落改造，各种奇葩角落利用","tag":"角落改造","desc":"楼梯下、过道、梅花角等鸡肋角落的改造方案"},
        {"title":"新风柜首测：这台柜子插电后太香了","tag":"家电首测","desc":"新风柜的开箱、安装、使用感受和避坑建议"},
        {"title":"定制书柜怎么做才能装下所有书","tag":"全屋定制","desc":"书柜定制的尺寸规划、层板设计和收纳技巧"},
        {"title":"厨房调味柜收纳改造，台面终于不乱了","tag":"柜子收纳","desc":"厨房调味柜/料理柜的收纳改造方案"},
        {"title":"电视墙背景墙角落改造，客厅颜值翻倍","tag":"角落改造","desc":"电视墙周边角落的装饰改造和收纳方案"},
        {"title":"洗碗机首次用，入户必看使用教程","tag":"家电首测","desc":"洗碗机开箱安装、首次使用、日常维护全攻略"},
    ]
    random.shuffle(pool)
    return pool[:10]

def gen_viral(hot):
    pool=[
        {"title":"全屋定制收纳柜入坑总结","tag":"热点","hot":"热度上升","angle":"短视频抢答式分享避坑经验"},
        {"title":"定制柜子前后对比","tag":"热点","hot":"热度上升","angle":"改造前后反差视频"},
        {"title":"角落改造前后对比","tag":"热点","hot":"热度上升","angle":"改造前后对比+改造过程记录"},
        {"title":"家电开箱测评","tag":"热点","hot":"热度上升","angle":"沉浸式开箱ASMR+首次使用体验"},
        {"title":"全屋定制收纳柜设计方案","tag":"热点","hot":"热度上升","angle":"详细展示各个空间的柜子设计"},
        {"title":"小户型柜子收纳技巧","tag":"热点","hot":"热度上升","angle":"小户型收纳技巧集锡"},
        {"title":"角落改造创意方案","tag":"热点","hot":"热度上升","angle":"鸡肋角落改造创意展示"},
        {"title":"家电使用技巧","tag":"热点","hot":"热度上升","angle":"家电使用小技巧合集"},
        {"title":"衣帽间收纳改造","tag":"热点","hot":"热度上升","angle":"衣帽间收纳改造全过程"},
        {"title":"厨房收纳改造","tag":"热点","hot":"热度上升","angle":"厨房收纳改造记录"},
    ]
    if hot:
        for h in hot[:5]:
            pool.append({"title":h.get("title","热点"),"tag":"热点","hot":h.get("hot","热度上升"),"angle":"家居视角解读"})
    random.shuffle(pool)
    return pool[:10]

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
