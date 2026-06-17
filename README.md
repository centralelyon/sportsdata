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

### ALEXIS_ Table Tennis Files

Table tennis match data follows a naming convention using player names: `ALEXIS-LEBRUN_vs_FAN-ZHENDONG_*`. Each match consists of four related files:

#### 1. Game Metadata JSON (`*_game.json`)

Contains match-level information such as player names, handedness, grips, event type, and creation metadata.

**Required fields:**
- `playerA`, `playerB`: Player names (string)
- `droitier_gaucher_joueurA`, `droitier_gaucher_joueurB`: Handedness - `droitier` (right-handed) or `gaucher` (left-handed)
- `prise_joueurA`, `prise_joueurB`: Grip type (string, e.g., `europeenne`)
- `date`: Match date in ISO 8601 format (YYYY-MM-DD)
- `epreuve`: Event type (string, e.g., `simple`)
- `fps`: Frames per second (number)

#### 2. Table Info JSON (`*_infos_table.json`)

Contains table detection metadata including corners, colors, and media paths.

**Required fields:**
- `x1-x4`, `y1-y4`: Table corner coordinates (numbers)
- `couleur_mediane_r/g/b`: Median table color RGB values (0-255)
- `couleur_moyenne_r/g/b`: Average table color RGB values (0-255)
- `perimetre`: Table perimeter in pixels (number)
- `aire`: Table area in pixels (number)
- `match`: Match identifier (string)
- `competition`: Competition name (string)
- `chemin_image`: URL or path to full table image
- `chemin_image_projetee`: URL or path to top-down projection image
- `chemin_image_projetee_cote`: URL or path to side projection image

#### 3. Perspective JSON (`*_perspective.json`)

Contains calibration and homography data for 3D perspective mapping.

**Structure:**
- `calibration.srcPct1`: Array of 4 source points with x/y coordinates as percentages (0-100)
- `calibration.destPct1`: Array of 4 destination points with x/y coordinates as percentages
- `homography.srcPts`: Array of 4 source points in pixels
- `homography.destPts`: Array of 4 destination points in pixels

#### 4. Annotation CSV (`*_annotation.csv`)

Contains shot-level annotations with player actions and ball tracking.

**Required columns:**
- `nom`: Player name (string)
- `debut`, `fin`: Frame range (integers)
- `genre`: Player gender (string, e.g., `garcon`, `fille`)
- `lateralite`: Shot handedness (`coup_droit`, `revers`, etc.)
- `set`: Set number (integer, 1-based)
- `systeme`: System classification (string, e.g., `att/att`)
- `coup`: Shot type or player identifier (string)
- `type_service`: Service type if applicable (string, optional)
- `type_coup`: Shot classification (string, optional)
- `zone_jeu`: Game zone (string, e.g., `g1`, `m2`, `d3`)
- `faute`: Fault or point outcome (string, optional)
- `effet_coup`: Shot spin/effect (string, optional)
- `coor_balle_x/y/z`: Ball coordinates at contact (numbers)
- `joueur_frappe`: Player executing the shot (string)
- `joueur_sur`: Opponent/player receiving (string)
- `coor_frappe_x/y/z`: Racket/hand coordinates at contact (numbers)
- `time_frappe`: Frame time (integer)
- `premier_rebond_x/y/z`: First bounce coordinates (numbers, optional)
- `time_premier_rebond`: First bounce frame time (integer, optional)
- `probleme_annotation`: Annotation issues (string, optional)

**Validation example:**

Validate individual basic files by file type:

```sh
PYTHONPATH=python python3 -m sportsdata.validators.cli \
  samples/table-tennis/valid/basic_game.json
```

Validate basic table-tennis samples together:

```sh
cd /Users/rvuillem/dev/sportsdata
PYTHONPATH=python python3 -m sportsdata.validators.cli \
  samples/table-tennis/valid/basic_game.json \
  samples/table-tennis/valid/basic_tracking.csv \
  samples/table-tennis/valid/flat_match.json
```

Command:

```sh
PYTHONPATH=python python3 -m sportsdata.validators.cli samples/table-tennis/valid/basic_game.json
```

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
