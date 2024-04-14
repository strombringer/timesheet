FROM python:alpine3.19 AS build-env

COPY process_timesheet.py /app/

WORKDIR /data

RUN apk add poppler-utils

CMD ["sh", "-c", "for f in ./*.pdf; do pdftotext -layout \"$f\" - | python /app/process_timesheet.py; done"]