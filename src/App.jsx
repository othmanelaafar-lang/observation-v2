import { Routes, Route } from 'react-router-dom';
import MainLayout from './layouts/MainLayout';
import Home from './pages/Home';
import Explorer from './pages/Explorer';
import Dashboard from './pages/Dashboard';
import ExpertProfile from './pages/ExpertProfile';
import About from './pages/About';

export default function App() {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route path="/" element={<Home />} />
        <Route path="/explorer" element={<Explorer />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/expert/:id" element={<ExpertProfile />} />
        <Route path="/about" element={<About />} />
      </Route>
    </Routes>
  );
}