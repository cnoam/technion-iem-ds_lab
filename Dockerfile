FROM  py_java_cpp_base  
MAINTAINER Noam Cohen "cnoam@technion.ac.il"
# install packages before copying the sources so they are cached in the next runs of docker-build
# but must copy the requirements.txt to be sure it is fresh
# current dir is /tmp
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt && rm requirements.txt
RUN apt-get update && apt-get install -y jq
COPY . /app
WORKDIR /app
EXPOSE 8000
# when running 'docker run' make sure to map the ports such as
# docker run -p80:8000 cf9
CMD ["gunicorn", "-b", "0.0.0.0:8000", "--workers", "3", "serverpkg.server:app"]


