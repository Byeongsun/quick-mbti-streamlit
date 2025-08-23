import json, random
import streamlit as st

# ----------------------- 기본 셋업 -----------------------
st.set_page_config(page_title="Quick-MBTI : 빠르게 MBTI를 알려줍니다", layout="centered")

AXES = ["EI", "SN", "TF", "JP"]
POLES = {
    "EI": ("E", "I"),
    "SN": ("S", "N"),
    "TF": ("T", "F"),
    "JP": ("J", "P"),
}

COMMON_TIPS = [
    "생활: 에너지 패턴을 이해하고 휴식 규칙을 마련하세요.",
    "일: 강점 역할을 명확히 하고 협업 방식을 합의하세요.",
    "인간관계: 기대·경계를 공유하고 피드백을 정례화하세요.",
    "학습: 목표를 단계로 나눠 진행률을 가시화하세요.",
]

MEANINGS = [
    ("E (Extraversion, 외향)", "사람들과의 교류·활동에서 에너지를 얻고, 외부 자극에 적극적으로 반응함"),
    ("I (Introversion, 내향)", "고요한 시간과 혼자만의 몰입에서 에너지를 회복하고, 신중한 내적 성찰을 선호함"),
    ("S (Sensing, 감각)", "현재의 구체적 사실·경험을 중시하고, 실용적이고 현실적인 정보에 신뢰를 둠"),
    ("N (Intuition, 직관)", "패턴·가능성과 같은 추상적 연결을 중시하고, 미래지향적 아이디어를 선호함"),
    ("T (Thinking, 사고)", "논리·일관성·원칙에 따라 판단하고, 공정한 기준을 우선함"),
    ("F (Feeling, 감정)", "사람·가치·관계의 조화를 중시하고, 공감과 배려를 판단에 반영함"),
    ("J (Judging, 판단)", "계획적·체계적으로 일을 정리하고, 마감과 규칙을 선호함"),
    ("P (Perceiving, 인식)", "상황에 맞춰 유연하게 적응하며, 열린 선택지를 유지하는 것을 선호함"),
]

# ----------------------- 유틸 -----------------------
def filter_by_audience(bank, aud):
    out = {ax: [] for ax in AXES}
    for ax in AXES:
        for q in bank.get(ax, []):
            tag = q.get("audience")
            if not tag or tag == "both" or tag == aud:
                out[ax].append(q)
    return out

def sample_two(lst):
    idx = list(range(len(lst)))
    random.shuffle(idx)
    if len(idx) >= 2:
        return [lst[idx[0]], lst[idx[1]]]
    elif len(idx) == 1:
        return [lst[idx[0]], lst[idx[0]]]
    return []

def compute_mbti(ans_list):
    count = dict(E=0,I=0,S=0,N=0,T=0,F=0,J=0,P=0)
    totals = dict(EI=0,SN=0,TF=0,JP=0)
    for a in ans_list:
        v = a["value"]
        if v in count:
            count[v] += 1
        totals[a["axis"]] += 1
    diff = {
        "EI": abs(count["E"]-count["I"]),
        "SN": abs(count["S"]-count["N"]),
        "TF": abs(count["T"]-count["F"]),
        "JP": abs(count["J"]-count["P"]),
    }
    def pick(a,b,default):
        return a if count[a] > count[b] else b if count[a] < count[b] else default
    typ = pick("E","I","E")+pick("S","N","S")+pick("T","F","T")+pick("J","P","J")
    return {"type":typ, "count":count, "totals":totals, "diff":diff}

def need_more_after2(axis, m): return m["totals"][axis]==2 and m["diff"][axis]==0
def need_more_after4(axis, m): return m["totals"][axis]==4 and m["diff"][axis]==0
def unresolved_after6(axis, m): return m["totals"][axis]==6 and m["diff"][axis]==0

def format_type_with_unresolved(model, unresolved_axes):
    lead = {
        "EI": "E" if model["count"]["E"]>=model["count"]["I"] else "I",
        "SN": "S" if model["count"]["S"]>=model["count"]["N"] else "N",
        "TF": "T" if model["count"]["T"]>=model["count"]["F"] else "F",
        "JP": "J" if model["count"]["J"]>=model["count"]["P"] else "P",
    }
    out=[]
    for ax in AXES:
        a,b = POLES[ax]
        out.append(f"({a}/{b})" if ax in unresolved_axes else lead[ax])
    return "".join(out)

# ----------------------- 상태 초기화 -----------------------
def reset_state():
    st.session_state.base = []
    st.session_state.base_ids = []
    st.session_state.used = {ax:set() for ax in AXES}
    st.session_state.answers = {}
    st.session_state.extra = []
    st.session_state.base_done = False
    st.session_state.result_ready = False
    st.session_state.unresolved_axes = []
    st.session_state.answer_log = []

if "base" not in st.session_state:
    reset_state()

# ----------------------- 데이터 로드 -----------------------
try:
    with open("questions_bank.json","r",encoding="utf-8") as f:
        DATA = json.load(f)
except Exception as e:
    st.error(f"questions_bank.json 파일을 열 수 없습니다: {e}")
    st.stop()

# 출제 범위 선택
aud = st.radio("출제 범위 선택", options=["일반","어르신(65세 이상)"], index=0, horizontal=True)
mode = "general" if aud.startswith("일반") else "senior"
bank = filter_by_audience(DATA, mode)

# ----------------------- 기본 문항 선택 -----------------------
if not st.session_state.base:
    base, base_ids, used = [], [], {ax:set() for ax in AXES}
    for ax in AXES:
        qs = bank.get(ax, [])
        qA,qB = sample_two(qs)
        q1 = dict(id=f"base_{ax}_1", axis=ax, **qA)
        q2 = dict(id=f"base_{ax}_2", axis=ax, **qB)
        base += [q1,q2]; base_ids += [q1["id"], q2["id"]]
        used[ax].add(qA["prompt"]); used[ax].add(qB["prompt"])
    random.shuffle(base)
    st.session_state.base = base
    st.session_state.base_ids = base_ids
    st.session_state.used = used

# ----------------------- 문항 렌더 -----------------------
st.header("문항")
for q in st.session_state.base + st.session_state.extra:
    st.markdown(f"**{q['prompt']}**")
    c1,c2 = st.columns(2)
    if c1.button(f"① {q['A']['label']}", key=f"{q['id']}_A"):
        st.session_state.answers[q["id"]] = {"axis":q["axis"],"value":q["A"]["value"],"label":q["A"]["label"],"prompt":q["prompt"],"is_extra":q.get("is_extra",False)}
    if c2.button(f"② {q['B']['label']}", key=f"{q['id']}_B"):
        st.session_state.answers[q["id"]] = {"axis":q["axis"],"value":q["B"]["value"],"label":q["B"]["label"],"prompt":q["prompt"],"is_extra":q.get("is_extra",False)}

# ----------------------- 평가 로직 -----------------------
base_answered = sum(1 for i in st.session_state.base_ids if i in st.session_state.answers)

def append_extra(axis, count=2):
    pool = bank.get(axis, [])
    remain = [q for q in pool if q["prompt"] not in st.session_state.used[axis]]
    random.shuffle(remain)
    added=0
    for it in remain:
        if added>=count: break
        qid=f"ex_{axis}_{random.randint(1,10**9)}"
        q = dict(id=qid, axis=axis, **it); q["is_extra"]=True
        st.session_state.extra.append(q)
        st.session_state.used[axis].add(it["prompt"])
        added+=1
    return added

# 기본 8 다 답하면 tie 축에 추가
if base_answered==8 and not st.session_state.base_done:
    model=compute_mbti(list(st.session_state.answers.values()))
    for ax in AXES:
        if need_more_after2(ax,model):
            append_extra(ax,2)
    st.session_state.base_done=True

# 추가문항 다 답했는지
all_ids = st.session_state.base_ids+[q["id"] for q in st.session_state.extra]
all_answered = all(i in st.session_state.answers for i in all_ids)

if base_answered==8 and all_answered:
    cur=list(st.session_state.answers.values())
    model=compute_mbti(cur)
    unresolved=[ax for ax in AXES if unresolved_after6(ax,model)]
    disp_type=format_type_with_unresolved(model, unresolved)
    st.subheader("결과")
    st.markdown(f"<h2>{disp_type}</h2>", unsafe_allow_html=True)

    st.subheader("팁")
    for t in COMMON_TIPS: st.write(t)

    st.subheader("MBTI 의미")
    for k,v in MEANINGS: st.write(f"- **{k}**: {v}")

    st.subheader("응답 로그")
    for i,a in enumerate(cur, start=1):
        tag="추가 " if a.get("is_extra") else ""
        st.write(f"{i}) [{a['axis']}] {tag}{a['prompt']}")
        st.write(f"   → 선택: {a['label']} ({a['value']})")

    st.stop()
