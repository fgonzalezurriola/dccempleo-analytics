import ReactEChartsCore from 'echarts-for-react/lib/core';
import * as echarts from 'echarts/core';
import { BarChart as EBarChart, LineChart as ELineChart } from 'echarts/charts';
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import type { ChartDataItem } from './types';

echarts.use([EBarChart, ELineChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer]);

const COLORS = [
  '#c4654a', '#6b8f71', '#c4944a', '#5b7b8f',
  '#8f6b7b', '#7b8f5b', '#4a6bc4', '#c46ba0',
  '#6b8fc4', '#8f7b5b', '#5b8f8f', '#c4654a',
  '#6bc48f', '#8f5b7b', '#c49a4a',
];

interface BarChartProps {
  data: ChartDataItem[];
  color?: string;
  height?: number;
}

export function BarChart({ data, color, height = 300 }: BarChartProps) {
  if (!data || data.length === 0) {
    return <div className="empty-state">Sin datos para este filtro</div>;
  }

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: '#faf6f0',
      borderColor: '#c9b99a',
      borderWidth: 1,
      textStyle: {
        fontFamily: "'DM Sans', system-ui, sans-serif",
        color: '#2c2418',
        fontSize: 12,
      },
    },
    grid: {
      left: 12,
      right: 16,
      top: 8,
      bottom: 0,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: data.map((d) => d.name),
      axisLabel: {
        rotate: 35,
        fontFamily: "'DM Sans', system-ui, sans-serif",
        fontSize: 11,
        color: '#5c4f3a',
      },
      axisLine: { lineStyle: { color: '#c9b99a' } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        fontFamily: "'DM Sans', system-ui, sans-serif",
        fontSize: 11,
        color: '#8a7d6b',
      },
      splitLine: { lineStyle: { color: '#e8dcc8', type: 'dashed' } },
      axisLine: { show: false },
    },
    series: [
      {
        type: 'bar',
        data: data.map((d, i) => ({
          value: d.count,
          itemStyle: {
            color: color || COLORS[i % COLORS.length],
            borderRadius: [2, 2, 0, 0],
          },
        })),
        barMaxWidth: 36,
        emphasis: {
          itemStyle: {
            shadowBlur: 8,
            shadowColor: 'rgba(0,0,0,0.15)',
          },
        },
      },
    ],
    animationDuration: 600,
    animationEasing: 'cubicOut',
  };

  return (
    <ReactEChartsCore
      echarts={echarts}
      option={option}
      style={{ height, width: '100%' }}
      notMerge
      lazyUpdate
    />
  );
}

export { COLORS };
