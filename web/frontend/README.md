# TDSE Copiloto de Triage RAG — Frontend

Interfaz web (React 19 + TypeScript + Vite + Tailwind CSS v4 + Recharts) para el
prototipo del copiloto de triage. Es una capa de presentación **opcional**:
consume la API en `web/backend/` (FastAPI), que a su vez envuelve el pipeline
principal (`src/`, `experiments/`) sin duplicar su lógica.

Ver `README.md` en la raíz del repositorio, sección **"Interfaz web
(React + TypeScript)"**, para el contexto completo, capturas y cómo se
relaciona con la interfaz de escritorio (`gui.py`) y la CLI (`demo.py`).

## Desarrollo

```bash
npm install
npm run dev       # http://localhost:5173, proxyea /api/* a http://127.0.0.1:8000
```

Requiere que `web/backend` esté corriendo (ver su propio README/instrucciones
en la raíz del proyecto) para que las pantallas con datos reales funcionen.

## Build de producción

```bash
npm run build      # type-checks (tsc -b) + build (vite build) -> dist/
npm run preview     # sirve el build de dist/ localmente
```

## Estructura

```
src/
  api.ts            Cliente tipado de la API (fetch + tipos de types.ts)
  types.ts          Tipos TypeScript en espejo de los modelos Pydantic del backend
  components/       Componentes compartidos (badges de nivel, tarjetas, spinners...)
  views/
    ConsultaView.tsx      Equivalente web de demo.py / la pestaña "Consulta individual" de gui.py
    ExperimentoView.tsx   Equivalente web de `python -m experiments.run_experiment`, con gráfico
    DatasetView.tsx       Equivalente web de `python -m experiments.analyze_external_data`, con gráficos
    ExplorarView.tsx      Explorador del corpus normativo y las 74 viñetas del gold standard
  App.tsx           Shell con navegación lateral entre las 4 vistas
```
