#!/usr/bin/env bash
set -e

# ROS 2 Jazzy deb installation for Ubuntu 24.04
# MoveIt 2 source setup for ROS 2 Jazzy (Ubuntu 24.04)

export ROS_DISTRO=jazzy  # Updated for Jazzy [web:1]

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
# Install ROS 2 Jazzy
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
    # 2. Setup ROS 2 apt sources (Official Method)
    ########################
    # Ensure Universe repository is enabled
    sudo apt install -y software-properties-common
    sudo add-apt-repository -y universe

    sudo apt update
    sudo apt install -y curl

    # Add the ROS 2 GPG key with the standard keyring method (more robust for Jazzy) [web:9]
    sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg

    # Add the repository to sources list
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

    ########################
    # 3. Update & upgrade
    ########################
    sudo apt update
    sudo apt upgrade -y

    ########################
    # 4. Install ROS 2 Jazzy
    ########################
    # Desktop (RViz, demos, tutorials)
    sudo apt install -y ros-jazzy-desktop

    # Dev tools (Critical for building source packages later)
    sudo apt install -y ros-dev-tools

    # Additional dependencies (Updated for Jazzy/Noble)
    # Note: 'python-catkin-pkg' is often 'python3-catkin-pkg' or covered by ros-dev-tools
    sudo apt install -y libpoco-dev libeigen3-dev libfmt-dev
    
    # ROS 2 Control & Navigation
    sudo apt install -y ros-jazzy-ros2-control ros-jazzy-ros2-controllers \
                        ros-jazzy-hardware-interface ros-jazzy-transmission-interface \
                        ros-jazzy-controller-interface ros-jazzy-realtime-tools
    
    # Robot description & messages
    sudo apt install -y ros-jazzy-xacro ros-jazzy-vision-msgs ros-jazzy-ackermann-msgs
    
    # Navigation & Mapping
    sudo apt install -y ros-jazzy-twist-mux ros-jazzy-navigation2 ros-jazzy-slam-toolbox ros-jazzy-octomap*

    # Gazebo Harmonic (Jazzy uses 'ros_gz' instead of 'gazebo_ros_pkgs') [web:25]
    sudo apt install -y ros-jazzy-ros-gz

    # Pinocchio (Note: Support on 24.04 may be experimental) [web:22]
    # If this fails, comment it out and rely on rosdep later.
    sudo apt install -y ros-jazzy-pinocchio || echo "Warning: ros-jazzy-pinocchio not found or failed to install."

    # Documentation tools (Using apt to avoid PEP 668 pip issues on 24.04)
    sudo apt install -y python3-sphinx python3-sphinx-autodoc-typehints python3-sphinx-rtd-theme

    ########################
    # 5. Environment setup hint
    ########################
    echo
    echo "Done. To use ROS 2 Jazzy in a new terminal, run:"
    echo "  source /opt/ros/jazzy/setup.bash"
    echo
}

########################
# Install MoveIt 2
########################
install_moveit2() {
    echo "=========================================="
    echo "Installing MoveIt 2 (Source)..."
    echo "=========================================="

    if ! check_ros2_installed; then
        echo "ERROR: ROS 2 ${ROS_DISTRO} must be installed before MoveIt 2."
        echo "Run: $0 ros2"
        exit 1
    fi

    ########################
    # 1. ROS build tools
    ########################
    sudo apt install -y python3-rosdep python3-colcon-common-extensions python3-colcon-mixin python3-vcstool

    if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then
        sudo rosdep init
    fi
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

    # MoveIt 2 Tutorials for Jazzy use the 'main' branch [web:7][web:10]
    if [ ! -d "moveit2_tutorials" ]; then
        git clone -b main https://github.com/moveit/moveit2_tutorials  # 'main' branch is for Jazzy
    else
        echo "moveit2_tutorials already exists, skipping clone"
    fi

    if [ -f "moveit2_tutorials/moveit2_tutorials.repos" ]; then
        vcs import --recursive < moveit2_tutorials/moveit2_tutorials.repos
    else
        echo "Warning: moveit2_tutorials.repos not found"
    fi

    ########################
    # 3. Install deps & build
    ########################
    cd ~/ws_moveit

    # Remove any binary installs of MoveIt to avoid conflicts with source build
    sudo apt remove -y ros-$ROS_DISTRO-moveit* || true

    # Install dependencies using rosdep
    sudo apt update
    rosdep install -r --from-paths . --ignore-src --rosdistro $ROS_DISTRO -y

    # Build (Sequencing executor often helps with memory on smaller machines)
    colcon build --mixin release --executor sequential

    ########################
    # 4. Source workspace
    ########################
    source ~/ws_moveit/install/setup.bash
    
    # Helper alias (Optional)
    # echo "source ~/ws_moveit/install/setup.bash" >> ~/.bashrc

    echo
    echo "Done! Tutorials ready for ROS 2 Jazzy."
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
        install_moveit2
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
        exit 1
        ;;
    esac
}

main "$@"
