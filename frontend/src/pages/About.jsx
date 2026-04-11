import { BookOpenCheck, HeartPulse, Microscope, ShieldCheck } from "lucide-react";

import DisclaimerBanner from "../components/DisclaimerBanner.jsx";
import Footer from "../components/Footer.jsx";

const aboutImage =
  "https://images.unsplash.com/photo-1559757148-5c350d0d3c56?auto=format&fit=crop&w=1400&q=82";

export default function About() {
  return (
    <>
      <section className="page-hero bg-slate-50">
        <div className="section-inner grid gap-10 lg:grid-cols-[1fr_0.9fr] lg:items-center">
          <div>
            <span className="eyebrow">About MediAssist AI</span>
            <h1>Academic RAG system for educational medical-book Q&A.</h1>
            <p>
              MediAssist AI turns a medical PDF into a searchable knowledge base and
              uses OpenAI only after retrieving relevant book context.
            </p>
          </div>
          <img className="h-[380px] w-full rounded-lg object-cover shadow-lg" src={aboutImage} alt="Medical team reviewing digital health information" />
        </div>
      </section>

      <section className="section bg-white">
        <div className="section-inner grid gap-5 md:grid-cols-2">
          <article className="card">
            <HeartPulse className="mb-4 text-cyan-700" size={30} />
            <h2>Mission</h2>
            <p>
              Make medical-book learning more interactive, explainable, and demo-ready
              for students while keeping safety boundaries visible.
            </p>
          </article>
          <article className="card">
            <Microscope className="mb-4 text-teal-700" size={30} />
            <h2>Vision</h2>
            <p>
              A portfolio-quality foundation that can later support richer document
              management, citations, evaluations, and clinical safety review.
            </p>
          </article>
        </div>
      </section>

      <section className="section bg-slate-50">
        <div className="section-inner">
          <div className="section-heading">
            <span className="eyebrow">AI + medical book retrieval</span>
            <h2>The chatbot uses retrieval before generation.</h2>
            <p>
              It loads pages from a PDF, splits them into overlapping chunks, creates
              HuggingFace embeddings, stores vectors in Chroma, retrieves relevant
              chunks, and sends them to OpenAI with a medical safety prompt.
            </p>
          </div>
          <div className="mt-10 grid gap-5 md:grid-cols-3">
            {[
              [BookOpenCheck, "Source-first", "Answers are grounded in indexed book chunks rather than open-ended memory."],
              [ShieldCheck, "Safety-aware", "The prompt restricts diagnosis, prescriptions, and fabricated medical claims."],
              [Microscope, "Explainable", "Returned snippets show where the answer context came from."]
            ].map(([Icon, title, text]) => (
              <article key={title} className="card">
                <Icon className="mb-4 text-cyan-700" size={28} />
                <h3>{title}</h3>
                <p>{text}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="section bg-white">
        <div className="section-inner grid gap-8 lg:grid-cols-[0.9fr_1.1fr]">
          <div>
            <span className="eyebrow">Safety and educational disclaimer</span>
            <h2>Designed for learning, not clinical decisions.</h2>
          </div>
          <DisclaimerBanner />
        </div>
      </section>

      <section className="section bg-cyan-700 text-white">
        <div className="section-inner">
          <span className="text-sm font-black uppercase text-cyan-100">Team / project info</span>
          <h2 className="mt-3 text-white">Full-stack academic submission.</h2>
          <p className="mt-4 max-w-3xl text-cyan-50">
            Built with React, Flask, Chroma, local embeddings, and OpenAI for a viva,
            academic demo, and recruiter-facing portfolio walkthrough.
          </p>
        </div>
      </section>

      <Footer />
    </>
  );
}
