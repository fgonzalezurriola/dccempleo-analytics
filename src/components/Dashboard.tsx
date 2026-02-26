import { useState, useEffect, useCallback } from 'react';
import { motion } from 'motion/react';
import { BarChart } from './BarChart';
import {
  AiToolsChart,
  MonthlyVolumeChart,
  SeniorityShiftChart,
  TechTrendsChart,
} from './InsightCharts';
import type {
  Section1Data,
  MetricsData,
  AiToolsTimeline,
  MonthlyVolume,
  SeniorityShiftYear,
  TechTrends,
  YearFilter,
  SeniorityFilter,
} from './types';

/* ═══════════════ Constants ═══════════════ */

const YEARS: { value: YearFilter; label: string; preview?: boolean }[] = [
  { value: 'all', label: 'Todos' },
  { value: '2023', label: '2023' },
  { value: '2024', label: '2024' },
  { value: '2025', label: '2025' },
  { value: '2026', label: '2026 (Parcial)', preview: true },
];

const SENIORITIES: { value: SeniorityFilter; label: string }[] = [
  { value: 'all', label: 'Todos' },
  { value: 'practice', label: 'Práctica' },
  { value: 'junior', label: 'Junior' },
  { value: 'semi_senior', label: 'Semi-Senior' },
  { value: 'senior', label: 'Senior' },
];

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0 },
};

const staggerContainer = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08 } },
};

/* ═══════════════ Helpers ═══════════════ */

async function fetchJSON<T>(url: string): Promise<T | null> {
  try {
    const res = await fetch(url);
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

/* ═══════════════ Dashboard ═══════════════ */

export default function Dashboard() {
  const [year, setYear] = useState<YearFilter>('all');
  const [seniority, setSeniority] = useState<SeniorityFilter>('all');

  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [section1, setSection1] = useState<Section1Data | null>(null);

  const [aiTools, setAiTools] = useState<AiToolsTimeline | null>(null);
  const [monthlyVolume, setMonthlyVolume] = useState<MonthlyVolume[] | null>(null);
  const [seniorityShift, setSeniorityShift] = useState<SeniorityShiftYear[] | null>(null);
  const [techTrends, setTechTrends] = useState<TechTrends | null>(null);

  // Fetch metrics once
  useEffect(() => {
    fetchJSON<MetricsData>('/data/metrics.json').then(setMetrics);
  }, []);

  // Fetch section 1 when filters change
  const loadSection1 = useCallback(async () => {
    const file = `/data/section1/${year}_${seniority}.json`;
    const data = await fetchJSON<Section1Data>(file);
    setSection1(data);
  }, [year, seniority]);

  useEffect(() => {
    loadSection1();
  }, [loadSection1]);

  // Fetch section 2 once (static, not filtered)
  useEffect(() => {
    Promise.all([
      fetchJSON<AiToolsTimeline>('/data/section2/ai_tools_timeline.json'),
      fetchJSON<MonthlyVolume[]>('/data/section2/monthly_volume.json'),
      fetchJSON<SeniorityShiftYear[]>('/data/section2/seniority_shift.json'),
      fetchJSON<TechTrends>('/data/section2/tech_trends.json'),
    ]).then(([ai, vol, sen, tech]) => {
      setAiTools(ai);
      setMonthlyVolume(vol);
      setSeniorityShift(sen);
      setTechTrends(tech);
    });
  }, []);

  // Filter out 2020 and 2026 from Insights charts (insufficient data)
  const EXCLUDED_YEARS = new Set(['2020', '2026']);

  const filteredSeniorityShift = seniorityShift?.filter(
    (d) => !EXCLUDED_YEARS.has(d.year),
  ) ?? null;

  const filteredTechTrends: TechTrends | null = techTrends
    ? (() => {
      const validIdx = techTrends.years
        .map((y, i) => ({ y, i }))
        .filter(({ y }) => !EXCLUDED_YEARS.has(y));
      return {
        years: validIdx.map(({ y }) => y),
        technologies: Object.fromEntries(
          Object.entries(techTrends.technologies).map(([tech, values]) => [
            tech,
            validIdx.map(({ i }) => values[i]),
          ]),
        ),
      };
    })()
    : null;

  const filteredMonthlyVolume = monthlyVolume?.filter(
    (d) => !d.month.startsWith('2020') && !d.month.startsWith('2026'),
  ) ?? null;

  const filteredAiTools: AiToolsTimeline | null = aiTools
    ? (() => {
      const validIdx = aiTools.months
        .map((m, i) => ({ m, i }))
        .filter(({ m }) => !m.startsWith('2020') && !m.startsWith('2026'));
      return {
        months: validIdx.map(({ m }) => m),
        tools: Object.fromEntries(
          Object.entries(aiTools.tools).map(([tool, values]) => [
            tool,
            validIdx.map(({ i }) => values[i]),
          ]),
        ),
        total_per_month: validIdx.map(({ i }) => aiTools.total_per_month[i]),
      };
    })()
    : null;

  // KPI for current year
  const yearMetrics = metrics?.years[year];
  const totalPosts = yearMetrics?.total ?? metrics?.total_messages ?? 0;
  const entryLevel = yearMetrics?.entry_level ?? metrics?.entry_level_messages ?? 0;
  const entryPct = totalPosts > 0 ? ((entryLevel / totalPosts) * 100).toFixed(1) : '0';

  return (
    <>
      {/* ─── HEADER ─── */}
      <motion.header
        className="site-header"
        initial="hidden"
        animate="visible"
        variants={fadeUp}
        transition={{ duration: 0.5 }}
      >
        <h1 className="site-title">DCC Empleo Analytics</h1>
        <p className="site-subtitle">
          Ofertas laborales tech en Chile - canal de telegram DCCEmpleoSinFiltro
        </p>
        {metrics && (
          <p className="site-meta">{metrics.date_span} · {metrics.total_messages.toLocaleString()} publicaciones</p>
        )}
      </motion.header>

      {/* ═══════════════ SECTION 1 ═══════════════ */}
      <motion.section
        initial="hidden"
        animate="visible"
        variants={staggerContainer}
      >
        <motion.div className="section-header" variants={fadeUp} transition={{ duration: 0.4 }}>
          <h2 className="section-title">Análisis de las ofertas de DCCEmpleoSinFiltro</h2>
          <p className="section-description">
            Nota: Este canal tiene un ambiente universitario, <br />
            No concluyas cosas sobre la gran cantidad de ofertas a entry level. <br />
            Hay evidencia de sobra de que el mercado junior está muy complicado.
          </p>
        </motion.div>

        {/* Filters */}
        <motion.div
          style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'center', marginBottom: '1.25rem' }}
          variants={fadeUp}
          transition={{ duration: 0.4 }}
        >
          <div className="filter-bar">
            <span className="filter-label">Año</span>
            {YEARS.map((y) => (
              <button
                key={y.value}
                className={`filter-btn${year === y.value ? ' active' : ''}${y.preview ? ' preview' : ''}`}
                onClick={() => setYear(y.value)}
              >
                {y.label}
              </button>
            ))}
          </div>

          <div className="filter-bar">
            <span className="filter-label">Nivel</span>
            {SENIORITIES.map((s) => (
              <button
                key={s.value}
                className={`filter-btn${seniority === s.value ? ' active' : ''}`}
                onClick={() => setSeniority(s.value)}
              >
                {s.label}
              </button>
            ))}
          </div>
        </motion.div>

        {/* KPI chips */}
        <motion.div className="kpi-strip" variants={fadeUp} transition={{ duration: 0.4 }}>
          <div className="kpi-chip">
            <span className="kpi-value">{totalPosts.toLocaleString()}</span>
            <span className="kpi-label">publicaciones</span>
          </div>
          <div className="kpi-chip">
            <span className="kpi-value">{entryLevel.toLocaleString()}</span>
            <span className="kpi-label">entry-level</span>
          </div>
          <div className="kpi-chip">
            <span className="kpi-value">{entryPct}%</span>
            <span className="kpi-label">son entry-level</span>
          </div>
          {year === 'all' && metrics && (
            <div className="kpi-chip">
              <span className="kpi-value">{metrics.messages_with_ai_dev_tools}</span>
              <span className="kpi-label">mencionan AI dev tools</span>
            </div>
          )}
        </motion.div>

        {/* Charts */}
        <motion.div className="charts-grid-3" variants={staggerContainer}>
          <motion.div className="chart-card" variants={fadeUp} transition={{ duration: 0.4 }}>
            <h3 className="chart-card-title">Top Lenguajes</h3>
            <BarChart data={section1?.languages ?? []} />
          </motion.div>

          <motion.div className="chart-card" variants={fadeUp} transition={{ duration: 0.4 }}>
            <h3 className="chart-card-title">Top Bases de Datos</h3>
            <BarChart data={section1?.databases ?? []} />
          </motion.div>

          <motion.div className="chart-card" variants={fadeUp} transition={{ duration: 0.4 }}>
            <h3 className="chart-card-title">Top Cloud</h3>
            <BarChart data={section1?.clouds ?? []} />
          </motion.div>
        </motion.div>
      </motion.section>

      {/* ─── DIVIDER ─── */}
      <hr className="section-divider" />

      {/* ═══════════════ SECTION 2 — Insights & Tendencias ═══════════════ */}
      <motion.section
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.1 }}
        variants={staggerContainer}
      >
        <motion.div className="section-header" variants={fadeUp} transition={{ duration: 0.4 }}>
          <h2 className="section-title">Insights &amp; Tendencias</h2>
          <p className="section-description">
            Evolución del mercado: herramientas AI, volumen de publicaciones, distribución de seniority y tendencias tecnológicas.
          </p>
        </motion.div>

        <motion.div className="charts-grid" variants={staggerContainer}>
          <motion.div className="chart-card" variants={fadeUp} transition={{ duration: 0.4 }}>
            <h3 className="chart-card-title">AI Dev Tools</h3>
            <AiToolsChart data={filteredAiTools} />
          </motion.div>

          <motion.div className="chart-card" variants={fadeUp} transition={{ duration: 0.4 }}>
            <h3 className="chart-card-title">Volumen Mensual de Publicaciones</h3>
            <MonthlyVolumeChart data={filteredMonthlyVolume} />
          </motion.div>

          <motion.div className="chart-card" variants={fadeUp} transition={{ duration: 0.4 }}>
            <h3 className="chart-card-title">Distribución de Seniority por Año</h3>
            <SeniorityShiftChart data={filteredSeniorityShift} />
          </motion.div>

          <motion.div className="chart-card" variants={fadeUp} transition={{ duration: 0.4 }}>
            <h3 className="chart-card-title">Tendencias Tecnológicas</h3>
            <TechTrendsChart data={filteredTechTrends} />
          </motion.div>
        </motion.div>
      </motion.section>

      {/* ─── FOOTER ─── */}
      <footer className="site-footer">
        <p>
          Datos extraídos de{' '}
          <a href="https://t.me/DCCEmpleoSinFiltro" target="_blank" rel="noopener noreferrer">
            DCCEmpleoSinFiltro
          </a>
          {' '}· Código en{' '}
          <a href="https://github.com/fgonzalezurriola/dccempleo-analytics" target="_blank" rel="noopener noreferrer">
            GitHub
          </a>
        </p>
        {metrics && (
          <p style={{ marginTop: '0.25rem' }}>
            Última actualización: {new Date(metrics.generated_at_utc).toLocaleDateString('es-CL')}
          </p>
        )}
      </footer>
    </>
  );
}
