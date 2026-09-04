import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Waves, LayoutDashboard, Database, Upload, MapPin, Cpu } from 'lucide-react';
import { api } from '../services/api';
import type { HealthCheckResponse } from '../types/sonar';

export const Navbar: React.FC = () => {
  const [health, setHealth] = useState<HealthCheckResponse | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await api.getHealth();
        setHealth(res);
      } catch (e) {
        console.error("Health check failed", e);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="bg-sonar-900/90 backdrop-blur border-b border-sonar-700/50 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Subtitle */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-tr from-sonar-accent/20 to-sonar-cyan/30 border border-sonar-accent/40 flex items-center justify-center text-sonar-accent shadow-lg shadow-sonar-accent/10">
              <Waves className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xl font-bold tracking-tight text-white font-mono">
                  Sonar<span className="text-sonar-accent">AI</span>
                </span>
                <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-sonar-700/60 text-sonar-accent border border-sonar-accent/20">
                  Log-First
                </span>
              </div>
              <p className="text-xs text-slate-400 font-sans">
                Intelligent Side-Scan Sonar Survey Analysis
              </p>
            </div>
          </div>

          {/* Navigation Items */}
          <nav className="hidden md:flex items-center space-x-1">
            <NavLink
              to="/dashboard"
              className={({ isActive }) =>
                `flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-sonar-800 text-sonar-accent border border-sonar-accent/30'
                    : 'text-slate-300 hover:bg-sonar-800/60 hover:text-white'
                }`
              }
            >
              <LayoutDashboard className="w-4 h-4" />
              <span>Dashboard</span>
            </NavLink>

            <NavLink
              to="/logs"
              className={({ isActive }) =>
                `flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-sonar-800 text-sonar-accent border border-sonar-accent/30'
                    : 'text-slate-300 hover:bg-sonar-800/60 hover:text-white'
                }`
              }
            >
              <Database className="w-4 h-4" />
              <span>Survey Logs</span>
            </NavLink>

            <NavLink
              to="/upload"
              className={({ isActive }) =>
                `flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-sonar-800 text-sonar-accent border border-sonar-accent/30'
                    : 'text-slate-300 hover:bg-sonar-800/60 hover:text-white'
                }`
              }
            >
              <Upload className="w-4 h-4" />
              <span>Upload Log</span>
            </NavLink>

            <NavLink
              to="/map"
              className={({ isActive }) =>
                `flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-sonar-800 text-sonar-accent border border-sonar-accent/30'
                    : 'text-slate-300 hover:bg-sonar-800/60 hover:text-white'
                }`
              }
            >
              <MapPin className="w-4 h-4" />
              <span>Map</span>
            </NavLink>
          </nav>

          {/* Model Provider Status Tag */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2 bg-sonar-800/80 px-3 py-1.5 rounded-full border border-sonar-700 text-xs">
              <Cpu className={`w-3.5 h-3.5 ${health?.is_mock ? 'text-sonar-amber' : 'text-sonar-emerald'}`} />
              <span className="font-mono text-slate-300 truncate max-w-[180px]">
                {health ? health.inference_provider : 'Connecting...'}
              </span>
              {health?.is_mock && (
                <span className="text-[9px] font-bold uppercase bg-sonar-amber/20 text-sonar-amber px-1.5 py-0.5 rounded">
                  DEMO MODE
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
