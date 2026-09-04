import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { DashboardPage } from './pages/Dashboard';
import { UploadPage } from './pages/UploadPage';
import { ProcessingPage } from './pages/ProcessingPage';
import { SurveyAnalysisPage } from './pages/SurveyAnalysisPage';
import { ImageAnalysisPage } from './pages/ImageAnalysisPage';
import { MapPage } from './pages/MapPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-sonar-950 text-slate-100 flex flex-col font-sans">
        <Navbar />

        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/logs" element={<DashboardPage />} />
            <Route path="/upload" element={<UploadPage />} />
            <Route path="/processing/:logId" element={<ProcessingPage />} />
            <Route path="/survey/:logId" element={<SurveyAnalysisPage />} />
            <Route path="/image/:logId/:imageId" element={<ImageAnalysisPage />} />
            <Route path="/map" element={<MapPage />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
};

export default App;
