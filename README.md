# NetraX — AI-Powered Criminal Network Analysis System

NetraX ingests fragmented crime data (FIRs, CDRs, financial transactions, surveillance notes),
extracts entities using NLP, builds a knowledge graph of criminal networks, and surfaces
key influencers, communities, and suspicious patterns for investigators.

## Architecture

```
Data Sources ──► Ingestion ──► Entity Extraction (spaCy + regex + resolution)
                                      │
                                      ▼
                              Knowledge Graph (NetworkX)
                                      │
                     ┌────────────────┼──────────────────┐
                     ▼                ▼                  ▼
              Influencer Rank   Community Detection   Anomaly Rules
                     └────────────────┼──────────────────┘
                                      ▼
                          FastAPI ◄── Investigator Dashboard (Cytoscape.js)
```

## Quickstart

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m spacy download en_core_web_sm

# 1. Generate synthetic demo dataset
.venv/bin/python scripts/generate_data.py

# 2. Run the analysis pipeline (ingest → extract → graph → analytics)
.venv/bin/python scripts/run_pipeline.py

# 3. Launch the investigator dashboard
.venv/bin/uvicorn backend.app.main:app --reload
# open http://localhost:8000
```

## Modules

| Path | Purpose |
|---|---|
| `scripts/generate_data.py` | Synthetic FIR/CDR/transaction/surveillance corpus with planted patterns |
| `backend/app/ingestion/` | Source parsers producing normalized records |
| `backend/app/nlp/entity_extractor.py` | NER (people/orgs/places) + regex (phones/vehicles/amounts) + alias resolution |
| `backend/app/graph/builder.py` | Multi-source knowledge graph with weighted relations |
| `backend/app/graph/analytics.py` | PageRank/betweenness influencers, Louvain cells, rule-based alerts |
| `backend/app/api/routes.py` | REST API for graph, profiles, and alerts |
| `frontend/index.html` | Interactive network dashboard |

## Planted ground-truth patterns (demo dataset)

- **Bridge node**: a launderer connecting two otherwise separate gangs (hidden link)
- **Structuring**: repeated cash deposits just below the ₹50k reporting threshold
- **Layering**: rapid multi-hop fund movement within hours
- **Night-call burst**: frequent 00:00–05:00 calls between conspirators

> Synthetic data only. All names, numbers, and events are fictional.
# SIH
# SIH
