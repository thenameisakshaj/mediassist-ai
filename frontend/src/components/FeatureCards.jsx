import { motion } from "framer-motion";
import { Activity, BookOpen, Brain, MessageSquareText, Search, ShieldCheck } from "lucide-react";

const features = [
  ["Book-Based Knowledge", "Indexes the uploaded medical PDF and uses retrieved passages as the answer source.", BookOpen],
  ["Retrieval Pipeline", "Splits pages into chunks, embeds each chunk, and searches Chroma for relevant context.", Search],
  ["OpenAI Answers", "Sends the retrieved context and user question to a modern OpenAI model for a concise response.", Brain],
  ["Safety Guardrails", "Avoids diagnosis claims, keeps content educational, and adds urgent-care guidance.", ShieldCheck],
  ["Chatbot UI", "Includes suggested prompts, loading states, source snippets, and graceful error handling.", MessageSquareText],
  ["Demo Ready", "Clear API routes, persistent vector storage, index status, and viva-friendly documentation.", Activity]
];

export default function FeatureCards() {
  return (
    <section className="section bg-white" id="features">
      <div className="section-inner">
        <div className="section-heading">
          <span className="eyebrow">Feature highlights</span>
          <h2>Real RAG architecture with a polished health-tech interface.</h2>
          <p>
            The project is organized so you can demo the site, explain the pipeline,
            and show how answers stay grounded in the indexed book.
          </p>
        </div>

        <div className="mt-12 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {features.map(([title, text, Icon], index) => (
            <motion.article
              key={title}
              initial={{ opacity: 0, y: 18 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-80px" }}
              transition={{ delay: index * 0.04, duration: 0.45 }}
              className="card group"
            >
              <div className="mb-5 grid h-12 w-12 place-items-center rounded-lg bg-cyan-50 text-cyan-700 transition group-hover:bg-cyan-600 group-hover:text-white">
                <Icon size={24} />
              </div>
              <h3>{title}</h3>
              <p>{text}</p>
            </motion.article>
          ))}
        </div>
      </div>
    </section>
  );
}
