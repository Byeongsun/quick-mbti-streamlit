# test_bank.py
import json, sys

REQUIRED_AXES = ["EI","SN","TF","JP"]
VALID_VALUES = {
    "EI": {"E","I"},
    "SN": {"S","N"},
    "TF": {"T","F"},
    "JP": {"J","P"},
}
VALID_AUDIENCE = {"general","senior","both", None}

def main(path="questions_bank.json"):
    with open(path,"r",encoding="utf-8") as f:
        data=json.load(f)
    # 축 존재/형식 확인
    for ax in REQUIRED_AXES:
        assert ax in data, f"축 누락: {ax}"
        assert isinstance(data[ax], list), f"{ax}는 리스트여야 합니다."
        assert len(data[ax])>=2, f"{ax} 축 문항이 2개 미만입니다."

    # 각 문항 필드 확인
    for ax in REQUIRED_AXES:
        vals=VALID_VALUES[ax]
        for i,q in enumerate(data[ax], start=1):
            assert "prompt" in q and isinstance(q["prompt"], str) and q["prompt"].strip(), f"{ax}[{i}] prompt 누락/형식 오류"
            aud = q.get("audience")
            assert aud in VALID_AUDIENCE, f"{ax}[{i}] audience 값 오류: {aud}"
            for key in ("A","B"):
                assert key in q and isinstance(q[key], dict), f"{ax}[{i}] {key} 항목 누락"
                assert "label" in q[key] and isinstance(q[key]["label"], str), f"{ax}[{i}] {key}.label 누락"
                assert "value" in q[key] and q[key]["value"] in vals, f"{ax}[{i}] {key}.value 값 오류(축 {ax}): {q[key].get('value')}"
    print("✅ JSON 검증 통과!")
    # 요약
    for ax in REQUIRED_AXES:
        print(f"- {ax}: {len(data[ax])}문항")

if __name__=="__main__":
    path = sys.argv[1] if len(sys.argv)>1 else "questions_bank.json"
    main(path)
