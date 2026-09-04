import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const Navbar: React.FC = () => {
  const location = useLocation();

    const linkStyle = (path: string) => ({
    textDecoration: 'none',
    color: location.pathname === path ? '#113065' : '#ffffff', // active dark text, inactive white
    backgroundColor: location.pathname === path ? '#FAF9F6' : 'transparent', // active light bg
    fontWeight: location.pathname === path ? 600 : 500,
    padding: '0.5rem 1rem',
    borderRadius: '0.5rem',
    marginLeft: '1rem',
    transition: 'all 0.2s',
    boxShadow: location.pathname === path ? '0 2px 6px rgba(0,0,0,0.15)' : 'none',
    border: 'none',
    cursor: 'pointer',
    });

  return (
    <nav style={{
      display: 'flex',
      alignItems: 'center',
      padding: '1rem 2rem',
      backgroundColor: '#113065',
      boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
      zIndex: 1000,
    }}>
      <h1 style={{ fontSize: '1rem', fontWeight: 700, color: '#ffffff', margin: 0 }}>GroundBreaker</h1>
      <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center' }}>
        <Link to="/dashboard" style={linkStyle('/dashboard')}>Dashboard</Link>
        <div style={{...linkStyle('/scan'), color: "grey"}}>Scan</div>
        {/* <Link to="/scan" style={linkStyle('/scan')}>Scan</Link> */}
      </div>
    </nav>
  );
};

export default Navbar;
