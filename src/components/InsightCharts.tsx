import ReactEChartsCore from 'echarts-for-react/lib/core';
import * as echarts from 'echarts/core';
import type { EChartsCoreOption } from 'echarts/core';
import { BarChart as EBarChart, LineChart as ELineChart } from 'echarts/charts';
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import type { AiToolsTimeline, MonthlyVolume, SeniorityShiftYear, TechTrends } from './types';
import { COLORS, TECH_COLORS } from './BarChart';

echarts.use([EBarChart, ELineChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer]);

/** Resolve a color for a tech/tool name, falling back to positional palette */
function getTechColor(name: string, index: number): string {
  return TECH_COLORS[name.toLowerCase()] ?? COLORS[index % COLORS.length];
}

const chartTextStyle = {
  fontFamily: "'Geist', Arial, system-ui, sans-serif",
  color: '#5c4f3a',
};

const tooltipStyle = {
  backgroundColor: '#faf6f0',
  borderColor: '#c9b99a',
  borderWidth: 1,
  textStyle: { ...chartTextStyle, fontSize: 12, color: '#2c2418' },
};

const toolNameMap: Record<string, string> = {
  cursor: 'Cursor',
  'claude code': 'Claude Code',
  'github copilot': 'GitHub Copilot',
  codex: 'Codex',
  antigravity: 'Antigravity',
  'claude desktop': 'Claude Desktop',
  'herramientas de ia': '"Herramientas de IA"',
};

const partialYearMarkLine = {
  symbol: 'none' as const,
  label: {
    show: true,
    formatter: '2026 parcial',
    color: '#111111',
    fontFamily: "'Geist', Arial, system-ui, sans-serif",
    fontSize: 11,
    position: 'end' as const,
  },
  lineStyle: {
    color: '#111111',
    type: 'dashed' as const,
    width: 1.5,
  },
  z: 10,
  data: [[
    { xAxis: '2026', yAxis: 'min' },
    { xAxis: '2026', yAxis: 'max' },
  ]],
};

/* ═══════════════ AI Tools Timeline ═══════════════ */

export function AiToolsChart({ data }: { data: AiToolsTimeline | null }) {
  if (!data || data.months.length === 0) {
    return <div className="empty-state">Sin datos de herramientas AI</div>;
  }

  const tools = Object.keys(data.tools);

  const option: EChartsCoreOption = {
    tooltip: {
      ...tooltipStyle,
      trigger: 'axis',
    },
    legend: {
      data: tools.map((t) => toolNameMap[t] || t),
      bottom: 0,
      textStyle: { ...chartTextStyle, fontSize: 11 },
      itemWidth: 16,
      itemHeight: 3,
    },
    grid: {
      left: 12,
      right: 16,
      top: 12,
      bottom: 40,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: data.months,
      axisLabel: { ...chartTextStyle, fontSize: 10, rotate: 35 },
      axisLine: { lineStyle: { color: '#c9b99a' } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: { ...chartTextStyle, fontSize: 11, color: '#8a7d6b' },
      splitLine: { lineStyle: { color: '#e8dcc8', type: 'dashed' } },
      axisLine: { show: false },
    },
    series: tools.map((tool, i) => ({
      name: toolNameMap[tool] || tool,
      type: 'line' as const,
      data: data.tools[tool],
      smooth: true,
      symbol: 'circle',
      symbolSize: 5,
      lineStyle: { width: 2.5, color: getTechColor(tool, i) },
      itemStyle: { color: getTechColor(tool, i) },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: getTechColor(tool, i) + '30' },
          { offset: 1, color: getTechColor(tool, i) + '05' },
        ]),
      },
    })),
    animationDuration: 800,
    animationEasing: 'cubicOut',
  };

  return (
    <ReactEChartsCore
      echarts={echarts}
      option={option}
      style={{ height: 340, width: '100%' }}
      notMerge
      lazyUpdate
    />
  );
}

/* ═══════════════ Monthly Volume ═══════════════ */

export function MonthlyVolumeChart({ data }: { data: MonthlyVolume[] | null }) {
  if (!data || data.length === 0) {
    return <div className="empty-state">Sin datos de volumen mensual</div>;
  }

  const option: EChartsCoreOption = {
    tooltip: {
      ...tooltipStyle,
      trigger: 'axis',
    },
    grid: {
      left: 12,
      right: 16,
      top: 12,
      bottom: 0,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: data.map((d) => d.month),
      axisLabel: { ...chartTextStyle, fontSize: 10, rotate: 35 },
      axisLine: { lineStyle: { color: '#c9b99a' } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLabel: { ...chartTextStyle, fontSize: 11, color: '#8a7d6b' },
      splitLine: { lineStyle: { color: '#e8dcc8', type: 'dashed' } },
      axisLine: { show: false },
    },
    series: [
      {
        type: 'line',
        data: data.map((d) => d.count),
        smooth: true,
        symbol: 'none',
        lineStyle: { width: 2, color: '#6b8f71' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#6b8f7130' },
            { offset: 1, color: '#6b8f7105' },
          ]),
        },
      },
    ],
    animationDuration: 800,
  };

  return (
    <ReactEChartsCore
      echarts={echarts}
      option={option}
      style={{ height: 280, width: '100%' }}
      notMerge
      lazyUpdate
    />
  );
}

/* ═══════════════ AI Adoption ═══════════════ */

export function AiAdoptionChart({
  aiTools,
  monthlyVolume,
}: {
  aiTools: AiToolsTimeline | null;
  monthlyVolume: MonthlyVolume[] | null;
}) {
  if (!aiTools || !monthlyVolume || aiTools.months.length === 0) {
    return <div className="empty-state">Sin datos de adopción de AI Dev Tools</div>;
  }

  const volumeByMonth = new Map(monthlyVolume.map((item) => [item.month, item.count]));
  const rows = aiTools.months
    .map((month, index) => {
      const total = volumeByMonth.get(month) ?? 0;
      const withAi = aiTools.total_per_month[index] ?? 0;
      return {
        month,
        total,
        withAi: Math.min(withAi, total),
        withoutAi: Math.max(total - withAi, 0),
      };
    })
    .filter((row) => row.total > 0);

  const option: EChartsCoreOption = {
    tooltip: {
      ...tooltipStyle,
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: unknown) => {
        const items = (Array.isArray(params) ? params : [params]) as Array<{ axisValue?: string }>;
        const month = String(items[0]?.axisValue ?? '');
        const row = rows.find((item) => item.month === month);
        if (!row) return month;
        const percentage = (count: number) => `${((count / row.total) * 100).toFixed(1)}%`;
        return [
          `<strong>${month}</strong>`,
          `Mencionan AI Dev Tools: ${row.withAi} (${percentage(row.withAi)})`,
          `No mencionan AI Dev Tools: ${row.withoutAi} (${percentage(row.withoutAi)})`,
          `Total: ${row.total}`,
        ].join('<br/>');
      },
    },
    legend: {
      data: ['Mencionan AI Dev Tools', 'No mencionan AI Dev Tools'],
      bottom: 0,
      textStyle: { ...chartTextStyle, fontSize: 11 },
      itemWidth: 16,
      itemHeight: 10,
    },
    grid: {
      left: 12,
      right: 16,
      top: 12,
      bottom: 40,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: rows.map((row) => row.month),
      axisLabel: { ...chartTextStyle, fontSize: 10, rotate: 35 },
      axisLine: { lineStyle: { color: '#c9b99a' } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLabel: { ...chartTextStyle, fontSize: 11, color: '#8a7d6b', formatter: '{value}%' },
      splitLine: { lineStyle: { color: '#e8dcc8', type: 'dashed' } },
      axisLine: { show: false },
    },
    series: [
      {
        name: 'Mencionan AI Dev Tools',
        type: 'bar',
        stack: 'adoption',
        data: rows.map((row) => (row.withAi / row.total) * 100),
        itemStyle: { color: '#c4654a' },
      },
      {
        name: 'No mencionan AI Dev Tools',
        type: 'bar',
        stack: 'adoption',
        data: rows.map((row) => (row.withoutAi / row.total) * 100),
        itemStyle: { color: '#c9b99a' },
      },
    ],
    animationDuration: 600,
  };

  return (
    <ReactEChartsCore
      echarts={echarts}
      option={option}
      style={{ height: 300, width: '100%' }}
      notMerge
      lazyUpdate
    />
  );
}

/* ═══════════════ Seniority Shift ═══════════════ */

export function SeniorityShiftChart({ data }: { data: SeniorityShiftYear[] | null }) {
  if (!data || data.length === 0) {
    return <div className="empty-state">Sin datos de seniority</div>;
  }

  const buckets = [
    { key: 'practice', label: 'Práctica' },
    { key: 'junior', label: 'Junior' },
    { key: 'semi_senior', label: 'Semi-Senior' },
    { key: 'senior', label: 'Senior' },
  ];

  const option: EChartsCoreOption = {
    tooltip: {
      ...tooltipStyle,
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
    },
    legend: {
      data: buckets.map((b) => b.label),
      bottom: 0,
      textStyle: { ...chartTextStyle, fontSize: 11 },
      itemWidth: 16,
      itemHeight: 10,
    },
    grid: {
      left: 12,
      right: 16,
      top: 12,
      bottom: 40,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: data.map((d) => d.year),
      axisLabel: { ...chartTextStyle, fontSize: 12 },
      axisLine: { lineStyle: { color: '#c9b99a' } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLabel: { ...chartTextStyle, fontSize: 11, color: '#8a7d6b' },
      splitLine: { lineStyle: { color: '#e8dcc8', type: 'dashed' } },
      axisLine: { show: false },
    },
    series: buckets.map((bucket, i) => ({
      name: bucket.label,
      type: 'bar' as const,
      stack: 'seniority',
      data: data.map((d) => (d as unknown as Record<string, number>)[bucket.key] || 0),
      itemStyle: {
        color: COLORS[i],
        borderRadius: i === buckets.length - 1 ? [2, 2, 0, 0] : undefined,
      },
      markLine: i === 0 ? partialYearMarkLine : undefined,
      emphasis: {
        itemStyle: { shadowBlur: 6, shadowColor: 'rgba(0,0,0,0.1)' },
      },
    })),
    animationDuration: 600,
  };

  return (
    <ReactEChartsCore
      echarts={echarts}
      option={option}
      style={{ height: 280, width: '100%' }}
      notMerge
      lazyUpdate
    />
  );
}

/* ═══════════════ Tech Trends ═══════════════ */

export function TechTrendsChart({ data }: { data: TechTrends | null }) {
  if (!data || data.years.length === 0) {
    return <div className="empty-state">Sin datos de tendencias</div>;
  }

  const techs = Object.keys(data.technologies);

  const option: EChartsCoreOption = {
    tooltip: {
      ...tooltipStyle,
      trigger: 'axis',
    },
    legend: {
      data: techs,
      bottom: 0,
      textStyle: { ...chartTextStyle, fontSize: 11 },
      itemWidth: 16,
      itemHeight: 3,
    },
    grid: {
      left: 12,
      right: 16,
      top: 12,
      bottom: 40,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: data.years,
      axisLabel: { ...chartTextStyle, fontSize: 12 },
      axisLine: { lineStyle: { color: '#c9b99a' } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLabel: { ...chartTextStyle, fontSize: 11, color: '#8a7d6b' },
      splitLine: { lineStyle: { color: '#e8dcc8', type: 'dashed' } },
      axisLine: { show: false },
    },
    series: techs.map((tech, i) => ({
      name: tech,
      type: 'line' as const,
      data: data.technologies[tech],
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: { width: 2.5, color: getTechColor(tech, i) },
      itemStyle: { color: getTechColor(tech, i) },
      markLine: i === 0 ? partialYearMarkLine : undefined,
    })),
    animationDuration: 800,
  };

  return (
    <ReactEChartsCore
      echarts={echarts}
      option={option}
      style={{ height: 280, width: '100%' }}
      notMerge
      lazyUpdate
    />
  );
}
