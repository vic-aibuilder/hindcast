# Hindcast

Hindcast is an internal Snarkitecture tool that takes a design brief and returns a
structured reading of what's visually saturated in that context — the moves everyone is
making, the overused defaults, the open ground where contrast lives. It is the opposite
of a trend forecast.

**Vertical:** brand and retail
**Sub-slices:** sneaker/streetwear · contemporary fashion (elevated/designer)
**City:** New York City, all five boroughs
**Time window:** 2025–present

## How it works

1. User submits a brief (sub-slice + free-text).
2. A retrieval agent queries Tavily and Are.na, augmenting a pre-built seed corpus.
3. Claude extracts schema attributes from each retrieved image.
4. Claude synthesizes 4–6 named saturation patterns from the aggregated data.
5. Output: image grid with editorial framing.

## Docs

- [PRD.md](PRD.md) — full product and engineering spec
- [ARCHITECTURE.md](ARCHITECTURE.md) — system design
- [AGENTS.md](AGENTS.md) — agent roles and loop logic
- [docs/schema.md](docs/schema.md) — definition layer (Schema v2.2)
- [ROADMAP.md](ROADMAP.md) — build sequencing and timeline

## Quickstart

_Placeholder — fill in once the pipeline exists._

```bash
cp .env.example .env
# populate .env with your keys
pip install -r requirements.txt
pytest
```

## Team

Christian · Gary · Victor
Partner: Snarkitecture — Alex Mustonen
