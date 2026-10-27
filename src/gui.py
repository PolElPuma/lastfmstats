#!/usr/bin/env python3
"""Interfaz de escritorio para generar calendarios de Last.fm."""
import sys
import threading
import webbrowser
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

APP_ROOT = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from load_scrobbles import ScrobblesAnalyzer, ScrobblesLoader
from main import calculate_complete_summary, filter_scrobbles_by_date


class LastFmStatsApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Last.fm Stats")
        self.root.geometry("700x620")
        self.root.minsize(620, 560)
        self.source = tk.StringVar(value="file")
        self.file_path = tk.StringVar()
        self.username = tk.StringVar()
        self.start_date = tk.StringVar()
        self.output_path = tk.StringVar(value=str(APP_ROOT / "calendar.html"))
        self.item_count = tk.StringVar(value="20")
        self.day_count = tk.StringVar(value="10")
        self.peak_count = tk.StringVar(value="10")
        self.streak_gap = tk.StringVar(value="48")
        self.streak_mode = tk.StringVar(value="gap")
        self.split_years = tk.BooleanVar(value=True)
        self.fetch_durations = tk.BooleanVar(value=False)
        self.open_browser = tk.BooleanVar(value=True)
        self._build_ui()

    def _build_ui(self) -> None:
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
        container = ttk.Frame(self.root, padding=22)
        container.pack(fill="both", expand=True)
        ttk.Label(container, text="Last.fm Stats", font=("Segoe UI", 22, "bold")).pack(anchor="w")
        ttk.Label(container, text="Genera un calendario interactivo con tus métricas y rachas.").pack(anchor="w", pady=(2, 18))

        source_frame = ttk.LabelFrame(container, text="Datos", padding=12)
        source_frame.pack(fill="x", pady=(0, 12))
        ttk.Radiobutton(source_frame, text="Archivo JSON", variable=self.source, value="file", command=self._update_source).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(source_frame, text="Usuario de Last.fm", variable=self.source, value="api", command=self._update_source).grid(row=0, column=1, sticky="w", padx=(14, 0))
        self.file_entry = ttk.Entry(source_frame, textvariable=self.file_path)
        self.file_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        self.browse_button = ttk.Button(source_frame, text="Elegir archivo", command=self._choose_input)
        self.browse_button.grid(row=1, column=2, padx=(8, 0), pady=(8, 0))
        self.username_entry = ttk.Entry(source_frame, textvariable=self.username)
        self.username_entry.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        source_frame.columnconfigure(0, weight=1)
        source_frame.columnconfigure(1, weight=1)

        settings = ttk.LabelFrame(container, text="Análisis", padding=12)
        settings.pack(fill="x", pady=(0, 12))
        fields = [
            ("Resultados por lista", self.item_count),
            ("Días destacados", self.day_count),
            ("Picos diarios", self.peak_count),
            ("Separación máxima (horas)", self.streak_gap),
        ]
        for index, (label, variable) in enumerate(fields):
            row, column = divmod(index, 2)
            cell = ttk.Frame(settings)
            cell.grid(row=row, column=column, sticky="ew", padx=(0, 12), pady=5)
            ttk.Label(cell, text=label).pack(anchor="w")
            ttk.Entry(cell, textvariable=variable, width=12).pack(anchor="w", pady=(3, 0))
        settings.columnconfigure(0, weight=1)
        settings.columnconfigure(1, weight=1)
        ttk.Label(settings, text="Regla de racha").grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Combobox(settings, textvariable=self.streak_mode, values=("gap", "calendar"), state="readonly", width=18).grid(row=3, column=0, sticky="w", pady=(3, 0))
        ttk.Label(settings, text="gap: horas entre escuchas · calendar: días naturales consecutivos").grid(row=3, column=1, sticky="w", padx=(0, 4), pady=(3, 0))

        options = ttk.Frame(container)
        options.pack(fill="x", pady=(0, 12))
        ttk.Checkbutton(options, text="Calcular resúmenes separados por año", variable=self.split_years).pack(anchor="w", pady=2)
        ttk.Checkbutton(options, text="Consultar duraciones en Last.fm (puede tardar y requiere Internet)", variable=self.fetch_durations).pack(anchor="w", pady=2)
        ttk.Checkbutton(options, text="Abrir el calendario al terminar", variable=self.open_browser).pack(anchor="w", pady=2)
        date_row = ttk.Frame(options)
        date_row.pack(fill="x", pady=(8, 0))
        ttk.Label(date_row, text="Desde (AAAA-MM-DD, opcional)").pack(side="left")
        ttk.Entry(date_row, textvariable=self.start_date, width=18).pack(side="left", padx=(10, 0))

        output_frame = ttk.LabelFrame(container, text="Salida", padding=12)
        output_frame.pack(fill="x", pady=(0, 14))
        ttk.Entry(output_frame, textvariable=self.output_path).pack(side="left", fill="x", expand=True)
        ttk.Button(output_frame, text="Guardar como…", command=self._choose_output).pack(side="left", padx=(8, 0))

        self.generate_button = ttk.Button(container, text="Generar calendario", command=self._start_generation)
        self.generate_button.pack(anchor="e")
        self.status = tk.StringVar(value="Listo")
        ttk.Label(container, textvariable=self.status, wraplength=650).pack(anchor="w", pady=(12, 0))
        self._update_source()

    def _update_source(self) -> None:
        is_file = self.source.get() == "file"
        self.file_entry.configure(state="normal" if is_file else "disabled")
        self.browse_button.configure(state="normal" if is_file else "disabled")
        self.username_entry.configure(state="disabled" if is_file else "normal")

    def _choose_input(self) -> None:
        path = filedialog.askopenfilename(
            title="Seleccionar historial de scrobbles",
            filetypes=(("JSON", "*.json"), ("Todos los archivos", "*.*")),
        )
        if path:
            self.file_path.set(path)

    def _choose_output(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Guardar calendario",
            defaultextension=".html",
            filetypes=(("HTML", "*.html"),),
            initialfile="calendar.html",
        )
        if path:
            self.output_path.set(path)

    def _start_generation(self) -> None:
        try:
            settings = {
                "n_items": int(self.item_count.get()),
                "n_days": int(self.day_count.get()),
                "n_peak_plays": int(self.peak_count.get()),
                "max_gap_hours": int(self.streak_gap.get()),
            }
            if any(value < 1 for value in settings.values()):
                raise ValueError("Los valores numéricos deben ser mayores que cero.")
            if self.streak_mode.get() not in ("gap", "calendar"):
                raise ValueError("Selecciona una regla de racha válida.")
            if self.source.get() == "file" and not self.file_path.get():
                raise ValueError("Selecciona un archivo JSON.")
            if self.source.get() == "api" and not self.username.get().strip():
                raise ValueError("Escribe tu usuario de Last.fm.")
            if not self.output_path.get().strip():
                raise ValueError("Selecciona dónde guardar el HTML.")
            date_text = self.start_date.get().strip()
            start_date = datetime.strptime(date_text, "%Y-%m-%d") if date_text else None
        except ValueError as error:
            messagebox.showerror("Configuración inválida", str(error))
            return

        job = {
            **settings,
            "source": self.source.get(),
            "file_path": self.file_path.get(),
            "username": self.username.get().strip(),
            "fetch_duration_data": self.fetch_durations.get(),
            "interval_mode": self.streak_mode.get(),
            "split_by_year": self.split_years.get(),
            "output_path": self.output_path.get(),
            "open_browser": self.open_browser.get(),
        }
        self.generate_button.configure(state="disabled")
        self.status.set("Cargando scrobbles y calculando estadísticas…")
        threading.Thread(target=self._generate, args=(job, start_date), daemon=True).start()

    def _generate(self, job: dict, start_date: Optional[datetime]) -> None:
        try:
            if getattr(sys, "frozen", False):
                app_data = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "LastFMStats" if os.name == "nt" else Path.home() / ".local" / "share" / "lastfmstats"
                data_dir = app_data / "data"
            else:
                data_dir = APP_ROOT / "data"
            data_dir.mkdir(parents=True, exist_ok=True)
            loader = ScrobblesLoader(str(data_dir))
            if job["source"] == "file":
                scrobbles = loader.load_file(job["file_path"])
            else:
                scrobbles = loader.download_recent_scrobbles(job["username"])
            if start_date:
                scrobbles = filter_scrobbles_by_date(scrobbles, start_date)
            if not scrobbles:
                raise ValueError("No se encontraron scrobbles para analizar.")

            summary = calculate_complete_summary(
                scrobbles,
                n_items=job["n_items"],
                n_days=job["n_days"],
                n_peak_plays=job["n_peak_plays"],
                max_gap_hours=job["max_gap_hours"],
                fetch_duration_data=job["fetch_duration_data"],
                interval_mode=job["interval_mode"],
                split_by_year=job["split_by_year"],
            )
            output_path = Path(job["output_path"]).expanduser().resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            ScrobblesAnalyzer.generate_calendar_html(
                scrobbles,
                output_file=str(output_path),
                summary=summary,
                n_items=job["n_items"],
                n_days=job["n_days"],
                n_peak_plays=job["n_peak_plays"],
                split_by_year=job["split_by_year"],
            )
            self.root.after(0, self._generation_finished, output_path, job["open_browser"])
        except Exception as error:
            self.root.after(0, self._generation_failed, str(error))

    def _generation_finished(self, output_path: Path, open_browser: bool) -> None:
        self.generate_button.configure(state="normal")
        self.status.set(f"Calendario generado: {output_path}")
        if open_browser:
            webbrowser.open(output_path.as_uri())

    def _generation_failed(self, error: str) -> None:
        self.generate_button.configure(state="normal")
        self.status.set("No se pudo generar el calendario.")
        messagebox.showerror("Error al generar", error)


def main() -> None:
    root = tk.Tk()
    LastFmStatsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()