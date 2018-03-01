# WASP Software Engineering and Cloud Computing - Cloud Computing Assignment
A cloud service designed to take user video conversion requests, and converts them to a predefined video format.

## Set up
The user requests are sent to the frontend, which in turn places them on a queue supported by a RabbitMQ server. The backend, which is reliable for the video conversion, gets assigned the requests from the queue and processes the requests and uploads the converted video file.

The frontend, backend, and the rabbitMQ are all hosted on separate virtual machines (VMs).

### Front end
To start a frontend VM simply run

`$ ./start_frontend.sh`

This command will create a VM on the Cloud and install the required packages the frontend needs for the service.
