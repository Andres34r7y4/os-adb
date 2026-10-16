# LinkedIn Post — OS-ADB (copiar/pegar)

Perdí 3 horas discutiendo por qué usamos Postgres… y nadie recordaba la decisión. 😅

Los ADRs terminan en hilos de Slack, PRs cerrados o "lo hablamos en una call". Seis meses después, pagas esa deuda de decisión con re-trabajo.

Para cortarlo de raíz construí OS-ADB (Architecture Decision Buffer):
herramienta Python CLI/TUI que registra una decisión en 2 segundos sin salir de la terminal.

```bash
adb add --title "Use SQLite per Module" --justification "Zero ops, git-friendly" --tag architecture
adb export --output ADR_LOG.md
```

💡 Lo interesante no es solo la tool, es cómo está construida:
→ Domain puro, 0 dependencias
→ Engine desacoplado por inyección de repositorio
→ Adapters intercambiables (SQLite hoy, Postgres mañana)
→ UI dual: CLI Typer/Rich + TUI Textual

Ejemplo vivo del Strict Layered Pattern que puedes robar para tus proyectos.

📌 Repo + quickstart de 30s (`make install` crea el .venv solo):
🔗 https://github.com/Andres34r7y4/os-adb

¿Cómo versionas tus ADRs hoy: Notion, Markdown en git, o memoria del equipo? 👇

#SoftwareArchitecture #Python #CleanCode #DeveloperExperience #Textual #CLI #ADR
