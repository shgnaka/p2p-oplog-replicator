---
title: "BitTorrent型発見を利用したP2Pコマンド同期MVP（CRDT移行前提）"
date: "2026-03-05"
tags: ["p2p", "synchronization", "bittorrent", "dht", "crdt", "event-log"]
status: "refine"
updated: "2026-03-05"
hypothesis: "BitTorrent的な分散ピア発見を下層に限定し、上層を署名付きイベントログ同期として分離すれば、完全サーバーレスでもPoCは成立し、CRDT移行可能なMVPを設計できる。"
impact: 5
effort: 4
risk: 4
---

## Problem

中央サーバー依存を避けた同期システムを構想する際、BitTorrentのP2P成立性をそのまま同期へ流用できるかが不明確だった。特に以下の論点を整理する必要がある。

- BitTorrentと同期システムで要件がどう異なるか
- 完全サーバーレス前提での接続成功限界
- LWW+tombstoneからCRDTへ移行できる設計条件

## Idea

`下層(Connectivity)` と `上層(Sync)` を分離して設計する。

- 下層: BitTorrent的手法を活用したピア発見・接続試行
  - DHT/PEXで候補収集
  - QUICチャネル確立
  - 再試行/欠損回復の搬送
- 上層: コマンド同期本体
  - 署名付きイベントログ複製
  - MVPは `LWW+tombstone`
  - 将来 `CRDT` へ移行可能な互換メタデータを初期導入

MVP仕様の主要決定:

- Wire: `JSON over QUIC`
- 認証: 固定メンバー公開鍵リスト + `Ed25519`
- 因果情報: `Lamport`（ただし `causal` は拡張可能な tagged-union）
- コマンド: 初期からユーザー定義 `command_schema` 拡張を許可

## Assumptions

- 完全サーバーレスを厳守し、リレーは使わない。
- そのため、到達不能ペアは一定割合で残ることを受容する。
- PoC段階の実現可能性は高いが、一般家庭回線での到達性はネットワーク条件依存で振れ幅が大きい。
- ユーザー定義コマンドは deterministic reducer を必須にし、非決定処理は拒否する。
- CRDT移行時は混在運用期間が必要で、`adapter` による変換不能イベントは隔離する。

## Validation Plan

### 1. 実現可能性検証（接続）

- 条件別に接続成功率を計測する（同一LAN、片側公開、両側家庭NAT）。
- 成功判定:
  - 同一LAN: 95%以上
  - 片側公開: 85%以上
  - 両側家庭NAT: 条件差の分布を取得し、失敗理由を分類できる

### 2. 収束性検証（同期）

- 重複再送、順序逆転、分断復帰を含むイベント列で全ノード収束を確認する。
- 成功判定:
  - `event_id` 冪等性成立
  - `delete tombstone` による再出現防止
  - 同一入力で全ノード同一最終状態

### 3. 将来移行検証（CRDT前提）

- `lww_v1 -> crdt_x_v1` adapterの試験実装で変換可否を計測する。
- 成功判定:
  - 変換可能イベントが全適用される
  - 変換不能は `QUARANTINE` に隔離され、状態破壊が起きない
  - 再マテリアライズ時に差分検出できる

## Decision Log

- 2026-03-05: `refine` で作成。理由: 構想の実現可能性評価から、MVPメッセージ仕様とCRDT移行戦略までの意思決定を一体化して固定したため。
- 2026-03-05: 完全サーバーレスを前提に採用。理由: 接続成功率より中央依存排除を優先する方針を選択したため。
- 2026-03-05: MVP競合解決を `LWW+tombstone` とし、`event_version`/`merge_strategy`/`causal`/`command_schema` を互換キーとして必須化。理由: 初期実装コストと将来CRDT移行可能性のバランスを取るため。

## Next Action

`docs/spec-mvp.md` 相当として、メッセージ型（HELLO/ACK/REQUEST/PUSH）と `Event` JSON Schema を1つの仕様書に落とし、適合テストケースA-Dを最低12本（各3本）作成する。
