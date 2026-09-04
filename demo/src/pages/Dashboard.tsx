import { useState } from 'react';
import { Home, AlertTriangle, Shield } from 'lucide-react';
import Model from '../components/Model';

interface SafetyFeature {
  id: number;
  name: string;
  room: string;
  status: string;
  icon: string;
  src: string;
}

interface Hazard {
  id: number;
  name: string;
  room: string;
  risk: string;
  riskColor: string;
  icon: string;
  src: string;
}

const Dashboard = () => {
  const [selectedRoom, setSelectedRoom] = useState<string | null>(null);
  const [selectedItem, setSelectedItem] = useState<Hazard | SafetyFeature | null>(null);

  const safetyFeatures: SafetyFeature[] = [
    { id: 0, name: 'Grab bar', room: 'Bedroom', status: 'ACTIVE', icon: '🏗️', src: '/img/grabbar.jpg' }
  ];

  const hazards: Hazard[] = [
    { id: 1, name: 'Bed', room: 'Bedroom', risk: 'MEDIUM RISK', riskColor: 'bg-red-100 text-red-800', icon: '🛏️', src: '/img/bed.jpg' },
    { id: 2, name: 'Rug', room: 'Bathroom', risk: 'HIGH RISK', riskColor: 'bg-red-100 text-red-800', icon: '🧣', src: '/img/rug.jpg' },
    { id: 3, name: 'Step', room: 'Bathroom', risk: 'HIGH RISK', riskColor: 'bg-green-100 text-green-800', icon: '👣', src: '/img/step1.jpg' },
    { id: 4, name: 'Step', room: 'Kitchen', risk: 'MEDIUM RISK', riskColor: 'bg-green-100 text-green-800', icon: '👣', src: '/img/step2.jpg' },
    { id: 5, name: 'Stair', room: 'Kitchen', risk: 'MEDIUM RISK', riskColor: 'bg-green-100 text-green-800', icon: '🪜', src: '/img/stair.jpg' },
    { id: 6, name: 'Couch', room: 'Living Room', risk: 'MEDIUM RISK', riskColor: 'bg-green-100 text-green-800', icon: '🛋️', src: '/img/couch.jpg' },
  ];

  const getRiskStyle = (risk: string) => {
    switch (risk) {
      case 'HIGH RISK': return { backgroundColor: '#fadadaff', color: '#991b1b' };
      case 'MEDIUM RISK': return { backgroundColor: '#fff8daff', color: '#92400e' };
      case 'LOW RISK': return { backgroundColor: '#dbfae4ff', color: '#166534' };
      default: return { backgroundColor: '#f3f4f6', color: '#374151' };
    }
  };

  const getRiskBorderColor = (risk: string) => {
    switch (risk) {
      case 'HIGH RISK': return '#e11f1fff';
      case 'MEDIUM RISK': return '#cbb431ff';
      case 'LOW RISK': return '#188643ff';
      default: return '#374151';
    }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'stretch', height: 'calc(100vh - 4.2rem)', backgroundColor: '#f4ede6ff' }}>
      <div style={{ flex: 1, maxWidth: '1600px', padding: '1.5rem', display: 'flex', flexDirection: 'column' }}>
        {/* Main Layout */}
        <div style={{ flex: 1, display: 'flex', gap: '1rem', minHeight: 0 }}>
          {/* Left Section */}
          <div style={{ flexGrow: 1, flex: 3, display: 'flex', flexDirection: 'column', gap: '1.5rem', minHeight: 0 }}>
            {/* Top Stats */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', flexShrink: 0 }}>
              {/* Overall Risk Score */}
              <div style={{ backgroundColor: 'white', borderRadius: '0.75rem', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', padding: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <div style={{ backgroundColor: '#dbeafe', padding: '0.75rem', borderRadius: '0.5rem' }}>
                    <Home size={32} color="#2563eb" />
                  </div>
                  <div>
                    <p style={{ color: '#49505eff', fontSize: '1rem', fontWeight: 'bold', margin: 0 }}>Overall Fall Risk</p>
                    <p style={{ fontSize: '2rem', fontWeight: 'bold', color: '#2563eb', margin: 0 }}>24.59%</p>
                  </div>
                </div>
              </div>
              {/* Total Hazards */}
              <div style={{ backgroundColor: 'white', borderRadius: '0.75rem', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', padding: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <div style={{ backgroundColor: '#fecaca', padding: '0.75rem', borderRadius: '0.5rem' }}>
                    <AlertTriangle size={32} color="#dc2626" />
                  </div>
                  <div>
                    <p style={{ color: '#49505eff', fontSize: '1rem', fontWeight: 'bold', margin: 0 }}>Total Fall Hazards</p>
                    <p style={{ fontSize: '2rem', fontWeight: 'bold', color: '#dc2626', margin: 0 }}>6</p>
                  </div>
                </div>
              </div>
              {/* Total Safety Features */}
              <div style={{ backgroundColor: 'white', borderRadius: '0.75rem', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', padding: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <div style={{ backgroundColor: '#bbf7d0', padding: '0.75rem', borderRadius: '0.5rem' }}>
                    <Shield size={32} color="#16a34a" />
                  </div>
                  <div>
                    <p style={{ color: '#49505eff', fontSize: '1rem', fontWeight: 'bold', margin: 0 }}>Total Safety Features</p>
                    <p style={{ fontSize: '2rem', fontWeight: 'bold', color: '#16a34a', margin: 0 }}>1</p>
                  </div>
                </div>
              </div>
            </div>

            
            <div style={{ flexGrow: 1, display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', minHeight: 0 }}>
              {/* Floor Plan */}
              <div style={{ gridColumn: '1 / span 2', minWidth: 0, display: 'flex', flexDirection: 'column', backgroundColor: 'white', borderRadius: '0.75rem', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', padding: '1.5rem' }}>
                <h3 style={{ fontSize: '1.8rem', fontWeight: 'bold', color: '#1f2937', marginTop: '0' }}> Assessment by Room</h3>
                <div style={{ flex: 1, width: '100%', minWidth: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#9ca3af' }}>
                  <Model selectedItem={selectedItem} />
                </div>
              </div>
              {/* Object Detected View Card */}
              <div style={{ gridColumn: 3, minWidth: 0, flex: 1, display: 'flex', flexDirection: 'column', backgroundColor: 'white', borderRadius: '0.75rem', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', padding: '1.5rem', overflowY: 'auto' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <h3 style={{ fontSize: '1.3rem', fontWeight: 'bold', marginBottom: '1rem' }}>Image</h3>
                  {/* cross to deselect */}
                  {selectedItem && (<div onClick={() => setSelectedItem(null)} style={{ cursor: 'pointer', fontSize: '1.5rem', color: '#9ca3af' }}>×</div>)}
                </div>
                {selectedItem ? (
                    <img src={selectedItem?.src} alt="Living Room" style={{ maxHeight: '85%', borderRadius: '0.5rem' }} />
                  ) : (
                    <div style={{ width: '100%', height: '100%', borderRadius: '0.5rem', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#9ca3af' }}>
                     Select a hazard or safety feature
                    </div>
                  )}
              </div>
            </div>
          </div>


          {/* Safety and Hazards Card */}
          <div style={{ flex: 1, backgroundColor: 'white', borderRadius: '0.75rem', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
            <div style={{ height: 'calc(100% - 3rem)', margin: '1.5rem', overflowY: 'auto', scrollbarGutter: 'stable', scrollbarColor: '#d1d5db #f9fafb', scrollbarWidth: 'thin' }}>
              <h3 style={{ fontSize: '1.3rem', fontWeight: 'bold', marginBottom: '1rem' }}>Safety Features</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', padding: '0.5rem' }}>
                {safetyFeatures.map((f) => (
                  <div 
                    key={f.id} 
                    style={{ 
                      display: 'flex', 
                      gap: '0.75rem', 
                      padding: '0.75rem', 
                      border: selectedItem?.id === f.id ? '2px solid #166534' : '1px solid #e5e7eb', 
                      borderRadius: '0.5rem',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease-in-out',
                      backgroundColor: 'white',
                      transform: 'scale(1)',
                      boxShadow: selectedItem?.id === f.id ? '0 4px 12px rgba(22, 163, 74, 0.15)' : '0 1px 3px rgba(0,0,0,0.1)'
                    }} 
                    onClick={() => setSelectedItem(f)}
                    onMouseEnter={(e) => {
                      if (selectedItem?.id !== f.id) {
                        e.currentTarget.style.transform = 'scale(1.02)';
                        e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
                        e.currentTarget.style.backgroundColor = '#f9fafb';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (selectedItem?.id !== f.id) {
                        e.currentTarget.style.transform = 'scale(1)';
                        e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)';
                        e.currentTarget.style.backgroundColor = 'white';
                      }
                    }}
                  >
                    <div style={{ fontSize: '1.5rem' }}>{f.icon}</div>
                    <div style={{ flex: 1 }}>
                      <h4 style={{ margin: 0, fontSize: '0.875rem', fontWeight: 600 }}>{f.name}</h4>
                      <p style={{ margin: 0, fontSize: '0.75rem', color: '#6b7280' }}>in {f.room}</p>
                      <span style={{ display: 'inline-block', marginTop: '0.25rem', padding: '0.25rem 0.5rem', backgroundColor: '#dcfce7', color: '#166534', borderRadius: '9999px', fontSize: '0.75rem' }}>{f.status}</span>
                    </div>
                  </div>
                ))}
              </div>
              
              <h3 style={{ fontSize: '1.3rem', fontWeight: 'bold', marginBottom: '1rem' }}>Hazards</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', overflowY: 'auto', padding: '0.5rem' }}>
                {hazards.map((h) => (
                  <div 
                    key={h.id} 
                    style={{ 
                      display: 'flex', 
                      gap: '0.75rem', 
                      padding: '0.75rem', 
                      border: selectedItem?.id === h.id ? `2px solid ${getRiskBorderColor(h.risk)}` : '1px solid #e5e7eb', 
                      borderRadius: '0.5rem',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease-in-out',
                      backgroundColor: 'white',
                      transform: 'scale(1)',
                      boxShadow: selectedItem?.id === h.id ? `0 4px 12px ${getRiskBorderColor(h.risk)}20` : '0 1px 3px rgba(0,0,0,0.1)'
                    }} 
                    onClick={() => setSelectedItem(h)}
                    onMouseEnter={(e) => {
                      if (selectedItem?.id !== h.id) {
                        e.currentTarget.style.transform = 'scale(1.02)';
                        e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
                        e.currentTarget.style.backgroundColor = '#f9fafb';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (selectedItem?.id !== h.id) {
                        e.currentTarget.style.transform = 'scale(1)';
                        e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)';
                        e.currentTarget.style.backgroundColor = 'white';
                      }
                    }}
                  >
                    <div style={{ fontSize: '1.5rem' }}>{h.icon}</div>
                    <div style={{ flex: 1 }}>
                      <h4 style={{ margin: 0, fontSize: '0.875rem', fontWeight: 600 }}>{h.name}</h4>
                      <p style={{ margin: 0, fontSize: '0.75rem', color: '#6b7280' }}>in {h.room}</p>
                      <span style={{ display: 'inline-block', marginTop: '0.25rem', padding: '0.25rem 0.5rem', borderRadius: '9999px', fontSize: '0.75rem', ...getRiskStyle(h.risk) }}>{h.risk}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Selected Room Info */}
        {selectedRoom && (
          <div style={{ marginTop: '1rem', backgroundColor: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '0.75rem', padding: '1rem', flexShrink: 0 }}>
            <h3 style={{ fontSize: '1.125rem', fontWeight: 600, color: '#1e40af', marginBottom: '0.5rem' }}>Selected Room: {selectedRoom}</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <h4 style={{ fontWeight: 500, marginBottom: '0.5rem' }}>Safety Features:</h4>
                <ul style={{ margin: 0, paddingLeft: '1rem', fontSize: '0.875rem' }}>
                  {safetyFeatures.filter(f => f.room === selectedRoom).map(f => <li key={f.id}>{f.name} ({f.status})</li>)}
                  {safetyFeatures.filter(f => f.room === selectedRoom).length === 0 && <li style={{ color: '#6b7280' }}>No safety features found</li>}
                </ul>
              </div>
              <div>
                <h4 style={{ fontWeight: 500, marginBottom: '0.5rem' }}>Hazards:</h4>
                <ul style={{ margin: 0, paddingLeft: '1rem', fontSize: '0.875rem' }}>
                  {hazards.filter(h => h.room === selectedRoom).map(h => <li key={h.id}>{h.name} ({h.risk})</li>)}
                  {hazards.filter(h => h.room === selectedRoom).length === 0 && <li style={{ color: '#6b7280' }}>No hazards found</li>}
                </ul>
              </div>
            </div>
            <button onClick={() => setSelectedRoom(null)} style={{ marginTop: '1rem', padding: '0.5rem 1rem', backgroundColor: '#2563eb', color: 'white', borderRadius: '0.5rem', border: 'none' }}>Close</button>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;