import { FileText, Layers3, MessageCircle, SearchCheck } from "lucide-react";

const steps = [
  ["Ingest PDF", "The backend reads the medical book page by page and keeps page metadata.", FileText],
  ["Chunk + Embed", "Text is split into overlapping chunks and converted into semantic vectors.", Layers3],
  ["Retrieve Context", "Chroma returns the most relevant chunks for the user question.", SearchCheck],
  ["Generate Answer", "OpenAI receives only the retrieved context and returns a concise educational answer.", MessageCircle]
];

export default function HowItWorks() {
  return (
    <section className="section bg-slate-50" id="workflow">
      <div className="section-inner">
        <div className="section-heading">
          <span className="eyebrow">How it works</span>
          <h2>From medical book to grounded response.</h2>
          <p>
            MediAssist AI is not a generic chatbot. It follows a retrieval-first
            workflow before answer generation.
          </p>
        </div>

        <div className="mt-12 grid gap-5 lg:grid-cols-4">
          {steps.map(([title, text, Icon], index) => (
            <article key={title} className="card relative">
              <div className="mb-5 flex items-center justify-between">
                <div className="grid h-12 w-12 place-items-center rounded-lg bg-teal-50 text-teal-700">
                  <Icon size={23} />
                </div>
                <span className="text-sm font-black text-slate-300">0{index + 1}</span>
              </div>
              <h3>{title}</h3>
              <p>{text}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
