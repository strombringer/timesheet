# Timesheet analysis for Work from Home percentage

Simple Docker container that outputs the Work From Home percentage for each timesheet pdf in a folder.

## How to use it

### Build Docker image

```
docker build -t timesheet:latest .
```

### Run Docker container

Assuming you're on a Windows machine and are in the folder that contains your timesheet pdfs:
```
docker run -v ${pwd}:/data timesheet
```

## Debugging

If the output is not what you expect, run the included commands one by one.

You need `pdftotext`, which you can install on Linux with

```
apt-get install poppler-utils
```

and MacOS with

```
brew install poppler
```

### Option 1

Run the file `input.pdf` through `pdftotext` and write the result to `output.txt`
```
pdftotext -layout input.pdf output.txt
```

Pipe `output.txt` through the python script

```
cat output.txt | python process_timesheet.py
```

### Option 2

Output pdftotext to stdout and pipe that directly through the Python script:

```
pdftotext -layout input.pdf - | python process_timesheet.py
```
