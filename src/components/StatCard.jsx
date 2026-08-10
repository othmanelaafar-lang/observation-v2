export default function StatCard({ icon: Icon, value, label, color }) {
  const colorMap = {
    green: 'from-morocco-green to-morocco-green-light',
    red: 'from-morocco-red to-morocco-red-light',
    gold: 'from-morocco-gold to-morocco-gold-light',
    blue: 'from-blue-600 to-blue-400',
  };
  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 card-hover">
      <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${colorMap[color] || colorMap.green} flex items-center justify-center text-white mb-4`}>
        <Icon size={22} />
      </div>
      <div className="font-display font-black text-3xl text-morocco-dark mb-1">{value}</div>
      <div className="text-sm font-semibold text-morocco-light">{label}</div>
    </div>
  );
}