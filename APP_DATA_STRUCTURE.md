# 埋蔵量占い アプリ・データ構成表

この文書は、現在のアプリを別フォルダ、別PC、別のCodexタスクへ移して開発を続けるための引き継ぎ資料です。

## 1. 現在の完成品

| 項目 | 内容 |
| --- | --- |
| アプリ本体 | `C:\Users\toyo-\Documents\Q_Bus\wayfarer-buried-fortune` |
| 方式 | HTML / CSS / JavaScriptだけで動く静的Webアプリ |
| 公開先 | GitHub Pagesを想定 |
| 地図ライブラリ | MapLibre GL JS 4.7.1（unpkgから読込） |
| 背景地図 | 国土地理院「淡色地図」 |
| 市区町村検索数 | 1,896件 |
| 地図フィーチャ総数 | 721,269件 |
| アプリ一式の容量 | 約406 MiB（425,619,870 bytes） |
| 結合キー | 5桁の `municipality_code`。先頭の `0` を消さず文字列として扱う |

## 2. 別の場所へ持っていく最小構成

最も安全なのは、`wayfarer-buried-fortune` フォルダを丸ごとコピーする方法です。実行・公開に必要な最小構成は次のとおりです。

```text
wayfarer-buried-fortune/
├─ index.html
├─ styles.css
├─ app.js
├─ .nojekyll
├─ data/
│  ├─ municipalities.json
│  ├─ by_municipality/
│  │  └─ {municipality_code}.geojson  × 1,896
│  └─ boundaries/
│     └─ {municipality_code}.geojson
└─ attribution/
   └─ 出典・ライセンス資料
```

`app_manifest.json`、`README.md`、`indexes/`、`reports/`、各種Python修復スクリプトは、実行には必須ではありません。ただし仕様確認、検証、将来のデータ修復に役立つため、開発先には一緒にコピーすることを推奨します。

## 3. ファイル構成表

| 区分 | ファイル／フォルダ | 規模 | アプリでの役割 | 読込時期 | 扱い |
| --- | --- | ---: | --- | --- | --- |
| 画面 | `index.html` | 1ファイル | 地図、検索、カテゴリメニュー、結果、ヘルプのHTML | 最初 | 必須 |
| デザイン | `styles.css` | 1ファイル | 画面配置、雲、暗転、ピンドロップ、モーダル等 | 最初 | 必須 |
| 動作 | `app.js` | 1ファイル | 検索、地図移動、データ取得、境界、ピン・面表示、結果集計 | 最初 | 必須 |
| GitHub Pages | `.nojekyll` | 1ファイル | Jekyll処理を無効化 | 公開時 | 必須 |
| 検索リスト | `data/municipalities.json` | 1,896件 / 約315 KiB | 部分一致の市区町村候補とデータファイルの対応表 | 起動時に1回 | 必須 |
| 市区町村別データ | `data/by_municipality/{municipality_code}.geojson` | 1,896ファイル / 約393 MiB | 選択した自治体のピン、面、件数、歴史・風土コメント | 市区町村選択時に1ファイルだけ | 必須 |
| 市区町村境界 | `data/boundaries/{municipality_code}.geojson` | 1,903ファイル / 約12 MiB | 選択区域の輪郭・薄い塗りと、区域外ピンの除外判定 | 市区町村選択時に1ファイルだけ | 必須 |
| 件数索引 | `indexes/municipality_layer_counts.json` | 約326 KiB | 全国分のカテゴリ件数を検査するための索引 | 現アプリは直接読まない | 保守用 |
| 出典資料 | `attribution/` | 7ファイル | 国交省、文化庁、Japan Food Facilities、CODH等の出典・ライセンス確認 | 現ヘルプ本文はHTML内蔵 | 公開時推奨 |
| 仕様メモ | `app_manifest.json` | 1ファイル | エントリーポイント、カテゴリ名、背景地図等の機械可読メモ | 現アプリは直接読まない | 保守用 |
| 検査記録 | `reports/` | 7ファイル | 座標・名称・境界修復の検証記録 | 読まない | 保守用 |
| 修復ツール | `repair_*.py`、`fix_known_coordinate_outliers.py`、`cache_municipality_boundaries.py` | 5ファイル | 元データの名称、位置、市区町村割当、境界を再修復 | 読まない | 保守用 |

## 4. 市区町村検索リスト

`data/municipalities.json` は配列です。1自治体の構造は次のとおりです。

| 項目 | 例 | 用途 |
| --- | --- | --- |
| `municipality_code` | `"01101"` | 全データをつなぐ5桁コード |
| `pref` | `"北海道"` | 都道府県表示・検索 |
| `city` | `"札幌市中央区"` | 市区町村表示・検索 |
| `label` | `"北海道 札幌市中央区"` | 検索候補表示 |
| `feature_count` | `9510` | 収録フィーチャ総数 |
| `data_path` | `data/by_municipality/01101.geojson` | 選択後に読むファイル |

検索は自治体名または都道府県名を含む部分一致です。既知の表記揺れは `app.js` の `municipalitySearchAliases` で補っています。

## 5. 市区町村別GeoJSON

`data/by_municipality/{municipality_code}.geojson` は通常の `FeatureCollection` に、アプリ用の市区町村情報を追加した形式です。

### トップレベル

| 項目 | 用途 |
| --- | --- |
| `type` | 常に `FeatureCollection` |
| `municipality_code` | 市区町村コード |
| `pref` / `city` | 都道府県名・市区町村名 |
| `display_comment` | 結果画面に表示する自然文の歴史・風土コメント |
| `display_comment_original` | 加筆前のコメント。比較・再編集用 |
| `story_enrichment` | 人物、名所、名産、歴史情報と参照URL。保守・説明用 |
| `layer_counts` | 当該自治体のカテゴリ別件数 |
| `total_features` | 当該自治体の全フィーチャ数 |
| `features` | ピンまたは面のGeoJSON Feature配列 |

### 各Featureの主な項目

| 項目 | 用途 |
| --- | --- |
| `properties.layer_id` | カテゴリ識別子。表示色・表示名・ON/OFFに使用 |
| `properties.name` | ポップアップに表示する施設・区域名 |
| `properties.category` | 元データ側の大分類 |
| `properties.address` | 住所。存在する場合のみ表示 |
| `properties.source` | ポップアップ用の短い出典名 |
| `properties.municipality_code` | 市区町村との結合・区域確認 |
| `properties.municipality_pref` | 都道府県名 |
| `properties.municipality_name` | 市区町村名 |
| `properties.municipality_code_method` | コード付与方法の検査情報 |
| `geometry` | `Point` / `MultiPoint` / `Polygon` / `MultiPolygon` |

ピンはPoint系、区域はPolygon系のまま表示します。面は1フィーチャを1件として数え、画面上から落ちる演出には含めません。

## 6. カテゴリ一覧

| `layer_id` | アプリ表示名 | 全国件数 | 主な表示 |
| --- | --- | ---: | --- |
| `cafe_restaurant` | 飲食店 | 514,555 | ピン |
| `public_facilities` | 公共施設 | 79,468 | ピン |
| `parks_playgrounds` | 公園・遊具 | 66,537 | ピン |
| `cultural_facilities` | 文化施設 | 43,884 | ピン |
| `scenic_nature_areas` | 景観・自然エリア | 9,386 | 面 |
| `tourism_resources` | 観光資源 | 6,525 | ピン |
| `landscape_important_buildings_trees` | 景観重要建造物・樹木 | 470 | ピン |
| `landscape_districts` | 景観地区 | 155 | 面またはピン（原典形状を維持） |
| `traditional_building_preservation_areas` | 伝統的建造物群保存地区 | 105 | 面 |
| `historical_scenic_priority_areas` | 歴史的風致重点地区 | 93 | 面 |
| `historic_landscape_areas` | 歴史的風土保存区域 | 91 | 面 |

カテゴリ色と表示名の正本は `app.js` の `layerLabels` と `layerColors` です。初期状態では全カテゴリがON、クラスタリングは行いません。

## 7. 市区町村境界GeoJSON

`data/boundaries/{municipality_code}.geojson` は通常のGeoJSON `FeatureCollection` です。Featureには `properties.municipality_code` と `Polygon` または `MultiPolygon` の境界形状を持たせます。

アプリは選択のたびに前回の境界を空にしてから、新しい境界へ差し替えます。ローカル境界を優先し、ファイルがない場合だけArcGISの `municipalityboundaries2020` サービスを予備取得先として使用します。

## 8. 歴史・風土コメントの正本

最新の編集用CSVは次のファイルです。

`C:\Users\toyo-\Documents\Q_Bus\municipality-enrichment\municipality_story_comments_natural.csv`

| 項目 | 内容 |
| --- | --- |
| 行数 | 1,896自治体 |
| 結合キー | `municipality_code` |
| アプリ表示に使う列 | `display_comment_enriched` |
| 元文 | `display_comment_original` |
| 補強情報 | 武将優先人物、故人の著名人、名誉市民、観光・名所、特産品、食文化、旧藩名、平安期地名など |
| 主な参照情報 | Wikipedia、Wikidata、ジャパンサーチ、既存のCODH系歴史データ |

現アプリでは、このCSVを実行時に直接読みません。`display_comment_enriched` と補強情報を各 `data/by_municipality/*.geojson` の `display_comment` / `story_enrichment` に埋め込んであります。そのため公開先へCSVを置かなくてもコメントは表示できます。CSVは再生成・文章修正の正本として保管してください。

補強処理一式は次の場所です。

`C:\Users\toyo-\Documents\Q_Bus\municipality-enrichment`

## 9. 実行時の読込順

1. `index.html` がMapLibre、`styles.css`、`app.js` を読み込む。
2. 起動時に `data/municipalities.json` だけを読む。
3. ユーザー入力を部分一致検索し、候補から5桁の `municipality_code` を確定する。
4. `data/by_municipality/{code}.geojson` と `data/boundaries/{code}.geojson` を並行して読む。
5. 境界を表示し、区域外へ誤割当されたPointを描画前に除外する。
6. Polygon系は面のまま表示し、Point系はGoogle風ピンで表示する。
7. 最大200本のPointだけを、X座標を変えず画面外上部から下方向へ落とす。
8. `layer_counts`、`total_features`、`display_comment` を結果画面へ表示する。

全国約406 MiBを一度に通信するわけではありません。通常の1回の検索では、検索リストと選択自治体のGeoJSON・境界だけを読みます。

## 10. 別の場所で開発するときの注意

- フォルダ構造と相対パスを維持する。
- `municipality_code` は数値へ変換せず、必ず5桁文字列で扱う。
- GeoJSONの座標順は `[経度, 緯度]`。
- `file://` 直開きでは `fetch()` が失敗する場合があるため、ローカルHTTPサーバーかGitHub Pagesで確認する。
- GitHub Pagesではリポジトリ直下、または公開対象フォルダ直下にこの最小構成を置く。
- `app.js` と `index.html` のクエリ文字列にある `APP_VERSION` を更新すると、古いブラウザキャッシュを避けやすい。
- MapLibre本体、国土地理院タイル、境界の予備取得は外部通信を使う。
- 全国版GeoJSONを新たに一括読込せず、市区町村別ファイル方式を維持する。
- 出典・ライセンスの詳細は `attribution/` と `index.html` のヘルプ本文をセットで管理する。

## 11. 開発先へ渡す優先順位

| 優先度 | 渡すもの | 理由 |
| --- | --- | --- |
| 1 | `wayfarer-buried-fortune` フォルダ一式 | 現在動作している完成形をそのまま再現できる |
| 2 | `municipality-enrichment/municipality_story_comments_natural.csv` | コメントを修正・再生成する正本 |
| 3 | `municipality-enrichment/municipality_enrichment.json` と同フォルダの処理スクリプト | 人物・名所等の再加工に必要 |
| 4 | `C:\WayfarerData\wayfarer-data` の元データ群 | 全GeoJSONを再構築するときだけ必要 |

新しい開発場所では、まず優先度1だけでアプリを起動できます。コメント本文を直す場合は優先度2以降も一緒に移してください。
