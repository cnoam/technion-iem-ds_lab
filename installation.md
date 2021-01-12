On the server that will run the checker:
* install ubuntu 18.04 (tested only with this build)
* install the server:
```
git clone https://github.com/noam1023/technion-iem-ds_lab.git checker
cd checker
./install.sh
```
* run the server in a new container:
```cd scripts && ./run_docker.sh server ```
* check that the server is up by accessing http://server-IP/
