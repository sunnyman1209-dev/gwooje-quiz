# 기우제반 퀴즈

기우제반 새디자인 해설집(`..\해설\*.md`)을 그대로 쓰는 모바일 퀴즈 웹앱. 학생이 혼자 공부하는 용도.

- 앱을 열면 무작위로 한 문제씩 나온다. 한 바퀴 동안 같은 문항은 다시 나오지 않고, 틀린 문항(△ 포함)은 10~20문제 뒤 한 번 더 나온다.
- 맞히면 0.8초 뒤 다음 문제, 틀리면 해설(근거·오답 이유·계산·개념 상자)을 보고 '다음'.
- 채점: 진위·4지·연결형 자동 / 단답형 인정 답안 목록(+ '내 답도 맞음') / 계산형 ±1% / 서술형은 핵심어 체크로 ○△×.
- 범위: 전체·오답만·기출/모의/예상/실기·회차·유형. 기록은 그 기기 브라우저에만 저장된다(로그인 없음).
- 출제 제외: 정답 정정 11건(해설의 `정정:` 줄로 자동), 확인필요 문항(`tools\exclude.txt`).

## 폴더
| 경로 | 내용 |
|---|---|
| `docs\` | 올리는 사이트 그대로(index.html, data\questions.json, fig\, robots.txt) |
| `tools\make_pack.py` | Cursor 전사 작업 묶음 만들기 → `work\packs\` |
| `tools\run_trans.ps1` | Cursor로 문항 전사 → `work\trans\*.jsonl` |
| `tools\build_data.py` | 해설 + 전사 → `docs\data\questions.json`, 그림 자르기 → `docs\fig\` |
| `tools\exclude.txt` | 출제에서 뺄 문항 |
| `work\` | 작업용(문항 이미지 사본, 전사 결과, 로그). 사이트에 올리지 않는다 |

## 고칠 때
- 해설을 고쳤으면: `python -I quiz\tools\build_data.py` → `docs\` 올리기.
- 문항 글자(지문·보기)를 고칠 때: `work\trans\<묶음>.jsonl`의 그 줄을 고치고 위와 같이 빌드.
- 확인필요 문항을 다시 출제하려면: `tools\exclude.txt`에서 줄을 지우고 `make_pack.py` → (그 문항 전사가 없으면 Cursor 전사) → 빌드.
