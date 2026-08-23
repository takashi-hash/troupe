"""合成の座長 — 審査のあいだ、人の操作を台本で叩く代役（Sim-Director）。

患者が合成なら、座長も合成——設計/どう作るか §5。
**新しい入り口を1つも作らない**: 窓の公開フォームを、人と同じ道（HTTP POST）で押す。
席は cookie の名乗り `Sim-Director`——力の源は登記簿で、pilot-on.sh が審査のあいだだけ
staff（座長の役）と clinicians（医師の名簿）の両方へ載せ、pilot-off.sh が外す。
だから起きることは全部 `Sim-Director` の名で帳簿と診療録に残る（開示は /how と README）。

やるのは3つだけ:
- **承認**: 承認待ちの仕事を承認する（受け持ちが Sim-Director の仕事だけ通る——I6 はそのまま）
- **署名**: 下書きの届いた今日の訪問に、下書きのまま署名する（記録は "signed by Sim-Director"）
- **月次請求の確定**: 終わった月の下書き請求を確定する。**旗が残る月は窓が断る**

**答える・差し戻す・打ち切る・旗を裁くは叩かない**——文章の判断と例外の適用を台本にやらせない。
質問と旗は本物の人間を待つ（それ自体が「判断は人に残る」の実演になる）。
"""

from __future__ import annotations

import html
import os
import re
import sys
import urllib.parse
import urllib.request

BASE = os.environ.get("TROUPE_WINDOW", "").rstrip("/")
SIGN_CAP = int(os.environ.get("PILOT_SIGN_CAP", "6"))


#: 代役の席。窓は cookie の名乗りで席を替える——力の源は登記簿(pilot-on が載せ、pilot-off が外す)
_SEAT = {"Cookie": "troupe_seat=Sim-Director"}


def _get(path: str) -> str:
    req = urllib.request.Request(BASE + path, headers=_SEAT)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def _post(path: str, fields: dict[str, str]) -> None:
    data = urllib.parse.urlencode(fields).encode("utf-8")
    req = urllib.request.Request(BASE + path, data=data, method="POST", headers=_SEAT)
    with urllib.request.urlopen(req, timeout=60) as r:
        r.read()


def approve_pending() -> int:
    """承認待ちを承認する。受け持ちでない仕事は断られて戻るだけ——傷はつかない。"""
    page = _get("/search?state=" + urllib.parse.quote("承認待ち"))
    ids = sorted(set(re.findall(r"href='/detail\?id=([^']+)'", page)))
    done = 0
    for job_id in ids:
        try:
            _post("/act", {"what": "approve", "id": job_id, "back": "/inbox", "text": ""})
            done += 1
            print(f"approve: {job_id}")
        except Exception as e:  # 1件の故障で残りを道連れにしない
            print(f"approve failed: {job_id}: {e}", file=sys.stderr)
    return done


def _visit_ids_with_draft() -> list[str]:
    """今日の道順から「Draft ready」の停留だけ拾う。済み・中止・支度なしは触らない。"""
    page = _get("/day")
    ids: list[str] = []
    # カード本体(class が stop-card で始まる要素)だけで割る——BEM の子(stop-card__…)では割らない
    for block in re.split(r"(?=<[a-z]+ class='stop-card[ '])", page):
        if "Draft ready" not in block:
            continue
        m = re.search(r"href='/visit\?id=([^']+)'", block)
        if m and m.group(1) not in ids:
            ids.append(m.group(1))
    return ids


def sign_ready_visits() -> int:
    """下書きの届いた訪問に、下書きのまま署名する。書き上げの編集は本物の人だけがする。"""
    done = 0
    for visit_id in _visit_ids_with_draft()[:SIGN_CAP]:
        try:
            page = _get("/visit?id=" + urllib.parse.quote(visit_id))
            soap = {}
            for field in ("s", "o", "a", "p"):
                m = re.search(rf"<textarea[^>]*name='{field}'[^>]*>(.*?)</textarea>", page, re.S)
                soap[field] = html.unescape(m.group(1)).strip() if m else ""
            draft = re.search(r"name='draft_id' value='([^']*)'", page)
            # 署名者は席そのもの——フォームの hidden が席の名を持つ
            m = re.search(r"name='signer' value='([^']*)'", page)
            signer = html.unescape(m.group(1)).strip() if m and m.group(1) else None
            if not (draft and draft.group(1) and signer and any(soap.values())):
                print(f"sign skipped (no draft/signer): {visit_id}")
                continue
            _post("/visit/act", {
                "what": "sign_note", "id": visit_id,
                "signer": signer,
                "draft_id": draft.group(1), "reason": "", **soap,
            })
            done += 1
            print(f"sign: {visit_id} by {signer}")
        except Exception as e:
            print(f"sign failed: {visit_id}: {e}", file=sys.stderr)
    return done


def confirm_last_month() -> int:
    """終わった月の下書き請求を確定する。旗が残る月は窓が断る——それでよい(裁きは残る)。"""
    page = _get("/billing")
    m = re.search(r"href='/billing\?month=(\d{4}-\d{2})'>\s*←", page)
    if not m:
        return 0
    prev = m.group(1)
    page = _get("/billing?month=" + prev)
    done = 0
    for pt in sorted(set(re.findall(
            r"name='what' value='confirm_claim'.*?name='patient' value='([^']+)'", page, re.S))):
        try:
            _post("/billing/act", {"what": "confirm_claim", "patient": pt, "month": prev})
            done += 1
            print(f"confirm: {pt} {prev}")
        except Exception as e:
            print(f"confirm failed: {pt}: {e}", file=sys.stderr)
    return done


def main() -> int:
    if not BASE:
        print("TROUPE_WINDOW is not set — nothing to drive", file=sys.stderr)
        return 1
    approved = approve_pending()
    signed = sign_ready_visits()
    confirmed = confirm_last_month()
    print(f"pilot done: approved {approved}, signed {signed}, confirmed {confirmed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
