# Validación ampliada de DeepSeek frente a TF-IDF (D110)

Generado el 2026-11-10 con `python -m src.modelos.validacion_deepseek`. Métricas de la clase `funerario` sin ponderar, con bootstrap de 2.000 réplicas estratificado por origen (semilla 2026).

## Conjunto principal (decide la regla de D110)

Lotes elegidos sin usar predicciones de ningún modelo: validacion_60_revisada, estrato_d_150, humanitarios_40.

| Modelo | Contratos | Funerarios | Precisión | Sensibilidad | F1 (IC 95 %) |
|---|---|---|---|---|---|
| tfidf_logistica | 250 | 58 | 0,964 | 0,931 | 0,947 (0,904–0,983) |
| deepseek_flash | 250 | 58 | 1,000 | 0,948 | 0,973 (0,936–1,000) |

**Resultado de la regla:** TF-IDF sigue como clasificador (límite inferior de DeepSeek 0,936 frente a límite superior de TF-IDF 0,983).

## Los 343 contratos (referencia; incluye lotes elegidos con predicciones del modelo)

| Modelo | Contratos | Funerarios | Precisión | Sensibilidad | F1 (IC 95 %) |
|---|---|---|---|---|---|
| tfidf_logistica | 343 | 105 | 0,877 | 0,952 | 0,913 (0,877–0,944) |
| deepseek_flash | 343 | 105 | 0,962 | 0,962 | 0,962 (0,935–0,986) |

## Por origen

| Origen | Modelo | Contratos | Funerarios | F1 | Precisión | Sensibilidad |
|---|---|---|---|---|---|---|
| validacion_60_revisada | tfidf_logistica | 60 | 23 | 0,913 | 0,913 | 0,913 |
| validacion_60_revisada | deepseek_flash | 60 | 23 | 0,978 | 1,000 | 0,957 |
| estrato_d_150 | tfidf_logistica | 150 | 0 | 0,000 | nan | nan |
| estrato_d_150 | deepseek_flash | 150 | 0 | 0,000 | nan | nan |
| humanitarios_40 | tfidf_logistica | 40 | 35 | 0,971 | 1,000 | 0,943 |
| humanitarios_40 | deepseek_flash | 40 | 35 | 0,971 | 1,000 | 0,943 |
| secop1_nuevos | tfidf_logistica | 30 | 15 | 1,000 | 1,000 | 1,000 |
| secop1_nuevos | deepseek_flash | 30 | 15 | 0,938 | 0,882 | 1,000 |
| top_valor | tfidf_logistica | 50 | 28 | 0,931 | 0,900 | 0,964 |
| top_valor | deepseek_flash | 50 | 28 | 0,947 | 0,931 | 0,964 |
| grupo5_revision | tfidf_logistica | 11 | 4 | 0,533 | 0,364 | 1,000 |
| grupo5_revision | deepseek_flash | 11 | 4 | 1,000 | 1,000 | 1,000 |
| adicionales_d81 | tfidf_logistica | 2 | 0 | 0,000 | 0,000 | nan |
| adicionales_d81 | deepseek_flash | 2 | 0 | 0,000 | nan | nan |

## Estabilidad de DeepSeek entre corridas

- Tres corridas con la misma instrucción y los mismos ocho ejemplos de D58; predicción final por mayoría.
- Contratos con la misma etiqueta en las tres corridas: 99,7 %.
- Respuestas inválidas: 0; empates resueltos con la primera corrida: 0.
- Costo real de las tres corridas: 0,099 USD.

## Matrices de confusión del conjunto principal (filas: humano)

**tfidf_logistica**

| humano \ modelo | funerario | mixto | no_funerario |
|---|---|---|---|
| funerario | 54 | 0 | 4 |
| mixto | 0 | 0 | 1 |
| no_funerario | 2 | 0 | 189 |

**deepseek_flash**

| humano \ modelo | funerario | mixto | no_funerario |
|---|---|---|---|
| funerario | 55 | 3 | 0 |
| mixto | 0 | 0 | 1 |
| no_funerario | 0 | 2 | 189 |
