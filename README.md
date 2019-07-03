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
# Running the tests
TBD
#Contributing
 use pull requests

# Instructions for the Tutor
As the tutor, you have to prepare:
- code that will execute the program
- code that verify the output is corret
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


TODO

Running the web application
The webapp runs as a Docker container.
First, build the container:
docker build . -t server:<current_tag> 
then run it
./run_docker <the ID you just created>

