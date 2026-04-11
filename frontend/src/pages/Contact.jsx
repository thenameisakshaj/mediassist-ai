import { useState } from "react";
import { Mail, MapPin, MessageCircleQuestion, Send } from "lucide-react";

import { submitContactForm } from "../api/client.js";
import Footer from "../components/Footer.jsx";

export default function Contact() {
  const [form, setForm] = useState({ name: "", email: "", message: "" });
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setStatus("");
    setError("");

    try {
      await submitContactForm(form);
      setStatus("Message received for the project demo.");
      setForm({ name: "", email: "", message: "" });
    } catch (err) {
      setError(err.message || "Unable to submit message.");
    }
  }

  return (
    <>
      <section className="page-hero bg-slate-50">
        <div className="section-inner">
          <span className="eyebrow">Contact</span>
          <h1>Project contact and demo notes.</h1>
          <p>
            Use this page for academic submission details, evaluator questions, and
            portfolio contact flow demonstration.
          </p>
        </div>
      </section>

      <section className="section bg-white">
        <div className="section-inner grid gap-8 lg:grid-cols-[1fr_0.85fr]">
          <form className="card" onSubmit={handleSubmit}>
            <h2>Contact form</h2>
            <p>Submissions are logged by the Flask backend for demo purposes.</p>
            <div className="mt-6 grid gap-4">
              <input
                className="input"
                placeholder="Name"
                value={form.name}
                onChange={(event) => setForm({ ...form, name: event.target.value })}
              />
              <input
                className="input"
                placeholder="Email"
                type="email"
                value={form.email}
                onChange={(event) => setForm({ ...form, email: event.target.value })}
              />
              <textarea
                className="input min-h-36 resize-y"
                placeholder="Message"
                value={form.message}
                onChange={(event) => setForm({ ...form, message: event.target.value })}
              />
              <button className="btn-primary w-full justify-center" type="submit">
                <Send size={18} /> Submit
              </button>
              {status && <p className="text-sm font-semibold text-teal-700">{status}</p>}
              {error && <p className="text-sm font-semibold text-rose-700">{error}</p>}
            </div>
          </form>

          <div className="space-y-5">
            <article className="card">
              <Mail className="mb-4 text-cyan-700" size={28} />
              <h2>Project details</h2>
              <p>Full-stack academic MVP: React frontend, Flask backend, Chroma vector store, OpenAI answer generation.</p>
            </article>
            <article className="card">
              <MapPin className="mb-4 text-teal-700" size={28} />
              <h2>Demo environment</h2>
              <p>Runs locally with separate frontend and backend servers for clear evaluation.</p>
            </article>
            <article className="card">
              <MessageCircleQuestion className="mb-4 text-cyan-700" size={28} />
              <h2>FAQ snippet</h2>
              <p>
                The bot answers from retrieved PDF chunks. If the context is insufficient,
                it must say it cannot answer confidently from the medical book.
              </p>
            </article>
          </div>
        </div>
      </section>

      <Footer />
    </>
  );
}
