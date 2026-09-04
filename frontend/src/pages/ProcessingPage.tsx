import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowRight, AlertCircle, RefreshCw } from 'lucide-react';
import { api } from '../services/api';
import type { AnalysisStatusResponse, SurveyLogDetail } from '../types/sonar';
import { ProcessingStatus } from '../components/ProcessingStatus';

export const ProcessingPage: React.FC = () => {
  const { logId } = useParams<{ logId: string }>();
  const navigate = useNavigate();

  const [status, setStatus] = useState<AnalysisStatusResponse | null>(null);
  const [logDetail, setLogDetail] = useState<SurveyLogDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!logId) return;

    let isMounted = true;

    const pollStatus = async () => {
      try {
        const statusRes = await api.getAnalysisStatus(logId);
        const detailRes = await api.getLogDetail(logId);

        if (isMounted) {
          setStatus(statusRes);
          setLogDetail(detailRes);
          setLoading(false);

          if (statusRes.status === 'UPLOADED') {
            await api.startAnalysis(logId);
          }
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.message || 'Failed to fetch analysis status.');
          setLoading(false);
        }
      }
    };

    pollStatus();
    const interval = setInterval(pollStatus, 1500);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [logId]);

  if (loading && !status) {
    return (
      <div className="p-16 text-center text-slate-300">
        <RefreshCw className="w-10 h-10 animate-spin mx-auto text-sonar-accent mb-3" />
        <p className="font-mono text-sm">Initializing Survey Pipeline...</p>
      </div>
    );
  }

  if (error || !status || !logDetail) {
    return (
      <div className="max-w-2xl mx-auto p-6 bg-sonar-rose/10 border border-sonar-rose/30 text-sonar-rose rounded-xl text-center">
        <AlertCircle className="w-10 h-10 mx-auto mb-2" />
        <h3 className="text-lg font-bold font-mono">Pipeline Error</h3>
        <p className="text-sm mt-1">{error || 'Survey log not found.'}</p>
        <button
          onClick={() => navigate('/dashboard')}
          className="mt-4 px-4 py-2 bg-sonar-800 text-white rounded-lg font-mono text-xs"
        >
          Return to Dashboard
        </button>
      </div>
    );
  }

  const isCompleted = status.status === 'COMPLETED';

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-12">
      <ProcessingStatus
        status={status}
        images={logDetail.images}
        logName={logDetail.log_name}
      />

      {/* Completion Banner */}
      {isCompleted && (
        <div className="bg-gradient-to-r from-sonar-emerald/20 via-sonar-800 to-sonar-cyan/20 border border-sonar-emerald/50 p-6 rounded-2xl shadow-2xl flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <h3 className="text-xl font-bold font-mono text-white">
              Analysis Completed!
            </h3>
            <p className="text-sm text-slate-300">
              All {status.total_images} survey frames have been analyzed by the Side-Scan Sonar engine.
            </p>
          </div>

          <button
            onClick={() => navigate(`/survey/${logId}`)}
            className="px-6 py-3 bg-sonar-accent hover:bg-sonar-accent/90 text-sonar-950 font-bold rounded-xl shadow-lg shadow-sonar-accent/20 flex items-center space-x-2 text-sm whitespace-nowrap"
          >
            <span>View Survey Results</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
};
