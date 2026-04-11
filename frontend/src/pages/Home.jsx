import { Link } from "react-router-dom";
import { ArrowRight, CheckCircle2, Database, LockKeyhole, Network } from "lucide-react";

import ChatWidget from "../components/ChatWidget.jsx";
import FeatureCards from "../components/FeatureCards.jsx";
import Footer from "../components/Footer.jsx";
import Hero from "../components/Hero.jsx";
import HowItWorks from "../components/HowItWorks.jsx";

const badges = ["OpenAI Responses API", "Chroma vector store", "Local embeddings", "PDF retrieval", "Safety prompt"];

export default function Home() {
  return (
    <>
      <Hero />

      <section className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-center gap-3 px-5 py-6 lg:px-8">
          {badges.map((badge) => (
            <span key={badge} className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-bold text-slate-700">
              {badge}
            </span>
          ))}
        </div>
      </section>

      <FeatureCards />
      <HowItWorks />

      <section className="section bg-white" id="assistant-preview">
        <div className="section-inner grid gap-10 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
          <div>
            <span className="eyebrow">AI assistant preview</span>
            <h2>Ask, retrieve, generate, and cite the context.</h2>
            <p className="mt-5 text-lg leading-8 text-slate-600">
              The chat panel is connected to the Flask API. When the vector index is built,
              each answer returns source snippets from the book so the demo feels explainable.
            </p>
            <div className="mt-8 grid gap-4">
              {[
                [Database, "Persistent Chroma DB keeps indexed chunks ready for demos."],
                [Network, "Retriever sends top matching chunks into the OpenAI prompt."],
                [LockKeyhole, "Secrets stay in .env files and never ship in frontend code."]
              ].map(([Icon, text]) => (
                <div key={text} className="flex gap-3 text-slate-700">
                  <Icon className="mt-1 text-cyan-700" size={20} />
                  <span>{text}</span>
                </div>
              ))}
            </div>
          </div>
          <ChatWidget compact />
        </div>
      </section>

      <section className="section bg-slate-50">
        <div className="section-inner">
          <div className="section-heading">
            <span className="eyebrow">Why choose MediAssist AI</span>
            <h2>Built for a clean demo and a strong viva explanation.</h2>
            <p>
              Every visible feature maps to a backend concept you can explain: routing,
              retrieval, embeddings, vector search, prompt safety, and source display.
            </p>
          </div>
          <div className="mt-10 grid gap-5 md:grid-cols-3">
            {["Grounded book lookup", "Modern medical-tech UI", "Clear ethical boundaries"].map((item) => (
              <article key={item} className="card">
                <CheckCircle2 className="mb-4 text-teal-700" size={28} />
                <h3>{item}</h3>
                <p>Focused implementation choices keep the product impressive without hiding the architecture.</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="section bg-white">
        <div className="section-inner">
          <div className="section-heading">
            <span className="eyebrow">Trust cards</span>
            <h2>Designed for evaluators, students, and portfolio reviewers.</h2>
          </div>
          <div className="mt-10 grid gap-5 md:grid-cols-3">
            {[
              ["Project evaluator", "The endpoints are named clearly and return JSON responses that are easy to inspect."],
              ["Viva examiner", "The RAG pipeline is split into small services for a straightforward architecture walkthrough."],
              ["Recruiter", "The frontend feels like a real health-tech product rather than a static template."]
            ].map(([title, text]) => (
              <article key={title} className="card">
                <h3>{title}</h3>
                <p>{text}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="section bg-cyan-700 text-white">
        <div className="section-inner flex flex-col items-start justify-between gap-8 md:flex-row md:items-center">
          <div>
            <span className="text-sm font-black uppercase text-cyan-100">CTA</span>
            <h2 className="mt-3 max-w-2xl text-white">Ready to demo the AI medical assistant?</h2>
            <p className="mt-4 max-w-2xl text-cyan-50">
              Add your medical PDF, rebuild the index, and ask questions from the bot page.
            </p>
          </div>
          <Link className="btn-secondary border-white bg-white text-cyan-800 hover:bg-cyan-50" to="/bot">
            Open Bot <ArrowRight size={18} />
          </Link>
        </div>
      </section>

      <Footer />
    </>
  );
}
