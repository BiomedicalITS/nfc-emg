docker run --network=host -p 50001-50004:50001-50004 --rm -it --name ur5e ros2/ur5e bash
# ros2 launch ur_robot_driver ur_control.launch.py ur_type:=ur5e robot_ip:=172.22.22.1 use_fake_hardware:=true launch_rviz:=true