import json, random, io, urllib.request
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

# ----------------------- 임베드 폴백(간단 샘플) -----------------------
EMBEDDED_BANK = {
    "EI": [
        {"audience":"general","prompt":"배우자가 저녁 산책 겸 근처 카페를 가자고 합니다.",
         "A":{"label":"바로 좋다고 하고 나간다.","value":"E"},
         "B":{"label":"집에서 쉬고 싶어 다음으로 미룬다.","value":"I"}},
        {"audience":"senior","prompt":"손주가 저녁에 같이 산책하자고 합니다.",
         "A":{"label":"밖에서 사람들 보며 이야기 나누는 게 즐겁다.","value":"E"},
         "B":{"label":"오늘은 조용히 쉬고 싶다.","value":"I"}},
    ],
    "SN": [
        {"audience":"general","prompt":"가족 여행을 계획합니다.",
         "A":{"label":"세부 일정·숙소·교통을 꼼꼼히 확정한다.","value":"S"},
         "B":{"label":"큰 그림을 먼저 그리고 현지에서 유연하게 정한다.","value":"N"}},
        {"audience":"senior","prompt":"정기 검진 예약을 잡아야 합니다.",
         "A":{"label":"병원·이동·준비사항을 구체적으로 확인해 확정한다.","value":"S"},
         "B":{"label":"생활 흐름을 보며 여유 있는 날로 생각해 둔다.","value":"N"}},
    ],
    "TF": [
        {"audience":"general","prompt":"배우자가 건강검진 결과에 대해 걱정합니다.",
         "A":{"label":"수치를 분석하고 다음 조치를 함께 정한다.","value":"T"},
         "B":{"label":"불안을 공감하고 마음을 안정시킨다.","value":"F"}},
        {"audience":"senior","prompt":"이웃과 소음 문제로 다툼이 있었습니다.",
         "A":{"label":"사실관계를 정리해 해결 절차를 제안한다.","value":"T"},
         "B":{"label":"감정을 달래며 관계가 상하지 않게 조율한다.","value":"F"}},
    ],
    "JP": [
        {"audience":"general","prompt":"가족 여행 날 아침 예상치 못한 비가 옵니다.",
         "A":{"label":"대체 일정을 적용해 모두에게 공유한다.","value":"J"},
         "B":{"label":"현장 분위기에 맞춰 즉흥적으로 바꾼다.","value":"P"}},
        {"audience":"senior","prompt":"정기 검진과 약 복용 일정을 관리합니다.",
         "A":{"label":"달력과 알람으로 미리 준비한다.","value":"J"},
         "B":{"label":"필요해지면 그때 확인해 진행한다.","value":"P"}},
    ],
}

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
    st.session_state.mode = None            # "general" | "senior"
    st.session_state.bank = None            # 필터된 뷰
    st.session_state.base = []              # 기본 8문항
    st.session_state.base_ids = []
    st.session_state.used = {ax:set() for ax in AXES}
    st.session_state.answers = {}           # id -> {"axis","value","label","prompt","is_extra"}
    st.session_state.pending_ids = []
    st.session_state.base_done = False
    st.session_state.result_ready = False
    st.session_state.unresolved_axes = []
    st.session_state.answer_log = []

if "mode" not in st.session_state:
    reset_state()

# ----------------------- 데이터 로드 위젯 -----------------------
st.title("Quick-MBTI : 빠르게 MBTI를 알려줍니다")

with st.expander("문항 데이터 로드 옵션", expanded=False):
    st.write("- 기본값: 같은 폴더의 `questions_bank.json`을 시도\n- 파일 업로드, 혹은 URL을 입력해도 됩니다.")
    file_up = st.file_uploader("JSON 파일 업로드 (선택)", type=["json"])
    url_inp = st.text_input("원격 JSON URL (선택)", value="")
    colA, colB = st.columns(2)
    with colA:
        aud = st.radio("출제 범위 선택", options=["일반","어르신(65세 이상)"], index=0, horizontal=True)
    with colB:
        st.write("")

    if st.button("문항 로드/리셋", type="primary"):
        # 데이터 우선순위: 업로드 > URL > 로컬 파일 > 임베드
        data = None
        err = None
        try:
            if file_up is not None:
                data = json.load(io.TextIOWrapper(file_up, encoding="utf-8"))
            elif url_inp.strip():
                with urllib.request.urlopen(url_inp.strip()) as r:
                    data = json.loads(r.read().decode("utf-8"))
            else:
                # 같은 폴더 파일 시도
                try:
                    with open("questions_bank.json","r",encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    data = EMBEDDED_BANK
        except Exception as e:
            err = e
            data = EMBEDDED_BANK

        reset_state()
        st.session_state.mode = "general" if aud.startswith("일반") else "senior"
        st.session_state.bank = filter_by_audience(data, st.session_state.mode)

        # 기본 8문항 선정
        base, base_ids = [], []
        used = {ax:set() for ax in AXES}
        for ax in AXES:
            bank_ax = st.session_state.bank.get(ax, [])
            if len(bank_ax) < 2:
                st.error(f"{ax} 축 문항이 2개 미만입니다. JSON을 보강하세요.")
                st.stop()
            qA, qB = sample_two(bank_ax)
            # id 부여
            q1 = dict(id=f"base_{ax}_1", axis=ax, **qA)
            q2 = dict(id=f"base_{ax}_2", axis=ax, **qB)
            base += [q1,q2]; base_ids += [q1["id"], q2["id"]]
            used[ax].add(qA["prompt"]); used[ax].add(qB["prompt"])
        random.shuffle(base)

        st.session_state.base = base
        st.session_state.base_ids = base_ids
        st.session_state.used = used

        if err:
            st.warning(f"외부 JSON 로드 실패 → 임베드로 대체: {err}")

# 이미 로드된 경우만 아래 진행
if st.session_state.bank:
    # ----------------------- 질문 렌더 -----------------------
    def radio_for(q):
        key = q["id"]
        prev = st.session_state.answers.get(key, {}).get("value")
        choice = st.radio(
            f"{q.get('prompt','')}",
            options=[
                (q["A"]["label"], q["A"]["value"]),
                (q["B"]["label"], q["B"]["value"])
            ],
            index=0 if prev==q["A"]["value"] else 1 if prev==q["B"]["value"] else None,
            key=f"k_{key}",
            horizontal=False,
            label_visibility="visible"
        )
        # Streamlit 라디오 결과는 튜플 아님 → 값만 들어옴. 위 옵션이 (label, value)면 label만 들어오니 아래로 보정
        # 안전하게 버튼 2개를 분리:
        pass

    st.subheader("문항")
    # 라디오를 각각의 두 버튼으로 구현 (Streamlit 라디오가 label/value 분리가 까다로움)
    for q in st.session_state.base:
        cA, cB = st.columns(2)
        st.markdown(f"**{q['prompt']}**")
        btnA = st.button(f"① {q['A']['label']}", key=f"btn_{q['id']}_A")
        btnB = st.button(f"② {q['B']['label']}", key=f"btn_{q['id']}_B")
        if btnA or btnB:
            picked = q["A"] if btnA else q["B"]
            st.session_state.answers[q["id"]] = {
                "axis": q["axis"],
                "value": picked["value"],
                "label": picked["label"],
                "prompt": q["prompt"],
                "is_extra": q.get("is_extra", False)
            }

    # 추가 문항 렌더
    if "extra" not in st.session_state:
        st.session_state.extra = []

    # 기본문항 응답 수 체크
    base_answered = sum(1 for i in st.session_state.base_ids if i in st.session_state.answers)

    # 평가/추가문항 로직
    def append_extra(axis, count=2):
        pool = st.session_state.bank.get(axis, [])
        remain = [q for q in pool if q["prompt"] not in st.session_state.used[axis]]
        random.shuffle(remain)
        added = 0
        for it in remain:
            if added >= count: break
            qid = f"ex_{axis}_{random.randint(1,10**9)}"
            q = dict(id=qid, axis=axis, **it)
            q["is_extra"] = True
            st.session_state.extra.append(q)
            st.session_state.used[axis].add(it["prompt"])
            added += 1
        return added

    # 기본 8개 다 답하면 tie 축에 2개 추가
    if base_answered == 8 and not st.session_state.base_done:
        cur = list(st.session_state.answers.values())
        model = compute_mbti(cur)
        added = 0
        for ax in AXES:
            if need_more_after2(ax, model):
                added += append_extra(ax, 2)
        st.session_state.base_done = True if added>=0 else True  # 플래그 세팅

    # 이미 추가된 문항 보여주고 선택 받기
    if st.session_state.extra:
        st.subheader("추가 문항 (동률 축)")
        for q in st.session_state.extra:
            st.markdown(f"**{q['prompt']}** _(추가)_")
            btnA = st.button(f"① {q['A']['label']}", key=f"btn_{q['id']}_A")
            btnB = st.button(f"② {q['B']['label']}", key=f"btn_{q['id']}_B")
            if btnA or btnB:
                picked = q["A"] if btnA else q["B"]
                st.session_state.answers[q["id"]] = {
                    "axis": q["axis"],
                    "value": picked["value"],
                    "label": picked["label"],
                    "prompt": q["prompt"],
                    "is_extra": True
                }

        # 4문항 단계에서도 동률이면 다시 2개 추가
        # (단, 같은 축 누적 6문항까지만)
        cur = list(st.session_state.answers.values())
        model = compute_mbti(cur)
        for ax in AXES:
            if model["totals"][ax]==4 and need_more_after4(ax, model):
                # 아직 6문항 미만이면 2개 추가
                already = sum(1 for a in cur if a["axis"]==ax)
                if already < 6:
                    append_extra(ax, 2)

    # 모든 추가문항까지 답했는지 확인
    all_ids = st.session_state.base_ids + [q["id"] for q in st.session_state.extra]
    all_answered = all(i in st.session_state.answers for i in all_ids)

    # 최종 평가
    if base_answered == 8 and all_answered:
        cur = list(st.session_state.answers.values())
        model = compute_mbti(cur)
        unresolved = [ax for ax in AXES if unresolved_after6(ax, model)]
        disp_type = format_type_with_unresolved(model, unresolved)

        st.session_state.result_ready = True
        st.session_state.unresolved_axes = unresolved
        # 응답 로그 텍스트
        # 시간순 정렬: 기본8 → 추가문항
        ordered = []
        for q in st.session_state.base + st.session_state.extra:
            if q["id"] in st.session_state.answers:
                a = st.session_state.answers[q["id"]]
                ordered.append(a)
        st.session_state.answer_log = ordered

    # ----------------------- 결과 -----------------------
    if st.session_state.result_ready:
        st.markdown("### 결과")
        st.markdown(f"<h2 style='margin-top:0'>{format_type_with_unresolved(compute_mbti(st.session_state.answer_log), st.session_state.unresolved_axes)}</h2>", unsafe_allow_html=True)

        st.markdown("### 팁")
        for t in COMMON_TIPS:
            st.write(t)

        st.markdown("### MBTI 의미")
        for k, v in MEANINGS:
            st.write(f"- **{k}**: {v}")

        st.markdown("### 응답 로그")
        if not st.session_state.answer_log:
            st.write("(응답 없음)")
        else:
            for i, a in enumerate(st.session_state.answer_log, start=1):
                tag = "추가 " if a.get("is_extra") else ""
                st.write(f"{i}) [{a['axis']}] {tag}{a['prompt']}")
                st.write(f"   → 선택: {a['label']} ({a['value']})")

        # 결과가 나오면 질문 영역을 감추기 위해 stop
        st.stop()
