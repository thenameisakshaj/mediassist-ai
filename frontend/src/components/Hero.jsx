import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight, BookOpen, ShieldCheck } from "lucide-react";

const heroImage =
  "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&w=1800&q=82";

function Counter({ value, suffix = "" }) {
  const [count, setCount] = useState(0);

  useEffect(() => {
    let frame;
    const duration = 1100;
    const startTime = performance.now();

    const tick = (time) => {
      const progress = Math.min((time - startTime) / duration, 1);
      setCount(Math.round(value * progress));
      if (progress < 1) {
        frame = requestAnimationFrame(tick);
      }
    };

    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [value]);

  return (
    <span>
      {count}
      {suffix}
    </span>
  );
}

export default function Hero() {
  return (
    <section
      className="relative isolate flex min-h-[86vh] items-center overflow-hidden bg-slate-950 px-5 py-20 text-white lg:px-8"
      style={{
        backgroundImage: `linear-gradient(90deg, rgba(15, 23, 42, 0.82), rgba(20, 184, 166, 0.46), rgba(248, 250, 252, 0.1)), url(${heroImage})`,
        backgroundPosition: "center",
        backgroundSize: "cover"
      }}
    >
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_35%,rgba(6,182,212,0.28),transparent_28%),linear-gradient(180deg,transparent,rgba(15,23,42,0.32))]" />
      <div className="relative mx-auto w-full max-w-7xl">
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
          className="max-w-3xl"
        >
          <div className="mb-6 inline-flex items-center gap-2 rounded-lg border border-white/30 bg-white/10 px-4 py-2 text-sm font-semibold text-cyan-50 backdrop-blur">
            <ShieldCheck size={17} />
            Book-grounded educational medical assistance
          </div>
          <h1 className="max-w-4xl text-5xl font-black leading-[1.02] text-white md:text-7xl">
            Medical answers grounded in your academic book.
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-cyan-50 md:text-xl">
            MediAssist AI combines a polished medical website with a retrieval-based
            chatbot that indexes a PDF, retrieves relevant context, and generates safe
            OpenAI-powered explanations.
          </p>
          <div className="mt-9 flex flex-col gap-4 md:flex-row">
            <Link className="btn-primary bg-cyan-500 hover:bg-cyan-400" to="/bot">
              Try Medical Bot <ArrowRight size={18} />
            </Link>
            <Link className="btn-secondary border-white/40 bg-white/10 text-white hover:bg-white/20" to="/about">
              <BookOpen size={18} /> See RAG Workflow
            </Link>
          </div>

          <div className="mt-12 grid max-w-2xl grid-cols-3 gap-3 text-white">
            {[
              ["PDF", "knowledge base"],
              ["4", "retrieved chunks"],
              ["24", "demo-ready routes"]
            ].map(([value, label]) => (
              <div key={label} className="rounded-lg border border-white/20 bg-white/10 p-4 backdrop-blur">
                <div className="text-2xl font-black">
                  {Number.isNaN(Number(value)) ? value : <Counter value={Number(value)} suffix={value === "24" ? "+" : ""} />}
                </div>
                <div className="mt-1 text-sm text-cyan-50">{label}</div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
}
