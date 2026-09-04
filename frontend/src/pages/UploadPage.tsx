import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FolderArchive, FileImage, FileSpreadsheet, Trash2, Play, AlertCircle, CheckCircle2, Layers } from 'lucide-react';
import { api } from '../services/api';
import type { SurveyLogDetail } from '../types/sonar';

export const UploadPage: React.FC = () => {
  const [logName, setLogName] = useState<string>('');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [selectedZip, setSelectedZip] = useState<File | null>(null);
  const [metadataFile, setMetadataFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadedLog, setUploadedLog] = useState<SurveyLogDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const zipInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const filesArr = Array.from(e.target.files).filter((f) => {
        const ext = f.name.toLowerCase();
        return ext.endsWith('.png') || ext.endsWith('.jpg') || ext.endsWith('.jpeg') || ext.endsWith('.tif') || ext.endsWith('.tiff');
      });

      filesArr.sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: 'base' }));

      setSelectedFiles((prev) => [...prev, ...filesArr]);
      setSelectedZip(null);
      setError(null);
    }
  };

  const handleZipSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const zip = e.target.files[0];
      if (zip.name.toLowerCase().endsWith('.zip')) {
        setSelectedZip(zip);
        setSelectedFiles([]);
        setError(null);
      } else {
        setError('Please select a valid .zip archive.');
      }
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files) {
      const filesArr = Array.from(e.dataTransfer.files);
      const zip = filesArr.find((f) => f.name.toLowerCase().endsWith('.zip'));

      if (zip) {
        setSelectedZip(zip);
        setSelectedFiles([]);
      } else {
        const validImgs = filesArr.filter((f) => {
          const ext = f.name.toLowerCase();
          return ext.endsWith('.png') || ext.endsWith('.jpg') || ext.endsWith('.jpeg') || ext.endsWith('.tif') || ext.endsWith('.tiff');
        });
        validImgs.sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true, sensitivity: 'base' }));
        setSelectedFiles((prev) => [...prev, ...validImgs]);
        setSelectedZip(null);
      }
      setError(null);
    }
  };

  const removeFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (!selectedZip && selectedFiles.length === 0) {
      setError('Please select SSS image files or a ZIP archive to upload.');
      return;
    }

    try {
      setUploading(true);
      setError(null);
      const nameToUse = logName.trim() || (selectedZip ? selectedZip.name.replace('.zip', '') : 'Survey_Log_' + new Date().toISOString().slice(0, 10));

      const log = await api.uploadSurveyLog(
        selectedZip ? undefined : selectedFiles,
        selectedZip || undefined,
        nameToUse,
        metadataFile || undefined
      );

      setUploadedLog(log);
    } catch (err: any) {
      setError(err.message || 'Upload failed.');
    } finally {
      setUploading(false);
    }
  };

  const handleStartAnalysis = async () => {
    if (!uploadedLog) return;
    try {
      await api.startAnalysis(uploadedLog.log_id);
      navigate(`/processing/${uploadedLog.log_id}`);
    } catch (err: any) {
      setError(`Failed to trigger analysis: ${err.message}`);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      {/* Title */}
      <div>
        <h1 className="text-3xl font-bold font-mono text-white tracking-tight">
          Upload SSS Image Log
        </h1>
        <p className="text-slate-300 text-sm mt-1">
          Upload a complete Side-Scan Sonar survey log for AI analysis. Multiple sonar frames will be processed sequentially.
        </p>
      </div>

      {error && (
        <div className="p-4 bg-sonar-rose/10 border border-sonar-rose/30 text-sonar-rose rounded-xl flex items-center space-x-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span className="text-sm font-medium">{error}</span>
        </div>
      )}

      {/* Main Upload Box */}
      {!uploadedLog ? (
        <div className="space-y-6">
          {/* Survey Name Input */}
          <div className="bg-sonar-900/80 p-5 rounded-xl border border-sonar-700/60 shadow-xl">
            <label className="block text-xs font-mono font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Survey Log Identifier / Name
            </label>
            <input
              type="text"
              value={logName}
              onChange={(e) => setLogName(e.target.value)}
              placeholder="e.g. Survey_001_North_Track"
              className="w-full px-4 py-2.5 bg-sonar-950 text-white rounded-lg border border-sonar-700 focus:outline-none focus:border-sonar-accent font-mono text-sm"
            />
          </div>

          <div className="bg-sonar-900/80 p-5 rounded-xl border border-sonar-700/60 shadow-xl">
            <label className="block text-xs font-mono font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Optional GPS Metadata CSV
            </label>
            <p className="text-xs text-slate-400 mb-3">CSV or JSON navigation metadata. Include filename or frame_id, latitude, and longitude. Matching is exact.</p>
            <div className="flex items-center gap-3">
              <input
                type="file"
                accept=".csv,.json,text/csv,application/json"
                onChange={(event) => setMetadataFile(event.target.files?.[0] || null)}
                className="block w-full text-xs text-slate-300 file:mr-3 file:rounded file:border-0 file:bg-sonar-800 file:px-3 file:py-2 file:text-xs file:text-white"
              />
              {metadataFile && <FileSpreadsheet className="w-5 h-5 text-sonar-cyan flex-shrink-0" />}
            </div>
          </div>

          {/* Drag and Drop Zone */}
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            className="border-2 border-dashed border-sonar-700 hover:border-sonar-accent/60 bg-sonar-900/40 rounded-2xl p-8 text-center transition-colors cursor-pointer"
          >
            <div className="w-14 h-14 bg-sonar-800 rounded-full flex items-center justify-center mx-auto mb-4 text-sonar-accent border border-sonar-700">
              <Upload className="w-7 h-7" />
            </div>

            <h3 className="text-lg font-bold text-white font-mono mb-1">
              Drop your SSS image log here
            </h3>
            <p className="text-slate-400 text-sm max-w-md mx-auto mb-6">
              Upload multiple Side-Scan Sonar survey images (PNG, JPG, TIF) or a ZIP archive containing your survey log.
            </p>

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center justify-center gap-3">
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="px-4 py-2 bg-sonar-800 hover:bg-sonar-700 text-white rounded-lg border border-sonar-700 text-sm font-medium flex items-center space-x-2 transition-colors"
              >
                <FileImage className="w-4 h-4 text-sonar-accent" />
                <span>Select Images</span>
              </button>

              <button
                type="button"
                onClick={() => zipInputRef.current?.click()}
                className="px-4 py-2 bg-sonar-800 hover:bg-sonar-700 text-white rounded-lg border border-sonar-700 text-sm font-medium flex items-center space-x-2 transition-colors"
              >
                <FolderArchive className="w-4 h-4 text-sonar-amber" />
                <span>Upload ZIP</span>
              </button>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".png,.jpg,.jpeg,.tif,.tiff"
              onChange={handleFileSelect}
              className="hidden"
            />
            <input
              ref={zipInputRef}
              type="file"
              accept=".zip"
              onChange={handleZipSelect}
              className="hidden"
            />
          </div>

          {/* Selected File Preview */}
          {(selectedFiles.length > 0 || selectedZip) && (
            <div className="bg-sonar-900/80 rounded-xl border border-sonar-700/60 p-6 shadow-xl space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-sonar-700">
                <h3 className="text-sm font-bold font-mono text-white flex items-center space-x-2">
                  <Layers className="w-4 h-4 text-sonar-accent" />
                  <span>Survey Log Preview</span>
                </h3>
                <span className="text-xs font-mono px-2.5 py-1 bg-sonar-800 rounded text-sonar-accent border border-sonar-700">
                  {selectedZip ? '1 ZIP Archive' : `${selectedFiles.length} images selected`}
                </span>
              </div>

              {selectedZip ? (
                <div className="p-4 bg-sonar-950/70 rounded-lg border border-sonar-800 flex items-center justify-between font-mono text-sm">
                  <div className="flex items-center space-x-3 text-sonar-amber">
                    <FolderArchive className="w-6 h-6" />
                    <div>
                      <div className="font-semibold text-white">{selectedZip.name}</div>
                      <div className="text-xs text-slate-400">
                        {(selectedZip.size / (1024 * 1024)).toFixed(2)} MB
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedZip(null)}
                    className="p-1 text-slate-400 hover:text-sonar-rose transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <div className="max-h-[300px] overflow-y-auto space-y-2 pr-1 font-mono text-xs">
                  {selectedFiles.map((file, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 bg-sonar-950/60 rounded border border-sonar-800 flex items-center justify-between hover:bg-sonar-800/40"
                    >
                      <div className="flex items-center space-x-3 truncate">
                        <span className="text-slate-500 w-8">{(idx + 1).toString().padStart(2, '0')}</span>
                        <span className="text-slate-200 font-semibold truncate">{file.name}</span>
                      </div>
                      <div className="flex items-center space-x-4 flex-shrink-0 text-slate-400">
                        <span>{(file.size / 1024).toFixed(1)} KB</span>
                        <button
                          onClick={() => removeFile(idx)}
                          className="p-1 hover:text-sonar-rose transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Start Upload Button */}
              <div className="pt-2 flex justify-end">
                <button
                  onClick={handleUpload}
                  disabled={uploading}
                  className="px-6 py-3 bg-sonar-accent hover:bg-sonar-accent/90 text-sonar-950 font-bold rounded-xl shadow-lg transition-colors flex items-center space-x-2 text-sm disabled:opacity-50"
                >
                  <Upload className="w-4 h-4" />
                  <span>{uploading ? 'Creating Survey Log...' : 'Start Upload'}</span>
                </button>
              </div>
            </div>
          )}
        </div>
      ) : (
        /* Upload Completed View */
        <div className="bg-sonar-900/80 rounded-xl border border-sonar-emerald/40 p-8 shadow-2xl space-y-6 text-center">
          <div className="w-16 h-16 bg-sonar-emerald/20 border border-sonar-emerald text-sonar-emerald rounded-full flex items-center justify-center mx-auto">
            <CheckCircle2 className="w-8 h-8" />
          </div>

          <div>
            <h2 className="text-2xl font-bold font-mono text-white">
              Survey Log Created Successfully
            </h2>
            <p className="text-slate-300 text-sm mt-1">
              Log Identifier: <strong className="text-sonar-accent font-mono">{uploadedLog.log_name}</strong> ({uploadedLog.total_images} images ready)
            </p>
          </div>

          <div className="flex justify-center space-x-4 pt-4">
            <button
              onClick={() => {
                setUploadedLog(null);
                setSelectedFiles([]);
                setSelectedZip(null);
              }}
              className="px-5 py-2.5 bg-sonar-800 hover:bg-sonar-700 text-slate-300 font-semibold rounded-xl border border-sonar-700 text-sm"
            >
              Upload Another Log
            </button>

            <button
              onClick={handleStartAnalysis}
              className="px-6 py-2.5 bg-sonar-accent hover:bg-sonar-accent/90 text-sonar-950 font-bold rounded-xl shadow-lg shadow-sonar-accent/20 text-sm flex items-center space-x-2"
            >
              <Play className="w-4 h-4 fill-current" />
              <span>Start AI Analysis</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
