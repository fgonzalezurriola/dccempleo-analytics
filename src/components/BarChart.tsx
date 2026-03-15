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

/** Brand-representative colors for technologies */
const TECH_COLORS: Record<string, string> = {
  // Languages
  python: '#3776AB',
  javascript: '#F0DB4F',
  typescript: '#3178C6',
  ruby: '#CC342D',
  java: '#E76F00',
  flutter: '#02569B',
  php: '#777BB4',
  go: '#00ADD8',
  'c#': '#68217A',
  c: '#555555',
  'c++': '#00599C',
  kotlin: '#7F52FF',
  swift: '#F05138',
  bash: '#4EAA25',
  dart: '#0175C2',
  rust: '#CE412B',
  scala: '#DC322F',
  r: '#276DC3',
  perl: '#39457E',
  elixir: '#6E4A7E',

  // Databases
  postgresql: '#336791',
  sql: '#CC7832',
  mongodb: '#47A248',
  mysql: '#4479A1',
  nosql: '#8B5E3C',
  firebase: '#FFCA28',
  dynamodb: '#4053D6',
  'sql server': '#CC2927',
  redis: '#DC382D',
  bigquery: '#669DF6',
  supabase: '#3ECF8E',
  elasticsearch: '#005571',
  oracle: '#F80000',
  mariadb: '#003545',
  redshift: '#8C4FFF',

  // Cloud
  aws: '#FF9900',
  gcp: '#4285F4',
  azure: '#0078D4',
  vercel: '#000000',
  'fly.io': '#7B3FE4',
  cloudflare: '#F38020',
  digitalocean: '#0080FF',
  railway: '#0B0D0E',
  render: '#46E3B7',

  // Frontend frameworks
  react: '#61DAFB',
  'next.js': '#111111',
  vue: '#42B883',
  nuxt: '#00DC82',
  angular: '#DD0031',
  angularjs: '#E23237',
  svelte: '#FF3E00',
  astro: '#FF5D01',

  // AI Dev Tools
  cursor: '#7B61FF',
  'claude code': '#D97706',
  'github copilot': '#000000',
  codex: '#10A37F',
  antigravity: '#6366F1',
  'claude desktop': '#D97706',
  'herramientas de ia': '#6B7280',
};

interface BarChartProps {
  data: ChartDataItem[];
  color?: string;
  height?: number;
}

export function BarChart({ data, color, height = 300 }: BarChartProps) {
  if (!data || data.length === 0) {
    return <div className="empty-state">Sin datos para este filtro</div>;
  }

  const getColor = (item: ChartDataItem, index: number) => {
    const techColor = TECH_COLORS[item.name.toLowerCase()];
    if (techColor) return techColor;
    return color || COLORS[index % COLORS.length];
  };

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: '#faf6f0',
      borderColor: '#c9b99a',
      borderWidth: 1,
      textStyle: {
        fontFamily: "'Geist', Arial, system-ui, sans-serif",
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
        interval: 0,
        rotate: 35,
        fontFamily: "'Geist', Arial, system-ui, sans-serif",
        fontSize: 11,
        color: '#5c4f3a',
      },
      axisLine: { lineStyle: { color: '#c9b99a' } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        fontFamily: "'Geist', Arial, system-ui, sans-serif",
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
            color: getColor(d, i),
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

export { COLORS, TECH_COLORS };
