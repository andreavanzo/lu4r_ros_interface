# lu4r\_ros\_interface

This package contains the ROS node that enables for the communcation between the [LU4R system](http://sag.art.uniroma2.it/sluchain.html "Go to the LU4R web page") and ROS. It is actually an orchestrator between the robot, the Android application (for Automatic Speech Recognition) and LU4R. It communicates with the Android application, acting as a Server. Once the list of transcriptions is received from the Android app, it is forwarded to LU4R.

The LU4R ROS interface is in charge of receiving the list of transcriptions from an external ASR (e.g., the LU4R Android app, here) and forward it to LU4R. In order to launch the node, you need ROS in your Linux machine. Once the ROS installation is completed, place the provided ROS package lu4r_ros_interface in your catkin_ws/src folder. Then, run

`roscore`

to start the ROS master. The ROS node can be finally launched through the following command:

`rosrun lu4r_ros_interface android_interface _port:=[port] _lu4r_ip:=[lu4r_ip_address] _lu4r_port:=[lu4r_port] _semantic_map:=[semantic_map]`

where:

* `_port`: the listening port of the LU4R ROS interface. This is required by the Android app, enabling a TCP connection between them.
* `_lu4r_ip_address`: the ip address of LU4R. If the LU4R and the LU4R ROS interface are on the same machine, ignore this argument.
* `_lu4r_port`: the listening port of LU4R.
* `_semantic_map`: the semantic map to be employed, among the ones available into semantic_maps. The semantic maps are in JSON format, and represent the configuration of the environment (e.g., objects, locations,...) in which the robot is operating. Whenever a simple configuration of LU4R is chosen, the interpretation process is sensitive to different semantic maps.

For more information, please visit the [LU4R system](http://sag.art.uniroma2.it/sluchain.html "Go to the LU4R web page") website.