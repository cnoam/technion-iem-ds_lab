On the server that will run the checker:
* install ubuntu 18.04 (tested only with this build)
* install the server:
```
git clone https://github.com/cnoam/technion-iem-ds_lab.git checker
cd checker
./install.sh
```

After successful completion, 
```
cd /checker_data/data/96224
copy spark_key into this folder (the private key)
```
* run the server in a new container:
```cd scripts && ./run_docker.sh```
* check that the server is up by accessing http://server-IP/
