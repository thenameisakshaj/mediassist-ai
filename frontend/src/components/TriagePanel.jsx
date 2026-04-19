import { useEffect, useMemo, useState } from "react";
import { Activity, AlertTriangle, Info, MapPin, Navigation } from "lucide-react";

const NEED_METER_META = {
  0: {
    label: "Informational",
    tone: "informational",
    icon: Info
  },
  1: {
    label: "Monitor",
    tone: "monitor",
    icon: Activity
  },
  2: {
    label: "Consult doctor",
    tone: "consult",
    icon: Activity
  },
  3: {
    label: "Urgent",
    tone: "urgent",
    icon: AlertTriangle
  }
};

function buildMapLinks(coords) {
  if (
    !Number.isFinite(coords?.latitude) ||
    !Number.isFinite(coords?.longitude)
  ) {
    return [];
  }

  const lat = Number(coords.latitude).toFixed(6);
  const lng = Number(coords.longitude).toFixed(6);
  const center = `${lat},${lng}`;

  return [
    {
      id: "google-doctors",
      label: "Google Maps: Nearby Doctors",
      url: `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
        `doctors near ${center}`
      )}`
    },
    {
      id: "google-clinics",
      label: "Google Maps: Nearby Clinics",
      url: `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
        `clinics near ${center}`
      )}`
    },
    {
      id: "apple-doctors",
      label: "Apple Maps: Nearby Doctors",
      url: `https://maps.apple.com/?ll=${encodeURIComponent(center)}&q=${encodeURIComponent(
        "Doctors"
      )}`
    },
    {
      id: "apple-clinics",
      label: "Apple Maps: Nearby Clinics",
      url: `https://maps.apple.com/?ll=${encodeURIComponent(center)}&q=${encodeURIComponent(
        "Clinics"
      )}`
    }
  ];
}

function shouldRenderTriage(triage) {
  return triage && typeof triage.needLevel === "number" && triage.needLabel;
}

export default function TriagePanel({ triage, sharedLocation, onLocationResolved }) {
  const [locationState, setLocationState] = useState(() =>
    sharedLocation ? "granted" : "idle"
  );
  const [locationError, setLocationError] = useState("");
  const [coords, setCoords] = useState(sharedLocation || null);

  useEffect(() => {
    if (!sharedLocation) return;
    setCoords(sharedLocation);
    setLocationState("granted");
    setLocationError("");
  }, [sharedLocation]);

  const mapLinks = useMemo(() => buildMapLinks(coords), [coords]);

  if (!shouldRenderTriage(triage)) {
    return null;
  }

  const needMeta = NEED_METER_META[triage.needLevel] || NEED_METER_META[0];
  const Icon = needMeta.icon;

  async function handleEnableLocation() {
    if (!navigator.geolocation) {
      setLocationState("error");
      setLocationError("Location is not available in this browser.");
      return;
    }

    setLocationState("loading");
    setLocationError("");

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const nextCoords = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude
        };
        setCoords(nextCoords);
        setLocationState("granted");
        onLocationResolved?.(nextCoords);
      },
      (error) => {
        setLocationState("denied");
        if (error.code === error.PERMISSION_DENIED) {
          setLocationError(
            "Location permission was denied. You can still use the chat without nearby care links."
          );
          return;
        }

        setLocationError(
          "I could not access your location right now. Please try again if you want nearby care links."
        );
      },
      {
        enableHighAccuracy: false,
        timeout: 10000,
        maximumAge: 300000
      }
    );
  }

  return (
    <div className={`triage-panel triage-panel-${needMeta.tone}`}>
      <div className="need-meter">
        <div className="need-meter-header">
          <div className="need-meter-title">
            <span className={`need-badge need-badge-${needMeta.tone}`}>
              <Icon size={14} />
              {triage.needLabel}
            </span>
            <p className="need-meter-copy">Medical need meter</p>
          </div>
          <div className="need-scale" aria-label={`Need level ${triage.needLevel}`}>
            {[0, 1, 2, 3].map((level) => (
              <span
                key={level}
                className={`need-scale-segment ${
                  level <= triage.needLevel
                    ? `need-scale-segment-active need-scale-segment-${needMeta.tone}`
                    : ""
                }`}
              />
            ))}
          </div>
        </div>
      </div>

      {triage.careGuidance && (
        <div className={`care-guidance care-guidance-${needMeta.tone}`}>
          <p>{triage.careGuidance}</p>
        </div>
      )}

      {triage.suggestNearbyCare && (
        <div className="nearby-care-panel">
          <div className="nearby-care-header">
            <p className="nearby-care-title">Nearby care</p>
            <p className="nearby-care-copy">
              Use your location only if you want map search links for nearby doctors or
              clinics.
            </p>
          </div>

          {!coords && (
            <button
              type="button"
              className="btn-secondary nearby-care-button"
              onClick={handleEnableLocation}
              disabled={locationState === "loading"}
            >
              <MapPin size={16} />
              {locationState === "loading"
                ? "Checking location..."
                : "Enable location for nearby care"}
            </button>
          )}

          {locationError && <p className="location-status location-status-error">{locationError}</p>}

          {coords && mapLinks.length > 0 && (
            <div className="nearby-care-links">
              <p className="location-status location-status-success">
                <Navigation size={14} />
                Location ready. Open a map search near your coordinates.
              </p>
              <div className="nearby-link-grid">
                {mapLinks.map((link) => (
                  <a
                    key={link.id}
                    href={link.url}
                    target="_blank"
                    rel="noreferrer"
                    className="nearby-link"
                  >
                    {link.label}
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
