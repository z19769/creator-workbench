#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, json, base64, datetime, requests

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

def make_payload(ins,vir,td):
    return json.dumps({"date":TODAY,"inspire":ins,"viral":vir,"teardown":td},ensure_ascii=False,indent=2)

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
    print("ins:",len(ins),"vir:",len(vir),"td:",len(td))
    c=make_payload(ins,vir,td)
    push_gist(c); push_repo(c)
    print("=== done ===")

if __name__=="__main__": main()
