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

## Metadata Values

The public Python import is `sportsdata`.

```py
import sportsdata

options = sportsdata.metadata_json_value_options("swimming", "distance")
```

For now, swimming `distance` is the first metadata field wired to external possible values. Its available JSON values come from `centralelyon/sportsdata` at:

```text
models/catalogs/swimming/distances.json
```

The field declaration is stored in `models/metadata/swimming/distance.json`. It points the UI to a selector for `Valeur JSON`, using the distance catalog values:

```text
50, 100, 200, 400, 800, 1500
```

Manual additions or corrections can be made in:

```text
models/catalogs/swimming/distances.overrides.json
```

Use `fixes` to correct an existing value by `id`, and `manualValues` to add a new selectable value.

## Model Flow

Fixed catalogs live under `models/catalogs/<scope>/`. Dynamic catalogs are generated from recipes under `models/derivations/`.

For example, swimming events are derived from stroke, sex, distance, and round catalogs:

```text
models/derivations/swimming/events.recipe.json
  -> models/catalogs/swimming/generated/events.json
```

Regenerate the swimming event selector catalog with:

```sh
PYTHONPATH=python python3 -m sportsdata.derivations
```

## Python Setup

From this repository root, the CLI can be run directly:

```sh
python3 -m sportsdata.validators.cli --help
python3 -m sportsdata.validators.cli --run-tests
```

This repository keeps the implementation packages under `python/`. If another working directory cannot import `sportsdata`, either run from the repository root, prefix commands with `PYTHONPATH=python`, or install the package.

Run without installation from the repository root:

```sh
PYTHONPATH=python python3 -m sportsdata.validators.cli --help
```

To run `python3 -m sportsdata.validators.cli` without `PYTHONPATH`, install the package in your active environment once:

```sh
python3 -m pip install -e .
python3 -m sportsdata.validators.cli --help
```

Editable installs also provide the shorter console command:

```sh
sportsdata-validate --help
```

## Validation

The Python validators run structural schema checks and sport-specific semantic checks for JSON and CSV sports data files.

```sh
PYTHONPATH=python python3 -m sportsdata.validators.cli \
  samples/swimming/valid/2024-JO_Paris_freestyle_hommes_100_finaleA.json \
  samples/table-tennis/valid/flat_match.json
```

Validate the full swimming tracking CSV example with an explicit format:

```sh
PYTHONPATH=python python3 -m sportsdata.validators.cli \
  --format swimming-tracking-csv \
  samples/swimming/valid/exemple_annotation_ligne_5_cycles.csv
```

The same format can also be addressed by its declaration id:

```sh
PYTHONPATH=python python3 -m sportsdata.validators.cli \
  --format formats.csv.swimming-tracking \
  samples/swimming/valid/exemple_annotation_ligne_5_cycles.csv
```

The basic swimming tracking CSV can be detected from its header:

```sh
PYTHONPATH=python python3 -m sportsdata.validators.cli \
  samples/swimming/valid/basic_tracking.csv
```

For swimming tracking CSVs, `eventId` is an annotation event id such as `dive`, `cycle`, or `finish` from `models/catalogs/swimming/annotation-events.json`.

For applications outside this checkout, set `SPORTSDATA_MODELS_ROOT` to the included repository's `models/` directory and put the included repository's `python/` directory on `PYTHONPATH` before loading catalogs or validators.

```sh
SPORTSDATA_REPO_ROOT=/path/to/external-repo/vendor/sportsdata \
SPORTSDATA_MODELS_ROOT=/path/to/external-repo/vendor/sportsdata/models \
PYTHONPATH=/path/to/external-repo/vendor/sportsdata/python \
python3 -m sportsdata.validators.cli \
  --format swimming-tracking-csv \
  /path/to/external-repo/data/exemple_annotation_ligne_5_cycles.csv
```

## Tests

Run the test suite with:

```sh
PYTHONPATH=python python3 -m sportsdata.validators.cli --run-tests
```

You can also run `unittest` directly:

```sh
PYTHONPATH=python python3 -m unittest
```

From an external repository that includes this repository under `vendor/sportsdata`, run:

```sh
cd /path/to/external-repo
SPORTSDATA_REPO_ROOT=$PWD/vendor/sportsdata \
SPORTSDATA_MODELS_ROOT=$PWD/vendor/sportsdata/models \
PYTHONPATH=$PWD/vendor/sportsdata/python \
python3 -m sportsdata.validators.cli --run-tests
```
