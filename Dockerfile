FROM  python:3.6-stretch
MAINTAINER Noam Cohen "cnoam@technion.ac.il"
RUN apt update -y && \
 apt install -y build-essential && \
 apt install -y cmake g++

# upgrade cmake 
WORKDIR /tmp
ADD https://github.com/Kitware/CMake/releases/download/v3.14.2/cmake-3.14.2-Linux-x86_64.sh  /tmp
RUN  chmod +x cmake-3.14.2-Linux-x86_64.sh && ./cmake-3.14.2-Linux-x86_64.sh --skip-license
ENV PATH="/tmp/bin:${PATH}"
#
RUN echo "export PATH=$PATH"

copy . /app
WORKDIR /app
RUN pip3 install --no-cache-dir -r requirements.txt
EXPOSE 8000
# when running 'docker run' make sure to map the ports such as
# docker run -p80:8000 cf9
CMD ["gunicorn", "-b", "0.0.0.0:8000", "--threads", "2", "server:app"]


