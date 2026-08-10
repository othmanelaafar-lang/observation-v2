import { useParams, Link } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { ArrowLeft, MapPin, Building2, GraduationCap, Mail, Award, Heart, ExternalLink } from 'lucide-react';
import ZelligePattern from '../components/ZelligePattern';
import { getTalentById } from '../services/api';
import { mapTalentToExpert } from '../utils/expertMapper';

function LinkItem({ href, label }) {
  return (
    <a
      className="flex items-center gap-2 text-morocco-medium break-all hover:text-morocco-green"
      href={href}
      target={href.startsWith('mailto:') ? undefined : '_blank'}
      rel={href.startsWith('mailto:') ? undefined : 'noreferrer'}
    >
      {href.startsWith('mailto:') ? <Mail size={14} /> : <ExternalLink size={14} />}
      {label}
    </a>
  );
}

export default function ExpertProfile() {
  const { id } = useParams();
  const [expert, setExpert] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;

    async function loadExpert() {
      setLoading(true);
      try {
        const data = await getTalentById(Number(id));
        if (alive) {
          setExpert(mapTalentToExpert(data));
        }
      } catch {
        if (alive) {
          setExpert(null);
        }
      } finally {
        if (alive) {
          setLoading(false);
        }
      }
    }

    loadExpert();
    return () => {
      alive = false;
    };
  }, [id]);

  if (loading) {
    return <div className="min-h-screen pt-32 text-center text-morocco-medium">Chargement du profil...</div>;
  }

  if (!expert) {
    return (
      <div className="min-h-screen pt-32 text-center">
        <h2 className="font-display font-bold text-2xl text-morocco-dark">Expert non trouvé</h2>
        <Link to="/explorer" className="text-morocco-green font-bold mt-4 inline-block">Retour à l'annuaire</Link>
      </div>
    );
  }

  const hasContact = Boolean(expert.email || expert.linkedin);
  const hasProfessionalProfiles = Boolean(expert.github || expert.website);
  const hasAcademicProfiles = Boolean(expert.orcid || expert.openalex || expert.scholar);

  return (
    <div className="min-h-screen pt-24 pb-20 bg-gradient-to-b from-morocco-cream to-white relative">
      <ZelligePattern />
      <div className="relative z-10 max-w-5xl mx-auto px-6">
        <Link to="/explorer" className="inline-flex items-center gap-2 text-morocco-green font-bold mb-8 hover:gap-3 transition-all">
          <ArrowLeft size={18} /> Retour à l'annuaire
        </Link>

        <div className="bg-white rounded-3xl shadow-xl border border-gray-100 overflow-hidden">
         <div className="h-10 bg-gradient-to-r from-morocco-green via-morocco-green-light to-morocco-gold relative">
            <div className="absolute bottom-0 left-0 right-0 h-16 bg-gradient-to-t from-white/20 to-transparent" />
          </div>
          <div className="px-8 pb-8">
            <div className="flex flex-col md:flex-row gap-6 mt-4 mb-8">
              {expert.photo ? <img src={expert.photo} alt={expert.name} className="w-32 h-32 rounded-3xl border-4 border-white shadow-xl object-cover" /> : null}
              <div className="pt-2 flex-1">
                <div className="flex flex-wrap items-center gap-3 mb-2">
                  <h1 className="font-display font-black text-3xl text-morocco-dark">{expert.name}</h1>
                  {expert.nameAr ? <span className="text-lg text-morocco-light font-semibold" dir="rtl">({expert.nameAr})</span> : null}
                </div>
                <p className="text-morocco-green font-bold text-lg mb-1">{expert.role}</p>
                <div className="flex flex-wrap gap-4 text-sm text-morocco-medium">
                  <span className="flex items-center gap-1"><MapPin size={14} /> {expert.city} - {expert.country}</span>
                  <span className="flex items-center gap-1"><Building2 size={14} /> {expert.organization}</span>
                  <span className="flex items-center gap-1"><GraduationCap size={14} /> {expert.university}</span>
                </div>
              </div>
              <div className="flex gap-3 mt-2 md:mt-0">
                {expert.email ? (
                  <a href={`mailto:${expert.email}`} className="btn-primary text-sm py-2.5">
                    <Mail size={16} /> Contacter
                  </a>
                ) : null}
              </div>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              <div className="md:col-span-2 space-y-8">
                {expert.bio ? (
                  <section>
                    <h3 className="font-display font-bold text-xl text-morocco-dark mb-3 flex items-center gap-2">
                      <Heart size={20} className="text-morocco-red" /> Biographie
                    </h3>
                    <p className="text-morocco-medium leading-relaxed">{expert.bio}</p>
                  </section>
                ) : null}

                <section>
                  <h3 className="font-display font-bold text-xl text-morocco-dark mb-3 flex items-center gap-2">
                    <Award size={20} className="text-morocco-gold" /> Compétences
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {expert.skills.map(s => (
                      <span key={s} className="px-4 py-2 rounded-xl bg-morocco-green/10 text-morocco-green font-bold text-sm">{s}</span>
                    ))}
                  </div>
                </section>

                <section>
                  <h3 className="font-display font-bold text-xl text-morocco-dark mb-3 flex items-center gap-2">
                    <Heart size={20} className="text-morocco-red" /> Centres d'intérêt
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {expert.interests.map(i => (
                      <span key={i} className="px-4 py-2 rounded-xl bg-morocco-cream text-morocco-medium font-semibold text-sm border border-gray-100">{i}</span>
                    ))}
                    {expert.interests.length === 0 ? <span className="text-sm text-morocco-light">Aucun centre d&apos;intérêt renseigné.</span> : null}
                  </div>
                </section>
              </div>

              <div className="space-y-6">
                <div className="bg-morocco-cream rounded-2xl p-6 border border-gray-100">
                  <h4 className="font-display font-bold text-morocco-dark mb-4">Indicateurs</h4>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-morocco-medium text-sm font-semibold">Publications</span>
                      <span className="font-display font-black text-2xl text-morocco-green">{expert.publications}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-morocco-medium text-sm font-semibold">H-Index</span>
                      <span className="font-display font-black text-2xl text-morocco-red">{expert.hIndex}</span>
                    </div>
                  </div>
                </div>

                <div className="bg-morocco-cream rounded-2xl p-6 border border-gray-100">
                  <h4 className="font-display font-bold text-morocco-dark mb-3">Domaine</h4>
                  <span className="inline-block px-4 py-2 rounded-xl bg-morocco-red/10 text-morocco-red font-bold text-sm">
                    {expert.domain}
                  </span>
                </div>

                {hasContact || hasProfessionalProfiles || hasAcademicProfiles ? (
                  <div className="bg-morocco-cream rounded-2xl p-6 border border-gray-100 space-y-5">
                    {hasContact ? (
                      <div>
                        <h4 className="font-display font-bold text-morocco-dark mb-3">Contacter</h4>
                        <div className="space-y-2 text-sm">
                          {expert.email ? <LinkItem href={`mailto:${expert.email}`} label={expert.email} /> : null}
                          {expert.linkedin ? <LinkItem href={expert.linkedin} label="LinkedIn" /> : null}
                        </div>
                      </div>
                    ) : null}

                    {hasProfessionalProfiles ? (
                      <div>
                        <h4 className="font-display font-bold text-morocco-dark mb-3">Profils professionnels</h4>
                        <div className="space-y-2 text-sm">
                          {expert.github ? <LinkItem href={expert.github} label="GitHub" /> : null}
                          {expert.website ? <LinkItem href={expert.website} label="Site perso" /> : null}
                        </div>
                      </div>
                    ) : null}

                    {hasAcademicProfiles ? (
                      <div>
                        <h4 className="font-display font-bold text-morocco-dark mb-3">Profils académiques</h4>
                        <div className="space-y-2 text-sm">
                          {expert.orcid ? <LinkItem href={expert.orcid} label="ORCID" /> : null}
                          {expert.openalex ? <LinkItem href={expert.openalex} label="OpenAlex" /> : null}
                          {expert.scholar ? <LinkItem href={expert.scholar} label="Scholar" /> : null}
                        </div>
                      </div>
                    ) : null}
                  </div>
                ) : null}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}