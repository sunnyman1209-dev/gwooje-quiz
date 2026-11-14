"""Cursor 전사(옮겨 적기) 작업 묶음 만들기.

python -I quiz/tools/make_pack.py      → quiz/work/packs/<묶음>.md  (Cursor 지시 + 문항 목록)
Cursor는 각 묶음의 결과를 quiz/work/trans/<묶음>.jsonl 에 한 줄 한 문항으로 쓴다.
"""
import json, os, re, sys

sys.stdout.reconfigure(encoding="utf-8")
Q = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # quiz/
H = os.path.dirname(Q)                                             # 기우제반_해설집/
sys.path.insert(0, os.path.join(H, "tools"))
from hs import parse  # noqa: E402

BATCHES = [("g1", ["g1"]), ("g2", ["g2"]), ("g3", ["g3"]), ("g4", ["g4"]), ("g5", ["g5"]),
           ("m1", ["m1"]), ("m2", ["m2"]), ("a", ["a"]),
           ("b1", ["b:1-56"]), ("b2", ["b:57-112"]), ("b3", ["b:113-999"]),
           ("c", ["c"]), ("s", ["s3d", "scam", "sman"])]

RULES = r"""# 퀴즈 문항 전사 작업

기우제반(컴퓨터응용가공산업기사) 문제집 문항을 **모바일 퀴즈 앱용 깔끔한 텍스트 데이터**로 옮겨 적는 작업이다.

## 반드시 지킬 것
- 문항마다 **이미지 파일을 직접 열어 본다**(경로는 각 문항에 있음). 아래 '추출 텍스트'는 PDF에서 뽑아 줄 순서가 섞이고 기호가 빠져 있다. 참고만 하고, 이미지를 기준으로 쓴다.
- 결과 파일 `quiz/work/trans/{batch}.jsonl` 하나만 만든다. 다른 파일은 만들거나 고치지 않는다.
- 한 줄에 한 문항, JSON 객체 하나. 목록의 문항을 **빠짐없이, 같은 순서로**. UTF-8.
- 문장은 원본 그대로 옮긴다(오탈자만 고침: 예 '명렁어'→'명령어'). 내용을 바꾸거나 요약하지 않는다.
- 빼는 것: '문제N)', '배점', '득점', '진위형/4지택일/단답형' 같은 유형 표시, 'O, X에 대한 번호를 찾아 쓰시오' 같은 진위형 안내문, '○ 계산 풀이 :', '○ 정답 :', 점선(……), 빈 답칸 '( )'(단, 문장 속 빈칸은 '(   )'로 남김).

## JSON 필드
{"id": "파트|번호", "type": "...", "stem": "...", "choices": null, "left": null, "right": null,
 "fig": null, "unit": null, "value": null, "accept": null, "keywords": null, "note": ""}

- id: 목록의 `파트|번호` 그대로. type: 목록의 '해설 유형' 그대로.
- stem: 문제 본문. 줄바꿈은 \n. 표가 있으면 `| a | b |` 마크다운 표로. 기하공차 등 기호는 유니코드(⏥ ⌭ ⊥ ∥ ◎ ⌖ ↗ ⌓ ⌒ ∠ ⌯ Ø ° ± μ)로.
- 진위형: stem = 판단할 문장만.
- 4지선다: choices = 보기 4개(①②③④ 표시는 빼고 문장만, 순서 그대로). 보기가 그림뿐이면 "그림 ①" 처럼 쓰고 fig로 보기 그림까지 포함.
- 연결형: left = 왼쪽 4개(① 순서), right = 오른쪽 4개(㉠ ㉡ ㉢ ㉣ 순서). 표시 기호는 빼고 내용만. 왼쪽이 기호·그림이면 유니코드 기호 또는 fig.
- 단답형: accept = 정답으로 인정할 답 목록(해설 정답 + 같은 뜻의 다른 이름·영문·약어. 예 ["크레이터 마모","크레이터","경사면 마모","crater wear"]). 짧은 낱말·코드가 답일 때만. 답이 문장으로 설명해야 하는 것이면 accept는 null, keywords를 채운다.
- 계산형: value = 최종 답 숫자 하나(해설 정답 기준, 단위 없이 숫자. 예 0.1), unit = 단위 문자열(예 "mm/날", "rpm", 없으면 ""). 답이 숫자 하나가 아니면(여러 값, 식) value null, keywords 채움.
- 서술형 및 accept/value를 못 쓰는 문항: keywords = 모범답안의 핵심어 2~6개(학생이 스스로 채점할 체크리스트. 예 ["풀림","불림","담금질","뜨임"]).
- fig: 문제를 풀려면 그림·사진·도면·표 이미지·글자로 못 옮기는 기호가 꼭 필요하면, 이미지에서 **그 그림 부분만** 자를 영역을 [x0, y0, x1, y1] (이미지 너비·높이에 대한 백분율 0~100, 정수)로. 글자로 다 옮길 수 있으면 null. 영역은 그림을 넉넉히(여백 약간) 감싸되 문제 글자·배점 칸은 되도록 빼라.
- note: 문항에 문제가 있으면 한 줄(예 '정답 번호와 보기 내용이 안 맞음', '이미지 잘림'). 없으면 "".
- 확인: 목록의 '해설 정답'과 옮긴 보기가 맞는지 본다(예 정답 '④ 바깥지름'이면 choices[3]이 바깥지름). 안 맞으면 note에 적는다.

## 끝나면
마지막에 "완료: N문항, fig M개, note K개"라고 한 줄 출력한다.

## 문항 목록
"""


def sel(inv, spec):
    pid, _, rng = spec.partition(":")
    items = inv[pid]["items"]
    if rng:
        a, b = map(int, rng.split("-"))
        items = [it for it in items if a <= it["seq"] <= b]
    return pid, items


def excluded():
    ex = set()
    for line in open(os.path.join(Q, "tools", "exclude.txt"), encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#"):
            ex.add(line)
    return ex


def main():
    inv = json.load(open(os.path.join(H, "data", "inventory.json"), encoding="utf-8"))
    ex = excluded()
    hs = {p: parse(os.path.join(H, "해설", f"{p}.md"))[0] for p in inv}
    for p, items in hs.items():
        for no, it in items.items():
            if it.get("정정"):
                ex.add(f"{p}|{no}")
    os.makedirs(os.path.join(Q, "work", "packs"), exist_ok=True)
    os.makedirs(os.path.join(Q, "work", "trans"), exist_ok=True)
    total = 0
    for name, specs in BATCHES:
        L = [RULES.replace("{batch}", name)]
        n = 0
        for spec in specs:
            pid, items = sel(inv, spec)
            for it in items:
                key = f"{pid}|{it['no']}"
                if key in ex:
                    continue
                h = hs[pid][it["no"]]
                q = re.sub(r"\n(배점 ?\d*|득점)(?=\n|$)", "", it["q"]).strip()
                L.append(f"### {key}")
                L.append(f"- 해설 유형: {h.get('유형')}")
                L.append(f"- 이미지: quiz/work/img/{it['img'][4:]}")
                L.append(f"- 해설 정답: {h.get('정답')}")
                if h.get("유형") in ("단답형", "계산형", "서술형") and (h.get("모범답안") or h.get("정의")):
                    L.append(f"- 참고(모범답안/정의): {(h.get('모범답안') or h.get('정의'))[:300]}")
                L.append("- 추출 텍스트:")
                L.append("```")
                L.append(q)
                L.append("```")
                n += 1
        open(os.path.join(Q, "work", "packs", f"{name}.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
        print(name, n)
        total += n
    print("합계", total, "/ 제외", len(ex))
    json.dump(sorted(ex), open(os.path.join(Q, "work", "excluded.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)


if __name__ == "__main__":
    main()
