import { Bot, BookOpen, BrainCircuit, Clock3, Lightbulb, ShieldCheck } from "lucide-react";

import Footer from "../components/Footer.jsx";

const services = [
  ["Symptom Information Assistant", "Explains symptom-related topics only when the indexed book context supports the answer.", Bot],
  ["Medical Topic Explainer", "Turns textbook-style language into concise educational explanations.", Lightbulb],
  ["Book-Based Knowledge Lookup", "Retrieves relevant PDF chunks and includes source snippets in the chat response.", BookOpen],
  ["Fast Chatbot Q&A", "Centralized API calls and a responsive React chat panel keep the demo smooth.", Clock3],
  ["Safe Educational Responses", "Avoids diagnosis, prescriptions, and unsupported claims while showing clear disclaimers.", ShieldCheck],
  ["Future Possibilities", "Can grow into multi-PDF indexing, admin uploads, evaluation dashboards, and citation scoring.", BrainCircuit]
];

export default function Features() {
  return (
    <>
      <section className="page-hero bg-slate-50">
        <div className="section-inner">
          <span className="eyebrow">Services / features</span>
          <h1>Medical education features powered by retrieval.</h1>
          <p>
            Each service is connected to the core idea: the assistant should consult the
            indexed book before generating an answer.
          </p>
        </div>
      </section>

      <section className="section bg-white">
        <div className="section-inner grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {services.map(([title, text, Icon]) => (
            <article className="card" key={title}>
              <Icon className="mb-4 text-cyan-700" size={30} />
              <h2>{title}</h2>
              <p>{text}</p>
            </article>
          ))}
        </div>
      </section>

      <Footer />
    </>
  );
}
