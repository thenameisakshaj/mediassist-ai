import { useState } from "react";
import { Link, NavLink } from "react-router-dom";
import { Menu, Stethoscope, X } from "lucide-react";

const links = [
  { to: "/", label: "Home" },
  { to: "/about", label: "About" },
  { to: "/features", label: "Services" },
  { to: "/bot", label: "AI Medical Bot" },
  { to: "/contact", label: "Contact" }
];

function navClass({ isActive }) {
  return `nav-link ${isActive ? "text-cyan-700" : "text-slate-700 hover:text-cyan-700"}`;
}

export default function Navbar() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/95 backdrop-blur">
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 lg:px-8">
        <Link to="/" className="flex items-center gap-3" onClick={() => setOpen(false)}>
          <span className="grid h-10 w-10 place-items-center rounded-lg bg-cyan-600 text-white shadow-sm">
            <Stethoscope size={22} />
          </span>
          <span className="text-lg font-bold text-slate-950">MediAssist AI</span>
        </Link>

        <div className="hidden items-center gap-7 md:flex">
          {links.map((link) => (
            <NavLink key={link.to} to={link.to} className={navClass}>
              {link.label}
            </NavLink>
          ))}
          <Link className="btn-primary" to="/bot">
            Ask the Bot
          </Link>
        </div>

        <button
          className="grid h-10 w-10 place-items-center rounded-lg border border-slate-200 text-slate-900 md:hidden"
          aria-label="Toggle navigation"
          onClick={() => setOpen((value) => !value)}
        >
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
      </nav>

      {open && (
        <div className="border-t border-slate-200 bg-white px-5 py-4 shadow-sm md:hidden">
          <div className="flex flex-col gap-4">
            {links.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                className={navClass}
                onClick={() => setOpen(false)}
              >
                {link.label}
              </NavLink>
            ))}
          </div>
        </div>
      )}
    </header>
  );
}
