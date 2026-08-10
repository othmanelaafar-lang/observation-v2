import { Link } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { Target, Users, Network, Lightbulb, ArrowRight } from 'lucide-react';
import Hero from '../components/Hero';
import ExpertCard from '../components/ExpertCard';
import ZelligePattern from '../components/ZelligePattern';
import { getTalents } from '../services/api';
import { mapTalentToExpert } from '../utils/expertMapper';

const objectives = [
  { icon: Target, title: 'Identifier', desc: 'Recenser les chercheurs, ingénieurs, doctorants et entrepreneurs marocains en IA à travers le monde.', color: 'green' },
  { icon: Lightbulb, title: 'Valoriser', desc: 'Donner une visibilité internationale aux parcours et réalisations de ces experts.', color: 'red' },
  { icon: Network, title: 'Mobiliser', desc: 'Faciliter les collaborations avec les universités, entreprises et institutions marocaines.', color: 'gold' },
  { icon: Users, title: 'Inspirer', desc: 'Offrir des modèles inspirants aux jeunes Marocains intéressés par l\'IA.', color: 'blue' },
];

export default function Home() {
  const [featured, setFeatured] = useState([]);

  useEffect(() => {
    let alive = true;

    async function loadFeatured() {
      try {
        const data = await getTalents({ page: 1, page_size: 8 });
        if (!alive) {
          return;
        }
        const mapped = (data.items || []).map(mapTalentToExpert);
        setFeatured(mapped.slice(0, 4));
      } catch {
        if (alive) {
          setFeatured([]);
        }
      }
    }

    loadFeatured();
    return () => {
      alive = false;
    };
  }, []);

  return (
    <div>
      <Hero />

      {/* Mission */}
      <section className="relative py-24 bg-white overflow-hidden">
        <ZelligePattern />
        <div className="relative z-10 max-w-7xl mx-auto px-6">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <div className="inline-flex items-center gap-2 bg-morocco-red/10 text-morocco-red px-4 py-1.5 rounded-full font-bold text-sm mb-4">
              Notre mission
            </div>
            <h2 className="font-display font-black text-4xl text-morocco-dark mb-4">Pourquoi un observatoire ?</h2>
            <p className="text-morocco-medium leading-relaxed">
              Les Marocains de l'IA constituent une richesse considérable pour le pays. Pourtant, ce vivier de compétences demeure largement méconnu et peu structuré.
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {objectives.map((obj, i) => (
              <div key={i} className="bg-morocco-cream rounded-2xl p-8 border border-gray-100 card-hover">
                <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br from-morocco-${obj.color} to-morocco-${obj.color}-light flex items-center justify-center text-white mb-5 shadow-lg`}>
                  <obj.icon size={26} />
                </div>
                <h3 className="font-display font-bold text-xl text-morocco-dark mb-2">{obj.title}</h3>
                <p className="text-morocco-medium text-sm leading-relaxed">{obj.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Experts */}
      <section className="py-24 bg-gradient-to-b from-morocco-cream to-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 gap-4">
            <div>
              <div className="inline-flex items-center gap-2 bg-morocco-gold/10 text-morocco-gold px-4 py-1.5 rounded-full font-bold text-sm mb-4">
                Experts à la une
              </div>
              <h2 className="font-display font-black text-4xl text-morocco-dark">Talents marocains mondiaux</h2>
            </div>
            <Link to="/explorer" className="btn-primary">
              Voir tous les experts <ArrowRight size={18} />
            </Link>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {featured.map(expert => <ExpertCard key={expert.id} expert={expert} />)}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="relative py-24 bg-morocco-dark overflow-hidden">
        <div className="zellige-bg-dark absolute inset-0 opacity-30" />
        <div className="relative z-10 max-w-4xl mx-auto px-6 text-center">
          <h2 className="font-display font-black text-4xl md:text-5xl text-white mb-6">
            Vous êtes un expert marocain en IA ?
          </h2>
          <p className="text-white/70 text-lg mb-10 max-w-2xl mx-auto">
            Rejoignez l'observatoire et faites partie d'un réseau structuré dédié à l'excellence marocaine en Intelligence Artificielle.
          </p>
          <Link to="/explorer" className="inline-flex items-center gap-3 bg-white text-morocco-green font-bold text-lg px-10 py-4 rounded-2xl shadow-2xl hover:scale-105 transition-transform">
            Rejoindre le réseau <ArrowRight size={20} />
          </Link>
        </div>
      </section>
    </div>
  );
}