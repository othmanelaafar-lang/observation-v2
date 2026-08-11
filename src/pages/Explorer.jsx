import { useEffect, useMemo, useState } from 'react';
import ExpertCard from '../components/ExpertCard';
import FilterBar from '../components/FilterBar';
import ZelligePattern from '../components/ZelligePattern';
import { getTalents } from '../services/api';
import { mapTalentToExpert } from '../utils/expertMapper';

const TIER_ORDER = ['Elite', 'Confirme', 'Emergent'];

export default function Explorer() {
  const [experts, setExperts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [domain, setDomain] = useState('Tous');
  const [country, setCountry] = useState('Tous');
  const [tier, setTier] = useState('Tous');

  useEffect(() => {
    let alive = true;

    async function loadExperts() {
      setLoading(true);
      setError('');
      try {
        const data = await getTalents({ page: 1, page_size: 500 });
        if (!alive) {
          return;
        }
        setExperts((data.items || []).map(mapTalentToExpert));
      } catch (err) {
        if (!alive) {
          return;
        }
        setError(err.message || 'Erreur de chargement');
      } finally {
        if (alive) {
          setLoading(false);
        }
      }
    }

    loadExperts();
    return () => {
      alive = false;
    };
  }, []);

  const filtered = useMemo(() => {
    return experts.filter(e => {
      const matchDomain = domain === 'Tous' || e.domain === domain;
      const matchCountry = country === 'Tous' || e.country === country;
      const matchTier = tier === 'Tous' || e.tier === tier;
      const q = search.toLowerCase();
      const matchSearch = !q ||
        e.name.toLowerCase().includes(q) ||
        e.country.toLowerCase().includes(q) ||
        e.city.toLowerCase().includes(q) ||
        e.skills.some(s => s.toLowerCase().includes(q)) ||
        e.organization.toLowerCase().includes(q);
      return matchDomain && matchCountry && matchTier && matchSearch;
    });
  }, [experts, search, domain, country, tier]);

  const tiers = useMemo(() => {
    const present = new Set(experts.map((e) => e.tier).filter(Boolean));
    const ordered = TIER_ORDER.filter((name) => present.has(name));
    const rest = [...present].filter((name) => !TIER_ORDER.includes(name)).sort();
    return ['Tous', ...ordered, ...rest];
  }, [experts]);

  const domains = useMemo(() => {
    const names = Array.from(new Set(experts.map((e) => e.domain).filter(Boolean)));
    return ['Tous', ...names];
  }, [experts]);

  const countries = useMemo(() => {
    const names = Array.from(new Set(experts.map((e) => e.country).filter(Boolean))).sort((a, b) => a.localeCompare(b));
    return ['Tous', ...names];
  }, [experts]);

  return (
    <div className="min-h-screen pt-28 pb-20 bg-gradient-to-b from-morocco-cream to-white relative">
      <ZelligePattern />
      <div className="relative z-10 max-w-7xl mx-auto px-6">
        <div className="mb-8 md:mb-10">
          <div className="inline-flex items-center gap-2 bg-morocco-green/10 text-morocco-green px-4 py-1.5 rounded-full font-bold text-sm mb-4">
            Annuaire
          </div>
          <h1 className="font-display font-black text-4xl md:text-5xl text-morocco-dark mb-4">Explorer les experts</h1>
          <p className="text-morocco-medium max-w-xl">
            {filtered.length} expert{filtered.length > 1 ? 's' : ''} recensé{filtered.length > 1 ? 's' : ''} dans {new Set(experts.map(e => e.country)).size} pays à travers le monde.
          </p>
        </div>

        <FilterBar
          search={search}
          setSearch={setSearch}
          domain={domain}
          setDomain={setDomain}
          domains={domains}
          country={country}
          setCountry={setCountry}
          countries={countries}
          tier={tier}
          setTier={setTier}
          tiers={tiers}
        />

        {!loading && !error ? (
          <div className="mb-6 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-morocco-green/15 bg-white/80 backdrop-blur px-4 py-3">
            <p className="text-sm font-semibold text-morocco-medium">
              {filtered.length} profil{filtered.length > 1 ? 's' : ''} affiche{filtered.length > 1 ? 's' : ''}
            </p>
            <p className="text-xs font-semibold uppercase tracking-wide text-morocco-light">
              Filtres actifs: {domain !== 'Tous' ? domain : 'Tous domaines'} • {country !== 'Tous' ? country : 'Tous pays'} • {tier !== 'Tous' ? tier : 'Tous niveaux'}
            </p>
          </div>
        ) : null}

        {loading ? (
          <div className="text-center py-12 text-morocco-medium">Chargement des experts...</div>
        ) : null}

        {error ? (
          <div className="text-center py-12 text-morocco-red font-semibold">{error}</div>
        ) : null}

        {!loading && !error && filtered.length === 0 ? (
          <div className="text-center py-20">
            <div className="text-6xl mb-4">🔍</div>
            <h3 className="font-display font-bold text-xl text-morocco-dark mb-2">Aucun expert trouvé</h3>
            <p className="text-morocco-light">Essayez d'autres critères de recherche.</p>
          </div>
        ) : null}

        {!loading && !error && filtered.length > 0 ? (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filtered.map(expert => <ExpertCard key={expert.id} expert={expert} />)}
          </div>
        ) : null}
      </div>
    </div>
  );
}