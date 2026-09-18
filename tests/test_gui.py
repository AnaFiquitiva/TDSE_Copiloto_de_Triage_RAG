"""Pruebas de la interfaz gráfica. Incluye tanto pruebas de humo (los widgets
se construyen sin error) como pruebas funcionales de la lógica real de cada
botón (`_compute()`), llamada directamente sin hilos ni mainloop -- esto
último es justo lo que faltaba cuando `ExperimentoTab` quedó con una llamada
desactualizada a `run_experiment.format_markdown()` tras agregarle un
parámetro nuevo: las pruebas de construcción no lo detectaron porque nunca
invocaban la lógica del botón. Si el entorno no tiene un display disponible
(p. ej. un runner de CI sin X11/Tk), las pruebas se omiten en lugar de fallar.
"""
import tkinter as tk
import unittest
from tkinter import ttk

try:
    _root = tk.Tk()
    _root.destroy()
    DISPLAY_AVAILABLE = True
except tk.TclError:
    DISPLAY_AVAILABLE = False


@unittest.skipUnless(DISPLAY_AVAILABLE, "No hay display disponible para Tkinter en este entorno")
class TestGuiConstruction(unittest.TestCase):
    def setUp(self):
        import gui  # import diferido: solo si hay display

        self.gui = gui
        self.root = tk.Tk()
        self.notebook = ttk.Notebook(self.root)

    def tearDown(self):
        try:
            self.root.destroy()
        except tk.TclError:
            pass  # ruido de teardown de Tcl/Tk sin efecto en el resultado de la prueba

    def test_all_tabs_construct_without_error(self):
        self.notebook.add(self.gui.ConsultaTab(self.notebook), text="Consulta individual")
        self.notebook.add(self.gui.ExperimentoTab(self.notebook), text="Experimento 2x2")
        self.notebook.add(self.gui.DatasetTab(self.notebook), text="Dataset real")
        self.root.update()


@unittest.skipUnless(DISPLAY_AVAILABLE, "No hay display disponible para Tkinter en este entorno")
class TestGuiComputeLogic(unittest.TestCase):
    """Llama directamente a `_compute()` de cada pestaña (sin hilos, sin
    mainloop): es la prueba que habría detectado el bug real de la llamada
    desactualizada a `format_markdown()` en ExperimentoTab."""

    def setUp(self):
        import gui

        self.gui = gui
        self.root = tk.Tk()
        self.notebook = ttk.Notebook(self.root)

    def tearDown(self):
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def test_consulta_tab_compute_returns_expected_tuple(self):
        tab = self.gui.ConsultaTab(self.notebook)
        suggestion, baseline_result, backend_used = tab._compute(
            "El paciente no respira y no reacciona.", "reformatted", "clinical_es", "deterministic"
        )
        self.assertIsNotNone(suggestion)
        self.assertIsNotNone(baseline_result)
        self.assertEqual(backend_used, "deterministic")

    def test_experimento_tab_compute_returns_markdown(self):
        result = self.gui.ExperimentoTab._compute()
        self.assertIn("Resultados del diseño experimental", result)

    def test_dataset_tab_compute_returns_markdown(self):
        result = self.gui.DatasetTab._compute()
        self.assertIn("Análisis del conjunto de datos externo real", result)


if __name__ == "__main__":
    unittest.main()
