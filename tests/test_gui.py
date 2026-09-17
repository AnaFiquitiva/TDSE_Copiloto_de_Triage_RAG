"""Pruebas de humo de la interfaz gráfica: solo verifican que los widgets se
construyen sin error (no hay mainloop ni interacción real). Si el entorno no
tiene un display disponible (p. ej. un runner de CI sin X11/Tk), la prueba se
omite en lugar de fallar.
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


if __name__ == "__main__":
    unittest.main()
