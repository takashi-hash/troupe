# Ichiza（一座）

AI が仕事を回し、**判断は人間**が持つ仕事場。

業務ルールの版から時計が、または人の依頼（頼む）から仕事が生まれ、
AI が取ってローカル LLM で進め、機械が検査し、
**頼む・承認・差し戻し・回答・打ち切りなど、判断だけが人に残る**（正本は設計/仕事が回る筋道 §1）。
起きたことはすべて帳簿（SQLite）に出来事として残る。

## いまの形

```
ログイン
 ├─ ollama serve（brew サービス。モデル: gpt-oss:20b——これ未満は非推奨）
 ├─ launchd: 時計のひと回り（60秒ごと＋帳簿の変化に即応）… 作る・配る・検査・仕分け・確かめ・突合
 └─ launchd: AI のひと回り（60秒ごと＋帳簿の変化に即応）… 着手 → LLM に問う → 見立ての巡回
```

常駐プロセスは ollama だけ。一座は60秒の脈で目を覚ましては帳簿を見て死ぬ——
**状態は全部 SQLite に在り、プロセスは何も覚えない**。だから雑に殺しても壊れない。

## 動かす

```sh
sh launchd/install.sh                                 # 常駐を配線（外すのは uninstall.sh）
uv run python main.py today --viewer 座長             # 今日 — 判断が要るものだけが出る
uv run python main.py act approve --id <識別子> --by 座長
uv run python main.py rule-add --name <業務ルール> --by 座長   # 題材: custom/<名>/topic.json
uv run python main.py rule-activate --name <業務ルール> --version 1 --by 座長
uv run python main.py window --viewer 座長            # 窓 — 今日・予定・履歴・検索（詳細は行から開く）
```

要件: macOS / uv / Ollama＋`gpt-oss:20b`（13GB。初回に `ollama pull gpt-oss:20b`）。

## 止める・撤去する

```sh
sh launchd/stop.sh agent      # 緊急停止 — AI の脈だけ止める（時計は回り続ける）
sh launchd/stop.sh            # 両方止める（再開は start.sh）
sh launchd/status.sh          # 脈と ollama の状態・直近のログ
sh launchd/uninstall.sh       # 撤去 — **帳簿 data/ は消さない**（消すのは人の手）
```

業務を止めるのは別の話——ルールは `rule-deactivate`、仕事は `act abandon`（判断は人間）。

## 確かめる

```sh
uv run pytest -q                    # 週Aの通し（本物の帳簿）を含む全試験
uv run pyright                      # domain・app は strict
uv run lint-imports                 # 依存は内向きのみ・集約の境界・ui は domain を知らない
uv run python tests/break_check.py  # 義務を1つずつ壊して、全部が赤くなるか
```

## 設計 — 5枚・1000行まで

**まず [`設計/どう作るか.md`](設計/どう作るか.md) を読む**
——書式の掟と、前の一座がなぜ失敗したかが書いてある。

| | 文書 | 何が書いてあるか |
|---|---|---|
| 1 | [起きてはいけないこと](設計/起きてはいけないこと.md) | **設計全部の源**。守るべきもの |
| 2 | [仕事とは何か](設計/仕事とは何か.md) | ドメイン・中核・語・値オブジェクト・集約・不変条件・状態と遷移・型で殺す |
| 3 | [仕事が回る筋道](設計/仕事が回る筋道.md) | 誰が始めるか・判断のありか・ファクトリ・interface・ドメインイベント |
| 4 | [人に見えるもの](設計/人に見えるもの.md) | 画面・渡す値・押せること・今日に出す条件 |
| 5 | [どう作るか](設計/どう作るか.md) | 書式・層・フォルダ・赤くする仕掛け |

設計とコードは突合テストが繋いでいる——遷移表・出来事・値オブジェクトの一覧は、
**設計の表を壊してもコードを壊しても赤くなる**。ずれたまま進めない。
