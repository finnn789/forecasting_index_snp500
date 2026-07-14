import { useEffect, useRef } from 'react'
import Plotly from 'plotly.js-dist-min'

const DEFAULT_CONFIG = {
  displayModeBar: false,
  responsive: true,
}

export function usePlotlyChart({ data, layout, config }) {
  const containerRef = useRef(null)

  useEffect(() => {
    const node = containerRef.current
    if (!node) return

    let cancelled = false
    let resizeObserver

    // Plotly.react() mutates the layout object it's given in place (baking
    // resolved axis `type`/`range`/`autorange` back onto layout.xaxis /
    // layout.yaxis). Chart components build their layout from the shared
    // BASE_LAYOUT constant (chartTheme.js) and don't all override xaxis/yaxis
    // with a fresh object — so without cloning here, one chart's inferred
    // axis type (e.g. 'date') leaks into BASE_LAYOUT and corrupts every
    // other chart that reuses it (e.g. a categorical heatmap axis rendering
    // as dates after a date-series chart ran first).
    const layoutCopy = JSON.parse(JSON.stringify(layout))

    Plotly.react(node, data, layoutCopy, { ...DEFAULT_CONFIG, ...config })
      .then(() => {
        // Only start observing once the initial draw has finished — starting
        // earlier races Plotly's internal layout setup and throws deep inside
        // plotly.js ("Cannot read properties of undefined (reading 'anchor')").
        if (cancelled) return
        resizeObserver = new ResizeObserver(() => {
          try {
            Plotly.Plots.resize(node)
          } catch {
            // ignore transient resize errors (e.g. during unmount)
          }
        })
        resizeObserver.observe(node)
      })
      .catch((error) => {
        console.error('Plotly render failed:', error)
      })

    return () => {
      cancelled = true
      resizeObserver?.disconnect()
      Plotly.purge(node)
    }
  }, [data, layout, config])

  return containerRef
}
