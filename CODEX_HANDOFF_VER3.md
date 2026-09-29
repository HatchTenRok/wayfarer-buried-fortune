# Wayfarer 埋蔵量占い Ver3 引継ぎ書

作成日: 2026-09-20  
対象版: Ver3 完成版  
方式: HTML / CSS / JavaScriptだけで動く静的Webアプリ

## 1. ノートPCで使う作業フォルダ

今後は、デスクトップPC・ノートPCとも次の場所へ統一する。

`C:\Users\body\Documents\Codex\wayfarer-buried-fortune`

GitHubから作業を再開する場合も、このフォルダへクローンまたは展開する。古いGitHub作業フォルダや `Documents\ChatGPT` は、このアプリの正規作業場所として使わない。

## 2. ZIPの扱い

配布物 `wayfarer-buried-fortune_Ver3_GitHub.zip` は、ZIP直下に `index.html`、`app.js`、`styles.css`、`.nojekyll`、`data` 等が入るGitHub用構成で作成している。

GitHubのリポジトリへZIPファイルそのものを置くだけではアプリは起動しない。ZIPを展開し、中身をリポジトリ直下へ入れてコミット・プッシュする。

## 3. ローカル起動

ビルドやnpmは不要。プロジェクト直下でHTTPサーバーを起動する。

```powershell
cd C:\Users\body\Documents\Codex\wayfarer-buried-fortune
python -m http.server 8765
```

ブラウザで次を開く。

`http://127.0.0.1:8765/index.html?preview=ver3`

`index.html` を直接ダブルクリックする方法は、ブラウザの `fetch()` 制限でデータ読込に失敗する場合があるため使わない。

## 4. GitHub Pages公開

1. ZIPを展開し、`index.html` がリポジトリ直下にあることを確認する。
2. 全ファイルをコミットしてGitHubへプッシュする。
3. GitHubのリポジトリ設定で Pages を開く。
4. Deploy from a branch、対象ブランチ `main`、フォルダ `/ (root)` を選ぶ。
5. 公開URLで検索、鑑定、ピン、出典表示を確認する。

データ量が多いため、GitHub Web画面から大量ファイルを個別アップロードするより、GitまたはGitHub Desktopでコミットする方が安全。

## 5. 現在のデータ件数

- 自治体: 1,896
- 基本地図フィーチャ: 626,230
- 歴史フィーチャ: 94,484
- 道の駅: 1,145
- 近世村ポリゴン: 59,808
- 寺社仏閣: 16,808
- 史跡・遺跡: 14,836
- 江戸期の街道区間: 895
- 宿場: 1,568
- 土木遺産: 569
- カードへ移した産業遺産名: 473名称、242自治体

歴史地名80,296件と産業遺産の地図ピン559件は、ランタイムGeoJSONから物理削除済み。

## 6. 現在の画面仕様

結果画面は3ページ。

1. 街のバランス
   - Wikipedia由来情報の総括タイトル
   - 件数ルールに基づく短い街歩きヒント
   - 全国順位を0～100へ換算したレーダーチャート
   - 軸先端は実際の収録件数
2. 鑑定コメント
   - 余分なページ内タイトルを置かず、コメント本文だけを表示
3. 風土・歴史
   - ゆかりの人物
   - 観光・歴史名所
   - 地域・都道府県の食文化
   - ご当地キャラクター
   - 各カードは全件展開・閉じる操作に対応

表示カテゴリは17個。歴史地名と産業遺産はメニューに存在しない。産業遺産は位置が不確実なため、名称だけを「観光・歴史名所」カードへ入れている。

近世村は2015年農業集落境界を利用した概略範囲で、白い外周線によって隣接村を判別する。江戸時代の正確な村境とは表示しない。

## 7. Wayfarer向け施設整理

元の自治体別GeoJSONから、次の施設名候補を除外済み。

- 学校、幼稚園、保育施設、特別支援学校
- 老人・介護施設
- 病院、診療所、薬局等
- 大学、短大、専門学校等
- 障がい者施設

公共施設・文化施設の同一自治体内にある同名Pointは、座標平均の代表ピン1本へ統合済み。重複15,169本を削除し、障がい者施設385件を削除した。

## 8. 主なファイル

- `index.html`: 画面と内蔵ヘルプ
- `app.js`: 地図、検索、カテゴリ、鑑定、ポップアップ
- `styles.css`: 画面デザインとレスポンシブ配置
- `data/by_municipality/`: 自治体別基本データ
- `data/history_by_municipality/`: 自治体別歴史データ
- `data/profiles/`: 鑑定結果、レーダー、カード情報
- `data/boundaries/`: 自治体境界
- `attribution/`: 出典と利用条件
- `APP_DATA_STRUCTURE.md`: 詳細なデータ構造
- `history_layer_cleanup_report.json`: 歴史地名・産業遺産整理結果
- `facility_cleanup_and_road_station_report.json`: 施設整理・道の駅追加結果

## 9. 保守スクリプト

- `build_ver3_integration.py`: Ver3元ZIPから歴史データとプロフィールを再構築
- `filter_wayfarer_ineligible_facilities.py`: Wayfarer不適合施設名を検査・除外
- `update_facility_data.py`: 同名ピン統合、障がい者施設除外、道の駅追加、件数再計算
- `finalize_history_layers.py`: 歴史地名・産業遺産ピンを外し、産業遺産名をカードへ移行
- `validate_ver3_integration.py`: 全1,896自治体の最終検査

再生成を行った場合は、最後に必ず `finalize_history_layers.py --apply` と `validate_ver3_integration.py .` を実行する。再生成後に歴史地名・産業遺産ピンを復活させないこと。

## 10. 最終検査状況

`validate_ver3_integration.py` はPASS済み。

- エラー: 0
- ブラウザコンソールエラー: 0
- 歴史地名レイヤー残存: 0
- 産業遺産ピン残存: 0
- 障がい者施設名残存: 0
- 公共・文化施設の同名Point重複: 0

元データの座標では現自治体へ安全に割り当てられなかった少数項目を除外した警告は残るが、アプリの整合性エラーではない。

## 11. 公開前の注意

- `attribution/` を削除しない。
- 地理院タイルの出典表示を常時表示のままにする。
- 国土数値情報P35-18を含むため、公開前に最新の利用条件・再配布条件を確認する。
- 市区町村選択時だけ対象自治体のデータを読む方式を維持する。全国分を一括読込しない。
- 大量データを編集した後は、件数索引、プロフィール、レーダー順位も必ず再計算する。

## 12. ノートPC側Codexへの最初の依頼文

> `C:\Users\body\Documents\Codex\wayfarer-buried-fortune` を正規作業フォルダとして使用してください。最初に `CODEX_HANDOFF_VER3.md`、`CODEX_DIARY_VER3.md`、`README.md`、`APP_DATA_STRUCTURE.md` を読み、既存ファイルを変更する前に構成と検証結果を確認してください。歴史地名と産業遺産ピンは意図的に削除済みなので復活させないでください。

