import React from 'react';
import { Database, Image, Target, AlertTriangle, CheckCircle2 } from 'lucide-react';
import type { SurveyLogSummary } from '../types/sonar';

interface SummaryCardsProps {
  logs: SurveyLogSummary[];
}

export const SummaryCards: React.FC<SummaryCardsProps> = ({ logs }) => {
  const totalLogs = logs.length;
  const totalImagesProcessed = logs.reduce((acc, l) => acc + (l.processed_images || 0), 0);
  const totalKnown = logs.reduce((acc, l) => acc + (l.known_count || 0), 0);
  const totalUnknown = logs.reduce((acc, l) => acc + (l.unknown_count || 0), 0);
  const totalReviewImages = logs.reduce((acc, l) => acc + (l.images_with_unknown_objects || 0), 0);
  const totalHighConf = logs.reduce((acc, l) => acc + (l.high_confidence_count || 0), 0);

  const cards = [
    {
      title: 'Total Survey Logs',
      value: totalLogs,
      icon: Database,
      color: 'text-sonar-cyan',
      bg: 'bg-sonar-cyan/10 border-sonar-cyan/30',
      description: 'Active survey image logs'
    },
    {
      title: 'Images Processed',
      value: totalImagesProcessed,
      icon: Image,
      color: 'text-sonar-accent',
      bg: 'bg-sonar-accent/10 border-sonar-accent/30',
      description: 'Sequential sonar frames'
    },
    {
      title: 'Known Shipwrecks',
      value: totalKnown,
      icon: Target,
      color: 'text-sonar-cyan',
      bg: 'bg-sonar-cyan/10 border-sonar-cyan/30',
      description: 'Known model detections'
    },
    {
      title: 'Potential Unknown Objects',
      value: totalUnknown,
      icon: AlertTriangle,
      color: 'text-sonar-amber',
      bg: 'bg-sonar-amber/10 border-sonar-amber/30',
      description: 'Anomalies & novel patterns'
    },
    {
      title: 'Images Requiring Human Review',
      value: totalReviewImages,
      icon: AlertTriangle,
      color: 'text-sonar-amber',
      bg: 'bg-sonar-amber/10 border-sonar-amber/30',
      description: 'Frames containing potential unknowns'
    },
    {
      title: 'High Confidence',
      value: totalHighConf,
      icon: CheckCircle2,
      color: 'text-sonar-emerald',
      bg: 'bg-sonar-emerald/10 border-sonar-emerald/30',
      description: 'Confidence score >= 85%'
    }
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className={`p-4 rounded-xl border ${card.bg} backdrop-blur bg-sonar-900/60 shadow-lg flex flex-col justify-between`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                {card.title}
              </span>
              <Icon className={`w-5 h-5 ${card.color}`} />
            </div>
            <div className="mt-3">
              <div className="text-3xl font-bold font-mono text-white tracking-tight">
                {card.value}
              </div>
              <p className="text-[11px] text-slate-400 mt-1">{card.description}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
};
