# test_exhaustive.py
from itertools import product
from collections import Counter

AXES = ["EI", "SN", "TF", "JP"]
POLES = {
    "EI": ("E","I"),
    "SN": ("S","N"),
    "TF": ("T","F"),
    "JP": ("J","P"),
}

def score_axis(bits, axis):
    """
    bits: 0/1 선택열 (0 = 첫 글자, 1 = 둘째 글자)
    axis: 'EI' | 'SN' | 'TF' | 'JP'
    반환: (winner, totals, diff, unresolved)
      - winner: 'E'/'I'... 혹은 동률이면 None
      - totals: 답한 문항 수
      - diff: 양쪽 득표 차이
      - unresolved: 6문항에서도 동률이면 True (괄호표기 대상)
    규칙: 2에서 동률이면 +2 → 4에서 동률이면 +2 → 6에서 동률이면 판정불가
    """
    a,b = POLES[axis]
    # 2문항
    cntA = bits[0]==0
    cntB = bits[0]==1
    cntA += bits[1]==0
    cntB += bits[1]==1
    if cntA>cntB: return (a, 2, abs(cntA-cntB), False)
    if cntB>cntA: return (b, 2, abs(cntA-cntB), False)

    # 동률 → 追加 2문항
    cntA += (bits[2]==0) + (bits[3]==0)
    cntB += (bits[2]==1) + (bits[3]==1)
    if cntA>cntB: return (a, 4, abs(cntA-cntB), False)
    if cntB>cntA: return (b, 4, abs(cntA-cntB), False)

    # 여전히 동률 → 追加 2문항 (최대 6)
    cntA += (bits[4]==0) + (bits[5]==0)
    cntB += (bits[4]==1) + (bits[5]==1)
    if cntA>cntB: return (a, 6, abs(cntA-cntB), False)
    if cntB>cntA: return (b, 6, abs(cntA-cntB), False)

    # 6문항에도 동률이면 판정 불가(괄호 표기)
    return (None, 6, 0, True)

def axis_all_paths(axis):
    """
    이 축에서 가능한 모든 선택 시퀀스를 생성.
    선택은 최대 6문항이지만, 규칙상 2/4에서 승부가 나면 더 이상 진행하지 않음.
    반환: 리스트[(display_token, path_len, path_bits)]
      display_token: 'E'/'I'.. 혹은 '(EI)'처럼 괄호로 2글자
    """
    a,b = POLES[axis]
    out=[]
    # 전수 시도: 6비트(0/1). 단, 조기결정 나면 뒤 비트는 무시.
    for bits in product([0,1], repeat=6):
        # 2 시점 평가
        w, t, diff, unr = score_axis(bits, axis)
        if t==2 and w is not None:
            out.append((w, 2, bits[:2])); continue
        if t==2 and w is None:
            # tie → 4까지 진행
            pass
        # 4 시점 평가
        if t==4 and w is not None:
            out.append((w, 4, bits[:4])); continue
        if t==4 and w is None:
            # tie → 6까지 진행
            pass
        # 6 시점 평가
        if t==6 and w is not None:
            out.append((w, 6, bits[:6])); continue
        if t==6 and unr:
            out.append((f"({a}{b})", 6, bits[:6])); continue
    # 중복 제거 (같은 결과/길이/패턴)
    uniq=set(); res=[]
    for tok, ln, pb in out:
        key=(tok, ln, tuple(pb))
        if key not in uniq:
            uniq.add(key); res.append((tok, ln, tuple(pb)))
    return res

def format_mbti(tokens):
    """축 순서대로 토큰을 붙여 최종 문자열 생성."""
    return "".join(tokens)

def main():
    per_axis = {ax: axis_all_paths(ax) for ax in AXES}
    # 요약: 축별 결과 분포
    print("=== 축별 결과 분포 ===")
    for ax in AXES:
        c = Counter(tok for tok,_,_ in per_axis[ax])
        print(f"- {ax}: {dict(c)}")

    # 전체 경우의 수(카르테시안 곱)
    all_types = Counter()
    anomalies = []

    for tok_ei, _, _ in per_axis["EI"]:
        for tok_sn, _, _ in per_axis["SN"]:
            for tok_tf, _, _ in per_axis["TF"]:
                for tok_jp, _, _ in per_axis["JP"]:
                    s = format_mbti([tok_ei, tok_sn, tok_tf, tok_jp])
                    # 이상 검출: 한 축에서 글자 2개가 동시에 (괄호 없이) 들어간 경우 등
                    # (여기선 괄호표기만 2글자 허용)
                    # 아주 단순 규칙: 괄호 없는 토큰은 1글자여야 한다.
                    bad = any((t[0]!="(" and len(t)!=1) for t in [tok_ei, tok_sn, tok_tf, tok_jp])
                    if bad:
                        anomalies.append(s)
                    all_types[s]+=1

    print("\n=== 최종 MBTI 표기 분포(상위 20) ===")
    for typ, cnt in all_types.most_common(20):
        print(f"{typ}: {cnt}")

    print(f"\n유니크 결과 수: {len(all_types)}")
    if anomalies:
        print("\n[경고] 형식 이상 케이스 발견:")
        for s in anomalies[:20]:
            print(" -", s)
    else:
        print("\n형식 이상 케이스 없음 (괄호 없는 토큰은 1글자 OK).")

if __name__ == "__main__":
    main()
