function parseCsvLike(text) {
  if (!text) {
    return [];
  }
  return text
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

function flagFromCountryCode(countryCode) {
  if (!countryCode || countryCode.length !== 2) {
    return '';
  }
  const code = countryCode.toUpperCase();
  return String.fromCodePoint(...[...code].map((char) => 127397 + char.charCodeAt()));
}

function displayCountry(countryCode) {
  if (!countryCode) {
    return 'Inconnu';
  }
  const flag = flagFromCountryCode(countryCode);
  return flag ? `${flag} ${countryCode}` : countryCode;
}

function buildConfidence(talent) {
  let score = 0;

  if (talent.orcid_url) {
    score += 30;
  }
  if (talent.openalex_url) {
    score += 25;
  }
  if (talent.github_url || talent.website_url || talent.linkedin) {
    score += 15;
  }
  if (talent.email) {
    score += 10;
  }
  if ((talent.publications || 0) > 0) {
    score += 10;
  }
  if ((talent.h_index || 0) >= 10) {
    score += 10;
  }

  const value = Math.min(score, 100);

  if (value >= 80) {
    return { value, label: 'Tres fiable', tone: 'green' };
  }
  if (value >= 55) {
    return { value, label: 'Fiable', tone: 'gold' };
  }
  return { value, label: 'A confirmer', tone: 'red' };
}

export function mapTalentToExpert(talent) {
  const skills = parseCsvLike(talent.skills_text);
  const domains = talent.domains || [];
  const universities = talent.universities || [];
  const confidence = buildConfidence(talent);

  return {
    id: talent.id,
    name: talent.full_name,
    nameAr: talent.name_ar || '',
    photo: talent.photo_url || '',
    country: displayCountry(talent.country),
    city: talent.city || 'Ville non renseignee',
    role: talent.role || 'Expert IA',
    organization: talent.organization || 'Organisation non renseignée',
    university: universities[0]?.name || 'Université non renseignée',
    bio: talent.bio || '',
    domain: domains[0]?.name || 'Artificial intelligence',
    skills: skills.length ? skills : domains.map((d) => d.name),
    publications: talent.publications || 0,
    hIndex: talent.h_index || 0,
    interests: parseCsvLike(talent.interests_text),
    email: talent.email || '',
    linkedin: talent.linkedin || '',
    website: talent.website_url || '',
    github: talent.github_url || '',
    orcid: talent.orcid_url || '',
    openalex: talent.openalex_url || '',
    scholar: talent.scholar_url || '',
    confidence,
    hasDirectContact: Boolean(talent.email || talent.linkedin),
    featured: Boolean(talent.featured),
  };
}
