# Decisiones de diseño

Lo que se decidió sobre la imagen de este perfil (README de GitHub y LinkedIn), con su motivo. Lo
rechazado no se vuelve a proponer salvo que haya un motivo nuevo.

## 2026-11-08 · Portada de LinkedIn

**Elegida: «Evolución»** (`assets/linkedin-banner.png`, generada con `tools/linkedin_banner.py`).
La misma ciudad de neón, el letrero KOTLIN, el terminal y el retrato del banner de GitHub, pero con
una sola línea discreta arriba («ANDROID · COMPOSE MULTIPLATFORM · AI AGENT TOOLING») y el terminal
de protagonista. Motivo: enseña en vez de contar, no compite con el nombre ni repite el titular, y se
reconoce como la misma persona que en GitHub.

- **Sin el nombre:** LinkedIn lo pone justo debajo de la portada, y la foto de perfil tapa la esquina
  inferior izquierda, que es donde iba.
- **Compose Multiplatform, no Kotlin Multiplatform:** el letrero ya dice KOTLIN, CMP implica KMP y
  enlaza con Jetpack Compose. Para las búsquedas no cuenta: el texto de una imagen no se indexa; eso lo
  cubren el titular («KMP/CMP») y las aptitudes.
- **Sin «remote»** en la portada: en LinkedIn la ven los compañeros de la empresa actual.
- **Zona tapada por la foto de perfil (escritorio):** x < ~400 e y > ~205 sobre 1584 × 396. Medida en
  el perfil de escritorio; la del móvil está sin comprobar.

**Descartadas:**
- La portada anterior de LinkedIn (robots de Android en neón sobre circuitos): genérica, cian y verde
  saturados, y solo decía «Android».
- Primera versión con titular a 54 px: en escritorio se veía más grande que el nombre (27 px frente
  a 24 px).
- «Pulida» (la primera con el titular a 38 px): correcta, pero repetía el titular y tenía más
  elementos y colores.
- «Atrevida» (sin texto, solo la escena): suelta no decía nada.
- Varias fotos de portada: solo con Premium; no compensa.

**Pendiente:** el banner de GitHub sigue diciendo «KOTLIN MULTIPLATFORM». Si se quiere que coincida,
se cambia en `tools/banner.py`.
