import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Scan from './pages/Scan';
import Billing from './pages/Billing';
import History from './pages/History';
import './styles/main.css';

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <Navbar />
        <main className="main-content">
          <Routes>
            <Route path="/"        element={<Navigate to="/scan" />} />
            <Route path="/scan"    element={<Scan />} />
            <Route path="/billing" element={<Billing />} />
            <Route path="/history" element={<History />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;