export default function ZelligePattern({ dark = false, className = "" }) {
  return (
    <div
      className={`absolute inset-0 pointer-events-none z-0 ${dark ? 'zellige-bg-dark' : 'zellige-bg'} ${className}`}
      style={{
        maskImage: 'linear-gradient(to bottom, transparent, black 8%, black 92%, transparent)',
        WebkitMaskImage: 'linear-gradient(to bottom, transparent, black 8%, black 92%, transparent)',
      }}
    />
  );
}