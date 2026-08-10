import { useEffect, useMemo, useState } from 'react';
import { Users, Globe, BookOpen, Building2, MapPin } from 'lucide-react';
import StatCard from '../components/StatCard';
import ChartBar from '../components/ChartBar';
import AnimatedCounter from '../components/AnimatedCounter';
import ZelligePattern from '../components/ZelligePattern';
import { getStats, getTalents } from '../services/api';
import { mapTalentToExpert } from '../utils/expertMapper';

const domainColors = ['#006233', '#C41E3A', '#C9A227', '#1B6B93', '#8B5CF6', '#8B8BA7'];

export default function Dashboard() {
  const [experts, setExperts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [stats, setStats] = useState({
    totalExperts: 0,
    countries: 0,
    domains: [],
    topUniversities: [],
    topCompanies: [],
  });

  useEffect(() => {
    let alive = true;

    async function loadDashboard() {
      setLoading(true);
      setError('');
      try {
        const [statsData, talentsData] = await Promise.all([
          getStats(10),
          getTalents({ page: 1, page_size: 100 }),
        ]);

        if (!alive) {
          return;
        }

        const mappedExperts = (talentsData.items || []).map(mapTalentToExpert);
        setExperts(mappedExperts);

        const topUniversities = Array.from(
          new Set(mappedExperts.map((e) => e.university).filter(Boolean))
        ).slice(0, 8);
        const topCompanies = Array.from(
          new Set(mappedExperts.map((e) => e.organization).filter(Boolean))
        ).slice(0, 8);

        setStats({
          totalExperts: statsData.total_talents || 0,
          countries: statsData.total_countries || 0,
          domains: (statsData.top_domains || []).map((d, index) => ({
            name: d.name,
            count: d.count,
            color: domainColors[index % domainColors.length],
          })),
          topUniversities,
          topCompanies,
        });
      } catch {
        if (alive) {
          setExperts([]);
          setError('Impossible de charger les statistiques pour le moment.');
        }
      } finally {
        if (alive) {
          setLoading(false);
        }
      }
    }

    loadDashboard();
    return () => {
      alive = false;
    };
  }, []);

  const countryCounts = useMemo(() => {
    const map = {};
    experts.forEach(e => { map[e.country] = (map[e.country] || 0) + 1; });
    return Object.entries(map).sort((a, b) => b[1] - a[1]);
  }, [experts]);

  const cityCounts = useMemo(() => {
    const map = {};
    experts.forEach((e) => {
      if (!e.city) {
        return;
      }
      map[e.city] = (map[e.city] || 0) + 1;
    });
    return Object.entries(map).sort((a, b) => b[1] - a[1]);
  }, [experts]);

  const maxDomain = Math.max(1, ...stats.domains.map(d => d.count));
  const topCountries = countryCounts.slice(0, 10);
  const topCities = cityCounts.slice(0, 10);

  if (loading) {
    return (
      <div className="min-h-screen pt-32 text-center text-morocco-medium">
        Chargement du tableau de bord...
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen pt-32 text-center">
        <p className="font-semibold text-morocco-red">{error}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen pt-28 pb-20 bg-gradient-to-b from-morocco-cream to-white relative">
      <ZelligePattern />
      <div className="relative z-10 max-w-7xl mx-auto px-6">
        <div className="mb-8 md:mb-10">
          <div className="inline-flex items-center gap-2 bg-morocco-gold/10 text-morocco-gold px-4 py-1.5 rounded-full font-bold text-sm mb-4">
            Tableau de bord
          </div>
          <h1 className="font-display font-black text-4xl md:text-5xl text-morocco-dark mb-4">Vue d'ensemble</h1>
          <p className="text-morocco-medium max-w-2xl">Statistiques et indicateurs clés de l&apos;observatoire, organisés pour visualiser rapidement la diaspora IA, les pôles géographiques et les axes d&apos;expertise.</p>
          <div className="mt-5 flex flex-wrap gap-3">
            <span className="inline-flex items-center rounded-full bg-white border border-morocco-green/20 px-4 py-2 text-sm font-semibold text-morocco-medium">
              {stats.totalExperts} profils analysés
            </span>
            <span className="inline-flex items-center rounded-full bg-white border border-morocco-green/20 px-4 py-2 text-sm font-semibold text-morocco-medium">
              {topCountries.length} pays les plus représentés
            </span>
            <span className="inline-flex items-center rounded-full bg-white border border-morocco-green/20 px-4 py-2 text-sm font-semibold text-morocco-medium">
              {topCities.length} villes de référence
            </span>
          </div>
        </div>

        <section className="rounded-3xl border border-morocco-green/15 bg-white/80 backdrop-blur p-5 md:p-7 mb-8">
          <h2 className="font-display font-bold text-xl text-morocco-dark mb-5">Indicateurs clés</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-5">
            <StatCard icon={Users} value={<AnimatedCounter end={stats.totalExperts} />} label="Experts recensés" color="green" />
            <StatCard icon={Globe} value={<AnimatedCounter end={stats.countries} />} label="Pays couverts" color="red" />
            <StatCard icon={MapPin} value={<AnimatedCounter end={cityCounts.length} />} label="Villes recensées" color="blue" />
            <StatCard icon={BookOpen} value={<AnimatedCounter end={stats.domains.length} />} label="Domaines IA" color="gold" />
            <StatCard icon={Building2} value={<AnimatedCounter end={stats.topCompanies.length} />} label="Entreprises partenaires" color="blue" />
          </div>
        </section>

        <section className="grid lg:grid-cols-2 gap-8">
          <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100">
            <div className="mb-6 flex items-center justify-between">
              <h3 className="font-display font-bold text-xl text-morocco-dark">Répartition par domaine</h3>
              <span className="text-xs font-semibold uppercase tracking-wide text-morocco-light">Top domaines</span>
            </div>
            <div className="space-y-4">
              {stats.domains.length > 0 ? (
                stats.domains.map(d => (
                  <ChartBar key={d.name} label={d.name} value={d.count} max={maxDomain} color={d.color} />
                ))
              ) : (
                <p className="text-sm text-morocco-light">Aucune donnée de domaine disponible.</p>
              )}
            </div>
          </div>

          <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100">
            <div className="mb-6 flex items-center justify-between">
              <h3 className="font-display font-bold text-xl text-morocco-dark">Top pays de résidence</h3>
              <span className="text-xs font-semibold uppercase tracking-wide text-morocco-light">Top 10</span>
            </div>
            <div className="space-y-4">
              {topCountries.length > 0 ? (
                topCountries.map(([country, count]) => (
                  <ChartBar key={country} label={country} value={count} max={topCountries[0]?.[1] || 1} color="#006233" />
                ))
              ) : (
                <p className="text-sm text-morocco-light">Aucune donnée pays disponible.</p>
              )}
            </div>
          </div>
        </section>

        <section className="grid lg:grid-cols-3 gap-8 mt-8">
          <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100">
            <div className="mb-6 flex items-center justify-between">
              <h3 className="font-display font-bold text-xl text-morocco-dark">Top villes de résidence</h3>
              <span className="text-xs font-semibold uppercase tracking-wide text-morocco-light">Top 10</span>
            </div>
            <div className="space-y-4">
              {topCities.length > 0 ? (
                topCities.map(([city, count]) => (
                  <ChartBar key={city} label={city} value={count} max={topCities[0]?.[1] || 1} color="#1B6B93" />
                ))
              ) : (
                <p className="text-sm text-morocco-light">Aucune ville disponible pour le moment.</p>
              )}
            </div>
          </div>

          <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="font-display font-bold text-xl text-morocco-dark">Universités de référence</h3>
              <span className="text-xs font-semibold uppercase tracking-wide text-morocco-light">Top 8</span>
            </div>
            {stats.topUniversities.length > 0 ? (
              <ul className="space-y-2">
                {stats.topUniversities.map((u, index) => (
                  <li key={u} className="flex items-center gap-3 rounded-xl border border-gray-100 bg-morocco-cream/50 px-3 py-2">
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-morocco-green/10 text-morocco-green text-xs font-bold">
                      {index + 1}
                    </span>
                    <span className="text-sm font-semibold text-morocco-dark">{u}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-morocco-light">Aucune université disponible.</p>
            )}
          </div>

          <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="font-display font-bold text-xl text-morocco-dark">Entreprises & Institutions</h3>
              <span className="text-xs font-semibold uppercase tracking-wide text-morocco-light">Top 8</span>
            </div>
            {stats.topCompanies.length > 0 ? (
              <ul className="space-y-2">
                {stats.topCompanies.map((c, index) => (
                  <li key={c} className="flex items-center gap-3 rounded-xl border border-morocco-red/10 bg-morocco-red/5 px-3 py-2">
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-morocco-red/10 text-morocco-red text-xs font-bold">
                      {index + 1}
                    </span>
                    <span className="text-sm font-semibold text-morocco-dark">{c}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-morocco-light">Aucune entreprise disponible.</p>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}