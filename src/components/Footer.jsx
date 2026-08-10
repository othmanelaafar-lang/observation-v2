import { Link } from 'react-router-dom';
import { Globe, Mail, MapPin } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="relative bg-morocco-dark text-white overflow-hidden">
      <div className="zellige-bg-dark absolute inset-0 opacity-40" />
      <div className="relative z-10 max-w-7xl mx-auto px-6 pt-16 pb-8">
        <div className="grid md:grid-cols-4 gap-10 mb-12">
          <div className="md:col-span-2">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-morocco-green to-morocco-green-light flex items-center justify-center text-white">
                <Globe size={20} />
              </div>
              <div className="font-display font-bold text-xl">
                Observatoire<span className="text-morocco-gold">IA</span>
              </div>
            </div>
            <p className="text-white/60 max-w-sm leading-relaxed">
              Identifier, valoriser et mobiliser les talents marocains de l'Intelligence Artificielle à travers le monde.
            </p>
          </div>
          <div>
            <h4 className="font-display font-bold mb-4 text-morocco-gold">Navigation</h4>
            <ul className="space-y-2 text-white/60">
              <li><Link to="/" className="hover:text-white transition-colors">Accueil</Link></li>
              <li><Link to="/explorer" className="hover:text-white transition-colors">Explorer</Link></li>
              <li><Link to="/dashboard" className="hover:text-white transition-colors">Dashboard</Link></li>
              <li><Link to="/about" className="hover:text-white transition-colors">À propos</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="font-display font-bold mb-4 text-morocco-gold">Contact</h4>
            <ul className="space-y-3 text-white/60">
              <li className="flex items-center gap-2"><Mail size={16} /> contact@observatoire-ia.ma</li>
              <li className="flex items-center gap-2"><MapPin size={16} /> Rabat, Maroc</li>
            </ul>
          </div>
        </div>
        <div className="border-t border-white/10 pt-6 flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-white/40">
          <p>© 2026 Observatoire Intelligent des Experts Marocains en IA</p>
          <p>Réalisé avec passion pour la diaspora marocaine</p>
        </div>
      </div>
    </footer>
  );
}