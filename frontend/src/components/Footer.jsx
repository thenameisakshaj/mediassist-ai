import { Link } from "react-router-dom";
import { Stethoscope } from "lucide-react";

export default function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white">
      <div className="mx-auto grid max-w-7xl gap-8 px-5 py-10 md:grid-cols-[1.4fr_1fr_1fr] lg:px-8">
        <div>
          <div className="flex items-center gap-3">
            <span className="grid h-10 w-10 place-items-center rounded-lg bg-cyan-600 text-white">
              <Stethoscope size={22} />
            </span>
            <span className="text-lg font-black text-slate-950">MediAssist AI</span>
          </div>
          <p className="mt-4 max-w-md text-sm leading-6 text-slate-600">
            An academic full-stack RAG project for educational medical-book question answering.
          </p>
        </div>
        <div>
          <h3 className="text-sm font-black text-slate-950">Project</h3>
          <div className="mt-4 grid gap-2 text-sm text-slate-600">
            <Link to="/about">About</Link>
            <Link to="/features">Services</Link>
            <Link to="/bot">AI Medical Bot</Link>
          </div>
        </div>
        <div>
          <h3 className="text-sm font-black text-slate-950">Safety</h3>
          <p className="mt-4 text-sm leading-6 text-slate-600">
            Educational use only. Not a replacement for professional medical advice.
          </p>
        </div>
      </div>
    </footer>
  );
}
