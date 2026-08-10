import { ArrowRight, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';
import ZelligePattern from './ZelligePattern';

export default function Hero() {
  return (
    <section className="relative min-h-screen flex items-center pt-20 overflow-hidden bg-gradient-to-br from-morocco-cream via-white to-morocco-sand">
      <ZelligePattern />
      <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-morocco-green/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/4" />
      <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-morocco-red/5 rounded-full blur-3xl translate-y-1/4 -translate-x-1/4" />

      <div className="relative z-10 max-w-7xl mx-auto px-6 grid lg:grid-cols-2 gap-16 items-center">
        <div className="space-y-8">
          <div className="inline-flex items-center gap-2 bg-morocco-green/10 border border-morocco-green/20 text-morocco-green px-5 py-2 rounded-full font-bold text-sm">
            <Sparkles size={16} className="animate-pulse" />
            Propulsé par l'Intelligence Artificielle
          </div>
          <h1 className="font-display font-black text-5xl lg:text-6xl xl:text-7xl leading-[1.1] text-morocco-dark">
            L'excellence marocaine<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-morocco-green to-morocco-green-light">
              en Intelligence
            </span><br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-morocco-red to-morocco-red-light">
              Artificielle
            </span>
          </h1>
          <p className="text-lg text-morocco-medium max-w-lg leading-relaxed">
            Identifier, valoriser et mettre en relation les experts marocains en IA à travers le monde. Un pont entre la diaspora et le Maroc.
          </p>
          <div className="flex flex-wrap gap-4">
            <Link to="/explorer" className="btn-primary text-lg px-8 py-4">
              Explorer les experts <ArrowRight size={20} />
            </Link>
            <Link to="/about" className="btn-secondary text-lg px-8 py-4">
              En savoir plus
            </Link>
          </div>
          <div className="flex gap-10 pt-4">
            <div><div className="font-display font-black text-3xl text-morocco-green">248+</div><div className="text-sm text-morocco-light font-semibold">Experts recensés</div></div>
            <div><div className="font-display font-black text-3xl text-morocco-red">32</div><div className="text-sm text-morocco-light font-semibold">Pays couverts</div></div>
            <div><div className="font-display font-black text-3xl text-morocco-gold">6</div><div className="text-sm text-morocco-light font-semibold">Domaines IA</div></div>
          </div>
        </div>

        <div className="relative hidden lg:flex justify-center">
          <div className="relative w-[420px] h-[420px]">
            <div className="absolute inset-0 rounded-full border-4 border-dashed border-morocco-gold/30 animate-[spin_20s_linear_infinite]" />
            <div className="absolute inset-4 rounded-full bg-gradient-to-br from-white to-morocco-cream shadow-2xl flex items-center justify-center overflow-hidden">
              <div className="text-center p-8">

  <img
    src="/ma.svg"
    alt="Carte du Maroc"
    className="w-48 h-auto mx-auto mb-6 drop-shadow-xl"
  />

  <h3 className="font-display font-black text-3xl text-morocco-dark mb-2">
    Observatoire IA
  </h3>

  <p className="text-morocco-medium font-semibold">
    Experts Marocains
  </p>

  <div className="mt-6 flex justify-center gap-3">
    <span className="text-2xl">🇲🇦</span>
    <span className="text-2xl">🌍</span>
    <span className="text-2xl">🤖</span>
  </div>

</div>
            </div>
            <div className="absolute -top-4 -right-4 bg-white rounded-2xl p-4 shadow-xl animate-bounce">
              <div className="font-display font-bold text-morocco-green">NLP</div>
              <div className="text-xs text-morocco-light">52 experts</div>
            </div>
            <div className="absolute -bottom-4 -left-4 bg-white rounded-2xl p-4 shadow-xl animate-bounce" style={{animationDelay:'1s'}}>
              <div className="font-display font-bold text-morocco-red">Vision</div>
              <div className="text-xs text-morocco-light">47 experts</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}