import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
// import Scan from './pages/Scan';
import Navbar from './components/Navbar';

const App: React.FC = () => (
  <Router>
    <Navbar />
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/dashboard" element={<Dashboard />} />
      {/* <Route path="/scan" element={<Scan />} /> */}
    </Routes>
  </Router>
);

export default App;
