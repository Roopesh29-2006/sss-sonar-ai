import type {
  HealthCheckResponse,
  SurveyLogSummary,
  SurveyLogDetail,
  ImageRecord,
  AnalysisStatusResponse,
  SurveyResultsResponse,
  DetectionItem
} from '../types/sonar';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorDetail = 'API Request Failed';
    try {
      const err = await response.json();
      errorDetail = err.detail || errorDetail;
    } catch {
      errorDetail = await response.text();
    }
    throw new Error(errorDetail);
  }
  return response.json();
}

export const api = {
  getHealth: async (): Promise<HealthCheckResponse> => {
    const res = await fetch(`${API_BASE_URL}/health`);
    return handleResponse<HealthCheckResponse>(res);
  },

  getLogs: async (): Promise<SurveyLogSummary[]> => {
    const res = await fetch(`${API_BASE_URL}/logs`);
    return handleResponse<SurveyLogSummary[]>(res);
  },

  getLogDetail: async (logId: string): Promise<SurveyLogDetail> => {
    const res = await fetch(`${API_BASE_URL}/logs/${logId}`);
    return handleResponse<SurveyLogDetail>(res);
  },

  uploadSurveyLog: async (
    files?: File[],
    zipFile?: File,
    logName?: string,
    metadataFile?: File
  ): Promise<SurveyLogDetail> => {
    const formData = new FormData();
    if (logName) {
      formData.append('log_name', logName);
    }
    if (metadataFile) {
      formData.append('metadata_file', metadataFile);
    }
    if (zipFile) {
      formData.append('zip_file', zipFile);
    } else if (files && files.length > 0) {
      files.forEach((file) => {
        formData.append('files', file);
      });
    } else {
      throw new Error('No files or ZIP archive selected.');
    }

    const res = await fetch(`${API_BASE_URL}/logs/upload`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<SurveyLogDetail>(res);
  },

  startAnalysis: async (logId: string): Promise<{ message: string; log_id: string; status: string }> => {
    const res = await fetch(`${API_BASE_URL}/logs/${logId}/analyze`, {
      method: 'POST',
    });
    return handleResponse<{ message: string; log_id: string; status: string }>(res);
  },

  getAnalysisStatus: async (logId: string): Promise<AnalysisStatusResponse> => {
    const res = await fetch(`${API_BASE_URL}/logs/${logId}/status`);
    return handleResponse<AnalysisStatusResponse>(res);
  },

  getSurveyResults: async (logId: string): Promise<SurveyResultsResponse> => {
    const res = await fetch(`${API_BASE_URL}/logs/${logId}/results`);
    return handleResponse<SurveyResultsResponse>(res);
  },

  getSurveyImages: async (logId: string): Promise<ImageRecord[]> => {
    const res = await fetch(`${API_BASE_URL}/logs/${logId}/images`);
    return handleResponse<ImageRecord[]>(res);
  },

  getImageDetail: async (logId: string, imageId: string): Promise<ImageRecord> => {
    const res = await fetch(`${API_BASE_URL}/logs/${logId}/images/${imageId}`);
    return handleResponse<ImageRecord>(res);
  },

  getSurveyDetections: async (logId: string): Promise<DetectionItem[]> => {
    const res = await fetch(`${API_BASE_URL}/logs/${logId}/detections`);
    return handleResponse<DetectionItem[]>(res);
  },

  getAssetUrl: (relativeOrPath: string): string => {
    if (!relativeOrPath) return '';
    if (relativeOrPath.startsWith('http')) return relativeOrPath;
    return `http://127.0.0.1:8000${relativeOrPath}`;
  }
};
