
# Exercise submission checker

This project is a web server for students to upload, build and execute programming tasks in C++,Python, Java etc.

The server runs in a Docker container, on a linux host.

It is developed as a small scale alternative to [CodeRunner](https://moodle.org/plugins/qtype_coderunner) .
#### Maturity: In development, pre alpha.

# Getting Started
<b>TODO</b> -- add content <br>

For support, send mail to the repository maintainer

## System Requirements
- ubuntu 18.04
- docker
- ssh access (for management and file uploading) 
## Installing

on the server that will run the checker:
* install docker: ```sudo apt install docker```
* clone the repo and cd into it
* create required directories:
  ```mkdir -p $HOME/data/logs```
  ## First time installation
  Currently need to manually build the dependency images:
  ```
  docker build -t python_cmake_base -f Dockerfile_base .
  docker build -t py_java_cpp_base -f Dockerfile_py_java_cpp_base .
  ```
  
## 

* build the docker container:
```docker build -t server . ```
* run the server in a new container:
```./scripts/run_docker.sh server ```
* check that the server is up by accessing http://\<server IP>/


# Running tests of the server
TBD

#Contributing
 use pull requests in github

# Instructions for the Tutor
As the tutor, you have to prepare:
- code that will execute the program
- code that verify the output is correct
    - _hint_: https://regex101.com/
- input data (the input test vector)
- output data (the output for the input for a correct solution)
    - optionally, another input and output tagged GOLDEN 


These coding parts are called __runner__ and __matcher__ (aka comparator)

Choosing the runner and matcher is done by reading a configuration file (located at {rootdir}/hw_settings.json)

You can see the current content in ```host_address/admin/show_ex_config```
   
Modifying/adding values is by uploading a new version of the file (in the admin page)
  

For example,
- in ex 1, a C/C++ program, exact text match is needed
- in ex 2, a Python program, there is a complicated scenario that requires regular expression.

The config file json will look like:
```
{
"94201":
 [ {
     "id": 1,
     "matcher" : "exact_match.py",
     "runner" :"check_cmake.sh",
     "timeout" : 5
   },
   {
     "id": 2,
     "matcher" : "tester_ex2.py",
     "runner" :"check_py.sh",
     "timeout" : 20
    }
 ]
}
```    


## Uploading data to the server
Use ssh and put the data files e.g. ```ref_hw_3_input``` in $HOME/data<br>
It will be mapped into the server's file system. 
<br>

## Using the correct runner
Depending on the assignment, choose an existing runner or write a new one.<br>
The runners are bash scripts that are run in a shell (for security) and accepts as arguments
the filename of the tested code, input data file, reference output file and matcher file name.<Br>
The script return 0 for success. <br>
NOTE: Comparison is done by running the matcher from within the runner script.
This will be changed in a future version.

These runners are already implemented:
  - check_cmake.sh: run cmake, make and execute the executable found.
  - check_py.sh: run the file ```main.py``` in the supplied archive
   (or just this file if no archive is used)
  - check_sh.sh: run the file using bash
   
     
## Adding/Modifying matcher
All matchers are written in Python3. 

Before writing a new one, check the existing scripts  - maybe you can use one of them as a baseline.
1. save the new ```tester.py``` in ```serverpkg.matchers``` dir.<br>
    The script must implement ```check(output_from_test_file_name,reference_file_name)``` <br>
    and return True if the files are considered a match.<br>
    For example ```def check(f1,ref): return True```<br>
    <strong>currently, you need to implement</strong> <br>
    <pre>
    if __name__ == "__main__":
        good = check(sys.argv[1], sys.argv[2])
        exit(0 if good else ExitCode.COMPARE_FAILED) </pre> 
    
2. Update the config file by uploading an updated version.<br>
    The current config can be seen at http://your-host/admin/show_ex_config, <br>
    and uploading from the admin page at http://your-host/admin
3. build a new Docker container, stop the current one, start the new one:
```
$ ssh myhost
(myhost) $ cd checker
(myhost) $ git pull
(myhost) $ cd scripts && ./again.sh
```

# Running the web application
The webapp runs as a Docker container.<br>
First, build the container: (in the project root directory)
> docker build **.** -t server:<current_tag>
 
then run it
> cd scripts && ./run_docker.sh server

OR - if you just want to build - stop - start fresh again:
> cd scripts &&  ./again.sh


# Reliability
I created a monitoring account that checks the server every couple minutes and send me email if the server is down. 

There is known problem that occasionally the server hangs.
 In such a case, ssh to the host, and execute ```scripts/restart_container.sh```
#Security
* The Docker container runs as user _nobody_, who has minimal privilages.
* The submitted code is run in a subprocess with limitations on
  * execution time (for each exercise we set a timeout value)
  * network connectivity (not implemented yet)
    
# Debugging
During development, it is easier to run only the python code without Docker:
 ``` 
 cd ~/checker
 source venv/bin/activate
 python3 run.py
  ```
  
  ## gunicorn
  To run with gunicorn (one step closer to the realworld configuration):
  ```
  cd ~/checker
  source venv/bin/activate
  gunicorn3 -b 0.0.0.0:8000 --workers 3 serverpkg.server:app
```
