lazygit() {
	if [ "$1" = "--amend" ]; then
		if [ "$2" = "--message" ] || [ "$2" = "-m" ]; then
			git add .
			git commit --amend -m "$3"
		else
			git add .
			git commit --amend
		fi
		git push --force
	elif [ "$1" = "--fixup" ]; then
		git add .
		git commit --fixup HEAD
		git push
	else
		git add .
		git commit -m "$1"
		git push
	fi
}

# alias sros='source /opt/ros/noetic/setup.bash'
# alias sros='source /opt/ros/noetic/setup.bash && [ -f devel/setup.bash ] && source devel/setup.bash'
# alias kros='killall -9 roscore rosmaster rosout roslaunch rosmaster; rosnode cleanup ; rosnode kill -a ; killall -9 gzclient ; killall -9 gzserver ;'

# ROS
alias sros='source /opt/ros/${ROS_DISTRO}/setup.bash && if [ -f "./install/setup.bash" ]; then source ./install/setup.bash; fi'
# . "$HOME/.local/bin/env"
senv() {
	if [ -f .venv/bin/activate ]; then
		source .venv/bin/activate
	else
		echo "No virtual environment found"
	fi
}
ROS_DISTRO="jazzy"
export QT_QPA_PLATFORM=xcb
alias sros='source /opt/ros/${ROS_DISTRO}/setup.bash && if [ -f "./install/setup.bash" ]; then source ./install/setup.bash; fi'
ccb() {
	colcon build --parallel-workers $(nproc)
}
cros() {
	if [ -n "$1" ]; then
		rm -rf build/"$1" install/"$1" log/"$1"
	else
		rm -rf build install log
	fi
}
kros() {
	echo "Nuking ROS 2 / Gazebo / RViz related processes..."
	# Only kill when pgrep finds PIDs (empty kill -9 can error / touch wrong targets)
	_kros_kill() {
		local p
		p=$(pgrep -f "$1" 2>/dev/null) || true
		[ -n "$p" ] && kill -9 $p 2>/dev/null
	}
	# CLI + common node names (many never contain the substring "ros2" in argv)
	for _pat in \
		'ros2' \
		'apriltag_node' \
		'component_container' \
		'ros2_control_node' \
		'static_transform_publisher' \
		'joint_state_publisher' \
		'robot_state_publisher' \
		'controller_manager' \
		'move_group' \
		'rviz2' \
		'gz sim' \
		'gz_ros' \
		'ros_gz' \
		'foxglove_bridge' \
		'z1_ctrl' \
		'ruby.*gz' \
		'realsense2_camera' \
		'ros-args'; do
		_kros_kill "$_pat"
	done
	# Installed ROS nodes: full path in argv is typical (catches stragglers like apriltag_node)
	if [ -n "${ROS_DISTRO:-}" ]; then
		_kros_kill "/opt/ros/${ROS_DISTRO}/lib/"
	fi
	ros2 daemon stop 2>/dev/null || true
	echo "Done."
}
sros

# NVIDIA Omniverse
ssim() {
	# Strip everything sros (and /opt/ros/jazzy/setup.bash) injected
	unset ROS_DISTRO ROS_VERSION ROS_PYTHON_VERSION ROS_LOCALHOST_ONLY \
		ROS_DOMAIN_ID AMENT_PREFIX_PATH COLCON_PREFIX_PATH \
		CMAKE_PREFIX_PATH ROS_AUTOMATIC_DISCOVERY_RANGE \
		RMW_IMPLEMENTATION _colcon_cd_root

	# Scrub PATH, LD_LIBRARY_PATH, PYTHONPATH, PKG_CONFIG_PATH of any /opt/ros entries
	_strip_ros() {
		echo "$1" | tr ':' '\n' | grep -v '/opt/ros/' | grep -v '^$' | paste -sd: -
	}
	export PATH=$(_strip_ros "$PATH")
	export LD_LIBRARY_PATH=$(_strip_ros "${LD_LIBRARY_PATH:-}")
	export PYTHONPATH=$(_strip_ros "${PYTHONPATH:-}")
	export PKG_CONFIG_PATH=$(_strip_ros "${PKG_CONFIG_PATH:-}")
	unset -f _strip_ros

	# Source Isaac Sim's 3.11 Jazzy underlay + overlay
	local ISAAC_WS=~/IsaacSim-ros_workspaces/build_ws/jazzy
	source "$ISAAC_WS/jazzy_ws/install/setup.bash"
	source "$ISAAC_WS/isaac_sim_ros_ws/install/setup.bash"

	# Sanity check
	echo "ROS env now points at:"
	echo "  AMENT_PREFIX_PATH=$AMENT_PREFIX_PATH" | tr ':' '\n' | head -5
	python3 -c "import sys; print(f'  python: {sys.version.split()[0]}')" 2>/dev/null

	# Launch Isaac Sim (source build in workspace)
	# cd "$HOME/IsaacSim/_build/linux-x86_64/release" && ./isaac-sim.sh
}
alias isaacsim_custom='cd "$HOME/IsaacSim_5.1.0/_build/linux-x86_64/release" && ./isaac-sim.sh'

senvi() {
	export LD_LIBRARY_PATH=./env_isaaclab/lib/python3.11/site-packages/nvidia/cu13/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}

	source ./env_isaaclab/bin/activate
}

# For reference
kros() {
	echo "Nuking ROS 2 / Gazebo / RViz and related processes..."
	# Only kill when pgrep finds PIDs (empty kill -9 can error / touch wrong targets)
	_kros_kill() {
		local p
		p=$(pgrep -f "$1" 2>/dev/null) || true
		[ -n "$p" ] && kill -9 $p 2>/dev/null
	}
	# CLI + common node names (many never contain the substring "ros2" in argv)
	for _pat in \
		'ros2' \
		'rqt' \
		'launch_ros' \
		'component_container' \
		'component_container_mt' \
		'composable_node' \
		'ros2_control_node' \
		'controller_manager' \
		'spawner' \
		'robot_state_publisher' \
		'joint_state_publisher' \
		'joint_state_broadcaster' \
		'static_transform_publisher' \
		'move_group' \
		'moveit' \
		'move_group_.*moveit' \
		'servo_node' \
		'rviz2' \
		'rviz' \
		'apriltag_node' \
		'aruco' \
		'image_proc' \
		'depth_image_proc' \
		'image_transport' \
		'stereo_image_proc' \
		'pointcloud_to_laserscan' \
		'realsense2_camera' \
		'v4l2_camera' \
		'camera_ros' \
		'gz sim' \
		'gz_ros' \
		'gz_ros2_control' \
		'ros_gz' \
		'ros_gz_bridge' \
		'ros_gz_image' \
		'ros_gz_sim' \
		'gzclient' \
		'gzserver' \
		'ign gazebo' \
		'ignition-gazebo' \
		'ruby.*gz' \
		'gazebo_ros' \
		'gazebo_ros2' \
		'foxglove_bridge' \
		'rosbridge' \
		'rosapi' \
		'ros1_bridge' \
		'topic_tools' \
		'zenoh-bridge-ros' \
		'bt_navigator' \
		'planner_server' \
		'controller_server' \
		'smoother_server' \
		'behavior_server' \
		'waypoint_follower' \
		'lifecycle_manager' \
		'amcl' \
		'collision_monitor' \
		'velocity_smoother' \
		'docking_server' \
		'route_server' \
		'gps_waypoint_follower' \
		'slam_toolbox' \
		'cartographer' \
		'map_server' \
		'map_saver' \
		'ekf_node' \
		'ekf_localization_node' \
		'navsat_transform' \
		'robot_localization' \
		'teleop_twist' \
		'twist_mux' \
		'joy_node' \
		'interactive_markers' \
		'z1_ctrl' \
		'webots_ros2' \
		'ros-args'; do
		_kros_kill "$_pat"
	done
	# Installed ROS nodes: full path in argv is typical (catches stragglers like apriltag_node)
	if [ -n "${ROS_DISTRO:-}" ]; then
		_kros_kill "/opt/ros/${ROS_DISTRO}/lib/"
	fi
	# Also sweep workspace install prefixes from typical colcon layouts (colon-separated)
	if [ -n "${COLCON_PREFIX_PATH:-}" ]; then
		IFS=: read -r -a _kros_ws <<<"${COLCON_PREFIX_PATH}"
		for _ws in "${_kros_ws[@]}"; do
			[ -n "$_ws" ] && _kros_kill "${_ws}/lib/"
		done
	fi
	# Clean up any leftover ROS2 daemon (stale graph cache)
	ros2 daemon stop 2>/dev/null || true
	echo "Done."
}
sros

# KEEP THIS FOR REFERENCE
# kros() {
# 	echo "Nuking ROS 2 / Gazebo / RViz related processes..."
# 	# Only kill when pgrep finds PIDs (empty kill -9 can error / touch wrong targets)
# 	_kros_kill() {
# 		local p
# 		p=$(pgrep -f "$1" 2>/dev/null) || true
# 		[ -n "$p" ] && kill -9 $p 2>/dev/null
# 	}
# 	# CLI + common node names (many never contain the substring "ros2" in argv)
# 	for _pat in \
# 		'ros2' \
# 		'apriltag_node' \
# 		'component_container' \
# 		'ros2_control_node' \
# 		'static_transform_publisher' \
# 		'joint_state_publisher' \
# 		'robot_state_publisher' \
# 		'controller_manager' \
# 		'move_group' \
# 		'rviz2' \
# 		'gz sim' \
# 		'gz_ros' \
# 		'ros_gz' \
# 		'foxglove_bridge' \
# 		'z1_ctrl' \
# 		'ruby.*gz' \
# 		'realsense2_camera' \
# 		'ros-args' \
# 		; do
# 		_kros_kill "$_pat"
# 	done
# 	# Installed ROS nodes: full path in argv is typical (catches stragglers like apriltag_node)
# 	if [ -n "${ROS_DISTRO:-}" ]; then
# 		_kros_kill "/opt/ros/${ROS_DISTRO}/lib/"
# 	fi
# 	ros2 daemon stop 2>/dev/null || true
# 	echo "Done."
# }

gsettings set org.gnome.desktop.interface enable-animations false

# WSL graphics settings
export MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
export MESA_NO_VULKAN=1
# export MESA_LOADER_DRIVER_OVERRIDE=iris
# export MESA_LOADER_DRIVER_OVERRIDE=d3d12

# export DISPLAY=$(ip route list default | awk '{print $3}'):0
# export DISPLAY=:0

export LIBGL_ALWAYS_SOFTWARE=1
# unset LIBGL_ALWAYS_SOFTWARE

# export LIBGL_ALWAYS_INDIRECT=1
# export LIBGL_ALWAYS_INDIRECT=0
