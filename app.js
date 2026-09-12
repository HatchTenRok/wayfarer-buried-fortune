const DATA_ROOT = "./data";
const APP_VERSION = "20260912-lite-1";
const MAX_DROP_PINS = 200;
const MAX_RENDERED_POINT_FEATURES = 3500;
const MIN_RENDERED_POINTS_PER_LAYER = 25;
const BOUNDARY_ROOT = `${DATA_ROOT}/boundaries`;
const BOUNDARY_QUERY_URL =
  "https://services.arcgis.com/wlVTGRSYTzAbjjiC/arcgis/rest/services/municipalityboundaries2020/FeatureServer/0/query";

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
};

const state = {
  municipalities: [],
  activeMunicipality: null,
  activeData: null,
  enabledLayers: new Set(Object.keys(layerLabels)),
  dropMarkers: [],
  popup: null,
  selectionRunId: 0,
};

const municipalitySearchAliases = {
  "27383": ["千早赤坂村", "ちはやあかさか", "ちはやあかさかむら"],
  "01668": ["白糖町"],
};

const elements = {
  menuButton: document.querySelector("#menuButton"),
  closeMenuButton: document.querySelector("#closeMenuButton"),
  sidePanel: document.querySelector("#sidePanel"),
  categoryList: document.querySelector("#categoryList"),
  openSearchButton: document.querySelector("#openSearchButton"),
  searchDialog: document.querySelector("#searchDialog"),
  cityInput: document.querySelector("#cityInput"),
  suggestions: document.querySelector("#suggestions"),
  ritualOverlay: document.querySelector("#ritualOverlay"),
  ritualCity: document.querySelector("#ritualCity"),
  resultDialog: document.querySelector("#resultDialog"),
  resultTitle: document.querySelector("#resultTitle"),
  rankLine: document.querySelector("#rankLine"),
  countGrid: document.querySelector("#countGrid"),
  storyText: document.querySelector("#storyText"),
  helpButton: document.querySelector("#helpButton"),
  helpDialog: document.querySelector("#helpDialog"),
  toast: document.querySelector("#toast"),
};

const map = new maplibregl.Map({
  container: "map",
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
    renderSuggestions("");
  } catch (error) {
    showToast("市区町村データを読み込めませんでした。dataフォルダを確認してください。");
    console.error(error);
  }
}

function wireEvents() {
  elements.menuButton.addEventListener("click", () => setMenuOpen(true));
  elements.closeMenuButton.addEventListener("click", () => setMenuOpen(false));
  elements.helpButton.addEventListener("click", () => elements.helpDialog.showModal());

  elements.openSearchButton.addEventListener("click", () => {
    elements.searchDialog.showModal();
    elements.cityInput.value = "";
    renderSuggestions("");
    requestAnimationFrame(() => elements.cityInput.focus());
  });

  elements.cityInput.addEventListener("input", () => renderSuggestions(elements.cityInput.value));

  map.on("click", (event) => {
    const pointFeatures = map.queryRenderedFeatures(event.point, {
      layers: visiblePointLayerIds(),
    });
    const features = pointFeatures.length
      ? pointFeatures
      : map.queryRenderedFeatures(event.point, {
          layers: visiblePolygonLayerIds(),
        });
    if (!features.length) return;
    showFeaturePopup(features[0], event.lngLat);
  });

  map.on("mousemove", (event) => {
    const hasPoint = map.queryRenderedFeatures(event.point, {
      layers: visiblePointLayerIds(),
    }).length;
    const hasPolygon =
      hasPoint ||
      map.queryRenderedFeatures(event.point, {
        layers: visiblePolygonLayerIds(),
      }).length;
    map.getCanvas().style.cursor = hasPolygon ? "pointer" : "";
  });
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
      <input type="checkbox" checked data-layer="${layerId}">
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
      <small>${item.feature_count.toLocaleString("ja-JP")}件</small>
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
    clearDropMarkers();
    clearMapData();
    updateBoundaryData(null);
    closePopup();
    state.activeMunicipality = municipality;
    showToast(`${municipality.label}を鑑定します。`);

    await mapReady;
    if (!isCurrentSelection(runId)) return;

    const [rawData, boundary] = await Promise.all([
      loadMunicipalityData(municipality),
      loadMunicipalityBoundary(municipality),
    ]);
    if (!isCurrentSelection(runId)) return;

    const data = filterMunicipalityData(rawData, boundary);
    state.activeData = data;

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

async function loadMunicipalityBoundary(municipality) {
  try {
    const localResponse = await fetch(
      cacheUrl(`${BOUNDARY_ROOT}/${municipality.municipality_code}.geojson`)
    );
    if (localResponse.ok) {
      const localData = await localResponse.json();
      if (localData.features?.length) return localData;
    }
  } catch (error) {
    console.warn("Local municipality boundary could not be loaded.", error);
  }

  const params = new URLSearchParams({
    where: `JCODE='${municipality.municipality_code}'`,
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
      if (data.features?.length) return data;
    } catch (error) {
      if (attempt === 2) {
        console.warn("Municipality boundary could not be loaded.", error);
      }
    }
    await wait(250 * (attempt + 1));
  }
  return null;
}

function wait(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

function filterMunicipalityData(data, boundary) {
  if (!boundary?.features?.length) return data;

  const boundaryIndex = buildBoundaryIndex(boundary);
  if (!boundaryIndex.length) return data;

  let removedOutsidePoints = 0;
  const features = (data.features || []).flatMap((feature) => {
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

  return {
    ...data,
    features,
    layer_counts: layerCounts,
    total_features: features.length,
    removed_outside_points: removedOutsidePoints,
  };
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
  });
  raiseBoundaryLayers();
  raisePointLayers();
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
    [pointLayerName(layerId), polygonLayerName(layerId)].forEach((id) => {
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

function visibleLayerIds() {
  return [...visiblePointLayerIds(), ...visiblePolygonLayerIds()];
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

function sourceName(layerId) {
  return `source-${layerId}`;
}

function pointLayerName(layerId) {
  return `points-${layerId}`;
}

function polygonLayerName(layerId) {
  return `polygons-${layerId}`;
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
  await wait(1500);
  if (isCurrentSelection(runId)) {
    elements.ritualOverlay.classList.remove("active");
  }
}

function dropRepresentativePins(features) {
  clearDropMarkers();
  const pointFeatures = features
    .filter((feature) => state.enabledLayers.has(feature.properties?.layer_id))
    .filter((feature) => feature.geometry?.type === "Point")
    .slice(0, MAX_DROP_PINS);

  pointFeatures.forEach((feature, index) => {
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

function showResult(data, renderMeta = null) {
  const counts = data.layer_counts || {};
  const total = data.total_features || data.features?.length || 0;
  elements.resultTitle.textContent = `${data.pref} ${data.city}`;
  const renderNote = renderMeta?.omittedPoints
    ? ` 地図は代表${renderMeta.renderedPoints.toLocaleString("ja-JP")}件を軽量表示中。`
    : "";
  elements.rankLine.textContent = `${rankText(total)}${renderNote}`;
  elements.storyText.textContent = data.display_comment || "この街には、まだ見つけていない地域の手がかりが眠っていそうです。";
  elements.countGrid.innerHTML = "";

  Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .forEach(([layerId, count]) => {
      const card = document.createElement("div");
      card.className = "count-card";
      card.innerHTML = `
        <span>${escapeHtml(layerLabels[layerId] || layerId)}</span>
        <strong>${Number(count).toLocaleString("ja-JP")}</strong>
      `;
      elements.countGrid.appendChild(card);
    });

  if (!elements.resultDialog.open) {
    elements.resultDialog.showModal();
  }
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
  const html = `
    <div class="popup-card">
      <h3>${escapeHtml(displayFeatureName(props))}</h3>
      <p>${escapeHtml(layerLabels[layerId] || layerId)}</p>
      ${props.subarea_name ? `<p>${escapeHtml(props.subarea_name)}</p>` : ""}
      ${props.address ? `<p>${escapeHtml(props.address)}</p>` : ""}
      ${props.source ? `<p>出典: ${escapeHtml(props.source)}</p>` : ""}
    </div>
  `;
  state.popup = new maplibregl.Popup({ closeButton: true, maxWidth: "320px" })
    .setLngLat(lngLat)
    .setHTML(html)
    .addTo(map);
}

function displayFeatureName(props) {
  const layerId = props.layer_id || "unknown";
  const rawName = String(props.name || "").trim();
  const invalidNames = new Set(["名称不明", "不明"]);
  if (rawName && !/^\d+$/.test(rawName) && !invalidNames.has(rawName)) {
    return rawName;
  }
  const layerLabel = layerLabels[layerId] || "区域";
  const municipalityName = props.municipality_name || state.activeData?.city;
  if (municipalityName) {
    return `${municipalityName}の${layerLabel}`;
  }
  return layerLabel;
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
  showToast.timer = setTimeout(() => elements.toast.classList.remove("show"), 2800);
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
