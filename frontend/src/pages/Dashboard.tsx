import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, RefreshCw, AlertCircle } from 'lucide-react';
import { api } from '../services/api';
import type { SurveyLogSummary } from '../types/sonar';
import { SummaryCards } from '../components/SummaryCards';
import { LogTable } from '../components/LogTable';

export const DashboardPage: React.FC = () => {
  const [logs, setLogs] = useState<SurveyLogSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const loadLogs = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getLogs();
      setLogs(data);
    } catch (err: any) {
      setError(err.message || 'Failed to connect to SonarAI backend.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLogs();
  }, []);

  const handleStartAnalysis = async (logId: string) => {
    try {
      await api.startAnalysis(logId);
      navigate(`/processing/${logId}`);
    } catch (err: any) {
      alert(`Failed to start analysis: ${err.message}`);
    }
  };

  return (
    <div className="space-y-8 pb-12">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-sonar-900 via-sonar-800 to-sonar-900 p-6 rounded-2xl border border-sonar-700/60 shadow-2xl">
        <div>
          <div className="flex items-center space-x-3 mb-1">
            <h1 className="text-3xl font-bold font-mono tracking-tight text-white">
              Sonar<span className="text-sonar-accent">AI</span>
            </h1>
            <span className="bg-sonar-accent/10 text-sonar-accent border border-sonar-accent/30 text-xs px-2.5 py-0.5 rounded-full font-mono font-semibold">
              Survey Analysis Platform
            </span>
          </div>
          <p className="text-slate-300 text-sm">
            Intelligent Side-Scan Sonar (SSS) Log Processing & Anomaly Detection System
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={loadLogs}
            className="p-2.5 bg-sonar-800 hover:bg-sonar-700 text-slate-300 rounded-xl border border-sonar-700 transition-colors"
            title="Refresh Data"
          >
            <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => navigate('/upload')}
            className="px-5 py-2.5 bg-sonar-accent hover:bg-sonar-accent/90 text-sonar-950 font-semibold rounded-xl transition-colors shadow-lg shadow-sonar-accent/20 flex items-center space-x-2 text-sm"
          >
            <Upload className="w-4 h-4" />
            <span>Upload SSS Survey Log</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-sonar-rose/10 border border-sonar-rose/30 text-sonar-rose rounded-xl flex items-center space-x-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span className="text-sm font-medium">{error}</span>
        </div>
      )}

      {/* Summary Cards */}
      <SummaryCards logs={logs} />

      {/* Recent Survey Logs Table */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold font-mono text-white tracking-tight">
            Recent Survey Logs
          </h2>
          <span className="text-xs text-slate-400 font-mono">
            Log-first processing active
          </span>
        </div>

        {loading && logs.length === 0 ? (
          <div className="p-12 text-center text-slate-400 bg-sonar-900/40 rounded-xl border border-sonar-800">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-2 text-sonar-accent" />
            <p className="text-sm">Loading survey logs...</p>
          </div>
        ) : (
          <LogTable logs={logs} onStartAnalysis={handleStartAnalysis} />
        )}
      </div>
    </div>
  );
};
