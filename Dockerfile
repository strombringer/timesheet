# First stage: getting Python dependencies
FROM python:alpine3.19 AS compiler
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# numpy wants this now for some reason
RUN apk update && apk add --virtual build-dependencies build-base gcc

RUN python -m venv /opt/venv
# Enable venv
ENV PATH="/opt/venv/bin:$PATH"

COPY ./requirements.txt /app/requirements.txt
RUN pip install -Ur requirements.txt

# delete the build dependencies again
RUN apk del build-dependencies

# Second stage: copy venv with python dependencies from first stage and install pdftotext tool
FROM python:alpine3.19 AS runner
WORKDIR /app
COPY --from=compiler /opt/venv /opt/venv

RUN apk add poppler-utils

# Enable venv
ENV PATH="/opt/venv/bin:$PATH"
COPY process_timesheet.py /app/

ENV TIMESHEET_QUOTA="70"
ENV TIMESHEET_DATEFORMAT="%d.%m.%Y"
ENV TIMESHEET_FORMAT="text"
ENV TIMESHEET_VACATION=""

CMD ["sh", "-c", "for f in /data/*.pdf; do pdftotext -layout \"$f\" - | python ./process_timesheet.py -q ${TIMESHEET_QUOTA} -d ${TIMESHEET_DATEFORMAT} -f ${TIMESHEET_FORMAT} -v ${TIMESHEET_VACATION}; done"]