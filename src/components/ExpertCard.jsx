import { Link } from 'react-router-dom';
import { MapPin, Building2, GraduationCap, ArrowRight } from 'lucide-react';

export default function ExpertCard({ expert }) {
  return (
    <div className="bg-white rounded-2xl overflow-hidden border border-gray-100 shadow-sm card-hover flex flex-col h-full">
      <div className="h-24 bg-gradient-to-r from-morocco-green to-morocco-green-light relative">
        {expert.photo ? (
          <div className="absolute -bottom-10 left-6">
            <img src={expert.photo} alt={expert.name} className="w-20 h-20 rounded-2xl border-4 border-white shadow-lg object-cover" />
          </div>
        ) : null}
      </div>
      <div className={`${expert.photo ? 'pt-12' : 'pt-6'} px-6 pb-6 flex-1 flex flex-col`}>
        <div className="flex items-start justify-between mb-2">
          <div>
            <h3 className="font-display font-bold text-lg text-morocco-dark">{expert.name}</h3>
            {expert.nameAr ? <p className="text-xs text-morocco-light font-semibold" dir="rtl">{expert.nameAr}</p> : null}
          </div>
          <span className="text-xs font-bold px-3 py-1 rounded-full bg-morocco-green/10 text-morocco-green">{expert.domain}</span>
        </div>
        <div className="flex flex-wrap gap-2 mb-3">
          {expert.hasDirectContact ? (
            <span className="text-xs font-bold px-3 py-1 rounded-full bg-blue-50 text-blue-700">
              Contact direct
            </span>
          ) : null}
        </div>
        {expert.bio ? <p className="text-sm text-morocco-medium mb-4 line-clamp-2">{expert.bio}</p> : null}
        <div className="space-y-2 text-sm text-morocco-light mb-4">
          <div className="flex items-center gap-2"><MapPin size={14} /> {expert.city} - {expert.country}</div>
          <div className="flex items-center gap-2"><Building2 size={14} /> {expert.organization}</div>
          <div className="flex items-center gap-2"><GraduationCap size={14} /> {expert.university}</div>
        </div>
        <div className="flex flex-wrap gap-1.5 mb-4">
          {expert.skills.slice(0, 3).map(s => (
            <span key={s} className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-morocco-cream text-morocco-medium">{s}</span>
          ))}
        </div>
        <div className="mt-auto">
          <Link to={`/expert/${expert.id}`} className="inline-flex items-center gap-2 text-morocco-green font-bold text-sm hover:gap-3 transition-all">
            Voir le profil <ArrowRight size={16} />
          </Link>
        </div>
      </div>
    </div>
  );
}