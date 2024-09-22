# First stage: getting Python dependencies
FROM python:alpine3.19 AS compiler
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN python -m venv /opt/venv
# Enable venv
ENV PATH="/opt/venv/bin:$PATH"

COPY ./requirements.txt /app/requirements.txt
RUN pip install -Ur requirements.txt

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

CMD ["sh", "-c", "for f in /data/*.pdf; do pdftotext -layout \"$f\" - | python ./process_timesheet.py -q ${TIMESHEET_QUOTA} -d ${TIMESHEET_DATEFORMAT} -f ${TIMESHEET_FORMAT}; done"]