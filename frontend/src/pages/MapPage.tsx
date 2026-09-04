import React, { useEffect, useMemo, useState } from 'react';
import { CircleMarker, MapContainer, Polyline, Popup, TileLayer } from 'react-leaflet';
import { LocateFixed, MapPin, Navigation, RefreshCw } from 'lucide-react';
import { api } from '../services/api';
import type { DetectionItem, ImageRecord, LocationInfo, SurveyResultsResponse, TrackPoint } from '../types/sonar';

type UserLocation = { latitude: number; longitude: number };
type SurveyData = { name: string; images: ImageRecord[]; results: SurveyResultsResponse };
type DetectionPoint = DetectionItem & { imageId: string; filename: string; imageIndex: number; location: LocationInfo };

const formatCoordinate = (value: number) => value.toFixed(6);

const getMapUrl = (latitude: number, longitude: number) =>
  `https://www.google.com/maps/search/?api=1&query=${latitude},${longitude}`;

const locationFromImage = (image: ImageRecord): LocationInfo | null => {
  if (image.location) return image.location;
  if (image.latitude == null || image.longitude == null) return null;
  return {
    latitude: image.latitude,
    longitude: image.longitude,
    source: 'uploaded_survey_metadata',
    match_method: 'legacy_filename',
    location_label: 'Frame location',
  };
};

const coordinate = (location: LocationInfo): [number, number] => [location.latitude, location.longitude];
const trackCoordinate = (point: TrackPoint): [number, number] => [point.latitude, point.longitude];

export const MapPage: React.FC = () => {
  const [surveys, setSurveys] = useState<SurveyData[]>([]);
  const [userLocation, setUserLocation] = useState<UserLocation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [locationError, setLocationError] = useState<string | null>(null);

  const loadLocations = async () => {
    try {
      setLoading(true);
      setError(null);
      const logs = await api.getLogs();
      const loaded = await Promise.all(logs.map(async (log) => ({
        name: log.log_name,
        images: await api.getSurveyImages(log.log_id),
        results: await api.getSurveyResults(log.log_id),
      })));
      setSurveys(loaded);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load survey locations.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadLocations();
  }, []);

  const track = useMemo(() => surveys.flatMap((survey) => survey.results.track), [surveys]);
  const framePoints = useMemo(() => surveys.flatMap((survey) => survey.images.flatMap((image) => {
    const location = locationFromImage(image);
    return location ? [{ ...image, location, surveyName: survey.name }] : [];
  })), [surveys]);
  const detectionPoints = useMemo<DetectionPoint[]>(() => surveys.flatMap((survey) => survey.images.flatMap((image) => {
    const fallback = locationFromImage(image);
    return (image.analysis_result?.detections || []).flatMap((detection) => {
      const location = detection.location || fallback;
      return location ? [{ ...detection, imageId: image.image_id, filename: image.filename, imageIndex: image.image_index, location }] : [];
    });
  })), [surveys]);

  const locateMe = () => {
    setLocationError(null);
    if (!navigator.geolocation) {
      setLocationError('Browser geolocation is not available.');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => setUserLocation({ latitude: coords.latitude, longitude: coords.longitude }),
      ({ message }) => setLocationError(message || 'Location permission was denied.'),
      { enableHighAccuracy: true, timeout: 10000 }
    );
  };

  const hasSurveyLocation = track.length > 0 || framePoints.length > 0 || detectionPoints.length > 0;
  const mapCenter: [number, number] = track.length > 0
    ? trackCoordinate(track[0])
    : framePoints.length > 0
      ? coordinate(framePoints[0].location)
      : userLocation ? [userLocation.latitude, userLocation.longitude] : [0, 0];

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-12">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold font-mono text-white tracking-tight">Survey Geolocation Map</h1>
          <p className="text-slate-300 text-sm mt-1">Survey navigation metadata and frame-level detections.</p>
        </div>
        <div className="flex gap-2">
          <button onClick={locateMe} className="px-3 py-2 bg-sonar-cyan/15 border border-sonar-cyan/40 rounded-lg text-sonar-cyan text-sm flex items-center gap-2">
            <LocateFixed className="w-4 h-4" /> Use my location
          </button>
          <button onClick={() => void loadLocations()} className="p-2 bg-sonar-800 border border-sonar-700 rounded-lg text-slate-300" title="Refresh survey locations">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {error && <div className="p-4 bg-sonar-rose/10 border border-sonar-rose/30 rounded-lg text-sonar-rose text-sm">{error}</div>}
      {locationError && <div className="p-4 bg-sonar-amber/10 border border-sonar-amber/30 rounded-lg text-sonar-amber text-sm">{locationError}</div>}

      {userLocation && (
        <div className="bg-sonar-900/80 border border-sonar-cyan/40 rounded-xl p-4 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3"><Navigation className="w-5 h-5 text-sonar-cyan" /><div><div className="text-xs text-slate-400">Your browser location, separate from survey data</div><div className="font-mono text-white">{formatCoordinate(userLocation.latitude)}, {formatCoordinate(userLocation.longitude)}</div></div></div>
          <a href={getMapUrl(userLocation.latitude, userLocation.longitude)} target="_blank" rel="noreferrer" className="text-sm text-sonar-cyan">Open in Google Maps</a>
        </div>
      )}

      {hasSurveyLocation ? (
        <>
          <div className="bg-sonar-900/80 border border-sonar-700/60 rounded-xl overflow-hidden">
            <MapContainer center={mapCenter} zoom={8} scrollWheelZoom className="h-[520px] w-full">
              <TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
              {surveys.map((survey) => survey.results.track.length > 1 && (
                <Polyline key={survey.name} positions={survey.results.track.map(trackCoordinate)} pathOptions={{ color: '#00bbf9', weight: 3 }} />
              ))}
              {framePoints.map((point) => (
                <CircleMarker key={`frame-${point.image_id}`} center={coordinate(point.location)} radius={5} pathOptions={{ color: '#00bbf9', fillColor: '#00bbf9', fillOpacity: 0.8 }}>
                  <Popup><strong>Survey frame</strong><br />{point.filename}<br />Frame location: {formatCoordinate(point.location.latitude)}, {formatCoordinate(point.location.longitude)}</Popup>
                </CircleMarker>
              ))}
              {detectionPoints.map((point) => {
                const unknown = point.status === 'unknown' || point.class_name === 'unknown_object';
                return (
                  <CircleMarker key={`detection-${point.imageId}-${point.object_id}`} center={coordinate(point.location)} radius={unknown ? 9 : 8} pathOptions={{ color: unknown ? '#ffb703' : '#10b981', fillColor: unknown ? '#ffb703' : '#10b981', fillOpacity: 0.95 }}>
                    <Popup>
                      <strong>{unknown ? 'Potential Unknown Object' : 'Known Shipwreck'}</strong><br />
                      Object ID: {point.object_id}<br />
                      Class: {point.class_name}<br />
                      Status: {point.status}<br />
                      {unknown ? <>Novelty score: {point.novelty_score?.toFixed(3) ?? 'N/A'}<br />Experimental object-discovery result - requires human verification.<br /></> : <>Confidence: {point.confidence == null ? 'N/A' : `${(point.confidence * 100).toFixed(1)}%`}<br /></>}
                      Latitude: {formatCoordinate(point.location.latitude)}<br />
                      Longitude: {formatCoordinate(point.location.longitude)}<br />
                      Frame/Image ID: {point.imageIndex} / {point.imageId}<br />
                      <em>Frame location, not exact object location</em>
                    </Popup>
                  </CircleMarker>
                );
              })}
            </MapContainer>
          </div>

          <div className="grid md:grid-cols-3 gap-4 text-sm">
            <div className="bg-sonar-900/80 border border-sonar-cyan/40 rounded-xl p-4"><div className="text-sonar-cyan font-mono font-bold">Survey track</div><div className="text-slate-300 mt-1">{track.length} real navigation points</div></div>
            <div className="bg-sonar-900/80 border border-sonar-emerald/40 rounded-xl p-4"><div className="text-sonar-emerald font-mono font-bold">Known shipwrecks</div><div className="text-slate-300 mt-1">{detectionPoints.filter((point) => point.status !== 'unknown').length} frame locations</div></div>
            <div className="bg-sonar-900/80 border border-sonar-amber/40 rounded-xl p-4"><div className="text-sonar-amber font-mono font-bold">Potential unknown objects</div><div className="text-slate-300 mt-1">{detectionPoints.filter((point) => point.status === 'unknown').length} frame locations</div></div>
          </div>
        </>
      ) : (
        <div className="bg-sonar-900/80 rounded-xl border border-sonar-700/60 p-10 text-center sonar-grid-pattern">
          <MapPin className="w-10 h-10 text-sonar-amber mx-auto mb-4" />
          <h3 className="text-xl font-bold font-mono text-white">Location data unavailable</h3>
          <p className="text-sm text-slate-400 max-w-lg mx-auto mt-2">{loading ? 'Loading survey navigation metadata...' : 'No valid navigation metadata was found for these frames. Upload the real survey navigation file with matching filenames or frame IDs.'}</p>
        </div>
      )}
    </div>
  );
};
