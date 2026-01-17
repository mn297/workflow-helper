#!/usr/bin/env bash
set -e

# ROS 2 Humble deb installation for Ubuntu 22.04 [page:1]
# MoveIt 2 source setup after ROS 2 Humble (Ubuntu 22.04) [page:1]

export ROS_DISTRO=humble # Confirm your ROS distro [attached_file:1]

########################
# Check if ROS 2 is installed
########################
check_ros2_installed() {
	if [ -f "/opt/ros/${ROS_DISTRO}/setup.bash" ]; then
		echo "ROS 2 ${ROS_DISTRO} appears to be installed at /opt/ros/${ROS_DISTRO}/"
		return 0
	else
		echo "ROS 2 ${ROS_DISTRO} is not installed."
		return 1
	fi
}

########################
# Install ROS 2 Humble
########################
install_ros2() {
	echo "=========================================="
	echo "Installing ROS 2 ${ROS_DISTRO}..."
	echo "=========================================="

	########################
	# 1. Locale
	########################
	sudo apt update
	sudo apt install -y locales
	sudo locale-gen en_US en_US.UTF-8
	sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
	export LANG=en_US.UTF-8

	########################
	# 2. Setup ROS 2 apt sources
	########################
	sudo apt install -y software-properties-common
	sudo add-apt-repository -y universe

	sudo apt update
	sudo apt install -y curl
	export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F\" '{print $4}')
	curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb"
	sudo dpkg -i /tmp/ros2-apt-source.deb

	########################
	# 3. Update & upgrade (important!)
	########################
	sudo apt update
	sudo apt upgrade -y # ensure systemd/udev and others are up to date [page:1]

	########################
	# 4. Install ROS 2 Humble
	########################
	# Desktop (RViz, demos, tutorials)
	sudo apt install -y ros-humble-desktop

	# Or, if you prefer minimal:
	# sudo apt install -y ros-humble-ros-base

	# Dev tools (optional but recommended)
	sudo apt install -y ros-dev-tools

	sudo apt install libpoco-dev ros-humble-pinocchio ros-humble-ament-cmake-clang-format clang-format ros-dev-tools libeigen3-dev libfmt-dev ros-humble-xacro
	sudo apt install -y ros-humble-ros2-control ros-humble-ros2-controllers ros-humble-hardware-interface ros-humble-transmission-interface ros-humble-rviz2
	sudo apt install -y ros-humble-controller-interface ros-humble-realtime-tools ros-humble-ros2-control ros-humble-ros2-controllers
	sudo apt install python-catkin-pkg python3-sphinx python3-sphinx-autodoc-typehints python3-sphinx-rtd-theme ros-humble-vision-msgs ros-humble-ackermann-msgs
	sudo apt install -y ros-humble-xacro ros-humble-twist-mux ros-humble-navigation2 ros-humble-slam-toolbox ros-humble-octomap*

	########################
	# 5. Environment setup hint
	########################
	echo
	echo "Done. To use ROS 2 Humble in a new terminal, run:"
	echo "  source /opt/ros/humble/setup.bash"
	echo
	echo "Example talker/listener test:"
	echo "  source /opt/ros/humble/setup.bash"
	echo "  ros2 run demo_nodes_cpp talker"
	echo "  ros2 run demo_nodes_py listener"
	echo
}

########################
# Install MoveIt 2
########################
install_moveit2() {
	echo "=========================================="
	echo "Installing MoveIt 2..."
	echo "=========================================="

	# Check if ROS 2 is installed first
	if ! check_ros2_installed; then
		echo "ERROR: ROS 2 ${ROS_DISTRO} must be installed before MoveIt 2."
		echo "Run: $0 ros2"
		exit 1
	fi

	########################
	# 1. ROS build tools (if not already installed)
	########################
	sudo apt install -y python3-rosdep python3-colcon-common-extensions python3-colcon-mixin python3-vcstool

	sudo rosdep init || echo "rosdep already initialized"
	rosdep update
	sudo apt update
	sudo apt dist-upgrade -y

	colcon mixin add default https://raw.githubusercontent.com/colcon/colcon-mixin-repository/master/index.yaml || echo "colcon mixin already added"
	colcon mixin update default

	########################
	# 2. Create workspace & download MoveIt 2 + tutorials
	########################
	mkdir -p ~/ws_moveit/src
	cd ~/ws_moveit/src

	if [ ! -d "moveit2_tutorials" ]; then
		git clone -b humble https://github.com/moveit/moveit2_tutorials # Humble branch [page:1]
	else
		echo "moveit2_tutorials already exists, skipping clone"
	fi

	if [ -f "moveit2_tutorials/moveit2_tutorials.repos" ]; then
		vcs import --recursive <moveit2_tutorials/moveit2_tutorials.repos # Ignore GitHub auth prompts [page:1]
	else
		echo "Warning: moveit2_tutorials.repos not found"
	fi

	########################
	# 3. Install deps & build
	########################
	cd ~/ws_moveit

	sudo apt remove ros-$ROS_DISTRO-moveit* # Remove any prior MoveIt debs [page:1]
	sudo apt update && rosdep install -r --from-paths . --ignore-src --rosdistro $ROS_DISTRO -y

	colcon build --mixin release # 20-30 min; add --executor sequential if low RAM [page:1]

	########################
	# 4. Source workspace
	########################
	source ~/ws_moveit/install/setup.bash
	echo "source ~/ws_moveit/install/setup.bash" >>~/.bashrc # Optional auto-source [page:1]

	echo
	echo "Done! Tutorials ready. Check MoveIt docs for next steps." [page:1]
	echo
}

########################
# Main script logic
########################
main() {
	case "${1:-all}" in
	ros2)
		install_ros2
		;;
	moveit2 | moveit)
		# install_moveit2
		;;
	check)
		if check_ros2_installed; then
			echo "ROS 2 ${ROS_DISTRO} is installed."
			exit 0
		else
			echo "ROS 2 ${ROS_DISTRO} is not installed."
			exit 1
		fi
		;;
	all)
		if ! check_ros2_installed; then
			install_ros2
		else
			echo "ROS 2 ${ROS_DISTRO} is already installed, skipping ROS 2 installation."
		fi
		install_moveit2
		;;
	*)
		echo "Usage: $0 [ros2|moveit2|check|all]"
		echo ""
		echo "  ros2     - Install ROS 2 Humble only"
		echo "  moveit2  - Install MoveIt 2 (requires ROS 2 to be installed)"
		echo "  check    - Check if ROS 2 is installed"
		echo "  all      - Install both ROS 2 and MoveIt 2 (default)"
		exit 1
		;;
	esac
}

main "$@"
