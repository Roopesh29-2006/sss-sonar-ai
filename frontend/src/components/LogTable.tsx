import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Play, ArrowRight, Clock, Image, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';
import type { SurveyLogSummary } from '../types/sonar';

interface LogTableProps {
  logs: SurveyLogSummary[];
  onStartAnalysis?: (logId: string) => void;
}

export const LogTable: React.FC<LogTableProps> = ({ logs, onStartAnalysis }) => {
  const navigate = useNavigate();

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-sonar-emerald/20 text-sonar-emerald border border-sonar-emerald/30">
            <CheckCircle className="w-3 h-3 mr-1" /> Completed
          </span>
        );
      case 'PROCESSING':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-sonar-cyan/20 text-sonar-cyan border border-sonar-cyan/30 animate-pulse">
            <Loader2 className="w-3 h-3 mr-1 animate-spin" /> Processing
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-sonar-rose/20 text-sonar-rose border border-sonar-rose/30">
            <AlertCircle className="w-3 h-3 mr-1" /> Failed
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-700/60 text-slate-300 border border-slate-600">
            <Clock className="w-3 h-3 mr-1" /> Ready
          </span>
        );
    }
  };

  if (logs.length === 0) {
    return (
      <div className="p-8 text-center bg-sonar-900/40 rounded-xl border border-sonar-800">
        <Image className="w-12 h-12 text-slate-500 mx-auto mb-3" />
        <h3 className="text-lg font-medium text-slate-200">No Survey Logs Found</h3>
        <p className="text-sm text-slate-400 mt-1 mb-4">Upload an SSS survey log or zip archive to get started.</p>
        <button
          onClick={() => navigate('/upload')}
          className="px-4 py-2 bg-sonar-accent text-sonar-950 font-semibold rounded-lg hover:bg-sonar-accent/90 transition-colors text-sm"
        >
          Upload Survey Log
        </button>
      </div>
    );
  }

  return (
    <div className="bg-sonar-900/70 rounded-xl border border-sonar-700/60 overflow-hidden shadow-xl">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-sonar-800/80 text-xs uppercase font-mono tracking-wider text-slate-400 border-b border-sonar-700">
            <tr>
              <th className="px-6 py-3.5">Survey Log Name</th>
              <th className="px-4 py-3.5 text-center">Images</th>
              <th className="px-4 py-3.5">Upload Date</th>
              <th className="px-4 py-3.5">Status</th>
              <th className="px-4 py-3.5 text-center">Detections</th>
              <th className="px-4 py-3.5 text-center">Unknowns</th>
              <th className="px-6 py-3.5 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-sonar-800/60">
            {logs.map((log) => {
              const formattedDate = new Date(log.upload_timestamp).toLocaleDateString(undefined, {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
              });

              return (
                <tr key={log.log_id} className="hover:bg-sonar-800/40 transition-colors">
                  <td className="px-6 py-4 font-medium text-white font-mono flex items-center space-x-2">
                    <span className="truncate max-w-[200px] sm:max-w-[280px]" title={log.log_name}>
                      {log.log_name}
                    </span>
                  </td>
                  <td className="px-4 py-4 text-center font-mono text-slate-200">
                    {log.total_images}
                  </td>
                  <td className="px-4 py-4 text-slate-400 text-xs">
                    {formattedDate}
                  </td>
                  <td className="px-4 py-4 whitespace-nowrap">
                    {getStatusBadge(log.status)}
                  </td>
                  <td className="px-4 py-4 text-center font-mono font-semibold text-sonar-accent">
                    {log.total_detections}
                  </td>
                  <td className="px-4 py-4 text-center font-mono font-semibold text-sonar-amber">
                    {log.unknown_count}
                  </td>
                  <td className="px-6 py-4 text-right whitespace-nowrap">
                    {log.status === 'COMPLETED' ? (
                      <button
                        onClick={() => navigate(`/survey/${log.log_id}`)}
                        className="inline-flex items-center space-x-1 px-3 py-1.5 bg-sonar-800 hover:bg-sonar-700 text-sonar-accent border border-sonar-accent/30 rounded-md text-xs font-medium transition-colors"
                      >
                        <span>View Results</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    ) : log.status === 'PROCESSING' ? (
                      <button
                        onClick={() => navigate(`/processing/${log.log_id}`)}
                        className="inline-flex items-center space-x-1 px-3 py-1.5 bg-sonar-cyan/20 hover:bg-sonar-cyan/30 text-sonar-cyan border border-sonar-cyan/40 rounded-md text-xs font-medium transition-colors"
                      >
                        <span>Live Pipeline</span>
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      </button>
                    ) : (
                      <button
                        onClick={() => {
                          if (onStartAnalysis) {
                            onStartAnalysis(log.log_id);
                          } else {
                            navigate(`/processing/${log.log_id}`);
                          }
                        }}
                        className="inline-flex items-center space-x-1 px-3 py-1.5 bg-sonar-accent text-sonar-950 hover:bg-sonar-accent/90 rounded-md text-xs font-semibold transition-colors"
                      >
                        <Play className="w-3.5 h-3.5 fill-current" />
                        <span>Start Analysis</span>
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
