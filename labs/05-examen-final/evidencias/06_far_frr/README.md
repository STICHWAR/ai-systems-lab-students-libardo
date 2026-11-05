# Medición FAR/FRR local — 5 de noviembre de 2026

- Consentimiento explícito de Santiago Villamizar y Libardo Bravo para sus fotografías nuevas, destinado exclusivamente a enrolamiento local y esta medición.
- Muestras válidas: 5 de Santiago y 4 de Libardo; un rostro y landmarks utilizables por imagen con YuNet a 0.80.
- Embeddings SFace: 128 dimensiones, almacenados sólo en `rostros/`.
- Pares genuinos únicos: 16 (10 de Santiago, 6 de Libardo).
- Pares impostores únicos: 20 (5 × 4).
- Identificadores de pares: 36 únicos; no se usaron auto-comparaciones ni pares invertidos.

| Umbral | FA | FR | FAR | FRR |
|---:|---:|---:|---:|---:|
| 0.300 | 3 | 0 | 15.0% | 0.0% |
| 0.363 | 0 | 0 | 0.0% | 0.0% |
| 0.450 | 0 | 0 | 0.0% | 0.0% |

Se mantiene 0.363 como umbral operativo: en esta muestra evita las falsas aceptaciones vistas a 0.300 sin aumentar los rechazos genuinos. El resultado no se generaliza a población, cámaras o ataques de presentación distintos. No se incluyen similitudes individuales, CSV, fotografías ni embeddings.
