import React, { useState } from "react";
import UploadTab from "./components/UploadTab";
import ChatTab from "./components/ChatTab";
import { Toaster } from "react-hot-toast";
import { motion, AnimatePresence } from "framer-motion";

export default function App() {
  const [tab, setTab] = useState("upload");

  return (
    <div className="min-h-screen flex flex-col items-center bg-gradient-to-br from-indigo-500 via-blue-600 to-purple-600 text-white p-6">
      {/* Toast notifications */}
      <Toaster position="top-right" />

      {/* Title */}
      <motion.h1
        initial={{ y: -30, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="text-4xl font-extrabold mb-8 drop-shadow-lg text-center"
      >
        🎧 AI Audiobook Generator
      </motion.h1>

      {/* Tabs */}
      <div className="flex space-x-4 mb-8">
        <button
          onClick={() => setTab("upload")}
          className={`px-6 py-2 rounded-full font-semibold transition-all duration-300 ${
            tab === "upload"
              ? "bg-white text-indigo-700 shadow-lg scale-105"
              : "bg-indigo-900/50 hover:bg-indigo-800/70 text-white"
          }`}
        >
          📤 Upload & Generate
        </button>

        <button
          onClick={() => setTab("chat")}
          className={`px-6 py-2 rounded-full font-semibold transition-all duration-300 ${
            tab === "chat"
              ? "bg-white text-indigo-700 shadow-lg scale-105"
              : "bg-indigo-900/50 hover:bg-indigo-800/70 text-white"
          }`}
        >
          💬 Ask Questions
        </button>
      </div>

      {/* Card container */}
      <div className="w-full max-w-3xl bg-white/95 rounded-2xl shadow-xl p-6 text-gray-900 backdrop-blur">
        <AnimatePresence mode="wait">
          {tab === "upload" ? (
            <motion.div
              key="upload"
              initial={{ opacity: 0, x: -30 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 30 }}
              transition={{ duration: 0.25 }}
            >
              <UploadTab />
            </motion.div>
          ) : (
            <motion.div
              key="chat"
              initial={{ opacity: 0, x: 30 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -30 }}
              transition={{ duration: 0.25 }}
            >
              <ChatTab />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
