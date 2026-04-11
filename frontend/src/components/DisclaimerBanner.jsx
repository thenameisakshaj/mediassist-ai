import { ShieldAlert } from "lucide-react";

export default function DisclaimerBanner({ compact = false }) {
  return (
    <div className={`disclaimer ${compact ? "p-4" : "p-5"}`}>
      <ShieldAlert className="mt-0.5 shrink-0 text-cyan-700" size={22} />
      <p>
        Educational use only. MediAssist AI does not provide diagnosis, prescriptions,
        or emergency care. For symptoms, treatment decisions, or urgent concerns,
        consult a licensed healthcare professional immediately.
      </p>
    </div>
  );
}
