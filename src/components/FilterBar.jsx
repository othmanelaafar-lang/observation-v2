import { Search, SlidersHorizontal } from 'lucide-react';

export default function FilterBar({
  search,
  setSearch,
  domain,
  setDomain,
  domains = ['Tous'],
  country,
  setCountry,
  countries = ['Tous'],
}) {
  return (
    <div className="space-y-5 mb-8 rounded-3xl border border-morocco-green/15 bg-white/85 backdrop-blur p-5 md:p-6 shadow-sm">
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-morocco-light" size={20} />
        <input
          type="text"
          placeholder="Rechercher un expert par nom, ville, compétence..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="w-full pl-12 pr-4 py-4 rounded-2xl border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-morocco-green/30 focus:border-morocco-green transition-all font-body"
        />
      </div>
      <div className="grid md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-morocco-light">
            <SlidersHorizontal size={16} />
            <p className="text-xs font-semibold uppercase tracking-wide">Domaine</p>
          </div>
          <select
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            className="w-full px-4 py-3 rounded-2xl border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-morocco-green/30 focus:border-morocco-green transition-all font-body text-morocco-medium"
          >
            {domains.map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
        </div>

        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-wide text-morocco-light">Pays</p>
          <select
            value={country}
            onChange={(e) => setCountry(e.target.value)}
            className="w-full px-4 py-3 rounded-2xl border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-morocco-green/30 focus:border-morocco-green transition-all font-body text-morocco-medium"
          >
            {countries.map((item) => (
              <option key={item} value={item}>{item}</option>
            ))}
          </select>
        </div>

      </div>
    </div>
  );
}