export const CHART_COLORS = {
  navy: '#0f172a',
  emerald: '#10b981',
  crimson: '#ef4444',
  amber: '#f59e0b',
  slate: '#64748b',
  gridline: '#e2e8f0',
}

export const CHART_PALETTE = [
  CHART_COLORS.navy,
  CHART_COLORS.emerald,
  CHART_COLORS.crimson,
  CHART_COLORS.amber,
  CHART_COLORS.slate,
  '#94a3b8',
]

const FONT_SANS = 'Inter, ui-sans-serif, system-ui, sans-serif'
const FONT_MONO = "'JetBrains Mono', ui-monospace, SFMono-Regular, monospace"

export const BASE_LAYOUT = {
  font: { family: FONT_SANS, color: CHART_COLORS.slate, size: 12 },
  paper_bgcolor: 'transparent',
  plot_bgcolor: 'transparent',
  margin: { l: 48, r: 16, t: 16, b: 32 },
  xaxis: {
    gridcolor: CHART_COLORS.gridline,
    linecolor: CHART_COLORS.gridline,
    tickfont: { family: FONT_MONO, size: 11 },
    zeroline: false,
  },
  yaxis: {
    gridcolor: CHART_COLORS.gridline,
    linecolor: CHART_COLORS.gridline,
    tickfont: { family: FONT_MONO, size: 11 },
    zeroline: false,
  },
}

export const CHART_FONTS = { sans: FONT_SANS, mono: FONT_MONO }
