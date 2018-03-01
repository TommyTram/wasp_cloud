# WASP Software Engineering and Cloud Computing - Cloud Computing Assignment
A cloud service designed to take user video conversion requests, and converts them to a predefined video format.

## Set up
The user requests are sent to the frontend, which in turn places them on a queue supported by a RabbitMQ server. The backend, which is reliable for the video conversion, gets assigned the requests from the queue and processes the requests and uploads the converted video file.

The frontend, backend, and the rabbitMQ are all hosted on separate virtual machines (VMs).

### RabbitMQ

To start a RabbitMQ VM simply run

`$ ./start_rabbitmq.sh`

This command will create  a VM on the Cloud and install the required packages that RabbitMQ needs in order to set up the communcation and a queue.

### Front end
To start a frontend VM simply run

`$ ./start_frontend.sh`

This command will create a VM on the Cloud and install the required packages the frontend needs for the service, and then start the python script under `frontend/frontend.py`.

### Back end
To start a backend VM simply run

`$ ./start_backend.sh`

This command will create a VM on the Cloud and install the required packages the backend needs for the service. The backend VM needs more packages than the frontend VM since it handles the actual processing of the requests. Therefore the startup time here is a bit longer. When the packages have been installed it starts the backend script `backend/backend.py` and awaits video conversion requests.


### Montior
To start the monitor module simply run

`$ python monitor.py`

This will start the monitoring script, where it analyzes the system and decides if the service needs more or less resources (backend VMs). In parallel any logs produced are stored under `logs/`.

### Workload generator
To simulate user requests to the system simply run

`$ python workload_generator.py -c <credentialsFile.txt>`,

where the credentials file corresponds to the settings needed to connect to the RabbitMQ server (please see the cloud tutorial http://wasp-sweden.org/graduate-school/courses/software-engineering-and-cloud-computing/cloud-computing/ for further information). Modifying this script, it is possible to change the user profile over time (how many users are sending requests to the service over time).


### Note
The same credential files created during the tutorial session (http://wasp-sweden.org/graduate-school/courses/software-engineering-and-cloud-computing/cloud-computing/) are needed for this to work

## Getting Started
The experiment we presented in the report we used an initial setup of only one frontend and one backend, together with a RabbitMQ server. To run the experiment presented in the report you will need the following:

RabbitMQ server: `$ ./start_rabbitmq.sh`. Check the IP assigned to the VM and create a `client_credentials.txt` file in the same way it was done in the tutorial session and place it under `wasp_cloud/`.

Frontend: `$ ./start_frontend.sh`

Backend: `$ ./start_backend.sh`

Monitor: `$ python monitor.py`

Note that these processes might take some time to start up first. When everything is up and running start the workload generator

Workload: `$ python workload_generator.py` 

The monitor will continuously print out the status of the queue and the CPU utilization of each backend. During runtime the logs will be written to the folder `logs/`.


