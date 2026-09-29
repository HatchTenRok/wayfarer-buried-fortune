const DATA_ROOT = "./data";
const APP_VERSION = "20260929-ver3-semifinal-popup-tabs-1";
const MAX_DROP_PINS = 200;
const MAX_RENDERED_POINT_FEATURES = 3500;
const MIN_RENDERED_POINTS_PER_LAYER = 25;
const BOUNDARY_ROOT = `${DATA_ROOT}/boundaries`;
const HISTORY_ROOT = `${DATA_ROOT}/history_by_municipality`;
const PROFILE_ROOT = `${DATA_ROOT}/profiles`;
const STORY_ASSET_ROOT = "./webp";
const STORY_RULES_PATH = `${DATA_ROOT}/story_asset_rules.json`;
const BOUNDARY_INDEX_PATH = `${DATA_ROOT}/boundary_index.json`;
const BOUNDARY_QUERY_URL =
  "https://services.arcgis.com/wlVTGRSYTzAbjjiC/arcgis/rest/services/municipalityboundaries2020/FeatureServer/0/query";

const storyIllustrationRules = [
  {
    id: "sekihi",
    src: "25_sekihi.webp",
    alt: "碑",
    keywords: ["治水碑", "記念碑", "石碑", "歌碑", "句碑", "顕彰碑", "碑", "境石標"],
  },
  {
    id: "bunkajin",
    src: "06_bunkajin_v2.webp",
    alt: "偉人",
    keywords: ["偉人", "文化人", "文豪", "作家", "歌人", "俳人", "画家", "ゆかりの人物", "人物"],
  },
  {
    id: "busho",
    src: "04_busho_fullbody_v3.webp",
    alt: "武将",
    keywords: ["武将", "戦国", "大名", "武士", "城主", "藩主", "将軍"],
  },
  {
    id: "kuge",
    src: "07_kuge.webp",
    alt: "公家",
    keywords: ["公家", "貴族", "朝廷"],
  },
  {
    id: "shiro",
    src: "09_shiro.webp",
    alt: "城",
    keywords: ["天守", "城郭", "城"],
  },
  {
    id: "shiroato",
    src: "11_shiroato_v2.webp",
    alt: "城跡",
    keywords: ["城跡", "城址", "館跡", "砦"],
  },
  {
    id: "jinya",
    src: "14_jinya.webp",
    alt: "陣屋",
    keywords: ["陣屋"],
  },
  {
    id: "jiin",
    src: "15_jiin.webp",
    alt: "寺院",
    keywords: ["寺院", "仏閣", "寺"],
  },
  {
    id: "jinja",
    src: "17_jinja_torii_haiden.webp",
    alt: "神社",
    keywords: ["神社", "寺社", "信仰", "祭礼", "鳥居"],
  },
  {
    id: "kyokai",
    src: "18_kyokai.webp",
    alt: "教会",
    keywords: ["教会"],
  },
  {
    id: "kofun",
    src: "19_kofun.webp",
    alt: "古墳",
    keywords: ["古墳", "墳墓"],
  },
  {
    id: "kominka",
    src: "20_kominka.webp",
    alt: "古民家",
    keywords: ["古民家", "町家", "民家"],
  },
  {
    id: "rekishi-chosha",
    src: "21_rekishi_chosha.webp",
    alt: "歴史的庁舎",
    keywords: ["庁舎", "役場", "歴史的建造物"],
  },
  {
    id: "hakubutsukan",
    src: "24_hakubutsukan_v3.webp",
    alt: "博物館",
    keywords: ["博物館", "美術館", "郷土館", "記念館", "資料館"],
  },
  {
    id: "todai",
    src: "28_todai.webp",
    alt: "灯台",
    keywords: ["灯台"],
  },
  {
    id: "kyu-ekisha",
    src: "29_kyu_ekisha.webp",
    alt: "旧駅舎",
    keywords: ["旧駅舎", "駅舎", "鉄道"],
  },
  {
    id: "keisho",
    src: "30_keisho.webp",
    alt: "景勝地",
    keywords: ["景勝", "名勝", "景観", "自然", "滝", "湖", "山"],
  },
  {
    id: "teien",
    src: "31_teien.webp",
    alt: "庭園",
    keywords: ["庭園", "庭"],
  },
];

const layerLabels = {
  cafe_restaurant: "飲食店",
  public_facilities: "公共施設",
  scenic_nature_areas: "景観・自然エリア",
  historic_landscape_areas: "歴史的風土保存区域",
  historical_scenic_priority_areas: "歴史的風致重点地区",
  traditional_building_preservation_areas: "伝統的建造物群保存地区",
  parks_playgrounds: "公園・遊具",
  cultural_facilities: "文化施設",
  tourism_resources: "観光資源",
  landscape_districts: "景観地区",
  landscape_important_buildings_trees: "景観重要建造物・樹木",
  historical_temples_shrines: "寺社仏閣",
  historical_sites_archaeology: "史跡・遺跡",
  bakumatsu_villages: "近世村のおおよその範囲",
  edo_roads: "江戸期の街道",
  edo_post_stations: "宿場",
  civil_engineering_heritage: "土木遺産",
};

const layerColors = {
  cafe_restaurant: "#d97706",
  public_facilities: "#2563eb",
  scenic_nature_areas: "#16a34a",
  historic_landscape_areas: "#7c3aed",
  historical_scenic_priority_areas: "#c2410c",
  traditional_building_preservation_areas: "#be123c",
  parks_playgrounds: "#65a30d",
  cultural_facilities: "#9333ea",
  tourism_resources: "#0891b2",
  landscape_districts: "#0f766e",
  landscape_important_buildings_trees: "#4d7c0f",
  historical_temples_shrines: "#a16207",
  historical_sites_archaeology: "#9f1239",
  bakumatsu_villages: "#7c3aed",
  edo_roads: "#92400e",
  edo_post_stations: "#ea580c",
  civil_engineering_heritage: "#0369a1",
};

const defaultEnabledLayers = new Set(Object.keys(layerLabels));

const radarMetricLayers = {
  dining: ["cafe_restaurant"],
  parks: ["parks_playgrounds"],
  public: ["public_facilities"],
  culture: ["cultural_facilities"],
  landscape: ["landscape_important_buildings_trees"],
  temples_shrines: ["historical_temples_shrines"],
  historic_sites: ["historical_sites_archaeology"],
  roads_posts: ["edo_roads", "edo_post_stations"],
  villages: ["bakumatsu_villages"],
  civil: ["civil_engineering_heritage"],
};

const wayfarerFacilityLayers = new Set([
  "cafe_restaurant",
  "cultural_facilities",
  "public_facilities",
  "tourism_resources",
]);

const wayfarerIneligibleFacilityPatterns = [
  /学校|學校|小學校|中學校|高等学校|高校|大学|短期大学|短大|大学院|大学校|高等専門学校|高専|専門学校|専修学校|各種学校|予備校|学院|学園|小学部|中学部|高等部|義務教育|中等教育|一貫校|分校|校舎|学生寮|キャンパス|school|university|college|academy/iu,
  /幼稚|幼児園|幼保園|保育|託児|こども園|子ども園|子供園|児童|乳児|幼児|学童|子育て|放課後(?:児童|等デイサービス)|療育(?:園|施設|センター)|kindergarten|nursery|day[ -]?care|child[ -]?care/iu,
  /特別支援|養護学校|盲学校|聾学校|ろう学校|障害児|障がい児|発達支援センター/iu,
  /(?:障害|障がい|障碍)(?:者|児)|身体障害|知的障害|精神障害|視覚障害|聴覚障害|視聴覚障|障害福祉|障がい福祉|盲人|ろうあ|聾唖|点字図書館|福祉作業所|就労(?:移行|継続)支援|生活介護事業所/iu,
  /老人|高齢者|特別養護|養護老人|軽費老人|介護|有料老人|老健|在宅介護|訪問介護|通所介護|デイサービス|デイケア|ケアハウス|ケアホーム|ケアセンター|グループホーム|シルバーハウス|サービス付き?高齢者向け?住宅|サ高住|nursing[ -]?home|senior[ -]?(?:home|care)/iu,
  /病院|医院|診療所|クリニック|医療|医科|メディカル(?:センター|クリニック)?|健診|検診|保健|救命|救急|療養所|助産院|ホスピス|透析センター|リハビリテーション(?:病院|センター)|リハビリセンター|歯科|眼科|耳鼻咽喉科|産婦人科|整形外科|(?:内科|外科|小児科|皮膚科|泌尿器科|精神科|心療内科)(?:医院|診療所|クリニック)?$|調剤|薬局|薬店|hospital|clinic|medical|hospice/iu,
];

const state = {
  municipalities: [],
  boundaryIndex: [],
  boundaryCache: new Map(),
  activeMunicipality: null,
  activeData: null,
  activeRenderMeta: null,
  activeStoryIllustrations: [],
  clickedMunicipality: null,
  clickedBoundary: null,
  clickLookupId: 0,
  storyIllustrationRules,
  enabledLayers: new Set(defaultEnabledLayers),
  dropMarkers: [],
  popup: null,
  selectionRunId: 0,
  resultPage: 0,
};

const municipalitySearchAliases = {
  "27383": ["千早赤坂村", "ちはやあかさか", "ちはやあかさかむら"],
  "01668": ["白糖町"],
};

const elements = {
  menuButton: document.querySelector("#menuButton"),
  closeMenuButton: document.querySelector("#closeMenuButton"),
  sidePanel: document.querySelector("#sidePanel"),
  restoreLayersButton: document.querySelector("#restoreLayersButton"),
  categoryList: document.querySelector("#categoryList"),
  inspectClickedButton: document.querySelector("#inspectClickedButton"),
  openSearchButton: document.querySelector("#openSearchButton"),
  reopenResultButton: document.querySelector("#reopenResultButton"),
  searchDialog: document.querySelector("#searchDialog"),
  cityInput: document.querySelector("#cityInput"),
  suggestions: document.querySelector("#suggestions"),
  ritualOverlay: document.querySelector("#ritualOverlay"),
  ritualCity: document.querySelector("#ritualCity"),
  storyArtLayer: document.querySelector("#storyArtLayer"),
  resultDialog: document.querySelector("#resultDialog"),
  resultTitle: document.querySelector("#resultTitle"),
  wikiSummaryTitle: document.querySelector("#wikiSummaryTitle"),
  resultHeadline: document.querySelector("#resultHeadline"),
  storyText: document.querySelector("#storyText"),
  rankLine: document.querySelector("#rankLine"),
  radarGrid: document.querySelector("#radarGrid"),
  metricDetails: document.querySelector("#metricDetails"),
  cultureCardGrid: document.querySelector("#cultureCardGrid"),
  resultTabs: [...document.querySelectorAll(".result-tab")],
  resultPages: [...document.querySelectorAll(".result-page")],
  resultDots: [...document.querySelectorAll("#resultDots span")],
  previousResultPage: document.querySelector("#previousResultPage"),
  nextResultPage: document.querySelector("#nextResultPage"),
  manualButton: document.querySelector("#manualButton"),
  manualDialog: document.querySelector("#manualDialog"),
  helpButton: document.querySelector("#helpButton"),
  helpDialog: document.querySelector("#helpDialog"),
  toast: document.querySelector("#toast"),
};

const map = new maplibregl.Map({
  container: "map",
  attributionControl: false,
  center: [137.8, 37.8],
  zoom: 4.15,
  minZoom: 3.4,
  maxZoom: 18,
  style: {
    version: 8,
    sources: {
      gsi_pale: {
        type: "raster",
        tiles: ["https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png"],
        tileSize: 256,
        attribution:
          '<a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank" rel="noreferrer">地理院タイル</a>',
      },
    },
    layers: [
      {
        id: "gsi-pale",
        type: "raster",
        source: "gsi_pale",
      },
    ],
  },
});

map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "top-right");
map.addControl(new maplibregl.AttributionControl({ compact: false }), "bottom-right");

const mapReady = new Promise((resolve) => {
  if (map.loaded()) {
    addPinImages();
    resolve();
  } else {
    map.once("load", () => {
      addPinImages();
      resolve();
    });
  }
});

init();

async function init() {
  renderCategoryControls();
  wireEvents();
  try {
    const response = await fetch(cacheUrl(`${DATA_ROOT}/municipalities.json`));
    if (!response.ok) throw new Error(`municipalities.json ${response.status}`);
    state.municipalities = await response.json();
    await Promise.all([loadBoundaryIndex(), loadStoryAssetRules()]);
    renderSuggestions("");
  } catch (error) {
    showToast("市区町村データを読み込めませんでした。dataフォルダを確認してください。");
    console.error(error);
  }
}

async function loadBoundaryIndex() {
  try {
    const response = await fetch(cacheUrl(BOUNDARY_INDEX_PATH));
    if (!response.ok) throw new Error(`boundary_index.json ${response.status}`);
    state.boundaryIndex = await response.json();
  } catch (error) {
    state.boundaryIndex = [];
    console.warn("Boundary index could not be loaded.", error);
  }
}

async function loadStoryAssetRules() {
  try {
    const response = await fetch(cacheUrl(STORY_RULES_PATH));
    if (!response.ok) throw new Error(`story_asset_rules.json ${response.status}`);
    const payload = await response.json();
    const externalRules = Array.isArray(payload) ? payload : payload.rules;
    state.storyIllustrationRules = mergeStoryIllustrationRules(
      storyIllustrationRules,
      externalRules || []
    );
  } catch (error) {
    state.storyIllustrationRules = storyIllustrationRules;
    console.warn("Story asset rules could not be loaded.", error);
  }
}

function wireEvents() {
  elements.menuButton.addEventListener("click", () => setMenuOpen(true));
  elements.closeMenuButton.addEventListener("click", () => setMenuOpen(false));
  elements.restoreLayersButton.addEventListener("click", restoreAllLayers);
  elements.manualButton.addEventListener("click", () => elements.manualDialog.showModal());
  elements.helpButton.addEventListener("click", () => elements.helpDialog.showModal());
  elements.inspectClickedButton.addEventListener("click", () => {
    if (state.clickedMunicipality) {
      selectMunicipality(state.clickedMunicipality);
    }
  });
  elements.reopenResultButton.addEventListener("click", () => {
    if (state.activeData) {
      showResult(state.activeData, state.activeRenderMeta);
    }
  });
  elements.resultDialog.addEventListener("close", hideStoryArtLayer);
  elements.radarGrid.addEventListener("click", (event) => {
    const action = event.target.closest("[data-map-metric]");
    if (action) showOnlyRadarMetric(action.dataset.mapMetric, action.dataset.metricLabel);
  });
  elements.radarGrid.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    const action = event.target.closest("[data-map-metric]");
    if (!action) return;
    event.preventDefault();
    showOnlyRadarMetric(action.dataset.mapMetric, action.dataset.metricLabel);
  });
  elements.cultureCardGrid.addEventListener("click", (event) => {
    const expandButton = event.target.closest("[data-culture-expand]");
    if (expandButton) {
      setCultureCardExpanded(expandButton.dataset.cultureExpand);
      return;
    }
    const collapseButton = event.target.closest("[data-culture-collapse]");
    if (collapseButton) setCultureCardExpanded(null);
  });
  elements.resultTabs.forEach((tab) => {
    tab.addEventListener("click", () => setResultPage(Number(tab.dataset.resultPage)));
  });
  elements.previousResultPage.addEventListener("click", () => setResultPage(state.resultPage - 1));
  elements.nextResultPage.addEventListener("click", () => setResultPage(state.resultPage + 1));
  elements.resultDialog.addEventListener("keydown", (event) => {
    if (event.key === "ArrowLeft") setResultPage(state.resultPage - 1);
    if (event.key === "ArrowRight") setResultPage(state.resultPage + 1);
  });

  elements.openSearchButton.addEventListener("click", () => {
    elements.searchDialog.showModal();
    elements.cityInput.value = "";
    renderSuggestions("");
    requestAnimationFrame(() => elements.cityInput.focus());
  });

  elements.cityInput.addEventListener("input", () => renderSuggestions(elements.cityInput.value));

  map.on("click", handleMapClick);

  map.on("mousemove", (event) => {
    const hasPoint = map.queryRenderedFeatures(event.point, {
      layers: visiblePointLayerIds(),
    }).length;
    const hasOtherGeometry =
      hasPoint ||
      map.queryRenderedFeatures(event.point, {
        layers: [...visiblePolygonLayerIds(), ...visibleLineLayerIds()],
      }).length;
    map.getCanvas().style.cursor = hasOtherGeometry ? "pointer" : "";
  });
}

async function handleMapClick(event) {
  const pointFeatures = map.queryRenderedFeatures(event.point, {
    layers: visiblePointLayerIds(),
  });
  const features = pointFeatures.length
    ? pointFeatures
    : map.queryRenderedFeatures(event.point, {
        layers: [...visiblePolygonLayerIds(), ...visibleLineLayerIds()],
      });
  if (features.length) {
    showFeaturePopup(features[0], event.lngLat);
  }

  const lookupId = ++state.clickLookupId;
  setClickedMunicipality(null, "checking");
  try {
    const clicked = await identifyMunicipalityAt(event.lngLat);
    if (lookupId !== state.clickLookupId) return;
    if (clicked) {
      setClickedMunicipality(clicked.municipality, "ready", clicked.boundary);
    } else {
      setClickedMunicipality(null, "empty");
      showToast("この地点の市区町村を見つけられませんでした。");
    }
  } catch (error) {
    if (lookupId !== state.clickLookupId) return;
    console.warn("Clicked municipality could not be identified.", error);
    setClickedMunicipality(null, "empty");
  }
}

function setClickedMunicipality(municipality, status = "idle", boundary = null) {
  state.clickedMunicipality = municipality;
  state.clickedBoundary = boundary;
  updateClickedBoundaryData(boundary);
  if (municipality) {
    elements.inspectClickedButton.disabled = false;
    elements.inspectClickedButton.textContent = `${municipality.city}を鑑定`;
    elements.inspectClickedButton.title = `${municipality.label}を鑑定します`;
    return;
  }

  elements.inspectClickedButton.disabled = true;
  elements.inspectClickedButton.title = "地図上の街をクリックすると鑑定できます";
  elements.inspectClickedButton.textContent =
    status === "checking" ? "クリック地点を確認中" : "クリックした街を鑑定";
}

function setMenuOpen(open) {
  elements.sidePanel.classList.toggle("open", open);
  elements.menuButton.setAttribute("aria-expanded", String(open));
}

function renderCategoryControls() {
  elements.categoryList.innerHTML = "";
  Object.entries(layerLabels).forEach(([layerId, label]) => {
    const item = document.createElement("label");
    item.className = "category-item";
    item.innerHTML = `
      <input type="checkbox" ${state.enabledLayers.has(layerId) ? "checked" : ""} data-layer="${layerId}">
      <span class="swatch" style="background:${layerColors[layerId] || "#64748b"}"></span>
      <span>${label}</span>
    `;
    item.querySelector("input").addEventListener("change", (event) => {
      if (event.target.checked) {
        state.enabledLayers.add(layerId);
      } else {
        state.enabledLayers.delete(layerId);
      }
      applyLayerVisibility();
      syncDropMarkers();
    });
    elements.categoryList.appendChild(item);
  });
}

function syncCategoryControls() {
  elements.categoryList.querySelectorAll("input[data-layer]").forEach((input) => {
    input.checked = state.enabledLayers.has(input.dataset.layer);
  });
}

function showOnlyRadarMetric(metricId, metricLabel = "選択カテゴリ") {
  const layerIds = radarMetricLayers[metricId];
  if (!layerIds?.length) return;

  state.enabledLayers.clear();
  layerIds.forEach((layerId) => state.enabledLayers.add(layerId));
  syncCategoryControls();
  applyLayerVisibility();
  syncDropMarkers();
  if (elements.resultDialog.open) elements.resultDialog.close();
  setMenuOpen(false);
  showToast(`${metricLabel}だけを地図に表示しました。地図右側の「復帰」で戻せます。`);
}

function restoreAllLayers() {
  state.enabledLayers = new Set(Object.keys(layerLabels));
  syncCategoryControls();
  applyLayerVisibility();
  syncDropMarkers();
  showToast("すべてのピンを表示しました。");
}

function renderSuggestions(query) {
  const normalized = normalize(query);
  const matches = state.municipalities
    .filter((item) => {
      if (!normalized) return true;
      return municipalitySearchText(item).includes(normalized);
    })
    .slice(0, 40);

  elements.suggestions.innerHTML = "";
  matches.forEach((item) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "suggestion";
    button.setAttribute("role", "option");
    button.innerHTML = `
      <span>${escapeHtml(item.label)}</span>
    `;
    button.addEventListener("click", () => selectMunicipality(item));
    elements.suggestions.appendChild(button);
  });
}

function normalize(value) {
  return String(value || "")
    .normalize("NFKC")
    .replace(/[阪坂]/g, "坂")
    .replace(/[ヶケがガ]/g, "が")
    .replace(/\s+/g, "")
    .toLowerCase();
}

function municipalitySearchText(item) {
  const aliases = municipalitySearchAliases[item.municipality_code] || [];
  return normalize(`${item.pref}${item.city}${item.label}${item.municipality_code}${aliases.join("")}`);
}

async function selectMunicipality(municipality) {
  const runId = ++state.selectionRunId;
  try {
    map.stop();
    elements.searchDialog.close();
    setMenuOpen(false);
    elements.ritualOverlay.classList.remove("active");
    hideStoryArtLayer();
    clearDropMarkers();
    clearMapData();
    updateBoundaryData(null);
    closePopup();
    setClickedMunicipality(null);
    state.activeMunicipality = municipality;
    state.activeData = null;
    state.activeRenderMeta = null;
    state.activeStoryIllustrations = [];
    syncReopenResultButton();
    showToast(`${municipality.label}を鑑定します。`);

    await mapReady;
    if (!isCurrentSelection(runId)) return;

    const [baseData, historyData, profile, boundary] = await Promise.all([
      loadMunicipalityData(municipality),
      loadMunicipalityHistoryData(municipality),
      loadMunicipalityProfile(municipality),
      loadMunicipalityBoundary(municipality),
    ]);
    if (!isCurrentSelection(runId)) return;

    const rawData = mergeMunicipalityData(baseData, historyData, profile);
    const data = filterMunicipalityData(rawData, boundary);
    state.activeData = data;
    state.activeStoryIllustrations = selectStoryIllustrations(data);
    preloadStoryIllustrations(state.activeStoryIllustrations);
    syncReopenResultButton();

    updateBoundaryData(boundary);
    const focusFeatures = boundary?.features?.length ? boundary.features : data.features;
    const bounds = calculateBounds(focusFeatures);
    if (bounds) {
      await flyToBounds(bounds);
    }
    if (!isCurrentSelection(runId)) return;

    await runRitual(municipality, runId);
    if (!isCurrentSelection(runId)) return;

    dropRepresentativePins(data.features);
    await wait(2300);
    if (!isCurrentSelection(runId)) return;

    const renderMeta = updateMapData(data);
    state.activeRenderMeta = renderMeta;
    clearDropMarkers();
    showResult(data, renderMeta);
  } catch (error) {
    if (!isCurrentSelection(runId)) return;
    console.error(error);
    showToast("この街のデータを読み込めませんでした。");
  }
}

function isCurrentSelection(runId) {
  return runId === state.selectionRunId;
}

async function loadMunicipalityData(municipality) {
  const response = await fetch(
    cacheUrl(`${DATA_ROOT}/by_municipality/${municipality.municipality_code}.geojson`)
  );
  if (!response.ok) {
    throw new Error(`${municipality.municipality_code}.geojson ${response.status}`);
  }
  return response.json();
}

async function loadMunicipalityHistoryData(municipality) {
  const response = await fetch(
    cacheUrl(`${HISTORY_ROOT}/${municipality.municipality_code}.geojson`)
  );
  if (!response.ok) {
    console.warn(`${municipality.municipality_code} history ${response.status}`);
    return { type: "FeatureCollection", features: [] };
  }
  return response.json();
}

async function loadMunicipalityProfile(municipality) {
  const response = await fetch(
    cacheUrl(`${PROFILE_ROOT}/${municipality.municipality_code}.json`)
  );
  if (!response.ok) {
    console.warn(`${municipality.municipality_code} profile ${response.status}`);
    return null;
  }
  return response.json();
}

function mergeMunicipalityData(baseData, historyData, profile) {
  return {
    ...baseData,
    display_comment: profile?.display_comment_enriched || baseData.display_comment,
    profile,
    history_layer_counts: historyData?.layer_counts || {},
    features: [...(baseData.features || []), ...(historyData?.features || [])],
  };
}

async function loadMunicipalityBoundary(municipality) {
  const code = municipality.municipality_code;
  if (state.boundaryCache.has(code)) {
    return state.boundaryCache.get(code);
  }

  try {
    const localResponse = await fetch(
      cacheUrl(`${BOUNDARY_ROOT}/${code}.geojson`)
    );
    if (localResponse.ok) {
      const localData = await localResponse.json();
      if (localData.features?.length) {
        state.boundaryCache.set(code, localData);
        return localData;
      }
    }
  } catch (error) {
    console.warn("Local municipality boundary could not be loaded.", error);
  }

  const params = new URLSearchParams({
    where: `JCODE='${code}'`,
    outFields: "*",
    returnGeometry: "true",
    outSR: "4326",
    f: "geojson",
  });
  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      const response = await fetch(`${BOUNDARY_QUERY_URL}?${params.toString()}`);
      if (!response.ok) throw new Error(`boundary ${response.status}`);
      const data = await response.json();
      if (data.features?.length) {
        state.boundaryCache.set(code, data);
        return data;
      }
    } catch (error) {
      if (attempt === 2) {
        console.warn("Municipality boundary could not be loaded.", error);
      }
    }
    await wait(250 * (attempt + 1));
  }
  state.boundaryCache.set(code, null);
  return null;
}

function wait(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

async function identifyMunicipalityAt(lngLat) {
  if (!state.boundaryIndex.length) return null;
  const lng = lngLat.lng;
  const lat = lngLat.lat;
  const candidates = state.boundaryIndex
    .filter((item) => pointInBounds(lng, lat, item.bounds))
    .sort((a, b) => boundsArea(a.bounds) - boundsArea(b.bounds));

  for (const item of candidates) {
    const boundary = await loadMunicipalityBoundary(item);
    if (!boundary?.features?.length) continue;
    const boundaryIndex = buildBoundaryIndex(boundary);
    if (pointInBoundary([lng, lat], boundaryIndex)) {
      return {
        municipality: item,
        boundary,
      };
    }
  }
  return null;
}

function pointInBounds(lng, lat, bounds) {
  if (!bounds) return false;
  const [west, south, east, north] = bounds;
  return lng >= west && lng <= east && lat >= south && lat <= north;
}

function boundsArea(bounds) {
  if (!bounds) return Infinity;
  const [west, south, east, north] = bounds;
  return Math.max(0, east - west) * Math.max(0, north - south);
}

function filterMunicipalityData(data, boundary) {
  let removedIneligibleFacilities = 0;
  let removedOutsidePoints = 0;
  const eligibleFeatures = (data.features || []).filter((feature) => {
    if (!isWayfarerIneligibleFacility(feature)) return true;
    removedIneligibleFacilities += 1;
    return false;
  });

  const boundaryIndex = boundary?.features?.length ? buildBoundaryIndex(boundary) : [];
  const features = eligibleFeatures.flatMap((feature) => {
    if (!boundaryIndex.length) return [feature];
    const geometry = feature.geometry;
    if (geometry?.type === "Point") {
      if (pointInBoundary(geometry.coordinates, boundaryIndex)) return [feature];
      removedOutsidePoints += 1;
      return [];
    }

    if (geometry?.type === "MultiPoint") {
      const coordinates = geometry.coordinates.filter((point) =>
        pointInBoundary(point, boundaryIndex)
      );
      removedOutsidePoints += geometry.coordinates.length - coordinates.length;
      if (!coordinates.length) return [];
      return [{ ...feature, geometry: { ...geometry, coordinates } }];
    }

    return [feature];
  });

  const layerCounts = features.reduce((counts, feature) => {
    const layerId = feature.properties?.layer_id || "unknown";
    counts[layerId] = (counts[layerId] || 0) + 1;
    return counts;
  }, {});

  if (removedOutsidePoints > 0) {
    console.info(
      `${data.pref} ${data.city}: ${removedOutsidePoints}件の境界外ポイントを表示対象から除外しました。`
    );
  }

  if (removedIneligibleFacilities > 0) {
    console.info(
      `${data.pref} ${data.city}: ${removedIneligibleFacilities}件のWayfarer不適合施設を表示対象から除外しました。`
    );
  }

  return {
    ...data,
    features,
    layer_counts: layerCounts,
    total_features: features.length,
    removed_outside_points: removedOutsidePoints,
    removed_ineligible_facilities: removedIneligibleFacilities,
  };
}

function isWayfarerIneligibleFacility(feature) {
  const layerId = feature.properties?.layer_id || "";
  if (!wayfarerFacilityLayers.has(layerId)) return false;
  const name = String(feature.properties?.name || "").normalize("NFKC");
  return wayfarerIneligibleFacilityPatterns.some((pattern) => pattern.test(name));
}

function buildBoundaryIndex(boundary) {
  const polygons = [];
  boundary.features.forEach((feature) => {
    const geometry = feature.geometry;
    const coordinates =
      geometry?.type === "Polygon"
        ? [geometry.coordinates]
        : geometry?.type === "MultiPolygon"
          ? geometry.coordinates
          : [];
    coordinates.forEach((rings) => {
      polygons.push({ rings, bounds: coordinateBounds(rings[0]) });
    });
  });
  return polygons;
}

function coordinateBounds(ring) {
  return ring.reduce(
    (bounds, [lng, lat]) => [
      Math.min(bounds[0], lng),
      Math.min(bounds[1], lat),
      Math.max(bounds[2], lng),
      Math.max(bounds[3], lat),
    ],
    [Infinity, Infinity, -Infinity, -Infinity]
  );
}

function pointInBoundary([lng, lat], boundaryIndex) {
  if (!Number.isFinite(lng) || !Number.isFinite(lat)) return false;
  return boundaryIndex.some(({ rings, bounds }) => {
    const [west, south, east, north] = bounds;
    if (lng < west || lng > east || lat < south || lat > north) return false;
    return pointInPolygon([lng, lat], rings);
  });
}

function pointInPolygon(point, rings) {
  if (!rings?.length || !pointInRing(point, rings[0])) return false;
  return !rings.slice(1).some((hole) => pointInRing(point, hole));
}

function pointInRing([x, y], ring) {
  let inside = false;
  for (let index = 0, previous = ring.length - 1; index < ring.length; previous = index, index += 1) {
    const [x1, y1] = ring[previous];
    const [x2, y2] = ring[index];
    if (pointOnSegment(x, y, x1, y1, x2, y2)) return true;
    const crosses = y1 > y !== y2 > y && x < ((x2 - x1) * (y - y1)) / (y2 - y1) + x1;
    if (crosses) inside = !inside;
  }
  return inside;
}

function pointOnSegment(x, y, x1, y1, x2, y2) {
  const cross = (x - x1) * (y2 - y1) - (y - y1) * (x2 - x1);
  if (Math.abs(cross) > 1e-10) return false;
  return (
    x >= Math.min(x1, x2) - 1e-10 &&
    x <= Math.max(x1, x2) + 1e-10 &&
    y >= Math.min(y1, y2) - 1e-10 &&
    y <= Math.max(y1, y2) + 1e-10
  );
}

function cacheUrl(path) {
  const separator = path.includes("?") ? "&" : "?";
  return `${path}${separator}v=${APP_VERSION}`;
}

function updateMapData(data) {
  const renderSet = buildRenderableFeatureSet(data.features || []);
  const byLayer = groupFeaturesByLayer(renderSet.features);
  Object.entries(layerLabels).forEach(([layerId]) => {
    const sourceId = sourceName(layerId);
    const pointLayerId = pointLayerName(layerId);
    const polygonLayerId = polygonLayerName(layerId);
    const lineLayerId = lineLayerName(layerId);
    const features = byLayer[layerId] || [];
    const collection = {
      type: "FeatureCollection",
      features,
    };

    if (map.getSource(sourceId)) {
      map.getSource(sourceId).setData(collection);
      return;
    }

    map.addSource(sourceId, {
      type: "geojson",
      data: collection,
    });

    map.addLayer({
      id: polygonLayerId,
      type: "fill",
      source: sourceId,
      filter: ["match", ["geometry-type"], ["Polygon", "MultiPolygon"], true, false],
      paint: {
        "fill-color": layerColors[layerId] || "#64748b",
        "fill-opacity": 0.22,
        "fill-outline-color": layerColors[layerId] || "#64748b",
      },
    });

    if (layerId === "bakumatsu_villages") {
      map.addLayer({
        id: polygonOutlineLayerName(layerId),
        type: "line",
        source: sourceId,
        filter: ["match", ["geometry-type"], ["Polygon", "MultiPolygon"], true, false],
        paint: {
          "line-color": "#ffffff",
          "line-width": ["interpolate", ["linear"], ["zoom"], 6, 1.4, 12, 2.6, 17, 4],
          "line-opacity": 0.96,
        },
      });
    }

    map.addLayer({
      id: pointLayerId,
      type: "symbol",
      source: sourceId,
      filter: ["match", ["geometry-type"], ["Point", "MultiPoint"], true, false],
      layout: {
        "icon-image": pinImageName(layerId),
        "icon-size": ["interpolate", ["linear"], ["zoom"], 7, 0.58, 13, 0.86, 17, 1.08],
        "icon-anchor": "bottom",
        "icon-allow-overlap": true,
        "icon-ignore-placement": true,
      },
    });

    map.addLayer({
      id: lineLayerId,
      type: "line",
      source: sourceId,
      filter: ["match", ["geometry-type"], ["LineString", "MultiLineString"], true, false],
      paint: {
        "line-color": layerColors[layerId] || "#64748b",
        "line-width": ["interpolate", ["linear"], ["zoom"], 6, 1.5, 12, 3.2, 17, 5],
        "line-opacity": 0.86,
      },
    });
  });
  raiseBoundaryLayers();
  raisePointLayers();
  raiseClickedBoundaryLayers();
  applyLayerVisibility();
  return renderSet.meta;
}

function buildRenderableFeatureSet(features) {
  const pointFeatures = features.filter(isPointLikeFeature);
  if (pointFeatures.length <= MAX_RENDERED_POINT_FEATURES) {
    return {
      features,
      meta: {
        totalPoints: pointFeatures.length,
        renderedPoints: pointFeatures.length,
        omittedPoints: 0,
      },
    };
  }

  const polygonFeatures = features.filter((feature) => !isPointLikeFeature(feature));
  const pointGroups = groupFeaturesByLayer(pointFeatures);
  let selectedPoints = Object.values(pointGroups).flatMap((items) => {
    const proportionalLimit = Math.round(
      (items.length / pointFeatures.length) * MAX_RENDERED_POINT_FEATURES
    );
    const limit = Math.min(
      items.length,
      Math.max(MIN_RENDERED_POINTS_PER_LAYER, proportionalLimit)
    );
    return pickEvenly(items, limit);
  });

  if (selectedPoints.length > MAX_RENDERED_POINT_FEATURES) {
    selectedPoints = pickEvenly(selectedPoints, MAX_RENDERED_POINT_FEATURES);
  }

  return {
    features: [...selectedPoints, ...polygonFeatures],
    meta: {
      totalPoints: pointFeatures.length,
      renderedPoints: selectedPoints.length,
      omittedPoints: pointFeatures.length - selectedPoints.length,
    },
  };
}

function isPointLikeFeature(feature) {
  const type = feature.geometry?.type;
  return type === "Point" || type === "MultiPoint";
}

function pickEvenly(items, limit) {
  if (limit >= items.length) return items;
  const picked = [];
  const step = items.length / limit;
  for (let index = 0; index < limit; index += 1) {
    picked.push(items[Math.floor(index * step)]);
  }
  return picked;
}

function updateBoundaryData(data) {
  const sourceId = "source-municipality-boundary";
  const fillLayerId = "municipality-boundary-fill";
  const lineLayerId = "municipality-boundary-line";
  const collection = data || {
    type: "FeatureCollection",
    features: [],
  };

  if (map.getSource(sourceId)) {
    map.getSource(sourceId).setData(collection);
    raiseBoundaryLayers();
    raisePointLayers();
    raiseClickedBoundaryLayers();
    return;
  }

  if (!map.isStyleLoaded()) return;

  map.addSource(sourceId, {
    type: "geojson",
    data: collection,
  });

  map.addLayer({
    id: fillLayerId,
    type: "fill",
    source: sourceId,
    paint: {
      "fill-color": "#f59e0b",
      "fill-opacity": 0.08,
    },
  });

  map.addLayer({
    id: lineLayerId,
    type: "line",
    source: sourceId,
    paint: {
      "line-color": "#f59e0b",
      "line-width": ["interpolate", ["linear"], ["zoom"], 6, 2.2, 12, 4, 16, 6],
      "line-opacity": 0.9,
    },
  });
  raiseBoundaryLayers();
  raisePointLayers();
  raiseClickedBoundaryLayers();
}

function updateClickedBoundaryData(data) {
  const sourceId = "source-clicked-municipality-boundary";
  const fillLayerId = "clicked-municipality-boundary-fill";
  const haloLayerId = "clicked-municipality-boundary-halo";
  const lineLayerId = "clicked-municipality-boundary-line";
  const collection = data || {
    type: "FeatureCollection",
    features: [],
  };

  if (map.getSource(sourceId)) {
    map.getSource(sourceId).setData(collection);
    raiseClickedBoundaryLayers();
    return;
  }

  if (!map.isStyleLoaded()) return;

  map.addSource(sourceId, {
    type: "geojson",
    data: collection,
  });

  map.addLayer({
    id: fillLayerId,
    type: "fill",
    source: sourceId,
    paint: {
      "fill-color": "#0f766e",
      "fill-opacity": 0.06,
    },
  });

  map.addLayer({
    id: haloLayerId,
    type: "line",
    source: sourceId,
    paint: {
      "line-color": "#ffffff",
      "line-width": ["interpolate", ["linear"], ["zoom"], 5, 4, 10, 7, 16, 11],
      "line-opacity": 0.94,
    },
  });

  map.addLayer({
    id: lineLayerId,
    type: "line",
    source: sourceId,
    paint: {
      "line-color": "#0f766e",
      "line-dasharray": [2, 1.1],
      "line-width": ["interpolate", ["linear"], ["zoom"], 5, 2.2, 10, 3.6, 16, 5],
      "line-opacity": 0.98,
    },
  });
  raiseClickedBoundaryLayers();
}

function clearMapData() {
  Object.keys(layerLabels).forEach((layerId) => {
    const source = map.getSource(sourceName(layerId));
    if (source) {
      source.setData({
        type: "FeatureCollection",
        features: [],
      });
    }
  });
}

function addPinImages() {
  Object.keys(layerLabels).forEach((layerId) => {
    const imageName = pinImageName(layerId);
    if (map.hasImage(imageName)) return;
    map.addImage(imageName, makePinImage(layerColors[layerId] || "#64748b"), {
      pixelRatio: 2,
    });
  });
}

function makePinImage(color) {
  const scale = 2;
  const width = 32;
  const height = 44;
  const canvas = document.createElement("canvas");
  canvas.width = width * scale;
  canvas.height = height * scale;
  const ctx = canvas.getContext("2d");
  ctx.scale(scale, scale);

  ctx.beginPath();
  ctx.ellipse(16, 40.5, 6.4, 2.2, 0, 0, Math.PI * 2);
  ctx.fillStyle = "rgba(15, 23, 42, 0.18)";
  ctx.fill();

  ctx.beginPath();
  ctx.moveTo(16, 42);
  ctx.bezierCurveTo(12, 34, 4, 27, 4, 17);
  ctx.bezierCurveTo(4, 8, 9.5, 3, 16, 3);
  ctx.bezierCurveTo(22.5, 3, 28, 8, 28, 17);
  ctx.bezierCurveTo(28, 27, 20, 34, 16, 42);
  ctx.closePath();
  ctx.fillStyle = color;
  ctx.fill();

  ctx.lineWidth = 2.2;
  ctx.strokeStyle = "#ffffff";
  ctx.stroke();

  ctx.beginPath();
  ctx.arc(16, 16.5, 5.2, 0, Math.PI * 2);
  ctx.fillStyle = "#ffffff";
  ctx.fill();

  return ctx.getImageData(0, 0, canvas.width, canvas.height);
}

function groupFeaturesByLayer(features) {
  return features.reduce((acc, feature) => {
    const layerId = feature.properties?.layer_id || "unknown";
    if (!acc[layerId]) acc[layerId] = [];
    acc[layerId].push(feature);
    return acc;
  }, {});
}

function applyLayerVisibility() {
  Object.keys(layerLabels).forEach((layerId) => {
    const visibility = state.enabledLayers.has(layerId) ? "visible" : "none";
    [
      pointLayerName(layerId),
      polygonLayerName(layerId),
      polygonOutlineLayerName(layerId),
      lineLayerName(layerId),
    ].forEach((id) => {
      if (map.getLayer(id)) {
        map.setLayoutProperty(id, "visibility", visibility);
      }
    });
  });
}

function raisePointLayers() {
  Object.keys(layerLabels).forEach((layerId) => {
    const id = pointLayerName(layerId);
    if (map.getLayer(id)) {
      map.moveLayer(id);
    }
  });
}

function raiseBoundaryLayers() {
  ["municipality-boundary-fill", "municipality-boundary-line"].forEach((id) => {
    if (map.getLayer(id)) {
      map.moveLayer(id);
    }
  });
}

function raiseClickedBoundaryLayers() {
  [
    "clicked-municipality-boundary-fill",
    "clicked-municipality-boundary-halo",
    "clicked-municipality-boundary-line",
  ].forEach((id) => {
    if (map.getLayer(id)) {
      map.moveLayer(id);
    }
  });
}

function visibleLayerIds() {
  return [...visiblePointLayerIds(), ...visiblePolygonLayerIds(), ...visibleLineLayerIds()];
}

function visiblePointLayerIds() {
  return Object.keys(layerLabels)
    .filter((layerId) => state.enabledLayers.has(layerId))
    .map((layerId) => pointLayerName(layerId))
    .filter((id) => map.getLayer(id));
}

function visiblePolygonLayerIds() {
  return Object.keys(layerLabels)
    .filter((layerId) => state.enabledLayers.has(layerId))
    .map((layerId) => polygonLayerName(layerId))
    .filter((id) => map.getLayer(id));
}

function visibleLineLayerIds() {
  return Object.keys(layerLabels)
    .filter((layerId) => state.enabledLayers.has(layerId))
    .map((layerId) => lineLayerName(layerId))
    .filter((id) => map.getLayer(id));
}

function sourceName(layerId) {
  return `source-${layerId}`;
}

function pointLayerName(layerId) {
  return `points-${layerId}`;
}

function polygonLayerName(layerId) {
  return `polygons-${layerId}`;
}

function polygonOutlineLayerName(layerId) {
  return `polygon-outline-${layerId}`;
}

function lineLayerName(layerId) {
  return `lines-${layerId}`;
}

function pinImageName(layerId) {
  return `pin-${layerId}`;
}

function calculateBounds(features) {
  const bounds = new maplibregl.LngLatBounds();
  let hasPoint = false;

  features.forEach((feature) => {
    walkCoordinates(feature.geometry?.coordinates, (lng, lat) => {
      if (Number.isFinite(lng) && Number.isFinite(lat)) {
        bounds.extend([lng, lat]);
        hasPoint = true;
      }
    });
  });

  return hasPoint ? bounds : null;
}

function walkCoordinates(coordinates, callback) {
  if (!Array.isArray(coordinates)) return;
  if (
    coordinates.length >= 2 &&
    typeof coordinates[0] === "number" &&
    typeof coordinates[1] === "number"
  ) {
    callback(coordinates[0], coordinates[1]);
    return;
  }
  coordinates.forEach((child) => walkCoordinates(child, callback));
}

function flyToBounds(bounds) {
  return new Promise((resolve) => {
    map.once("moveend", resolve);
    map.fitBounds(bounds, {
      padding: { top: 88, right: 56, bottom: 112, left: 56 },
      duration: 1900,
      maxZoom: 12.8,
      essential: true,
    });
  });
}

async function runRitual(municipality, runId) {
  if (!isCurrentSelection(runId)) return;
  elements.ritualCity.textContent = municipality.city;
  elements.ritualOverlay.classList.add("active");
  showStoryArtLayer(state.activeStoryIllustrations);
  await wait(1900);
  if (isCurrentSelection(runId)) {
    elements.ritualOverlay.classList.remove("active");
  }
}

function dropRepresentativePins(features) {
  clearDropMarkers();
  const pointFeatures = features
    .filter((feature) => state.enabledLayers.has(feature.properties?.layer_id))
    .filter((feature) => feature.geometry?.type === "Point");
  const groups = Object.values(groupFeaturesByLayer(pointFeatures)).map((items) =>
    pickEvenly(items, Math.min(items.length, Math.max(4, Math.ceil(MAX_DROP_PINS / 10))))
  );
  const representativePoints = [];
  let itemIndex = 0;
  while (representativePoints.length < MAX_DROP_PINS && groups.some((items) => itemIndex < items.length)) {
    groups.forEach((items) => {
      if (representativePoints.length < MAX_DROP_PINS && items[itemIndex]) {
        representativePoints.push(items[itemIndex]);
      }
    });
    itemIndex += 1;
  }

  representativePoints.forEach((feature, index) => {
    const [lng, lat] = feature.geometry.coordinates;
    const layerId = feature.properties?.layer_id || "unknown";
    const screenPoint = map.project([lng, lat]);
    const mapRect = map.getContainer().getBoundingClientRect();
    const finalLeft = mapRect.left + screenPoint.x - 16;
    const finalTop = mapRect.top + screenPoint.y - 44;
    const pin = document.createElement("div");
    pin.className = "drop-marker";
    pin.innerHTML = pinSvg(layerColors[layerId] || "#64748b");
    pin.style.left = `${finalLeft}px`;
    pin.style.top = `${finalTop}px`;
    pin.style.setProperty("--drop-start-y", `${-(finalTop + 72)}px`);
    pin.style.animationDelay = `${Math.min(index * 18, 1600)}ms`;
    pin.title = displayFeatureName(feature.properties || {});
    pin.dataset.layer = layerId;
    document.body.appendChild(pin);
    state.dropMarkers.push(pin);
  });
}

function pinSvg(color) {
  return `
    <svg viewBox="0 0 32 44" width="32" height="44" aria-hidden="true">
      <path d="M16 42C12 34 4 27 4 17C4 8 9.5 3 16 3C22.5 3 28 8 28 17C28 27 20 34 16 42Z" fill="${color}" stroke="#fff" stroke-width="2.2"/>
      <circle cx="16" cy="16.5" r="5.2" fill="#fff"/>
    </svg>
  `;
}

function clearDropMarkers() {
  state.dropMarkers.forEach((marker) => marker.remove());
  state.dropMarkers = [];
}

function syncDropMarkers() {
  state.dropMarkers.forEach((marker) => {
    const display = state.enabledLayers.has(marker.dataset.layer) ? "" : "none";
    marker.style.display = display;
  });
}

function mergeStoryIllustrationRules(defaultRules, externalRules) {
  const merged = new Map();

  defaultRules.forEach((rule, index) => {
    const normalized = normalizeStoryIllustrationRule(rule, index);
    if (normalized) merged.set(normalized.id, normalized);
  });

  externalRules.forEach((rule, index) => {
    const normalized = normalizeStoryIllustrationRule(rule, index);
    if (!normalized) return;
    const current = merged.get(normalized.id);
    if (!current) {
      merged.set(normalized.id, normalized);
      return;
    }

    merged.set(normalized.id, {
      ...current,
      ...normalized,
      keywords: uniqueStrings([...(current.keywords || []), ...(normalized.keywords || [])]),
      priority: normalized.priority || current.priority || 0,
    });
  });

  return [...merged.values()];
}

function normalizeStoryIllustrationRule(rule, index = 0) {
  const id = String(rule?.id || "").trim();
  if (!id) return null;

  const keywords = uniqueStrings(
    Array.isArray(rule.keywords) ? rule.keywords.map((keyword) => String(keyword || "")) : []
  );
  if (!keywords.length) return null;

  return {
    id,
    src: String(rule.src || "").trim(),
    alt: String(rule.alt || keywords[0]).trim(),
    keywords,
    priority: Number(rule.priority || 0),
    index,
  };
}

function uniqueStrings(values) {
  const seen = new Set();
  const result = [];
  values.forEach((value) => {
    const normalized = String(value || "").normalize("NFKC").trim();
    if (!normalized || seen.has(normalized)) return;
    seen.add(normalized);
    result.push(normalized);
  });
  return result;
}

function selectStoryIllustrations(data) {
  const context = buildStoryMatchContext(data);
  const matches = state.storyIllustrationRules
    .map((rule, index) => {
      const commentScore = scoreStoryKeywords(context.comment, rule.keywords, 8);
      const quotedScore = scoreStoryKeywords(context.quoted, rule.keywords, 22);
      const featureScore = scoreStoryKeywords(context.featureNames, rule.keywords, 3, 80);
      return {
        ...rule,
        score: commentScore + quotedScore + featureScore,
        index,
      };
    })
    .filter((rule) => rule.score > 0)
    .sort((a, b) => {
      return (
        b.score - a.score ||
        (b.priority || 0) - (a.priority || 0) ||
        a.index - b.index
      );
    })
    .map(({ score, index, priority, ...rule }) => rule);

  return matches;
}

function buildStoryMatchContext(data) {
  const comment =
    typeof data === "string" ? data : data?.display_comment || "";
  const quoted = extractQuotedPhrases(comment).join(" ");
  const featureNames = uniqueStrings(
    (data?.features || [])
      .map((feature) => feature.properties?.name)
      .filter(Boolean)
  ).join(" ");

  return {
    comment: normalizeStoryText(comment),
    quoted: normalizeStoryText(quoted),
    featureNames: normalizeStoryText(featureNames),
  };
}

function extractQuotedPhrases(text) {
  return [...String(text || "").matchAll(/「([^」]{1,80})」/g)].map((match) => match[1]);
}

function normalizeStoryText(text) {
  return String(text || "").normalize("NFKC");
}

function scoreStoryKeywords(text, keywords, weight, cap = Infinity) {
  const score = keywords.reduce((total, keyword) => {
    const normalizedKeyword = normalizeStoryText(keyword).trim();
    if (!normalizedKeyword) return total;
    const occurrences = countKeywordOccurrences(text, normalizedKeyword);
    if (!occurrences) return total;
    const lengthScore = normalizedKeyword.length >= 3
      ? normalizedKeyword.length + 2
      : normalizedKeyword.length;
    return total + occurrences * lengthScore * weight;
  }, 0);
  return Math.min(score, cap);
}

function countKeywordOccurrences(text, keyword) {
  let count = 0;
  let position = 0;
  while (position < text.length) {
    const foundAt = text.indexOf(keyword, position);
    if (foundAt === -1) break;
    count += 1;
    position = foundAt + keyword.length;
  }
  return count;
}

function preloadStoryIllustrations(illustrations) {
  illustrations.forEach((illustration) => {
    const image = new Image();
    image.src = `${STORY_ASSET_ROOT}/${illustration.src}`;
  });
}

function showStoryArtLayer(illustrations = state.activeStoryIllustrations) {
  if (!illustrations.length) {
    hideStoryArtLayer();
    return;
  }

  const total = illustrations.length;
  const placements = storyArtPlacements(total);
  const imageSize = storyArtSize(total);
  const artItems = illustrations
    .map((illustration, index) => {
      const delay = Math.min(index * 80, 720);
      const placement = placements[index];
      return `<img class="story-art" src="${STORY_ASSET_ROOT}/${escapeHtml(illustration.src)}" alt="${escapeHtml(illustration.alt)}" style="--story-left: ${placement.left}%; --story-top: ${placement.top}%; --story-size: ${imageSize}vw; --story-delay: ${delay}ms;">`;
    })
    .join("");

  elements.storyArtLayer.innerHTML = `
    <div class="story-art-board">
      ${artItems}
    </div>
  `;
  elements.storyArtLayer.classList.add("active");
}

function storyArtSize(total) {
  if (total <= 2) return 26;
  if (total <= 4) return 21;
  if (total <= 8) return 16;
  if (total <= 12) return 13;
  return 11;
}

function storyArtPlacements(total) {
  const placements = Array.from({ length: total });
  const sideIndexes = [[], [], [], []];
  for (let index = 0; index < total; index += 1) {
    sideIndexes[index % sideIndexes.length].push(index);
  }

  sideIndexes[0].forEach((itemIndex, sideIndex) => {
    placements[itemIndex] = {
      left: interpolateSlot(sideIndex, sideIndexes[0].length, 16, 84),
      top: 12,
    };
  });
  sideIndexes[1].forEach((itemIndex, sideIndex) => {
    placements[itemIndex] = {
      left: 91,
      top: interpolateSlot(sideIndex, sideIndexes[1].length, 22, 74),
    };
  });
  sideIndexes[2].forEach((itemIndex, sideIndex) => {
    placements[itemIndex] = {
      left: interpolateSlot(sideIndex, sideIndexes[2].length, 84, 16),
      top: 84,
    };
  });
  sideIndexes[3].forEach((itemIndex, sideIndex) => {
    placements[itemIndex] = {
      left: 9,
      top: interpolateSlot(sideIndex, sideIndexes[3].length, 74, 22),
    };
  });

  return placements;
}

function interpolateSlot(index, count, start, end) {
  if (count <= 1) return (start + end) / 2;
  return start + ((end - start) * index) / (count - 1);
}

function hideStoryArtLayer() {
  elements.storyArtLayer.classList.remove("active");
  clearTimeout(hideStoryArtLayer.timer);
  hideStoryArtLayer.timer = setTimeout(() => {
    if (!elements.storyArtLayer.classList.contains("active")) {
      elements.storyArtLayer.innerHTML = "";
    }
  }, 280);
}

function syncReopenResultButton() {
  elements.reopenResultButton.hidden = !state.activeData;
}

function showResult(data, renderMeta = null) {
  showStoryArtLayer(state.activeStoryIllustrations);
  const profile = data.profile;
  const total = data.total_features || data.features?.length || 0;
  elements.resultTitle.textContent = `${data.pref} ${data.city}`;
  elements.wikiSummaryTitle.textContent =
    profile?.wiki_summary_title || `${data.city}に伝わる土地の物語`;
  elements.resultHeadline.textContent = profile?.headline || rankText(total);
  elements.storyText.textContent =
    profile?.display_comment_enriched || data.display_comment || "この街の鑑定コメントは現在未収録です。";
  const renderNote = renderMeta?.omittedPoints
    ? ` 地図は代表${renderMeta.renderedPoints.toLocaleString("ja-JP")}件を軽量表示中。`
    : "";
  elements.rankLine.textContent = `線の長さは全国順位換算（0～100）、先端の数字は収録件数です。軸名を押すと、そのカテゴリだけを地図に表示します。${renderNote}`;
  const radarGroups = profile?.radar_groups || [];
  elements.radarGrid.innerHTML = radarGroups.length
    ? radarGroups.map(renderRadarGroup).join("")
    : `<p class="empty-result">全国比較データを準備中です。</p>`;
  elements.metricDetails.innerHTML = radarGroups
    .flatMap((group) => group.metrics || [])
    .map(renderMetricDetail)
    .join("");
  renderCultureCards(profile?.culture_cards || {});
  setResultPage(0);

  if (!elements.resultDialog.open) {
    elements.resultDialog.showModal();
  }
}

function renderRadarGroup(group) {
  const metrics = group.metrics || [];
  if (metrics.length < 3) return "";
  const center = 180;
  const radius = 102;
  const labelRadius = 142;
  const pointAt = (index, valueRadius) => {
    const angle = -Math.PI / 2 + (Math.PI * 2 * index) / metrics.length;
    return [
      center + Math.cos(angle) * valueRadius,
      center + Math.sin(angle) * valueRadius,
    ];
  };
  const polygon = (scale) =>
    metrics
      .map((_metric, index) => pointAt(index, radius * scale).map((value) => value.toFixed(1)).join(","))
      .join(" ");
  const valuePolygon = metrics
    .map((metric, index) => {
      const score = Math.max(0, Math.min(100, Number(metric.percentile || 0)));
      return pointAt(index, radius * (score / 100)).map((value) => value.toFixed(1)).join(",");
    })
    .join(" ");
  const axes = metrics
    .map((_metric, index) => {
      const [x, y] = pointAt(index, radius);
      return `<line x1="${center}" y1="${center}" x2="${x.toFixed(1)}" y2="${y.toFixed(1)}"></line>`;
    })
    .join("");
  const labels = metrics
    .map((metric, index) => {
      const [x, y] = pointAt(index, labelRadius);
      const anchor = x < center - 18 ? "end" : x > center + 18 ? "start" : "middle";
      const label = metric.short_label || metric.label;
      return `
        <g class="radar-axis-action" role="button" tabindex="0" focusable="true"
          data-map-metric="${escapeHtml(metric.id)}" data-metric-label="${escapeHtml(label)}"
          aria-label="${escapeHtml(label)}だけを地図に表示">
          <text class="radar-label" x="${x.toFixed(1)}" y="${(y - 5).toFixed(1)}" text-anchor="${anchor}">
            <tspan>${escapeHtml(label)}</tspan>
            <tspan class="radar-count" x="${x.toFixed(1)}" dy="15">${formatNumber(metric.count)}件</tspan>
          </text>
        </g>
      `;
    })
    .join("");
  return `
    <article class="radar-card">
      <div class="radar-card-head">
        <h3>${escapeHtml(group.title || "全国比較")}</h3>
        <span>全国順位スコア</span>
      </div>
      <svg class="radar-chart" viewBox="0 0 360 360" role="img" aria-label="${escapeHtml(group.title || "全国比較")}のレーダーチャート">
        <g class="radar-grid-lines">
          <polygon points="${polygon(1)}"></polygon>
          <polygon points="${polygon(0.75)}"></polygon>
          <polygon points="${polygon(0.5)}"></polygon>
          <polygon points="${polygon(0.25)}"></polygon>
          ${axes}
        </g>
        <polygon class="radar-value" points="${valuePolygon}"></polygon>
        ${labels}
      </svg>
    </article>
  `;
}

function renderMetricDetail(metric) {
  const average = Number(metric.national_average || 0).toLocaleString("ja-JP", {
    maximumFractionDigits: 1,
  });
  const rankLabel = metric.rank
    ? `全国${formatNumber(metric.rank)}位 / ${formatNumber(metric.municipality_total)}`
    : "該当データなし";
  return `
    <div class="metric-detail">
      <span>${escapeHtml(metric.label)}</span>
      <strong>${formatNumber(metric.count)}件</strong>
      <small>${rankLabel}</small>
      <small>全国平均 ${average}件</small>
    </div>
  `;
}

function renderCultureCards(cards) {
  const definitions = [
    ["notable_people", "ゆかりの人物", "人"],
    ["tourism_landmarks", "観光・歴史名所", "景"],
    ["food_culture", "地域・都道府県の食文化", "食"],
    ["mascots", "ご当地キャラクター", "楽"],
  ];
  const html = definitions
    .map(([key, label, icon]) => {
      const items = Array.isArray(cards[key]) ? cards[key] : [];
      if (!items.length) return "";
      const omitted = Math.max(0, items.length - 5);
      return `
        <article class="culture-card" data-culture-card="${key}">
          <div class="culture-card-head">
            <span aria-hidden="true">${icon}</span>
            <h3>${label}</h3>
            ${omitted > 0 ? `<button class="culture-collapse-button" type="button" data-culture-collapse="${key}" hidden>× 閉じる</button>` : ""}
          </div>
          <ul>${items
            .map(
              (item, index) =>
                `<li class="${index >= 5 ? "culture-extra-item" : ""}"${index >= 5 ? " hidden" : ""}>${escapeHtml(item)}</li>`
            )
            .join("")}</ul>
          ${
            omitted > 0
              ? `<button class="culture-expand-button" type="button" data-culture-expand="${key}">ほか${formatNumber(omitted)}件をすべて見る</button>`
              : ""
          }
        </article>
      `;
    })
    .filter(Boolean)
    .join("");
  elements.cultureCardGrid.innerHTML = html || `<p class="empty-result">この街の風土・歴史カードは現在未収録です。</p>`;
  setCultureCardExpanded(null);
}

function setCultureCardExpanded(cardKey) {
  const cards = [...elements.cultureCardGrid.querySelectorAll("[data-culture-card]")];
  const hasExpandedCard = Boolean(cardKey);
  elements.cultureCardGrid.classList.toggle("has-expanded-card", hasExpandedCard);

  cards.forEach((card) => {
    const expanded = card.dataset.cultureCard === cardKey;
    card.classList.toggle("expanded", expanded);
    card.querySelectorAll(".culture-extra-item").forEach((item) => {
      item.hidden = !expanded;
    });
    const expandButton = card.querySelector("[data-culture-expand]");
    const collapseButton = card.querySelector("[data-culture-collapse]");
    if (expandButton) expandButton.hidden = expanded;
    if (collapseButton) collapseButton.hidden = !expanded;
  });

  if (cardKey) {
    const expandedCard = elements.cultureCardGrid.querySelector(".culture-card.expanded");
    expandedCard?.scrollIntoView({ behavior: "smooth", block: "start" });
    expandedCard?.querySelector("[data-culture-collapse]")?.focus({ preventScroll: true });
  }
}

function setResultPage(pageIndex) {
  const lastPage = Math.max(0, elements.resultPages.length - 1);
  state.resultPage = Math.max(0, Math.min(lastPage, pageIndex));
  elements.resultTabs.forEach((tab, index) => {
    const active = index === state.resultPage;
    tab.classList.toggle("active", active);
    if (active) tab.setAttribute("aria-current", "page");
    else tab.removeAttribute("aria-current");
  });
  elements.resultPages.forEach((page, index) => {
    const active = index === state.resultPage;
    page.classList.toggle("active", active);
    page.hidden = !active;
  });
  elements.resultDots.forEach((dot, index) => dot.classList.toggle("active", index === state.resultPage));
  elements.previousResultPage.disabled = state.resultPage === 0;
  elements.nextResultPage.disabled = state.resultPage === lastPage;
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString("ja-JP");
}

function rankText(total) {
  if (total >= 2500) return `S級の埋蔵量。${total.toLocaleString("ja-JP")}件の手がかりがあります。`;
  if (total >= 1000) return `A級の濃さ。${total.toLocaleString("ja-JP")}件の候補が見えています。`;
  if (total >= 300) return `発見向きの街。${total.toLocaleString("ja-JP")}件から探索できます。`;
  if (total >= 80) return `穴場の気配。${total.toLocaleString("ja-JP")}件の手がかりがあります。`;
  return `じっくり歩きたい街。${total.toLocaleString("ja-JP")}件の手がかりがあります。`;
}

function showFeaturePopup(feature, lngLat) {
  closePopup();
  const props = feature.properties || {};
  const layerId = props.layer_id || "unknown";
  const categoryLabel = layerLabels[layerId] || layerId;
  const subareaName = formatSubareaName(props.subarea_name, categoryLabel);
  const sourceUrl = safeExternalUrl(props.source_url);
  const accuracyNote = formatAccuracyNote(props.accuracy_note);
  const html = `
    <div class="popup-card">
      <h3>${escapeHtml(displayFeatureName(props))}</h3>
      <p>${escapeHtml(categoryLabel)}</p>
      ${subareaName ? `<p>${escapeHtml(subareaName)}</p>` : ""}
      ${props.address ? `<p>${escapeHtml(props.address)}</p>` : ""}
      ${accuracyNote ? `<p class="popup-note">注意: ${escapeHtml(accuracyNote)}</p>` : ""}
      ${props.source ? `<p>出典: ${escapeHtml(props.source)}</p>` : ""}
      ${sourceUrl ? `<p><a href="${escapeHtml(sourceUrl)}" target="_blank" rel="noreferrer">出典ページを開く</a></p>` : ""}
    </div>
  `;
  state.popup = new maplibregl.Popup({
    anchor: "bottom",
    closeButton: true,
    maxWidth: "320px",
    offset: [0, -46],
  })
    .setLngLat(lngLat)
    .setHTML(html)
    .addTo(map);
}

function formatSubareaName(subareaName, categoryLabel) {
  const value = String(subareaName || "").trim();
  if (!value) return "";
  return normalize(value) === normalize(categoryLabel) ? "" : value;
}

function formatAccuracyNote(note) {
  return String(note || "").replace(
    "江戸時代の正確な村境ではありません",
    "江戸時代の正確な村境でない可能性があります",
  );
}

function safeExternalUrl(value) {
  try {
    const url = new URL(String(value || ""));
    return url.protocol === "https:" || url.protocol === "http:" ? url.href : "";
  } catch (_error) {
    return "";
  }
}

function displayFeatureName(props) {
  const layerId = props.layer_id || "unknown";
  const rawName = String(props.name || "").trim();
  const invalidNames = new Set(["名称不明", "不明"]);
  const personalRestaurantName = isPersonalRestaurantName(rawName, layerId);
  if (
    rawName &&
    !/^\d+$/.test(rawName) &&
    !invalidNames.has(rawName) &&
    !personalRestaurantName
  ) {
    return rawName;
  }
  const layerLabel = layerLabels[layerId] || "区域";
  if (personalRestaurantName) {
    return `${layerLabel}候補`;
  }
  const municipalityName = props.municipality_name || state.activeData?.city;
  if (municipalityName) {
    return `${municipalityName}の${layerLabel}`;
  }
  return layerLabel;
}

function isPersonalRestaurantName(name, layerId) {
  if (layerId !== "cafe_restaurant") return false;
  const normalized = String(name || "").normalize("NFKC").trim();
  if (!normalized) return false;
  const businessWords = /店|屋|亭|庵|堂|館|園|カフェ|喫茶|食堂|酒場|居酒屋|バー|スナック|レストラン|キッチン|ラーメン|そば|寿司|焼|鮨|料理|弁当|パン|菓子|商店|株式会社|有限会社|合同会社|商事|食品|フーズ|フード|観光|ホテル|旅館|民宿|温泉|農園|工房|製菓|製麺|水産|精肉|青果|市場/;
  if (businessWords.test(normalized)) return false;
  const parts = normalized.split(/\s+/).filter(Boolean);
  if (parts.length !== 2) return false;
  return parts.every((part) => /^[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}ー]{2,5}$/u.test(part));
}

function closePopup() {
  if (state.popup) {
    state.popup.remove();
    state.popup = null;
  }
}

function showToast(message) {
  elements.toast.textContent = message;
  elements.toast.classList.add("show");
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => elements.toast.classList.remove("show"), 1500);
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
