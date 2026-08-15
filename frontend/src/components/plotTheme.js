export const CHART_COLORS = {
  groupA: "#27728a",
  groupB: "#a35c35",
  ink: "#172027",
  muted: "#617078",
  grid: "#e2e8ea",
  danger: "#a9432c",
  interval: "#27728a"
};

export const PLOT_CONFIG = {
  displaylogo: false,
  responsive: true,
  scrollZoom: false,
  modeBarButtonsToRemove: ["lasso2d", "select2d", "autoScale2d"]
};

export const BASE_AXIS = {
  automargin: true,
  gridcolor: CHART_COLORS.grid,
  linecolor: "#c6d0d4",
  tickcolor: "#c6d0d4",
  tickfont: { color: CHART_COLORS.muted, size: 11 },
  titlefont: { color: "#40515b", size: 12 },
  zerolinecolor: "#b8c5ca"
};

export const BASE_LAYOUT = {
  autosize: true,
  margin: { l: 56, r: 20, t: 54, b: 52 },
  paper_bgcolor: "#ffffff",
  plot_bgcolor: "#fbfcfc",
  colorway: [CHART_COLORS.groupA, CHART_COLORS.groupB],
  font: { color: CHART_COLORS.ink, family: "Inter, system-ui, sans-serif" },
  title: { x: 0.04, xanchor: "left", font: { color: CHART_COLORS.ink, size: 15 } },
  legend: {
    orientation: "h",
    x: 0,
    y: 1.14,
    font: { color: CHART_COLORS.muted, size: 11 }
  },
  hoverlabel: {
    bgcolor: CHART_COLORS.ink,
    bordercolor: CHART_COLORS.ink,
    font: { color: "#ffffff", size: 12 }
  },
  hovermode: "closest"
};

export function axisLayout(overrides = {}) {
  return { ...BASE_AXIS, ...overrides };
}
