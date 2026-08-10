import { Target, Eye, Lightbulb, Users, Network, Award } from 'lucide-react';
import ZelligePattern from '../components/ZelligePattern';

const team = [
  { name: 'LAAFAR Othman', initials: 'LO' },
  { name: 'LATIFI Noura', initials: 'LN' },
  { name: 'LASSANA Kouma', initials: 'LK' },
];

const values = [
  { icon: Target, title: 'Vision', text: 'Faire de l\'IA un terrain de rapprochement entre la diaspora marocaine et le Maroc.' },
  { icon: Eye, title: 'Mission', text: 'Identifier, recenser et valoriser les experts marocains de l\'IA établis à l\'étranger.' },
  { icon: Lightbulb, title: 'Innovation', text: 'Transformer la richesse humaine des experts en un levier de développement national.' },
];

export default function About() {
  return (
    <div className="min-h-screen pt-24 pb-20 bg-gradient-to-b from-morocco-cream to-white relative">
      <ZelligePattern />
      <div className="relative z-10 max-w-7xl mx-auto px-6">
        <div className="text-center max-w-3xl mx-auto mb-20">
          <div className="inline-flex items-center gap-2 bg-morocco-red/10 text-morocco-red px-4 py-1.5 rounded-full font-bold text-sm mb-4">
            À propos
          </div>
          <h1 className="font-display font-black text-4xl md:text-5xl text-morocco-dark mb-6">
            Observatoire Intelligent des Experts Marocains en IA
          </h1>
          <p className="text-lg text-morocco-medium leading-relaxed">
            Un concept stratégique pour mieux identifier, valoriser et mobiliser les chercheurs, ingénieurs, doctorants et entrepreneurs marocains évoluant dans le domaine de l'Intelligence Artificielle à travers le monde.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 mb-24">
          {values.map((v, i) => (
            <div key={i} className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100 card-hover text-center">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-morocco-green to-morocco-green-light flex items-center justify-center text-white mx-auto mb-5 shadow-lg">
                <v.icon size={28} />
              </div>
              <h3 className="font-display font-bold text-xl text-morocco-dark mb-3">{v.title}</h3>
              <p className="text-morocco-medium text-sm leading-relaxed">{v.text}</p>
            </div>
          ))}
        </div>

        <div className="bg-white rounded-3xl p-8 md:p-12 shadow-xl border border-gray-100 mb-24">
          <h2 className="font-display font-black text-3xl text-morocco-dark mb-8 text-center">Objectifs de l'observatoire</h2>
          <div className="grid md:grid-cols-2 gap-6">
            {[
              'Identifier les experts marocains en IA établis à l\'étranger',
              'Valoriser leurs parcours et réalisations',
              'Constituer un réseau structuré de compétences',
              'Faciliter les collaborations avec les universités et entreprises marocaines',
              'Encourager le mentorat et le transfert de connaissances',
              'Inspirer les jeunes Marocains à s\'orienter vers l\'IA',
            ].map((obj, i) => (
              <div key={i} className="flex items-start gap-4 p-4 rounded-xl bg-morocco-cream/50">
                <div className="w-8 h-8 rounded-lg bg-morocco-green text-white flex items-center justify-center font-display font-bold text-sm shrink-0">{i + 1}</div>
                <p className="text-morocco-dark font-semibold">{obj}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="text-center mb-12">
          <h2 className="font-display font-black text-3xl text-morocco-dark mb-4">Équipe projet</h2>
          <p className="text-morocco-medium">Encadré par Pr. Nabil El Moutawakil El Alami</p>
        </div>
        <div className="grid md:grid-cols-3 gap-8 max-w-3xl mx-auto">
          {team.map((m, i) => (
            <div key={i} className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100 text-center card-hover">
              <div className="w-20 h-20 rounded-full bg-gradient-to-br from-morocco-red to-morocco-red-light text-white flex items-center justify-center text-2xl font-display font-bold mx-auto mb-4 shadow-lg">
                {m.initials}
              </div>
              <h3 className="font-display font-bold text-lg text-morocco-dark">{m.name}</h3>
              
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}