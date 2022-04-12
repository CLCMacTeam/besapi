
FROM ubuntu:latest

# MAINTAINER is deprecated, but I don't know how else to set the `AUTHOR` metadata
MAINTAINER james@jgstew.com

# Labels.
LABEL maintainer="james@jgstew.com"

# https://medium.com/@chamilad/lets-make-your-docker-image-better-than-90-of-existing-ones-8b1e5de950d
LABEL org.label-schema.schema-version="1.0"
LABEL org.label-schema.name="besapi"
LABEL org.label-schema.description="Run besapi REST API CLI for BigFix on Ubuntu:latest"
LABEL org.label-schema.docker.cmd="docker run --rm -it besapi"

# https://docs.docker.com/develop/develop-images/dockerfile_best-practices/
RUN apt-get update && apt-get install -y curl git python3 python3-pip && rm -rf /var/lib/apt/lists/*

WORKDIR /tmp

# install requirements
COPY requirements.txt /tmp/
RUN pip3 install --requirement requirements.txt --quiet
RUN rm -f /tmp/requirements.txt

COPY . /tmp/besapi
WORKDIR /tmp/besapi
RUN python3 ./tests/tests.py
WORKDIR /tmp/besapi/src
# ENTRYPOINT [ "/bin/bash" ]

CMD [ "python3", "-m", "besapi" ]

# Interactive:
#   docker run --rm -it --entrypoint bash besapi
# Run recipe from within Interactive shell
#   python3 -m besapi
