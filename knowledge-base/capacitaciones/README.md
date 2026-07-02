# Capacitaciones / auditorías (videos)

Pon aquí los videos (o audios) de las capacitaciones y auditorías, y/o sus
transcripciones. **Nada de esta carpeta se versiona en git** (son datos de la
empresa); solo este README.

## Cómo se ingieren

```bash
# Ver qué chunks saldrían, sin gastar API ni tocar la DB:
python scripts/seed_trainings.py --dry-run

# Ingesta real (transcribe si hace falta, vectoriza y guarda en knowledge_chunks):
python scripts/seed_trainings.py
```

- Si junto al video hay un `.srt`/`.vtt`/`.txt` con el mismo nombre, se usa esa
  transcripción (no se transcribe de nuevo).
- Si solo está el video/audio, se transcribe con **faster-whisper** local
  (primera vez descarga el modelo, ~500 MB para `small`) y el `.srt` queda
  guardado aquí para las siguientes corridas.
- Los fragmentos donde se menciona un numeral de la norma ("…el numeral 6.1.1
  exige…") quedan etiquetados con ese numeral y el RAG de generación los
  recupera junto con la norma y ACOTUR. El resto queda disponible por
  similitud semántica.
- La corrida es idempotente: cada ejecución reemplaza TODO el source
  `capacitaciones`.

Formatos soportados: `.mp4 .mov .mkv .avi .webm .m4a .mp3 .wav .ogg` y
transcripciones `.srt .vtt .txt`.
