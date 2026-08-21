# Ichiza（一座）— Worker と LlmPort（app＋adapters）

**版**: v1.6（2026-08-21。v1.6: LlmPort に name（申告と突き合わせる実態）。chat の形はまだ設計どおりでないことを明記。v1.5: v1.5: 源の読み方は土台、対応表はカスタム。v1.4: v1.4: 実行ループに「源を読む」（漏れ）と証拠の作り方。v1.3: v1.3: 落ちたときの作法（例外は帳簿に落とす）。v1.2: v1.2: 使用上限の執行者を働き手に置いた。v1.1: v1.1: §5「AI の磨きは業務ごと」を追加）
**状態**: **有効になった**（2026-08-21、人が有効化した）

AI エージェントの性能はこのプロジェクトの生命線。この紙が決めるのは **①Worker の実行ループ ②プロンプトの構造 ③LlmPort と MCP ④評価（性能をどう測り、どう上げるか）**。世間で LLMOps と呼ばれるものの大半（プロンプト管理・トレース・予算・監視）は既にモデルの中（Definition の Version・Event・Budget・MorningSheet）——ここでは残りだけを設計する。

---

## 1. Worker の実行ループ（app）

```
announce（照合。Board の言葉と CapabilityDeclaration）
→ Ready の Job を探す（受けられるもの: 何を受けるか×Sensitivity×手の届く範囲）
→ take（1体1件。同時に2件持たない）
→ 実行:
    Briefing を解決 → **源を読む**（作業情報の source_refs を ReadPort で。読んだ中身は
      証拠の引用になる） → プロンプト組み立て（読んだ中身を材料として渡す）
      → LlmPort.chat（Tool つき）
    ループごとに: Progress を刻む／Budget を数える（超えたら ContentFailure）
    材料が欠けたら inquire → AwaitingAnswer（answer で再開）
    手に負えなければ release（理由つき）
    **落ちたら**（LLM が応えない・源が読めない・道具が失敗した）:
      例外を外へ逃がさず、EnvironmentFailure に落として帳簿に残す（FailureOccurred）。
      作業情報は EnvironmentFailure が持って帰る——戻れるように
→ Artifact と **Evidence**（何をどこから読んだか——引用と指紋）を置いて submit
→ 次へ
```

- **例外を握りつぶさない**——外へ逃がすと画面に何も出ず、札が切れるまで（既定10分）誰にも見えない。
  捕まえて帳簿に落とせば、履歴に残り、triage が再試行を数えられる
- 何度目の再試行かは**帳簿が持つ**（Retried の数を数える）。状態に持たせると、未着手へ戻った時に消える
- 落ちたら Lease が切れて Job は戻る（patrol）。ループ自体に状態を持たない——**再開に必要なものは全部 Ledger にある**
- Reception も Review も同じループの Worker。違いは枠プロンプトと出力の型だけ
  - Reception の出力: Instruction／Proposal／質問 の3種の判別つき構造
  - Review の出力: ReviewResult（Passed | Returned{reason}）

## 2. プロンプトの構造（性能設計の本体）

プロンプトは**2つに割れる**。混ぜない:

| 部分 | 中身 | 住む場所・版管理 |
|---|---|---|
| **FramePrompt**（枠） | Worker 共通の作法——Briefing の読み方／Tool をいつ使うか／Progress の刻み方／inquire してよい条件（判断を求めない）／Artifact の出力形式／AcceptanceCriteria への自己確認 | **コード**（app/）。git で版管理。変更は評価を承認する |
| **業務の指示**（中身） | このタスクをどうやるか・良い例・悪い例 | **Definition の Version**（データ）。積むだけ・enact で効く・**評価に合格してから enact** |

組み立て: `FramePrompt ＋ Constitution の言葉 ＋ Definition の該当 Version ＋ AcceptanceCriteria（参照解決した本文） ＋ 材料 ＋ 出力形式`。**組み立ては純粋関数**——同じ Briefing からは同じプロンプト（テスト可能）。

改善ループ（新しい仕組みは足さない）: Worker が業務の指示の改善を **Proposal** として出す → **Evaluation** で数字を出す → Human が enact。プロンプトの変更履歴は Version が自動で持つ。

## 3. LlmPort と MCP（adapters）

- `LlmPort.chat(messages, tools) → 応答（本文 or Tool 呼び）`。実装は Ollama。
  **いまの実装は `chat(prompt) → str` で、messages も tools もまだ無い**（段5で Ollama に繋ぐときの形）。
  `LlmPort.name` は在る——CapabilityDeclaration の `model_name` と突き合わせる**実態**で、
  申告した名の LLM が本当に居るかを起動で確かめる（`tests/test_startup.py`）
- Tool 呼びは **MCP** に翻訳する。繋いでよいサーバは CapabilityDeclaration の「手の届く範囲」の一覧——**一覧に無いサーバへは物理的に接続しない**（Tool は Reversible に限る。Irreversible は WritePort＝Apply の二相）
- **源の読み方の型は土台**（ファイル・コマンド）、**どの源をどう読むかの対応表はカスタム**
  （`custom/<題材>/sources.toml`）——土台は「検査の結果」が何かを知らない
- LlmPort の**偽物**（決まった応答を返す実装）を tests 用に最初から作る——Worker ループのテストは LLM 無しで回す
- **仮の実装も adapters に置く**（`adapters/stub_llm.py`）。組み立ての根に口の実装を置かない——
  本物（Ollama）に差し替えるとき、触るのは adapters の1ファイルだけになる

## 4. Evaluation（性能をどう測るか）

**運用時**は設計済み: AgreementRate（Review の判定×人の判定）・Budget・Event のトレース。ここで決めるのは**開発時**:

- **評価セットは発明しない**——Definition の AcceptanceCriteria と具体例がそれ（例が仕様の延長）。「この入力ならこの性質を満たす Artifact」の対を Definition が持つ
- **採点はまず決定的な Check で**（形式・必須項目・禁則の文字列——白黒つくもの）。LLM に LLM を採点させるのは、その採点者自身の AgreementRate が取れてから
- **門番**: 新しい Definition の Version・FramePrompt の変更・モデルの変更は、**評価に合格してから effect**（enact／merge）
- **AgreementRate の標本**: ①Checkpoint のある Job は、人の判断（approve か差し戻しか）がそのまま正解ラベル——**全件が自動で標本になる** ②Checkpoint の無い Job から無作為に少数抜き、MorningSheet ではなく暇な時に人が答え合わせ。導出は Reconciliation（判定は1箇所）——保存しない
- **モデル選定**: 同じ評価セットを候補モデルで回した実測で決める。宣言で選ばない

## 5. AI の磨きは業務ごと（仕組みは Generic、中身は Custom）

AI の性能の上げ方は、業務が変われば変わる——運転と庶務と診療では、良い Artifact の形も、危ない失敗も、要る厳しさも違う。だから**磨きも §8 の線で割る**:

| 磨きの中身（業務ごと＝Custom のデータ） | 磨きの仕組み（共通＝Foundation） |
|---|---|
| 業務の指示（Definition の Version）と良い例・悪い例 | Proposal → Evaluation → enact の改善ループ |
| 評価セット（AcceptanceCriteria と具体例） | Evaluation の回し方・採点の Check |
| Review の観点（何を差し戻すか） | Review という仕組みと ReviewResult の型 |
| AgreementRate の合格水準（診療は高く、運転は緩く） | AgreementRate の実測と標本の取り方 |
| モデルの選択（CapabilityDeclaration に載せる） | LlmPort と実測による選定手順 |
| Checkpoint の位置（どこで人が見るか） | Checkpoint という仕組み |

- **題材①（運転）で磨くのは主に仕組みの側**——改善ループ・評価・標本が本物のデータで回ることの確認。失敗が軽い題材だから、仕組みの穴を安全に踏める
- **題材②③で磨くのは中身の側**——仕組みは持ち越し、業務の指示・例・合格水準だけを現場と一緒に作る（発見作業）
- 磨きの記録は全部 Ledger に残る（Version・Evaluation の結果・AgreementRate）——「どの業務をどこまで磨いたか」は History と JobSheet で辿れる

## 6. テストと評価（この層の流儀）

| 何を | どう |
|---|---|
| Worker ループ | 偽 LlmPort で全遷移（take→submit／inquire→answer→再開／release／Budget 超え→ContentFailure）。LLM 無しで決定的に |
| プロンプト組み立て | 同じ Briefing → 同じプロンプト（固定出力テスト）。Constitution の言葉が入っていること |
| Budget の執行 | **働き手が執行する**——超えていたら LLM を呼ばずに ContentFailure へ落とす（BudgetExceeded＋FailureOccurred）。上限0で赤、見張りを消して赤も確認済み |
| MCP 翻訳 | 一覧外のサーバ名 → 接続前に拒否されること。壊して赤 |
| Evaluation 自身 | わざと悪い業務の指示（禁則入り）が**不合格になる**こと——評価の「壊すと赤」 |

評価軸: I3「通る」（判断以外が人に残らない）の実測は、Checkpoint 以外で人が手を動かした Event の数から導く。
