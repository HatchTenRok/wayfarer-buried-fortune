# 埋蔵量占い アプリ・データ構成表

この文書は、現在のアプリを別フォルダ、別PC、別のCodexタスクへ移して開発を続けるための引き継ぎ資料です。

## 1. 現在の完成品

| 項目 | 内容 |
| --- | --- |
| アプリ本体 | `wayfarer-buried-fortune-ver3-integrated-20260920`（この文書があるフォルダ） |
| 方式 | HTML / CSS / JavaScriptだけで動く静的Webアプリ |
| 公開先 | GitHub Pagesを想定 |
| 地図ライブラリ | MapLibre GL JS 4.7.1（unpkgから読込） |
| 背景地図 | 国土地理院「淡色地図」 |
| 市区町村検索数 | 1,896件 |
| 基本地図フィーチャ | 626,230件（不適合施設削除・同名ピン統合・道の駅追加後） |
| Ver3歴史フィーチャ | 94,484件（歴史地名・産業遺産ピン削除後、街道の自治体別区間を含む） |
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
│  ├─ boundary_index.json
│  ├─ story_asset_rules.json
│  ├─ by_municipality/
│  │  └─ {municipality_code}.geojson  × 1,896
│  ├─ history_by_municipality/
│  │  └─ {municipality_code}.geojson  × 1,896
│  ├─ profiles/
│  │  └─ {municipality_code}.json  × 1,896
│  └─ boundaries/
│     └─ {municipality_code}.geojson
├─ webp/
│  └─ 鑑定演出画像
└─ attribution/
   └─ 出典・ライセンス資料
```

`app_manifest.json`、`README.md`、`indexes/`、`reports/`、各種Python修復スクリプトは、実行には必須ではありません。ただし仕様確認、検証、将来のデータ修復に役立つため、開発先には一緒にコピーすることを推奨します。

## 3. ファイル構成表

| 区分 | ファイル／フォルダ | 規模 | アプリでの役割 | 読込時期 | 扱い |
| --- | --- | ---: | --- | --- | --- |
| 画面 | `index.html` | 1ファイル | 地図、検索、カテゴリメニュー、結果、マニュアル、ヘルプのHTML | 最初 | 必須 |
| デザイン | `styles.css` | 1ファイル | 画面配置、雲、暗転、ピンドロップ、モーダル等 | 最初 | 必須 |
| 動作 | `app.js` | 1ファイル | 検索、地図移動、データ取得、境界、ピン・面表示、結果集計 | 最初 | 必須 |
| GitHub Pages | `.nojekyll` | 1ファイル | Jekyll処理を無効化 | 公開時 | 必須 |
| 検索リスト | `data/municipalities.json` | 1,896件 / 約315 KiB | 部分一致の市区町村候補とデータファイルの対応表 | 起動時に1回 | 必須 |
| 境界索引 | `data/boundary_index.json` | 1,896件 / 約285 KiB | 地図クリック地点から市区町村候補を絞り込む軽量索引 | 起動時に1回 | 必須 |
| 演出画像ルール | `data/story_asset_rules.json` | 18件 | 鑑定文・候補名とWebP画像を紐づけるカテゴリ定義 | 起動時に1回 | 必須 |
| 市区町村別データ | `data/by_municipality/{municipality_code}.geojson` | 1,896ファイル / 約225 MiB | 選択した自治体のピン、面、件数、歴史・風土コメント | 市区町村選択時に1ファイルだけ | 必須 |
| 自治体別歴史データ | `data/history_by_municipality/{municipality_code}.geojson` | 1,896ファイル / 約95.7 MiB | 寺社、史跡・遺跡、近世村、街道・宿場、土木遺産 | 市区町村選択時に1ファイルだけ | 必須 |
| 自治体別鑑定プロフィール | `data/profiles/{municipality_code}.json` | 1,896ファイル / 約8.3 MiB | 全国順位、全国平均、鑑定文、人物・名所・食文化・キャラクター | 市区町村選択時に1ファイルだけ | 必須 |
| 市区町村境界 | `data/boundaries/{municipality_code}.geojson` | 1,903ファイル / 約12 MiB | 選択区域の輪郭・薄い塗りと、区域外ピンの除外判定 | 市区町村選択時に1ファイルだけ | 必須 |
| 鑑定演出画像 | `webp/*.webp` | 18ファイル / 約5.4 MiB | `story_asset_rules.json` の語句に一致したカテゴリを暗転中・結果背面へすべて表示するイラスト | 市区町村選択時 | 必須 |
| 件数索引 | `indexes/municipality_layer_counts.json` | 約326 KiB | 全国分のカテゴリ件数を検査するための索引 | 現アプリは直接読まない | 保守用 |
| 出典資料 | `attribution/` | 7ファイル | 国交省、文化庁、Japan Food Facilities、CODH等の出典・ライセンス確認 | 現ヘルプ本文はHTML内蔵 | 公開時推奨 |
| 仕様メモ | `app_manifest.json` | 1ファイル | エントリーポイント、カテゴリ名、背景地図等の機械可読メモ | 現アプリは直接読まない | 保守用 |
| 検査記録 | `reports/` | 7ファイル | 座標・名称・境界修復の検証記録 | 読まない | 保守用 |
| 修復・保守ツール | `repair_*.py`、`fix_known_coordinate_outliers.py`、`cache_municipality_boundaries.py`、`filter_cafe_restaurant_noise.py`、`filter_wayfarer_ineligible_facilities.py`、`update_facility_data.py`、`finalize_history_layers.py` | 9ファイル | 元データの名称、位置、市区町村割当、境界、施設ノイズ除外、同名ピン統合、道の駅追加、歴史レイヤー整理を再処理 | 読まない | 保守用 |

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
| `layer_counts` | 当該自治体のカテゴリ別件数 |
| `total_features` | 当該自治体の全フィーチャ数 |
| `features` | ピンまたは面のGeoJSON Feature配列 |

公開用のランタイムGeoJSONは軽量化済みです。`display_comment_original`、`story_enrichment`、各Featureの重複自治体情報などは通信量削減のため除外しています。文章の再編集・補強情報の確認には、正本CSVと加工元データを参照してください。

### 各Featureの主な項目

| 項目 | 用途 |
| --- | --- |
| `properties.layer_id` | カテゴリ識別子。表示色・表示名・ON/OFFに使用 |
| `properties.name` | ポップアップに表示する施設・区域名 |
| `properties.address` | 住所。存在する場合のみ表示 |
| `properties.source` | ポップアップ用の短い出典名 |
| `properties.subarea_name` | 区域名など。存在する場合のみ表示 |
| `geometry` | `Point` / `MultiPoint` / `Polygon` / `MultiPolygon` |

ピンはPoint系、区域はPolygon系のまま表示します。面は1フィーチャを1件として数え、画面上から落ちる演出には含めません。

## 6. カテゴリ一覧

| `layer_id` | アプリ表示名 | 全国件数 | 主な表示 |
| --- | --- | ---: | --- |
| `cafe_restaurant` | 飲食店 | 443,731 | ピン |
| `public_facilities` | 公共施設 | 75,475 | ピン（道の駅1,145件を含む） |
| `parks_playgrounds` | 公園・遊具 | 66,537 | ピン |
| `cultural_facilities` | 文化施設 | 23,664 | ピン |
| `scenic_nature_areas` | 景観・自然エリア | 9,386 | 面 |
| `tourism_resources` | 観光資源 | 6,523 | ピン |
| `landscape_important_buildings_trees` | 景観重要建造物・樹木 | 470 | ピン |
| `landscape_districts` | 景観地区 | 155 | 面またはピン（原典形状を維持） |
| `traditional_building_preservation_areas` | 伝統的建造物群保存地区 | 105 | 面 |
| `historical_scenic_priority_areas` | 歴史的風致重点地区 | 93 | 面 |
| `historic_landscape_areas` | 歴史的風土保存区域 | 91 | 面 |

カテゴリ色と表示名の正本は `app.js` の `layerLabels` と `layerColors` です。全17カテゴリを初期ONにします。クラスタリングは行いません。

Ver3追加の地図カテゴリは `historical_temples_shrines`、`historical_sites_archaeology`、`bakumatsu_villages`、`edo_roads`、`edo_post_stations`、`civil_engineering_heritage` です。近世村は概略範囲です。歴史地名は削除済みで、産業遺産は地図に出さず、名称だけをプロフィールの「観光・歴史名所」へ収録します。

上表はWayfarer不適合施設10,719件を元GeoJSONから削除した後の件数です。現アプリは安全策として、自治体データの読み込み時にも同じ条件を再確認し、画面に表示するカテゴリ件数と総件数を再計算します。

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

現アプリでは、このCSVを実行時に直接読みません。`display_comment_enriched` は各 `data/by_municipality/*.geojson` の `display_comment` に埋め込んであります。そのため公開先へCSVを置かなくてもコメントは表示できます。補強情報そのものは軽量化後のランタイムGeoJSONには含めていないため、CSVは再生成・文章修正の正本として保管してください。

補強処理一式は次の場所です。

`C:\Users\toyo-\Documents\Q_Bus\municipality-enrichment`

## 9. 実行時の読込順

1. `index.html` がMapLibre、`styles.css`、`app.js` を読み込む。
2. 起動時に `data/municipalities.json`、`data/boundary_index.json`、`data/story_asset_rules.json` を読む。
3. ユーザー入力を部分一致検索し、候補から5桁の `municipality_code` を確定する。
4. `data/by_municipality/{code}.geojson`、`data/history_by_municipality/{code}.geojson`、`data/profiles/{code}.json`、`data/boundaries/{code}.geojson` を並行して読む。
5. 境界を表示し、区域外へ誤割当されたPointを描画前に除外する。
6. Polygon系は面のまま表示し、Point系はGoogle風ピンで表示する。
7. `data/story_asset_rules.json` のカテゴリ語句を使い、`display_comment` の本文・引用名所・候補名から一致したWebPイラストをすべて選び、鑑定中の暗転演出と結果画面の背面に表示する。
8. Pointが多い自治体では、地図描画用Pointをカテゴリ比率に応じた最大3,500件の代表表示に抑える。結果件数は `layer_counts` / `total_features` の全件数を使う。
9. 最大200本のPointだけを、X座標を変えず画面外上部から下方向へ落とす。
10. 事前計算済みプロフィールから、Wikipedia由来情報の総括タイトルと全国順位レーダー、見出しなしの鑑定コメント本文、風土・歴史カードを3ページで表示する。
11. レーダーの軸名を押すと、対応する `layer_id` だけをONにして結果画面を閉じる。地図右側の「復帰」は全17カテゴリをONに戻す。
12. 風土・歴史カードは先頭5件を表示し、展開ボタンで全件を4カード分の領域へ広げる。鑑定演出画像は結果画面を閉じた時点で消す。
13. 短い見出しは、飲食店が全国30位以内、街道・宿場が1件以上、土木遺産が1件以上、近世村が5件以上という件数ルールを優先する。その他は「充実」と断定せず、街歩きの手がかりとして表現する。
14. 公共施設・文化施設の同一自治体内の同名Pointは座標平均の代表点へ統合する。障がい者施設385件を削除し、国土数値情報P35-18の道の駅1,145件を公共施設へ追加する。

結果画面を閉じた後も、右側の小さな「鑑定結果」ボタンから現在選択中の市区町村の説明を再表示できます。その下の「復帰」は全カテゴリをONに戻します。また、地図上をクリックすると `data/boundary_index.json` と候補自治体の境界GeoJSONでクリック地点の市区町村を判定し、下部の「クリックした街を鑑定」ボタンから再鑑定できます。左メニューは画面高を超える場合に縦スクロールし、「使い方・データの見方」には操作手順、件数の読み方、飲食店データの除外方針、注意事項をHTML内蔵で記載しています。国土地理院タイルの出典表示は折りたたみません。

飲食店データは元データの `name` に営業者名・個人名らしい値が入っている場合があります。`app.js` の表示名判定で、空白区切りの日本語氏名らしい飲食店名はポップアップ上「飲食店候補」として表示します。

全国約238 MiBのランタイムデータを一度に通信するわけではありません。通常の1回の検索では、起動時の軽量索引と選択自治体のGeoJSON・境界だけを読みます。

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
