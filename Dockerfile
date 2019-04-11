FROM ubuntu:18.04
MAINTAINER Noam Cohen "cnoam@technion.ac.il"
RUN apt update -y && \
 apt install -y python-pip python-dev build-essential && \
 apt install -y cmake g++

copy . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 8000
# when running 'docker run' make sure to map the ports such as
# docker run -p80:8000 cf9
CMD ["gunicorn", "-b", "0.0.0.0:8000", "server:app"]