import { BrowserRouter, Route, Routes } from "react-router-dom";

import Navbar from "../components/Navbar.jsx";
import About from "../pages/About.jsx";
import Contact from "../pages/Contact.jsx";
import Features from "../pages/Features.jsx";
import Home from "../pages/Home.jsx";
import MedicalBot from "../pages/MedicalBot.jsx";

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Navbar />
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/about" element={<About />} />
          <Route path="/features" element={<Features />} />
          <Route path="/bot" element={<MedicalBot />} />
          <Route path="/contact" element={<Contact />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}
