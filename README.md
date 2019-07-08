_note:_  This repo can contain anything relevant for the DS lab that can be made **public**

# Exercise submission checker

This project is a web server for students to upload, build and execute programming tasks in C++ and Python.

The server runs in a Docker container, on a linux host.

It is developed as a small scale alternative to [CodeRunner](https://moodle.org/plugins/qtype_coderunner) .
#### Maturity: In development, pre alpha.

# Getting Started
TBD
## Prerequisites
- ubuntu 18.04
- docker
- ssh access (for management and file uploading) 
## Installing
TBD
# Running tests of the server
TBD
#Contributing
 use pull requests

# Instructions for the Tutor
As the tutor, you have to prepare:
- code that will execute the program
- code that verify the output is correct
    - _hint_: https://regex101.com/
- input data (the input test vector)
- output data (the output for the input for a correct solution)
    - optionally, another input and output tagged GOLDEN 


These coding parts are called __executor__ and __matcher__ (aka comparator)
###Currently, choosing the  __executor__ and __matcher__ is coded in the source.
##### It will be moved to a config file

For example,
- in ex 1, exact text match is needed
- in ex 3, there is a complicated scenario that requires regular expression.
- in ex 4, the output text needs exact matching but the numberical values have to be rounded to 0.01 before comparing , so 0.6543 and 0.65 are considered equal.

## Uploading data to the server
Use ssh and put the data files e.g. 'ref_hw_3_input' in $HOME/data<br>
It will be mapped into the server's file system. 
<br>

## Modifying executor/matcher
1. put the new ```tester.py``` in the source code dir.
2. modify server.py to use the correct tester.
3. build a new Docker container, stop the current one, start the new one:
> $ ./again.sh


# Running the web application
The webapp runs as a Docker container.<br>
First, build the container:
> docker build **.** -t server:<current_tag>
 
then run it
> ./run_docker.sh <the ID you just created>

OR - if you just want to build - stop - start fresh again:
> ./again.sh


# Reliability
I created a monitoring account that checks the server every couple minutes and send me email if the server is down. 

There is known problem that occasionally the server hangs.
 In such a case, ssh to the host, and execute ```./restart_container.sh```
#Security
* The Docker container runs as user _nobody_, who has minimal privilages.
* The submitted code is run in a subprocess with limitations on
  * execution time (for each exercise we set a timeout value)
  * network connectivity (not implemented yet)
    