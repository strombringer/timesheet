FROM alpine:latest AS build-env

#COPY . /app

WORKDIR /data

RUN apk add poppler-utils

CMD ["sh", "-c", "pdftotext -layout input.pdf -"]
#CMD ["ls", "-al"]