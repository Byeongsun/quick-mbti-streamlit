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

def compute_counts(answer_list):
    counts = dict(E=0,I=0,S=0,N=0,T=0,F=0,J=0,P=0)
    totals = dict(EI=0,SN=0,TF=0,JP=0)
    for a in answer_list:
        v = a["value"]
        if v in counts: counts[v]+=1
        totals[a["axis"]] += 1
    return counts, totals

def format_type(tokens_by_axis):
    return "".join(tokens_by_axis[ax] for ax in AXES)

def percent(a, b):
    tot = a + b
    if tot == 0: return (0, 0)
    pa = int(round(a * 100.0 / tot))
    pb = 100 - pa
    return (pa, pb)

# ----------------------- 상태 초기화 -----------------------
def reset_state():
    st.session_state.base = []
    st.session_state.base_ids = []
    st.session_state.used = {ax:set() for ax in AXES}
    st.session_state.answers = {}
    st.session_state.extra = []
    st.session_state.result_ready = False
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

# === 모드 라디오 ===
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

# 🔑 현재 모드에 맞는 문항 bank
bank = filter_by_audience(DATA, st.session_state.mode)

# ----------------------- 기본 8문항 선정 -----------------------
if not st.session_state.base:
    base, base_ids, used = [], [], {ax:set() for ax in AXES}
    for ax in AXES:
        qs = bank.get(ax, [])
        if len(qs) < 2:
            st.error(f"{ax} 축 문항이 2개 미만입니다. JSON을 보강하세요.")
            st.stop()
        qA, qB = sample_two(qs)
        q1 = dict(id=f"base_{ax}_1", axis=ax, **qA)
        q2 = dict(id=f"base_{ax}_2", axis=ax, **qB)
        base += [q1, q2]; base_ids += [q1["id"], q2["id"]]
        used[ax].add(qA["prompt"]); used[ax].add(qB["prompt"])
    random.shuffle(base)
    st.session_state.base = base
    st.session_state.base_ids = base_ids
    st.session_state.used = used

# ----------------------- 문항 렌더 -----------------------
def render_question(q, number):
    key = f"sel_{q['id']}"
    options = [q["A"]["label"], q["B"]["label"]]

    prev_val = st.session_state.answers[q["id"]]["value"] if q["id"] in st.session_state.answers else None
    default_idx = 0 if prev_val == q["A"]["value"] else 1 if prev_val == q["B"]["value"] else None

    choice = st.radio(
        f"{number}) {q['prompt']}",
        options=options,
        index=default_idx,
        key=key,
        horizontal=False
    )

    picked = None
    if choice == q["A"]["label"]:
        picked = q["A"]
    elif choice == q["B"]["label"]:
        picked = q["B"]

    if picked:
        st.session_state.answers[q["id"]] = {
            "axis": q["axis"],
            "value": picked["value"],
            "label": picked["label"],
            "prompt": q["prompt"],
            "is_extra": q.get("is_extra", False)
        }
    elif q["id"] in st.session_state.answers:
        del st.session_state.answers[q["id"]]

# ----------------------- 동률 검사 -----------------------
def add_tiebreaker_if_needed(ax):
    a, b = POLES[ax]
    answers = [v for v in st.session_state.answers.values() if v["axis"]==ax]
    if len(answers) == 2:  # 기본 2개 다 풀린 경우
        ca = sum(1 for v in answers if v["value"]==a)
        cb = sum(1 for v in answers if v["value"]==b)
        if ca == cb:
            if not any(q.get("is_extra") and q["axis"]==ax for q in st.session_state.extra):
                pool = bank.get(ax, [])
                remain = [q for q in pool if q["prompt"] not in st.session_state.used[ax]]
                if not remain:
                    st.warning(f"{ax} 축에 추가 문항이 없습니다. JSON을 보강하세요.")
                    return
                it = random.choice(remain)
                qid = f"ex_{ax}_{random.randint(1,10**9)}"
                st.session_state.extra.append({**it, "id":qid, "axis":ax, "is_extra":True})
                st.session_state.used[ax].add(it["prompt"])

# ----------------------- 문항 출력 -----------------------
st.header("문항")
all_qs = st.session_state.base + st.session_state.extra
for idx, q in enumerate(all_qs, start=1):
    render_question(q, idx)

# 축별로 tie 여부 확인 → 즉시 추가문항 생성
for ax in AXES:
    add_tiebreaker_if_needed(ax)

# ----------------------- 제출 버튼 -----------------------
def all_present_answered():
    ids = [q["id"] for q in (st.session_state.base + st.session_state.extra)]
    return all(i in st.session_state.answers for i in ids)

unanswered_count = len([q for q in (st.session_state.base + st.session_state.extra) if q["id"] not in st.session_state.answers])
st.info(f"남은 미응답 문항: {unanswered_count}개")

ready_for_submit = all_present_answered()
submit = st.button("제출", type="primary", disabled=not ready_for_submit)

# ----------------------- 제출 처리 -----------------------
if submit:
    cur = [st.session_state.answers[q["id"]] for q in (st.session_state.base + st.session_state.extra)]
    counts, totals = compute_counts(cur)
    tokens, per_axis_percent = {}, {}

    for ax in AXES:
        a, b = POLES[ax]
        if counts[a] == counts[b]:
            tokens[ax] = f"({a}{b})"
        else:
            tokens[ax] = a if counts[a] > counts[b] else b
        pa, pb = percent(counts[a], counts[b])
        per_axis_percent[ax] = (pa, pb, totals[ax])

    disp_type = format_type(tokens)

    st.subheader("결과")
    st.markdown(f"<h2>{disp_type}</h2>", unsafe_allow_html=True)

    st.markdown("### 축별 선택 비율")
    for ax in AXES:
        a, b = POLES[ax]
        pa, pb, tot = per_axis_percent[ax]
        st.write(f"- {ax}: {a} {pa}% / {b} {pb}%  (총 {tot}문항)")

    st.subheader("팁")
    for t in COMMON_TIPS:
        st.write(t)

    st.subheader("MBTI 의미")
    for k,v in MEANINGS:
        st.write(f"- **{k}**: {v}")

    st.subheader("응답 로그")
    for i,a in enumerate(cur, start=1):
        tag="추가 " if a.get("is_extra") else ""
        st.write(f"{i}) [{a['axis']}] {tag}{a['prompt']}")
        st.write(f"   → 선택: {a['label']} ({a['value']})")

    st.session_state.result_ready = True
    st.session_state.submitted = True
    st.stop()
