#!/usr/bin/env bash
set -euo pipefail

# ROS 2 Jazzy Jalisco (deb) + MoveIt 2 on Ubuntu 24.04 Noble.
#
#   ./setup_ros2_jazzy_deb.sh [ros2|moveit-deb|moveit-source|check|all]
#
# apt sources come from the ros2-apt-source package. That is the current
# official method; the hand-rolled /usr/share/keyrings/ros-archive-keyring.gpg
# plus /etc/apt/sources.list.d/ros2.list recipe this script used to carry
# breaks whenever the ROS signing key is rotated.

ROS_DISTRO_NAME="jazzy"
export ROS_DISTRO="$ROS_DISTRO_NAME"

MOVEIT_WS="${MOVEIT_WS:-$HOME/ws_moveit}"
ROS_SETUP="/opt/ros/${ROS_DISTRO_NAME}/setup.bash"

########################
# Helpers
########################
apt_install() {
	sudo apt install -y "$@"
}

# Best effort: packages that may not exist for every arch / sync state.
apt_install_optional() {
	sudo apt install -y "$@" || echo "WARNING: could not install: $*"
}

# ROS setup files are not always -u clean, so relax it while sourcing.
source_env() {
	set +u
	# shellcheck source=/dev/null
	source "$1"
	set -u
}

check_ubuntu() {
	. /etc/os-release
	local codename="${UBUNTU_CODENAME:-${VERSION_CODENAME:-unknown}}"

	if [ "$codename" != "noble" ]; then
		echo "ERROR: ROS 2 ${ROS_DISTRO_NAME} targets Ubuntu 24.04 (noble)."
		echo "Detected: ${PRETTY_NAME:-unknown}, codename=${codename}"
		echo "Set ALLOW_UNSUPPORTED_UBUNTU=1 to try anyway."
		[ "${ALLOW_UNSUPPORTED_UBUNTU:-0}" = "1" ] || exit 1
	fi

	echo "Ubuntu codename: ${codename}"
}

########################
# Check if ROS 2 is installed
########################
check_ros2_installed() {
	if [ -f "$ROS_SETUP" ]; then
		echo "ROS 2 ${ROS_DISTRO_NAME} appears to be installed at /opt/ros/${ROS_DISTRO_NAME}/"
		return 0
	else
		echo "ROS 2 ${ROS_DISTRO_NAME} is not installed."
		return 1
	fi
}

require_ros2() {
	if ! check_ros2_installed; then
		echo "ERROR: ROS 2 ${ROS_DISTRO_NAME} must be installed first."
		echo "Run: $0 ros2"
		exit 1
	fi
	source_env "$ROS_SETUP"
}

########################
# ROS 2 apt sources (ros2-apt-source package)
########################
setup_apt_sources() {
	apt_install software-properties-common curl ca-certificates gnupg
	sudo add-apt-repository -y universe
	sudo apt update

	local codename
	codename="$(. /etc/os-release && echo "${UBUNTU_CODENAME:-${VERSION_CODENAME}}")"

	local api_tmp deb_tmp
	api_tmp="$(mktemp /tmp/ros-apt-release.XXXXXX.json)"
	deb_tmp="$(mktemp /tmp/ros2-apt-source.XXXXXX.deb)"
	trap 'rm -f "$api_tmp" "$deb_tmp"' RETURN

	curl -sSf -o "$api_tmp" \
		"https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest"

	local version
	version="$(grep -Fm1 '"tag_name"' "$api_tmp" | awk -F'"' '{print $4}')"

	if [ -z "$version" ]; then
		echo "ERROR: could not read the ros-apt-source release tag from the GitHub API."
		exit 1
	fi

	echo "Latest ros-apt-source version: ${version}"

	curl -fSL -o "$deb_tmp" \
		"https://github.com/ros-infrastructure/ros-apt-source/releases/download/${version}/ros2-apt-source_${version}.${codename}_all.deb"

	apt_install "$deb_tmp"
	sudo apt update
}

########################
# Install ROS 2 Jazzy
########################
install_ros2() {
	echo "=========================================="
	echo "Installing ROS 2 ${ROS_DISTRO_NAME}..."
	echo "=========================================="

	check_ubuntu

	########################
	# 1. Locale
	########################
	sudo apt update
	apt_install locales
	sudo locale-gen en_US en_US.UTF-8
	sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
	export LANG=en_US.UTF-8
	export LC_ALL=en_US.UTF-8

	########################
	# 2. apt sources
	########################
	setup_apt_sources

	########################
	# 3. Upgrade first, so systemd/udev are current
	########################
	sudo apt upgrade -y

	########################
	# 4. ROS 2 desktop + build tooling
	########################
	# Desktop: RViz, demos, tutorials.
	apt_install "ros-${ROS_DISTRO_NAME}-desktop"

	# Needed for any later source build (colcon, rosdep, vcstool, ...).
	apt_install ros-dev-tools

	# Common C++ deps for robot packages.
	apt_install libpoco-dev libeigen3-dev libfmt-dev

	########################
	# 5. Robotics packages
	########################
	# ros2_control stack.
	apt_install \
		"ros-${ROS_DISTRO_NAME}-ros2-control" \
		"ros-${ROS_DISTRO_NAME}-ros2-controllers" \
		"ros-${ROS_DISTRO_NAME}-controller-manager" \
		"ros-${ROS_DISTRO_NAME}-controller-interface" \
		"ros-${ROS_DISTRO_NAME}-hardware-interface" \
		"ros-${ROS_DISTRO_NAME}-transmission-interface" \
		"ros-${ROS_DISTRO_NAME}-realtime-tools" \
		"ros-${ROS_DISTRO_NAME}-joint-state-broadcaster" \
		"ros-${ROS_DISTRO_NAME}-joint-trajectory-controller" \
		"ros-${ROS_DISTRO_NAME}-position-controllers" \
		"ros-${ROS_DISTRO_NAME}-effort-controllers"

	# Robot description, state and messages.
	apt_install \
		"ros-${ROS_DISTRO_NAME}-xacro" \
		"ros-${ROS_DISTRO_NAME}-tf2-ros" \
		"ros-${ROS_DISTRO_NAME}-robot-state-publisher" \
		"ros-${ROS_DISTRO_NAME}-joint-state-publisher" \
		"ros-${ROS_DISTRO_NAME}-joint-state-publisher-gui" \
		"ros-${ROS_DISTRO_NAME}-vision-msgs" \
		"ros-${ROS_DISTRO_NAME}-ackermann-msgs"

	# Navigation and mapping. The octomap pattern is quoted so apt expands it,
	# not the shell.
	apt_install \
		"ros-${ROS_DISTRO_NAME}-twist-mux" \
		"ros-${ROS_DISTRO_NAME}-navigation2" \
		"ros-${ROS_DISTRO_NAME}-nav2-bringup" \
		"ros-${ROS_DISTRO_NAME}-slam-toolbox" \
		"ros-${ROS_DISTRO_NAME}-octomap*"

	# Gazebo Harmonic bridge. Jazzy uses ros_gz, not gazebo_ros_pkgs; the
	# metapackage pulls ros-gz-sim and ros-gz-bridge.
	apt_install "ros-${ROS_DISTRO_NAME}-ros-gz"

	# Rigid body dynamics; not always available on every arch.
	apt_install_optional "ros-${ROS_DISTRO_NAME}-pinocchio"

	# Doc tooling via apt, to avoid the PEP 668 pip restrictions on 24.04.
	apt_install python3-sphinx python3-sphinx-autodoc-typehints python3-sphinx-rtd-theme

	########################
	# 6. Environment setup hint
	########################
	echo
	echo "Done. To use ROS 2 ${ROS_DISTRO_NAME} in a new terminal, run:"
	echo "  source ${ROS_SETUP}"
	echo
	echo "Test it with:"
	echo "  ros2 run demo_nodes_cpp talker"
	echo "  ros2 run demo_nodes_py listener   # in a second terminal"
	echo
}

########################
# Install MoveIt 2 from debs (the fast path)
########################
install_moveit_deb() {
	echo "=========================================="
	echo "Installing MoveIt 2 (debs)..."
	echo "=========================================="

	require_ros2

	sudo apt update
	apt_install \
		"ros-${ROS_DISTRO_NAME}-moveit" \
		"ros-${ROS_DISTRO_NAME}-moveit-py" \
		"ros-${ROS_DISTRO_NAME}-moveit-configs-utils" \
		"ros-${ROS_DISTRO_NAME}-moveit-ros-move-group" \
		"ros-${ROS_DISTRO_NAME}-moveit-ros-visualization" \
		"ros-${ROS_DISTRO_NAME}-moveit-kinematics" \
		"ros-${ROS_DISTRO_NAME}-moveit-planners" \
		"ros-${ROS_DISTRO_NAME}-moveit-simple-controller-manager" \
		"ros-${ROS_DISTRO_NAME}-moveit-setup-assistant"

	echo
	echo "Done. MoveIt 2 debs installed."
	echo
}

########################
# Install MoveIt 2 from source, with the tutorials workspace
########################
install_moveit_source() {
	echo "=========================================="
	echo "Installing MoveIt 2 (source) into ${MOVEIT_WS}..."
	echo "=========================================="

	require_ros2

	########################
	# 1. ROS build tools
	########################
	apt_install python3-rosdep python3-colcon-common-extensions python3-colcon-mixin python3-vcstool

	if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then
		sudo rosdep init
	fi
	rosdep update
	sudo apt update
	sudo apt dist-upgrade -y

	colcon mixin add default \
		https://raw.githubusercontent.com/colcon/colcon-mixin-repository/master/index.yaml ||
		echo "colcon mixin 'default' already added"
	colcon mixin update default

	########################
	# 2. Workspace + sources
	########################
	mkdir -p "${MOVEIT_WS}/src"
	cd "${MOVEIT_WS}/src"

	# MoveIt 2 tutorials track Jazzy on the main branch.
	if [ ! -d moveit2_tutorials ]; then
		git clone -b main https://github.com/moveit/moveit2_tutorials
	else
		echo "moveit2_tutorials already cloned, skipping"
	fi

	if [ -f moveit2_tutorials/moveit2_tutorials.repos ]; then
		vcs import --recursive <moveit2_tutorials/moveit2_tutorials.repos
	else
		echo "WARNING: moveit2_tutorials.repos not found"
	fi

	########################
	# 3. Deps and build
	########################
	cd "$MOVEIT_WS"

	# The debs would shadow the source build, so drop them first. Quoted so
	# apt expands the pattern, not the shell.
	sudo apt remove -y "ros-${ROS_DISTRO_NAME}-moveit*" || true

	sudo apt update
	rosdep install -r --from-paths src --ignore-src --rosdistro "$ROS_DISTRO_NAME" -y

	# Sequential executor keeps peak RAM down; this takes 20-30 min.
	colcon build --mixin release --executor sequential

	########################
	# 4. Source the workspace
	########################
	source_env "${MOVEIT_WS}/install/setup.bash"

	# Not appended to ~/.bashrc on purpose: the repo's .bashrc sources ROS via
	# the sros alias, which already picks up ./install/setup.bash.
	echo
	echo "Done. MoveIt 2 tutorials built for ROS 2 ${ROS_DISTRO_NAME}."
	echo "  source ${MOVEIT_WS}/install/setup.bash"
	echo
}

########################
# Main script logic
########################
usage() {
	cat <<EOF
Usage: $0 [ros2|moveit-deb|moveit-source|check|all]

  ros2           Install ROS 2 ${ROS_DISTRO_NAME} and common robotics packages
  moveit-deb     Install MoveIt 2 from debs (fast; requires ros2)
  moveit-source  Build MoveIt 2 + tutorials in ${MOVEIT_WS} (requires ros2;
                 removes the MoveIt debs first)
  check          Report whether ROS 2 ${ROS_DISTRO_NAME} is installed
  all            ros2, then moveit-source (default)
EOF
}

main() {
	case "${1:-all}" in
	ros2)
		install_ros2
		;;
	moveit-deb | moveit2-deb)
		install_moveit_deb
		;;
	moveit-source | moveit2 | moveit)
		install_moveit_source
		;;
	check)
		check_ros2_installed
		;;
	all)
		if ! check_ros2_installed; then
			install_ros2
		else
			echo "ROS 2 ${ROS_DISTRO_NAME} is already installed, skipping."
		fi
		install_moveit_source
		;;
	-h | --help | help)
		usage
		;;
	*)
		usage
		exit 1
		;;
	esac
}

main "$@"
