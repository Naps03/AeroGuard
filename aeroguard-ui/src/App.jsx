import React, { useState, useEffect } from 'react';
import { Wind, Thermometer, Droplets, Activity, Clock, AlertTriangle, CheckCircle, Timer, Trash2, Users, Calendar } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

// Graphdaten
const historyData = [
  { time: '00:00', co2: 450, temp: 21, hum: 40, iaq: 95 },
  { time: '04:00', co2: 440, temp: 20, hum: 42, iaq: 98 },
  { time: '08:00', co2: 600, temp: 21, hum: 45, iaq: 85 },
  { time: '10:00', co2: 950, temp: 23, hum: 50, iaq: 65 },
  { time: '12:00', co2: 1200, temp: 24, hum: 55, iaq: 45 },
  { time: '14:00', co2: 800, temp: 22, hum: 48, iaq: 75 },
  { time: '18:00', co2: 500, temp: 21, hum: 43, iaq: 90 },
  { time: '22:00', co2: 460, temp: 20, hum: 41, iaq: 94 },
];

function App() {
  // Standardwerte für die Sensoren, bevor die API-Daten geladen werden
  const [sensorData, setSensorData] = useState({
    co2: 0,
    temperature: 0,
    humidity: 0,
    iaq_score: 0,
    prediction_minutes: null
  });

  // Testwerte für den Belegungsplan
  const [occupations, setOccupations] = useState([]);
  const [newDay, setNewDay] = useState("Montag");
  const [newStart, setNewStart] = useState("");
  const [newEnd, setNewEnd] = useState("");
  const [newLabel, setNewLabel] = useState("");

  // 2. API-Aufruf
  useEffect(() => {
  const fetchData = async () => {
    try {
      // 1. Sensordaten
      const resSensors = await fetch('http://127.0.0.1:8000/api/sensor-test');
      const dataS = await resSensors.json();
      setSensorData(dataS);

      // 2. Belegungsdaten
      const resOcc = await fetch('http://127.0.0.1:8000/api/occupations');
      const dataO = await resOcc.json();
      console.log("Données reçues de la DB:", dataO);
      setOccupations(dataO); 
    } catch (error) {
      console.error("Erreur de fetch:", error);
    }
  };

  fetchData();
  const interval = setInterval(fetchData, 5000);
  return () => clearInterval(interval);
}, []);


  const addOccupation = async () => {
  if (newStart && newEnd && newLabel) {
    const newEntry = { 
      day: newDay, 
      start_time: newStart, 
      end_time: newEnd, 
      label: newLabel 
    };

    try {
      const response = await fetch('http://127.0.0.1:8000/api/occupations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newEntry)
      });

      if (response.ok) {
        setOccupations([...occupations, { ...newEntry, id: Date.now() }]);
        setNewStart(""); setNewEnd(""); setNewLabel("");
      }
    } catch (error) {
      console.error("Erreur lors de l'enregistrement:", error);
    }
  }
};

  const deleteOccupation = async (id) => {
  try {
    const response = await fetch(`http://127.0.0.1:8000/api/occupations/${id}`, {
      method: 'DELETE',
    });

    if (response.ok) {
      setOccupations(occupations.filter(o => o.id !== id));
    } else {
      console.error("Erreur lors de la suppression sur le serveur");
    }
  } catch (error) {
    console.error("Erreur réseau :", error);
  }
};

  const isAlert = sensorData.co2 > 1000;
  const predictionMinutes = 25; 

  return (
    <div className="min-h-screen bg-slate-50 p-4 md:p-8 font-sans text-slate-900">
      <header className="max-w-6xl mx-auto mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-black tracking-tighter text-blue-600">AeroGuard</h1>
          <p className="text-slate-500 text-sm font-medium uppercase tracking-widest">Smart Home Room Manager</p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-white shadow-sm border rounded-full text-xs font-bold text-slate-600 uppercase">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          In Echtzeit (Backend API)
        </div>
      </header>

      <main className="max-w-6xl mx-auto">
        {/* StatCards zum Anzeigen der Sensordaten*/}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard icon={<Wind />} color="text-red-600" bg="bg-red-50" title="CO2" value={sensorData.co2} unit="ppm" />
          <StatCard icon={<Thermometer />} color="text-blue-600" bg="bg-blue-50" title="Temperatur" value={sensorData.temperature} unit="°C" />
          <StatCard icon={<Droplets />} color="text-yellow-600" bg="bg-yellow-50" title="Feuchtigkeit" value={sensorData.humidity} unit="%" />
          <StatCard icon={<Activity />} color="text-green-600" bg="bg-green-50" title="IAQ Score" value={sensorData.iaq_score} unit="/100" />
        </div>

        {/* Wertbedingte Warnmeldung */}
        {isAlert ? (
          <div className="mb-8 p-6 rounded-3xl border-4 border-red-500 bg-red-50 text-red-700 animate-pulse shadow-xl flex items-center gap-6">
            <AlertTriangle size={48} className="shrink-0" />
            <div>
              <h2 className="text-2xl font-black uppercase">Lüftung erforderlich!</h2>
              <p className="text-lg font-bold">Der CO2-Wert ({sensorData.co2} ppm) ist zu hoch.</p>
            </div>
          </div>
        ) : (
          <div className="mb-8 space-y-4">
            <div className="p-6 rounded-3xl border border-green-200 bg-green-50 text-green-700 flex items-center gap-4 shadow-sm">
              <CheckCircle size={32} className="shrink-0" />
              <div>
                <h2 className="text-xl font-bold">Raumluft ist optimal</h2>
                <p className="text-sm opacity-80 font-medium text-green-600">Aktuell ist keine Lüftung notwendig.</p>
              </div>
            </div>
            
            <div className="p-6 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-3xl text-white shadow-lg flex items-center gap-6">
              <div className="bg-white/20 p-4 rounded-2xl backdrop-blur-sm"><Timer size={32} /></div>
              <div>
                <h3 className="text-sm font-bold uppercase tracking-wider opacity-80">KI-Prognose</h3>
                <p className="text-2xl font-black">
                  {sensorData.prediction_minutes === null ? (
                    "Analyse läuft..."
                  ) : sensorData.prediction_minutes === -1 ? (
                    "Luft stabil"
                  ) : sensorData.prediction_minutes === 0 ? (
                    "Sofort lüften!"
                  ) : (
                  <>Lüftung voraussichtlich in: <span className="bg-white text-blue-700 px-4 py-1 rounded-xl ml-2 shadow-inner">{sensorData.prediction_minutes} Min.</span></>
                  )}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Graph */}
        <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-100 mb-8">
          <div className="flex items-center gap-2 mb-8">
            <Clock className="text-slate-400" size={24} />
            <h2 className="text-2xl font-black text-slate-800 italic uppercase">Historischer Verlauf</h2>
          </div>
          <div className="h-[400px] w-full text-xs font-bold">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={historyData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="time" axisLine={false} tickLine={false} />
                <YAxis axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ borderRadius: '24px', border: 'none', boxShadow: '0 25px 50px -12px rgb(0 0 0 / 0.15)' }} />
                <Legend iconType="circle" wrapperStyle={{ paddingTop: '30px' }} />
                <Line type="monotone" dataKey="co2" name="CO2 (ppm)" stroke="#ef4444" strokeWidth={4} dot={false} />
                <Line type="monotone" dataKey="temp" name="Temperatur (°C)" stroke="#3b82f6" strokeWidth={3} dot={false} strokeDasharray="5 5" />
                <Line type="monotone" dataKey="hum" name="Feuchtigkeit (%)" stroke="#eab308" strokeWidth={3} dot={false} />
                <Line type="monotone" dataKey="iaq" name="IAQ Score" stroke="#22c55e" strokeWidth={4} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Belegungsplan */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <div className="bg-white p-8 rounded-3xl shadow-sm border border-slate-100">
            <h2 className="text-2xl font-black mb-6 flex items-center gap-3"><Users className="text-blue-600" /> Belegungsplan</h2>
            <div className="flex flex-col gap-4">
              <select value={newDay} onChange={(e) => setNewDay(e.target.value)} className="p-4 bg-slate-50 rounded-2xl font-bold border-none focus:ring-2 focus:ring-blue-500">
                <option>Montag</option><option>Dienstag</option><option>Mittwoch</option><option>Donnerstag</option><option>Freitag</option><option>Samstag</option>
              </select>
              <div className="grid grid-cols-2 gap-4">
                <input type="time" value={newStart} onChange={(e) => setNewStart(e.target.value)} className="p-4 bg-slate-50 rounded-2xl font-bold border-none" />
                <input type="time" value={newEnd} onChange={(e) => setNewEnd(e.target.value)} className="p-4 bg-slate-50 rounded-2xl font-bold border-none" />
              </div>
              <input type="text" placeholder="Kursname" value={newLabel} onChange={(e) => setNewLabel(e.target.value)} className="p-4 bg-slate-50 rounded-2xl font-bold border-none" />
              <button onClick={addOccupation} className="bg-blue-600 text-white p-4 rounded-2xl font-black hover:bg-blue-700 shadow-lg transition-all">SPEICHERN</button>
            </div>
          </div>

          <div className="bg-slate-100/50 p-8 rounded-3xl border border-dashed border-slate-300">
            <h2 className="text-xl font-bold mb-6 text-slate-500 uppercase flex items-center gap-2"><Calendar size={20}/> Aktuelle Belegung</h2>
            <div className="space-y-3 h-[300px] overflow-y-auto pr-2">
              {occupations.map(occ => (
                <div key={occ.id} className="bg-white p-4 rounded-2xl flex justify-between items-center shadow-sm border-l-4 border-blue-500">
                  <div>
                    <p className="text-xs font-bold text-blue-600 uppercase">{occ.day}</p>
                    <p className="font-black text-slate-800">{occ.label}</p>
                    <p className="text-xs text-slate-400 font-bold">{occ.start_time} - {occ.end_time} Uhr</p>
                  </div>
                  <button onClick={() => deleteOccupation(occ.id)} className="text-slate-300 hover:text-red-500 transition-colors">
                    <Trash2 size={20} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

// StatCard Konfiguration
function StatCard({ icon, color, bg, title, value, unit }) {
  return (
    <div className="bg-white p-6 rounded-3xl shadow-sm border border-slate-100 transition-all hover:shadow-md">
      <div className="flex items-center gap-4 mb-4">
        <div className={`p-3 ${bg} ${color} rounded-2xl`}>{React.cloneElement(icon, { size: 24 })}</div>
        <h3 className="font-bold text-slate-400 text-xs uppercase tracking-widest">{title}</h3>
      </div>
      <p className="text-4xl font-black text-slate-900">{value}<span className="text-lg font-normal text-slate-400 ml-1">{unit}</span></p>
    </div>
  );
}

export default App;