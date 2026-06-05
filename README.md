# sportsdata
Sports data models and samples

## Layout

The repository keeps model values as JSON so the same source can be loaded by web selectors and Python validators.

```text
models/
  catalogs/      Fixed and generated selector values.
  derivations/   Recipes used to build dynamic values from fixed catalogs.
  schemas/       JSON structure checks by common area and sport.
  formats/       File-format declarations.
  rules/         Semantic validation rule descriptions.
python/          Dependency-free Python loaders and validators.
web/src/         Small TypeScript helpers for loading catalogs and schemas.
samples/         Valid sample files used by tests.
tests/           Unit tests for catalogs, derivations, schemas, and rules.
```

## Model Flow

Fixed catalogs live under `models/catalogs/<scope>/`. Dynamic catalogs are generated from recipes under `models/derivations/`.

For example, swimming events are derived from stroke, sex, distance, and round catalogs:

```text
models/derivations/swimming/events.recipe.json
  -> models/catalogs/swimming/generated/events.json
```

Regenerate the swimming event selector catalog with:

```sh
PYTHONPATH=python python3 -m sportsdata_models.derivations
```

## Validation

The Python validators run structural schema checks and sport-specific semantic checks.

```sh
PYTHONPATH=python python3 -m sportsdata_models.validators.cli \
  samples/swimming/valid/2024-JO_Paris_freestyle_hommes_100_finaleA.json \
  samples/table-tennis/valid/flat_match.json
```

For applications outside this checkout, set `SPORTSDATA_MODELS_ROOT` to the `models/` directory before loading catalogs or validators.

## Tests

Run the test suite with:

```sh
python3 -m unittest
```
