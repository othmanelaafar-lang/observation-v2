import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, Globe } from 'lucide-react';

const links = [
  { to: '/', label: 'Accueil' },
  { to: '/explorer', label: 'Explorer' },
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/about', label: 'À propos' },
];

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 30);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => setMobileOpen(false), [location]);

  return (
    <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${scrolled ? 'bg-white/95 backdrop-blur-xl shadow-md' : 'bg-transparent'}`}>
      <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-morocco-green to-morocco-green-light flex items-center justify-center text-white shadow-lg group-hover:scale-105 transition-transform">
            <Globe size={20} />
          </div>
          <div className="font-display font-bold text-xl tracking-tight">
            Observatoire<span className="text-morocco-red">IA</span>
          </div>
        </Link>

        <div className="hidden md:flex items-center gap-8">
          {links.map(l => (
            <Link
              key={l.to}
              to={l.to}
              className={`font-semibold text-sm transition-colors relative ${location.pathname === l.to ? 'text-morocco-green' : 'text-morocco-medium hover:text-morocco-green'}`}
            >
              {l.label}
              {location.pathname === l.to && (
                <span className="absolute -bottom-1 left-0 right-0 h-0.5 bg-morocco-green rounded-full" />
              )}
            </Link>
          ))}
          <Link to="/explorer" className="btn-primary text-sm py-2.5 px-5">
            Explorer les experts
          </Link>
        </div>

        <button className="md:hidden text-morocco-dark" onClick={() => setMobileOpen(!mobileOpen)}>
          {mobileOpen ? <X size={28} /> : <Menu size={28} />}
        </button>
      </div>

      {mobileOpen && (
        <div className="md:hidden bg-white border-t border-gray-100 px-6 py-4 flex flex-col gap-3 shadow-xl">
          {links.map(l => (
            <Link key={l.to} to={l.to} className="py-3 px-4 rounded-xl font-semibold hover:bg-morocco-cream text-morocco-dark">
              {l.label}
            </Link>
          ))}
        </div>
      )}
    </nav>
  );
}