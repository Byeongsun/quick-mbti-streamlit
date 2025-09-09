# dev_debug.py
import streamlit as st
from itertools import product
from collections import Counter

st.set_page_config(page_title="Quick-MBTI 디버그(전수 시뮬레이터)", layout="centered")

AXES = ["EI","SN","TF","JP"]
POLES = {
    "EI": ("E","I"),
    "SN": ("S","N"),
    "TF": ("T","F"),
    "JP": ("J","P"),
}

def score_axis(bits, axis):
    a,b = POLES[axis]
    # 2문항
    cntA = (bits[0]==0) + (bits[1]==0)
    cntB = (bits[0]==1) + (bits[1]==1)
    if cntA>cntB: return (a, 2, False)
    if cntB>cntA: return (b, 2, False)
    # 4문항
    cntA += (bits[2]==0) + (bits[3]==0)
    cntB += (bits[2]==1) + (bits[3]==1)
    if cntA>cntB: return (a, 4, False)
    if cntB>cntA: return (b, 4, False)
    # 6문항
    cntA += (bits[4]==0) + (bits[5]==0)
    cntB += (bits[4]==1) + (bits[5]==1)
    if cntA>cntB: return (a, 6, False)
    if cntB>cntA: return (b, 6, False)
    # 미결정
    return (f"({a}{b})", 6, True)

def axis_paths(axis):
    out=[]
    for bits in product([0,1], repeat=6):
        tok, ln, unresolved = score_axis(bits, axis)
        # 조기결정이면 뒤 비트는 의미없지만, 여기선 전체 6비트로 경로 식별
        out.append((tok, ln, bits))
    # 유니크
    uniq=set(); res=[]
    for tok, ln, bits in out:
        key=(tok, ln, bits)
        if key not in uniq:
            uniq.add(key); res.append((tok, ln, bits))
    return res

st.title("Quick-MBTI 디버그(전수 시뮬레이터)")

st.write("각 축 독립 전수조사 → 카르테시안 곱으로 최종 표기 생성")

per_axis = {ax: axis_paths(ax) for ax in AXES}

st.subheader("축별 결과 요약")
for ax in AXES:
    c = Counter(tok for tok,_,_ in per_axis[ax])
    st.write(f"- **{ax}**: {dict(c)}")

# 전체 결과 조합
all_types = Counter()
for t_ei, _, _ in per_axis["EI"]:
    for t_sn, _, _ in per_axis["SN"]:
        for t_tf, _, _ in per_axis["TF"]:
            for t_jp, _, _ in per_axis["JP"]:
                all_types[t_ei + t_sn + t_tf + t_jp] += 1

st.subheader("최종 MBTI 표기 (상위 50)")
for typ, cnt in all_types.most_common(50):
    st.write(f"{typ}: {cnt}")

st.write(f"유니크 결과 수: {len(all_types)}")
