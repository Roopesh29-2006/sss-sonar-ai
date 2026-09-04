import React from 'react';
import { Activity, Sparkles, Cpu } from 'lucide-react';
import type { SSLFeatures } from '../types/sonar';

interface SSLFeatureViewerProps {
  sslFeatures?: SSLFeatures | null;
}

export const SSLFeatureViewer: React.FC<SSLFeatureViewerProps> = ({ sslFeatures }) => {
  const featureVector = sslFeatures?.feature_vector || Array.from({ length: 64 }, () => Math.random() * 2 - 1);
  const similarity = sslFeatures?.similarity_score ?? 0.88;
  const novelty = sslFeatures?.novelty_score ?? 0.14;
  const isMock = sslFeatures?.is_mock ?? true;

  // Display top 48 features as a heat-bar matrix
  const displaySlice = featureVector.slice(0, 48);

  return (
    <div className="bg-sonar-900/80 rounded-xl border border-sonar-700/60 p-4 shadow-xl">
      <div className="flex items-center justify-between pb-3 border-b border-sonar-700/60 mb-3">
        <div className="flex items-center space-x-2">
          <Cpu className="w-4 h-4 text-sonar-cyan" />
          <h3 className="text-sm font-semibold text-white">
            SSL Feature Representation
          </h3>
        </div>
        {isMock && (
          <span className="text-[10px] font-mono uppercase bg-sonar-amber/20 text-sonar-amber px-2 py-0.5 rounded border border-sonar-amber/30">
            DEMO SSL FEATURES
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
        {/* Similarity score */}
        <div className="bg-sonar-950/70 p-3 rounded-lg border border-sonar-800 flex items-center justify-between">
          <div>
            <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
              Cosine Similarity
            </span>
            <span className="text-lg font-bold font-mono text-sonar-cyan">
              {(similarity * 100).toFixed(1)}%
            </span>
          </div>
          <Sparkles className="w-5 h-5 text-sonar-cyan opacity-80" />
        </div>

        {/* Novelty score */}
        <div className="bg-sonar-950/70 p-3 rounded-lg border border-sonar-800 flex items-center justify-between">
          <div>
            <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
              Novelty / Anomaly Score
            </span>
            <span className={`text-lg font-bold font-mono ${novelty > 0.5 ? 'text-sonar-amber' : 'text-sonar-emerald'}`}>
              {(novelty * 100).toFixed(1)}%
            </span>
          </div>
          <Activity className="w-5 h-5 text-sonar-amber opacity-80" />
        </div>
      </div>

      {/* Embedding Vector Visual Heatmap */}
      <div>
        <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-1.5">
          <span>SSL Encoder Embedding Vector (128-D)</span>
          <span>Dim [0..47]</span>
        </div>

        <div className="grid grid-cols-12 gap-1 p-2 bg-sonar-950/90 rounded border border-sonar-800">
          {displaySlice.map((val, i) => {
            const intensity = Math.min(Math.max((val + 1) / 2, 0), 1);
            const colorClass =
              val > 0.3
                ? `rgba(0, 245, 212, ${0.3 + intensity * 0.7})`
                : val < -0.3
                ? `rgba(244, 63, 94, ${0.3 + intensity * 0.7})`
                : `rgba(0, 187, 249, ${0.2 + intensity * 0.5})`;

            return (
              <div
                key={i}
                className="h-5 rounded-sm transition-all hover:scale-110"
                style={{ backgroundColor: colorClass }}
                title={`Dim ${i}: ${val.toFixed(4)}`}
              />
            );
          })}
        </div>

        <div className="flex justify-between items-center text-[10px] text-slate-500 font-mono mt-2">
          <span>-1.0 (Low similarity)</span>
          <span className="italic">Modular interface ready for PyTorch SSL Encoder .pth</span>
          <span>+1.0 (High activation)</span>
        </div>
      </div>
    </div>
  );
};
