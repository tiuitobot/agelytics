# Agelytics Onboarding (Rápido)

## Visão Geral
- `agelytics/`: núcleo determinístico (parser, db, report, pdf, overlay server).
- `integrations/openclaw/`: automações e integração com Telegram/OpenClaw.
- `knowledge/aoe2/`: base de conhecimento estática (civs, matchups, benchmarks).
- `data/`: banco SQLite e artefatos locais (gitignored).

Fluxo principal:
1. replay `.aoe2record` -> `parser.py`
2. persistência -> `db.py` (SQLite)
3. consumo -> CLI (`report/stats/patterns/pdf`) e overlay (`overlay_server.py`)

## Como Rodar
- Criar ambiente:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

- Ingest:
```bash
python3 -m agelytics ingest /caminho/savegame -v
```

- Match report:
```bash
python3 -m agelytics report --last -p <PLAYER>
python3 -m agelytics report --id <MATCH_ID> -p <PLAYER>
```

- Overlay:
```bash
./scripts/start_overlay.sh
# UI: http://localhost:5555/overlay
```

- Watcher (live, focado em overlay):
```bash
./scripts/start_watcher.sh
```

- Watcher OpenClaw/cron:
```bash
python3 -m integrations.openclaw.watcher
# ou via cron: integrations/openclaw/watch_cron.sh
```

## Scouting Overlay: Como Funciona
1. watcher detecta partida e envia contexto em `POST /api/match-context`
2. overlay (`static/overlay.html`) faz polling de `/api/match-context`
3. quando contexto muda, overlay dispara `GET /api/scout/{opponent_name}`
4. UI renderiza scouting + matchup/civ info

Ponto importante sobre o "bug" no `trigger_scouting`:
- `trigger_scouting` é **prewarm opcional** (cache/latência).
- A funcionalidade principal do overlay **não depende** dele.
- Mesmo com erro no prewarm, o overlay segue funcionando via polling de `match-context` e scout direto no frontend.

## Onde Ficam Scripts OpenClaw
- `integrations/openclaw/watcher.py`: ingest + notificação Telegram
- `integrations/openclaw/live_watcher.py`: watcher de partida ao vivo para overlay
- `integrations/openclaw/watch_cron.sh`: wrapper de cron
- `integrations/openclaw/callback.sh`: roteamento de callbacks
- detalhes: `integrations/openclaw/README.md`

## Como Contribuir
- Branching sugerido:
  - `feature/<tema-curto>`
  - `fix/<tema-curto>`
- Commits pequenos e descritivos (1 assunto por commit).
- Validar antes de commit:
```bash
python3 -m py_compile agelytics/*.py integrations/openclaw/*.py
python3 -m agelytics --help
```
- Smoke test recomendado quando houver DB local:
```bash
python3 -m agelytics report --last -p <PLAYER>
```

## Backlog do Bruno: Estado Real (Fev/2026)
- `housing`: implementado (housed count, lower/upper bounds, TC idle effective).
- `tc idle breakdown no match report`: **implementado** (parser + persistência + exibição no report).
- `winsorizada no scouting aggregate`: **implementado** (agregações de scouting em média winsorizada 10%).
- `cross-validation`: implementado no fluxo de scouting PDF (lower x upper por era).
- `badges/disclaimer`: implementado em `agelytics/pdf_disclaimer.py`.
- `pdf engine unificado`: **parcial** (há múltiplos geradores: `pdf_report.py`, `pdf_scouting.py`, `pdf_analysis.py`).
- `aplicar no match report`: **parcialmente fechado** (TC breakdown + housing/effective range no report textual e persistência no DB; unificação total de engine PDF ainda pendente).
