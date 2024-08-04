# Timesheet analysis for Work from Home percentage

Simple Docker container that outputs the Work From Home percentage for each timesheet pdf in a folder.

## How to use it

### Run Docker container from Dockerhub

Run the docker container from within the folder that contains your timesheet pdfs:

Unix/MacOS:

```bash
docker run -t -v $(pwd):/data strombringer/timesheet
```

Windows:

```bash
docker run -t -v ${pwd}:/data strombringer/timesheet
```

The `-t` parameter is only needed for the highlighting of the current home office quota. Skip it, if you don't need that.

#### Parameters (WIP - currently only usable directly with the Python script)

|Name|Default|Description|
|--|--|--|
| quota | 70 | Home Office quota |
| dateformat | %d.%m.%Y | Date format of the dates in the first line of the input files (e.g. 01.07.2024|
| format | text \| json | text = nicely formatted report table, json = all values of the report as a json document|

## Contributing

### Build Docker image locally

```bash
docker build -t timesheet:latest .
```

## Debugging

If the output is not what you expect, run the included commands one by one.

### Requirements

You need `pdftotext`, which you can install on Linux with

```bash
apt-get install poppler-utils
```

and MacOS with

```bash
brew install poppler
```

You also need the Python packages listed in `requirements.txt`

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -Ur requirements.txt
```

### Option 1

Run the file `input.pdf` through `pdftotext` and write the result to `output.txt`

```bash
pdftotext -layout input.pdf output.txt
```

Pipe `output.txt` through the python script

```bash
cat output.txt | python process_timesheet.py
```

### Option 2

Output pdftotext to stdout and pipe that directly through the Python script:

```bash
pdftotext -layout input.pdf - | python process_timesheet.py
```

## Examples

### Pretty-printed json with jq

```bash
cat output.txt | python process_timesheet.py -f json | jq .
```