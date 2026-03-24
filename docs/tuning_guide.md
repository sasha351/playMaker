# Tuning Guide

## Default Weights

| Metric             | Default | Description                                      |
|--------------------|---------|--------------------------------------------------|
| bpm_smoothness     | 0.35    | Penalises large BPM jumps between tracks         |
| energy_coherence   | 0.35    | How well energy follows the expected curve       |
| genre_consistency  | 0.20    | Fraction of tracks matching the dominant genre   |
| transition_score   | 0.10    | Composite BPM + energy transition quality        |

## Rating-Based Tuning

After generating a playlist, rate it 1–5 stars. The auto-tuner nudges weights:

- Rating 5 → weights increased (positive reinforcement)
- Rating 3 → no change
- Rating 1 → weights decreased

## A/B Tuning

Run two different configurations and pick the winner. The winning config's weights
are reinforced, and the losing config's weights are penalised.

## Saving Profiles

```bash
# Dump current weights
dj tune --dump-weights > my_weights.json

# Apply a TOML suggestions file
dj tune --apply suggestions.toml
```

Profiles are stored at `~/.localdj/profiles/<name>.json`.
