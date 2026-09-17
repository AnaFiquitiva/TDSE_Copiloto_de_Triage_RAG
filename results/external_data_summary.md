# Análisis del conjunto de datos externo real (Datos Abiertos Colombia)

Fuente: [Clasificación en Triage Urgencias](https://www.datos.gov.co/Salud-y-Protecci-n-Social/Clasificaci-n-en-Triage-Urgencias/vt5n-eu2r), Datos Abiertos Colombia (dataset id `vt5n-eu2r`), descargado el 2026-09-17 vía la API Socrata (`https://www.datos.gov.co/resource/vt5n-eu2r.csv`).

Registros totales: 89453. **Este conjunto no contiene el relato libre del paciente**, solo nivel de triage y marcas de tiempo administrativas; no se usa para entrenar ni evaluar el copiloto (ver `experiments/analyze_external_data.py`).

## Distribución real de niveles de triage

| Nivel | N | % |
|---|---|---|
| I | 203 | 0.23% |
| II | 2710 | 3.03% |
| III | 79198 | 88.54% |
| IV | 6934 | 7.75% |
| V | 408 | 0.46% |

Esta distribución respalda empíricamente la decisión metodológica del documento del proyecto de sobremuestrear los niveles I-II en el conjunto de prueba sintético (Sección 5): en datos operativos reales, los niveles I-II representan apenas 3.3% de los casos, insuficiente para medir con precisión el desempeño donde el costo de un error es mayor.

## Tiempo de ingreso a atención, por nivel (minutos)

Se descartan registros con duración negativa o mayor a 24 horas (errores de captura administrativa). Esto es un dato agregado de una red de IPS reportante, no una medición prospectiva in situ como la que describe el documento del proyecto (Sección 3); se reporta aquí únicamente como referencia secundaria.

| Nivel | N válidos | Mediana (min) | Media (min) |
|---|---|---|---|
| I | 201 | 28.3 | 45.4 |
| II | 2695 | 22.4 | 34.0 |
| III | 79029 | 35.0 | 52.9 |
| IV | 6929 | 74.0 | 89.2 |
| V | 405 | 79.0 | 98.1 |
