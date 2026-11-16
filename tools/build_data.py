r"""퀴즈 데이터 만들기: 해설\*.md(정답·해설) + quiz/work/trans/*.jsonl(문항 전사) → quiz/docs/data/questions.json, quiz/docs/fig/*.png

python -I quiz/tools/build_data.py          해설을 고친 뒤 이것만 다시 돌리고 docs 를 올리면 된다.
"""
import glob, json, os, re, sys

sys.stdout.reconfigure(encoding="utf-8")
Q = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H = os.path.dirname(Q)
sys.path.insert(0, os.path.join(H, "tools"))
from hs import parse  # noqa: E402

CIRC = "①②③④⑤⑥"
PAIR = "㉠㉡㉢㉣㉤㉥"
# 목차 기준: 1~5회 = 기출, 모의1·2 + 105·137·189쪽 문제 = 모의고사, 225쪽 이후 = 단원별 출제 예상
GROUP = {"g": "기출", "m": "모의", "a": "모의", "b": "모의", "c": "모의", "s": "단원별 출제 예상"}
TITLE = {"a": "모의 3회", "b": "모의 4회", "c": "모의 5회",
         "s3d": "3D형상모델링", "scam": "CNC밀링 CAM", "sman": "CNC밀링 매뉴얼 프로그래밍"}


def load_trans():
    T = {}
    for f in sorted(glob.glob(os.path.join(Q, "work", "trans", "*.jsonl"))):
        for i, line in enumerate(open(f, encoding="utf-8-sig"), 1):
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"경고 {os.path.basename(f)}:{i} JSON 오류 {e}")
                continue
            T[o["id"]] = o
    return T


def answer_key(t, a, warn):
    a = (a or "").strip()
    if t == "진위형":
        return "O" if "O" in a[:3] else "X"
    if t == "4지선다":
        if a[:1] in CIRC:
            return CIRC.index(a[0])
        warn("4지 정답 형식")
        return None
    if t == "연결형":
        pairs = re.findall(r"([①-⑥])-([㉠-㉥])", a)
        if not pairs:
            warn("연결 정답 형식")
            return None
        key = [None] * len(pairs)
        for l, r in pairs:
            key[CIRC.index(l)] = PAIR.index(r)
        return key
    return None


def crop(img_rel, box, out):
    from PIL import Image
    im = Image.open(os.path.join(Q, "work", "img", img_rel))
    # Cursor가 준 영역(box)은 부정확한 경우가 많아, 원본 문항 이미지 전체를 쓰고 흰 여백만 깎는다.
    from PIL import ImageChops
    im = im.convert("RGB")
    diff = ImageChops.difference(im, Image.new("RGB", im.size, "white")).convert("L").point(lambda v: 255 if v > 24 else 0)
    bb = diff.getbbox()
    if bb:
        pad = 8
        im = im.crop((max(0, bb[0] - pad), max(0, bb[1] - pad), min(im.width, bb[2] + pad), min(im.height, bb[3] + pad)))
    im.save(out, optimize=True)


def main():
    inv = json.load(open(os.path.join(H, "data", "inventory.json"), encoding="utf-8"))
    excluded = set(json.load(open(os.path.join(Q, "work", "excluded.json"), encoding="utf-8")))
    T = load_trans()
    figdir = os.path.join(Q, "docs", "fig")
    os.makedirs(figdir, exist_ok=True)
    for f in glob.glob(os.path.join(figdir, "*.png")):
        os.remove(f)
    out, parts, missing, nwarn = [], [], 0, 0
    for pid, part in inv.items():
        items, _ = parse(os.path.join(H, "해설", f"{pid}.md"))
        concepts = {}
        for no, it in items.items():          # 같은 파트 개념 상자 모으기
            if it.get("개념"):
                cid, _, title = it["개념"].partition("|")
                concepts[cid.strip()] = {"title": title.strip(), "body": it["개념본문"]}
        n = 0
        for src in part["items"]:
            key = f"{pid}|{src['no']}"
            if key in excluded:
                continue
            tr = T.get(key)
            if not tr:
                missing += 1
                continue
            h = items[src["no"]]
            t = h["유형"]

            def warn(msg):
                nonlocal nwarn
                nwarn += 1
                print(f"경고 {key}: {msg}")

            q = {"id": key, "p": pid, "t": t, "stem": (tr.get("stem") or "").strip()}
            for k in ("choices", "left", "right", "unit", "value", "accept", "keywords"):
                if tr.get(k) not in (None, "", []):
                    q[k] = tr[k]
            q["ans"] = answer_key(t, h.get("정답"), warn)
            q["ansText"] = h.get("정답", "")
            if t == "4지선다" and q["ans"] is not None and len(q.get("choices") or []) <= q["ans"]:
                warn("보기 수 부족")
            if t == "연결형" and q["ans"] and (len(q.get("left") or []) != len(q["ans"]) or len(q.get("right") or []) < len(q["ans"])):
                warn("연결 칸 수 불일치")
            if t == "단답형" and not q.get("accept") and not q.get("keywords"):
                warn("단답 채점 정보 없음")
            if t == "계산형" and q.get("value") is None and not q.get("keywords"):
                warn("계산 채점 정보 없음")
            if t == "서술형" and not q.get("keywords"):
                warn("서술 핵심어 없음")
            if tr.get("note"):
                print(f"메모 {key}: {tr['note']}")
            if tr.get("fig"):
                name = re.sub(r"[^0-9A-Za-z가-힣_-]", "_", key.replace("|", "_")) + ".png"
                try:
                    crop(src["img"][4:], tr["fig"], os.path.join(figdir, name))
                    q["fig"] = "fig/" + name
                except Exception as e:  # noqa: BLE001
                    warn(f"그림 자르기 실패 {e}")
            ex = {}
            for k in ("근거", "고친문장", "정의", "비슷한말", "모범답안", "보충"):
                if h.get(k):
                    ex[k] = h[k]
            for k in ("짝", "오답", "계산"):
                if h["_lists"].get(k):
                    ex[k] = h["_lists"][k]
            cid = (h.get("개념") or "").partition("|")[0].strip() or (h.get("참조") or "").strip()
            if cid in concepts:
                ex["개념"] = concepts[cid]
            q["ex"] = ex
            out.append(q)
            n += 1
        parts.append({"id": pid, "title": TITLE.get(pid, part["title"]), "group": GROUP[pid[0]], "n": n})
    data = {"parts": parts, "questions": out}
    os.makedirs(os.path.join(Q, "docs", "data"), exist_ok=True)
    json.dump(data, open(os.path.join(Q, "docs", "data", "questions.json"), "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    print(f"문항 {len(out)}개 (전사 없음 {missing}, 경고 {nwarn}, 그림 {sum(1 for q in out if q.get('fig'))})")


if __name__ == "__main__":
    main()
