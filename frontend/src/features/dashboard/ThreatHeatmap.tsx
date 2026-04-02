import { useQuery } from '@tanstack/react-query'
import { useEffect, useRef } from 'react'
import * as d3 from 'd3'
import { fetchHeatmap } from '../../lib/dashboardApi'
import { Spinner } from '../../components/ui/Spinner'
import { ErrorBanner } from '../../components/ui/ErrorBanner'
import type { HeatmapData } from '../../types'

/** Pure function — exported for unit testing. */
export function buildCellMap(data: HeatmapData): Map<string, number> {
  const map = new Map<string, number>()
  for (const cell of data.cells) {
    map.set(`${cell.actorId}:${cell.assetId}`, cell.intensity)
  }
  return map
}

function HeatmapSvg({ data }: { data: HeatmapData }) {
  const ref = useRef<SVGSVGElement>(null)

  useEffect(() => {
    if (!ref.current) return
    const svg = d3.select(ref.current)
    svg.selectAll('*').remove()

    const margin = { top: 40, right: 20, bottom: 20, left: 160 }
    const cellSize = 48
    const width = data.assets.length * cellSize + margin.left + margin.right
    const height = data.actors.length * cellSize + margin.top + margin.bottom

    svg.attr('width', width).attr('height', height)

    const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

    // Scales
    const x = d3.scaleBand()
      .domain(data.assets.map((a) => a.assetId))
      .range([0, data.assets.length * cellSize])
      .padding(0.05)

    const y = d3.scaleBand()
      .domain(data.actors.map((a) => a.groupId))
      .range([0, data.actors.length * cellSize])
      .padding(0.05)

    const color = d3.scaleSequential([0, 1], d3.interpolateReds)
    const cellMap = buildCellMap(data)

    // Cells
    for (const actor of data.actors) {
      for (const asset of data.assets) {
        const intensity = cellMap.get(`${actor.groupId}:${asset.assetId}`) ?? 0
        g.append('rect')
          .attr('x', x(asset.assetId) ?? 0)
          .attr('y', y(actor.groupId) ?? 0)
          .attr('width', x.bandwidth())
          .attr('height', y.bandwidth())
          .attr('fill', intensity === 0 ? '#f3f4f6' : color(intensity))
          .attr('rx', 3)
      }
    }

    // Asset labels (top)
    g.append('g').call(
      d3.axisTop(x)
        .tickFormat((id) => data.assets.find((a) => a.assetId === id)?.name ?? id)
    )
      .selectAll('text')
      .style('font-size', '11px')
      .attr('transform', 'rotate(-30)')
      .style('text-anchor', 'start')

    // Actor labels (left)
    g.append('g').call(
      d3.axisLeft(y)
        .tickFormat((id) => data.actors.find((a) => a.groupId === id)?.name ?? id)
    )
      .selectAll('text')
      .style('font-size', '11px')
  }, [data])

  return <svg ref={ref} />
}

export function ThreatHeatmap() {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['heatmap'],
    queryFn: fetchHeatmap,
    staleTime: 30_000,
  })

  return (
    <div>
      <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide mb-3">
        Threat Heatmap
      </h2>
      <div
        data-testid="heatmap-container"
        className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4"
      >
        {isLoading && <Spinner />}
        {isError && (
          <ErrorBanner
            message="Failed to load heatmap"
            onRetry={() => void refetch()}
          />
        )}
        {data && <HeatmapSvg data={data} />}
      </div>
    </div>
  )
}
