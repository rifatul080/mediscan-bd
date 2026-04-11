import { NavLink } from 'react-router-dom';

function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        Medi<span>Scan</span> BD
      </div>
      <div className="navbar-links">
        <NavLink to="/scan" className={({ isActive }) => isActive ? 'active' : ''}>
          📷 Scan
        </NavLink>
        <NavLink to="/billing" className={({ isActive }) => isActive ? 'active' : ''}>
          🧾 Billing
        </NavLink>
        <NavLink to="/history" className={({ isActive }) => isActive ? 'active' : ''}>
          📋 History
        </NavLink>
      </div>
    </nav>
  );
}

export default Navbar;