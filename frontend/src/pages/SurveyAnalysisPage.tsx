import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, PieChart, Pie
} from 'recharts';
import { Target, RefreshCw } from 'lucide-react';
import { api } from '../services/api';
import type { SurveyResultsResponse, ImageRecord } from '../types/sonar';

export const SurveyAnalysisPage: React.FC = () => {
  const { logId } = useParams<{ logId: string }>();
  const navigate = useNavigate();

  const [results, setResults] = useState<SurveyResultsResponse | null>(null);
  const [images, setImages] = useState<ImageRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!logId) return;

    const loadData = async () => {
      try {
        setLoading(true);
        const res = await api.getSurveyResults(logId);
        const imgs = await api.getSurveyImages(logId);
        setResults(res);
        setImages(imgs);
      } catch (err: any) {
        setError(err.message || 'Failed to load survey results.');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [logId]);

  if (loading) {
    return (
      <div className="p-16 text-center text-slate-300">
        <RefreshCw className="w-10 h-10 animate-spin mx-auto text-sonar-accent mb-3" />
        <p className="font-mono text-sm">Loading Survey Analysis Metrics...</p>
      </div>
    );
  }

  if (error || !results) {
    return (
      <div className="max-w-xl mx-auto p-6 bg-sonar-rose/10 border border-sonar-rose/30 text-sonar-rose rounded-xl text-center">
        <p className="font-mono text-sm">{error || 'Survey results not found.'}</p>
        <button
          onClick={() => navigate('/dashboard')}
          className="mt-4 px-4 py-2 bg-sonar-800 text-white rounded-lg font-mono text-xs"
        >
          Return to Dashboard
        </button>
      </div>
    );
  }

  // Chart data preparation
  const chartData = results.detections_per_image.map((d) => ({
    name: `#${d.image_index}`,
    filename: d.filename,
    imageId: d.image_id,
    Known: d.known_count,
    Unknown: d.unknown_count,
    Total: d.detections_count
  }));

  const pieData = [
    { name: 'Known Shipwreck', value: results.known_count, color: '#00F5D4' },
    { name: 'Potential Unknown Objects', value: results.unknown_count, color: '#FFB703' }
  ];

  return (
    <div className="space-y-8 pb-12">
      {/* Top Header Summary */}
      <div className="bg-sonar-900/80 p-6 rounded-2xl border border-sonar-700/60 shadow-2xl space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-sonar-700/60 pb-4">
          <div>
            <span className="text-xs font-mono text-sonar-accent uppercase tracking-wider block">
              Survey Analysis Summary
            </span>
            <h1 className="text-3xl font-bold font-mono text-white mt-1">
              {results.log_name}
            </h1>
          </div>

          {results.is_mock && (
            <span className="text-xs font-mono font-semibold bg-sonar-amber/20 text-sonar-amber px-3 py-1.5 rounded-lg border border-sonar-amber/30">
              DEMO RESULTS
            </span>
          )}
        </div>

        {/* Survey Stat Badges */}
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-9 gap-3 text-center">
          <div className="bg-sonar-950/70 p-3 rounded-lg border border-sonar-800">
            <span className="text-[10px] font-mono text-slate-400 uppercase block">Total Images</span>
            <span className="text-xl font-bold font-mono text-white">{results.total_images}</span>
          </div>

          <div className="bg-sonar-950/70 p-3 rounded-lg border border-sonar-800">
            <span className="text-[10px] font-mono text-slate-400 uppercase block">Processed</span>
            <span className="text-xl font-bold font-mono text-sonar-cyan">{results.processed_images}</span>
          </div>

          <div className="bg-sonar-950/70 p-3 rounded-lg border border-sonar-800">
            <span className="text-[10px] font-mono text-slate-400 uppercase block">Total Objects</span>
            <span className="text-xl font-bold font-mono text-sonar-accent">{results.total_detections}</span>
          </div>

          <div className="bg-sonar-950/70 p-3 rounded-lg border border-sonar-800">
            <span className="text-[10px] font-mono text-slate-400 uppercase block">Known (Shipwreck)</span>
            <span className="text-xl font-bold font-mono text-sonar-emerald">{results.known_count}</span>
          </div>

          <div className="bg-sonar-950/70 p-3 rounded-lg border border-sonar-800">
            <span className="text-[10px] font-mono text-slate-400 uppercase block">Potential Unknown Objects</span>
            <span className="text-xl font-bold font-mono text-sonar-amber">{results.unknown_count}</span>
          </div>

          <div className="bg-sonar-950/70 p-3 rounded-lg border border-sonar-800">
            <span className="text-[10px] font-mono text-slate-400 uppercase block">Images With Shipwrecks</span>
            <span className="text-xl font-bold font-mono text-sonar-cyan">{results.images_with_known_detections}</span>
          </div>

          <div className="bg-sonar-950/70 p-3 rounded-lg border border-sonar-800">
            <span className="text-[10px] font-mono text-slate-400 uppercase block">Images Requiring Human Review</span>
            <span className="text-xl font-bold font-mono text-sonar-amber">{results.images_with_unknown_objects}</span>
          </div>

          <div className="bg-sonar-950/70 p-3 rounded-lg border border-sonar-800">
            <span className="text-[10px] font-mono text-slate-400 uppercase block">High Confidence</span>
            <span className="text-xl font-bold font-mono text-indigo-400">{results.high_confidence_count}</span>
          </div>

          <div className="bg-sonar-950/70 p-3 rounded-lg border border-sonar-800">
            <span className="text-[10px] font-mono text-slate-400 uppercase block">Avg Confidence</span>
            <span className="text-xl font-bold font-mono text-white">{(results.average_confidence * 100).toFixed(1)}%</span>
          </div>
        </div>
      </div>

      {/* Visual Analytics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Detections Per Image Chart */}
        <div className="lg:col-span-2 bg-sonar-900/80 p-6 rounded-2xl border border-sonar-700/60 shadow-xl">
          <h3 className="text-sm font-bold font-mono text-white mb-4">
            Detections Per Sonar Image Frame
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <XAxis dataKey="name" stroke="#64748B" fontSize={11} />
                <YAxis stroke="#64748B" fontSize={11} allowDecimals={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0B132B', borderColor: '#2A365C', color: '#fff' }}
                />
                <Bar dataKey="Known" fill="#00F5D4" stackId="a" name="Shipwreck" />
                <Bar dataKey="Unknown" fill="#FFB703" stackId="a" name="Potential Unknown Objects" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Known vs Unknown Breakdown */}
        <div className="bg-sonar-900/80 p-6 rounded-2xl border border-sonar-700/60 shadow-xl flex flex-col justify-between">
          <h3 className="text-sm font-bold font-mono text-white mb-2">
            Target Classification Ratio
          </h3>
          <div className="h-52 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: '#0B132B', borderColor: '#2A365C' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center space-x-6 text-xs font-mono">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded-full bg-sonar-accent" />
              <span>Known ({results.known_count})</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded-full bg-sonar-amber" />
              <span>Potential Unknown Objects ({results.unknown_count})</span>
            </div>
          </div>
        </div>
      </div>

      {/* Image Sequence Timeline Carousel Bar */}
      <div className="bg-sonar-900/80 p-6 rounded-2xl border border-sonar-700/60 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold font-mono text-white uppercase tracking-wider">
              Sequential Image Log Timeline
            </h3>
            <p className="text-xs text-slate-400">Click any image frame to launch the high-resolution AI Sonar Overlay Inspector.</p>
          </div>
        </div>

        <div className="flex items-center space-x-2 overflow-x-auto pb-3 pt-1">
          {images.map((img) => {
            const hasDet = img.analysis_result?.detections && img.analysis_result.detections.length > 0;
            const detCount = img.analysis_result?.detections?.length || 0;

            return (
              <button
                key={img.image_id}
                onClick={() => navigate(`/image/${logId}/${img.image_id}`)}
                className={`flex-shrink-0 p-2.5 rounded-lg border text-left font-mono transition-all hover:scale-105 ${
                  hasDet
                    ? 'bg-sonar-800/80 border-sonar-accent/50 hover:border-sonar-accent'
                    : 'bg-sonar-950/60 border-sonar-800 hover:border-sonar-700'
                }`}
              >
                <div className="text-[10px] text-slate-400">Frame #{img.image_index}</div>
                <div className="text-xs font-bold text-white truncate max-w-[90px]" title={img.filename}>
                  {img.filename}
                </div>
                <div className="mt-1 flex items-center justify-between text-[10px]">
                  {hasDet ? (
                    <span className="text-sonar-accent font-semibold flex items-center">
                      <Target className="w-3 h-3 mr-0.5" /> {detCount} det
                    </span>
                  ) : (
                    <span className="text-slate-500">Normal</span>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
