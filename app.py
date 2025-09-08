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
    """
    요구사항: 동률인 축은 괄호로 두 글자를 붙여 표기.
    예: (EI)STJ, E(SN)TP 등
    """
    out=[]
    for ax in AXES:
        a,b = POLES[ax]
        if ax in unresolved_axes:
            out.append(f"({a}{b})")
        else:
            # 동률이 아니면 더 큰 쪽 한 글자
            lead = a if model["count"][a] >= model["count"][b] else b
            out.append(lead)
    return "".join(out)

# ----------------------- 상태 초기화 -----------------------
def reset_state():
    st.session_state.base = []
    st.session_state.base_ids = []
    st.session_state.used = {ax:set() for ax in AXES}
    st.session_state.answers = {}     # id -> {"axis","value","label","prompt","is_extra"}
    st.session_state.extra = []
    st.session_state.base_done = False
    st.session_state.result_ready = False
    st.session_state.unresolved_axes = []
    st.session_state.answer_log = []
    st.session_state.submitted = False

if "mode" not in st.session_state:
    st.session_state.mode = "general"
if "base" not in st.session_state:
    reset_state()

# ----------------------- 데이터 로드 -----------------------
try:
    with open("questions_bank.json","r",encoding="utf-8") as f:
        DATA = json.load(f)
except Exception as e:
    st.error(f"questions_bank.json 파일을 열 수 없습니다: {e}")
    st.stop()

# === 모드 라디오 (변경 시 상태 초기화) ===
def on_mode_change():
    st.session_state.mode = "general" if st.session_state._aud.startswith("일반") else "senior"
    reset_state()

st.title("Quick-MBTI : 빠르게 MBTI를 알려줍니다")

st.radio(
    "출제 범위 선택",
    options=["일반","어르신(65세 이상)"],
    index=0 if st.session_state.mode=="general" else 1,
    horizontal=True,
    key="_aud",
    on_change=on_mode_change
)

# 현재 모드에 맞는 뱅크
bank = filter_by_audience(DATA, st.session_state.mode)

# ----------------------- 기본 문항 선택 -----------------------
if not st.session_state.base:
    base, base_ids, used = [], [], {ax:set() for ax in AXES}
    for ax in AXES:
        qs = bank.get(ax, [])
        if len(qs) < 2:
            st.error(f"{ax} 축 문항이 2개 미만입니다. JSON을 보강하세요.")
            st.stop()
        qA,qB = sample_two(qs)
        q1 = dict(id=f"base_{ax}_1", axis=ax, **qA)
        q2 = dict(id=f"base_{ax}_2", axis=ax, **qB)
        base += [q1,q2]; base_ids += [q1["id"], q2["id"]]
        used[ax].add(qA["prompt"]); used[ax].add(qB["prompt"])
    random.shuffle(base)
    st.session_state.base = base
    st.session_state.base_ids = base_ids
    st.session_state.used = used

# ----------------------- 문항 렌더(번호, 선택 유지, 미응답 표시) -----------------------
def render_question(q, number):
    answered = q["id"] in st.session_state.answers
    badge = "" if answered else " <span style='color:#b91c1c'>(미응답)</span>"
    st.markdown(f"**{number}) {q['prompt']}**{badge}", unsafe_allow_html=True)

    # 라디오로 선택 유지(값/인덱스 매핑)
    key = f"sel_{q['id']}"
    options = [q["A"]["label"], q["B"]["label"]]
    default_idx = None
    prev = st.session_state.answers[q["id"]]["value"] if answered else None
    if prev == q["A"]["value"]:
        default_idx = 0
    elif prev == q["B"]["value"]:
        default_idx = 1

    choice = st.radio(
        " ",
        options=options,
        index=default_idx,
        key=key,
        horizontal=False,
        label_visibility="collapsed"
    )
    # 라디오 선택을 answers에 반영
    picked = q["A"] if choice == q["A"]["label"] else q["B"]
    st.session_state.answers[q["id"]] = {
        "axis": q["axis"],
        "value": picked["value"],
        "label": picked["label"],
        "prompt": q["prompt"],
        "is_extra": q.get("is_extra", False)
    }

st.header("문항")

# 번호 부여: 기본 8 + 추가 문항까지 연속 번호
all_qs = st.session_state.base + st.session_state.extra
for idx, q in enumerate(all_qs, start=1):
    render_question(q, idx)

# ----------------------- 평가/추가문항 로직 -----------------------
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

# “현재 제시된” 문항이 모두 응답되었는지
def all_present_answered():
    ids = [q["id"] for q in (st.session_state.base + st.session_state.extra)]
    return all(i in st.session_state.answers for i in ids)

# 1단계: 기본 8개가 모두 응답되면, 동률 축에 추가 2문항 생성
base_answered = sum(1 for i in st.session_state.base_ids if i in st.session_state.answers)
if base_answered==8 and not st.session_state.base_done:
    model=compute_mbti(list(st.session_state.answers.values()))
    added=0
    for ax in AXES:
        if need_more_after2(ax,model):
            added += append_extra(ax,2)
    st.session_state.base_done=True  # 추가 0이더라도 1단계 완료로 간주

# 2단계: 추가문항까지 답하면, 4문항 상태에서 동률인 축에 다시 2문항(최대 6)
if st.session_state.extra and all_present_answered():
    cur = list(st.session_state.answers.values())
    model = compute_mbti(cur)
    for ax in AXES:
        if model["totals"][ax]==4 and need_more_after4(ax, model):
            # 이미 6 미만인 경우에만 더 추가
            already = sum(1 for a in cur if a["axis"]==ax)
            if already < 6:
                append_extra(ax, 2)

# “지금 보이는 문항” 기준으로 모두 응답했는지 재평가
ready_for_submit = all_present_answered()

# ----------------------- 제출 버튼(조건부 활성화) -----------------------
col1, col2 = st.columns([1,3])
with col1:
    submit = st.button("제출", type="primary", disabled=not ready_for_submit)
with col2:
    # 남은 미응답 개수 표시
    ids_now = [q["id"] for q in (st.session_state.base + st.session_state.extra)]
    unanswered = [i for i in ids_now if i not in st.session_state.answers]
    if unanswered:
        st.info(f"미응답 문항: {len(unanswered)}개")

if submit:
    # 최종 평가는 제출 시점에만 수행/표시
    cur = list(st.session_state.answers.values())
    model = compute_mbti(cur)
    unresolved = []
    for ax in AXES:
        # 6문항까지 갔는데도 동률이면 판정 불가 → 괄호표기
        if unresolved_after6(ax, model):
            unresolved.append(ax)
    disp_type = format_type_with_unresolved(model, unresolved)

    # 결과 화면
    st.subheader("결과")
    st.markdown(f"<h2>{disp_type}</h2>", unsafe_allow_html=True)

    st.subheader("팁")
    for t in COMMON_TIPS: st.write(t)

    st.subheader("MBTI 의미")
    for k,v in MEANINGS: st.write(f"- **{k}**: {v}")

    st.subheader("응답 로그")
    # 시간순: 기본8 → 추가
    ordered = []
    for q in (st.session_state.base + st.session_state.extra):
        if q["id"] in st.session_state.answers:
            ordered.append(st.session_state.answers[q["id"]])
    for i,a in enumerate(ordered, start=1):
        tag="추가 " if a.get("is_extra") else ""
        st.write(f"{i}) [{a['axis']}] {tag}{a['prompt']}")
        st.write(f"   → 선택: {a['label']} ({a['value']})")

    # 제출 후에는 추가 입력 방지
    st.session_state.submitted = True
    st.stop()
