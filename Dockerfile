FROM  python_cmake_base
MAINTAINER Noam Cohen "cnoam@technion.ac.il"

copy . /app
WORKDIR /app
RUN pip3 install --no-cache-dir -r requirements.txt
EXPOSE 8000
# when running 'docker run' make sure to map the ports such as
# docker run -p80:8000 cf9
CMD ["gunicorn", "-b", "0.0.0.0:8000", "--threads", "2", "server:app"]


