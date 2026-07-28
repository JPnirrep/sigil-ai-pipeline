#!/usr/bin/env python3
"""
KLEIA-UP Book — Sigil Plugin
Encapsule le pipeline DOCX → EPUB + PDF dans un plugin Sigil output.
"""

import os, sys, json, tempfile, shutil, subprocess, traceback
from pathlib import Path

# Le pipeline KLEIA-UP doit être accessible
_PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
_POC_DIR = os.path.join(_PLUGIN_DIR, "..", "..")
if _POC_DIR not in sys.path:
    sys.path.insert(0, os.path.abspath(_POC_DIR))


def pipeline_action(bk):
    """
    Point d'entrée du plugin Sigil.
    bk: BookContainer — l'EPUB ouvert dans Sigil
    """
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox

    root = tk.Tk()
    root.title("KLEIA-UP Book Pipeline")
    root.geometry("520x300")
    root.resizable(False, False)

    # ── UI ──
    frame = ttk.Frame(root, padding=20)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="KLEIA-UP Book Pipeline", font=("", 14, "bold")).pack()
    ttk.Label(frame, text="DOCX KDP → EPUB 3 + PDF print-ready", foreground="gray").pack(pady=(0,15))

    # DOCX path
    ttk.Label(frame, text="Fichier DOCX (template KDP) :").pack(anchor="w")
    docx_entry = ttk.Entry(frame, width=60)
    docx_entry.pack(fill="x", pady=(2,5))

    def browse_docx():
        path = filedialog.askopenfilename(
            title="Sélectionner le DOCX template KDP",
            filetypes=[("Word documents", "*.docx"), ("All files", "*.*")]
        )
        if path:
            docx_entry.delete(0, "end")
            docx_entry.insert(0, path)

    ttk.Button(frame, text="Parcourir...", command=browse_docx).pack(anchor="w")

    # Options
    opts_frame = ttk.Frame(frame)
    opts_frame.pack(fill="x", pady=10)

    genre_var = tk.StringVar(value="auto")
    ttk.Label(opts_frame, text="Genre :").grid(row=0, column=0, sticky="w")
    genre_combo = ttk.Combobox(opts_frame, textvariable=genre_var,
                                values=["auto", "fiction", "scifi", "fantasy", "nonfiction"],
                                width=15, state="readonly")
    genre_combo.grid(row=0, column=1, sticky="w", padx=5)

    fmt_epub = tk.BooleanVar(value=True)
    fmt_pdf = tk.BooleanVar(value=True)
    ttk.Checkbutton(opts_frame, text="EPUB", variable=fmt_epub).grid(row=1, column=0, sticky="w")
    ttk.Checkbutton(opts_frame, text="PDF print", variable=fmt_pdf).grid(row=1, column=1, sticky="w")

    # Status / log
    status_text = tk.Text(frame, height=6, width=60, state="disabled")
    status_text.pack(fill="both", pady=(5,10))

    def log(msg):
        status_text.config(state="normal")
        status_text.insert("end", msg + "\n")
        status_text.see("end")
        status_text.config(state="disabled")
        root.update()

    # ── Run ──
    def run():
        docx_path = docx_entry.get().strip()
        if not docx_path or not os.path.isfile(docx_path):
            messagebox.showerror("Erreur", "Sélectionne un fichier DOCX valide.")
            return

        formats = []
        if fmt_epub.get(): formats.append("epub")
        if fmt_pdf.get(): formats.append("pdf")
        if not formats:
            messagebox.showerror("Erreur", "Sélectionne au moins un format.")
            return

        genre = genre_var.get()
        if genre == "auto": genre = None

        try:
            from kleia_up_book import run_pipeline
            output_dir = os.path.join(os.path.dirname(docx_path), "kleia-up-output")
            log(f"🚀 Pipeline KLEIA-UP lancé...")
            log(f"   DOCX: {docx_path}")
            log(f"   Formats: {', '.join(formats)}")
            log(f"   Genre: {genre or 'auto'}")

            results = run_pipeline(docx_path, output_dir, genre=genre, format=formats)

            log(f"\n✅ Terminé en {results['timing']['total']}s")
            log(f"   Titre: {results['book']['title']}")
            log(f"   Chapitres: {results['book']['chapters']}")
            log(f"   Template: {results['book']['trim']}")
            log(f"   Genre: {results['book']['genre_detected']}")
            log(f"   Thème: {results['book']['theme']}")

            for fmt, path in results['paths'].items():
                sz = os.path.getsize(path)
                log(f"\n   ✓ {fmt.upper()}: {Path(path).name} ({sz/1024:.0f} KB)")

            if results['errors']:
                log(f"\n⚠ Erreurs: {results['errors']}")

            log(f"\n📁 Dossier: {output_dir}")

        except Exception as e:
            log(f"\n❌ Erreur: {e}")
            traceback.print_exc()

    ttk.Button(frame, text="▶ Lancer la production", command=run).pack()

    root.mainloop()
    return 0
