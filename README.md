# 埋蔵量占い

GitHub Pagesで公開するための静的Webアプリです。

## 使うファイル

- `index.html`: アプリ本体
- `styles.css`: 画面デザインと演出
- `app.js`: 地図、検索、演出、ピン表示
- `data/municipalities.json`: 市区町村検索候補
- `data/by_municipality/*.geojson`: 市区町村別の地図データ
- `data/boundaries/*.geojson`: 市区町村別の輪郭データ
- `indexes/municipality_layer_counts.json`: 市区町村別のカテゴリ件数
- `attribution/`: 出典・ライセンス確認用

## 公開方法

このフォルダの中身をGitHubリポジトリに置き、GitHub Pagesで公開します。
ビルド工程は不要です。

## データ読み込み

アプリは最初に `data/municipalities.json` だけを読み込みます。
市区町村を選ぶと、対応する `data/by_municipality/{municipality_code}.geojson` と `data/boundaries/{municipality_code}.geojson` だけを読み込みます。
全国GeoJSONを一括で読まないため、GitHub Pagesでも扱いやすい構成です。
