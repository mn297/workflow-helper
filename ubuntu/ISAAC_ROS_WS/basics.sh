#!/bin/bash

# https://nvidia-isaac-ros.github.io/repositories_and_packages/isaac_ros_pose_estimation/isaac_ros_foundationpose/index.html
# https://nvidia-isaac-ros.github.io/repositories_and_packages/isaac_ros_object_detection/isaac_ros_rtdetr/index.html

set -e

install_prereqs() {
    echo "Installing required packages..."
    sudo apt-get update
    sudo apt-get install -y ros-jazzy-isaac-ros-examples
    sudo git lfs install --system
}

install_from_binary() {
    echo "Installing from binary..."
    install_prereqs
    sudo apt-get install -y --no-install-recommends \
        curl \
        jq \
        tar \
        git-lfs \
        ros-jazzy-isaac-ros-foundationpose \
        ros-jazzy-isaac-ros-rtdetr \
        ros-jazzy-isaac-ros-rtdetr-models-install \
        ros-jazzy-isaac-ros-examples \
        ros-jazzy-isaac-ros-realsense \
        ros-jazzy-rviz2 \
        ros-jazzy-vision-msgs-rviz-plugins \
        ros-jazzy-rqt-image-view \
        ros-jazzy-cv-bridge
}

install_from_source() {
    echo "Installing from source..."
    install_prereqs
    
    # Remove binary versions if they exist
    sudo apt-get remove -y \
        ros-jazzy-isaac-ros-rtdetr-models-install \
        ros-jazzy-isaac-ros-foundationpose-models-install \
        ros-jazzy-isaac-ros-rtdetr \
        ros-jazzy-isaac-ros-foundationpose || true

    cd "${ISAAC_ROS_WS}/src"
    
    # RT-DETR
    if [ ! -d "isaac_ros_object_detection" ]; then
        git clone -b release-4.3 https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_object_detection.git isaac_ros_object_detection
    fi
    rosdep update
    rosdep install --from-paths "${ISAAC_ROS_WS}/src/isaac_ros_object_detection/isaac_ros_rtdetr" --ignore-src -y
    sudo apt-get install -y ros-jazzy-isaac-ros-rtdetr-models-install
    ros2 run isaac_ros_rtdetr_models_install install_rtdetr_models.sh --eula
    
    cd "${ISAAC_ROS_WS}"
    colcon build --symlink-install --packages-up-to isaac_ros_rtdetr --base-paths "${ISAAC_ROS_WS}/src/isaac_ros_object_detection/isaac_ros_rtdetr"

    # FoundationPose
    cd "${ISAAC_ROS_WS}/src"
    if [ ! -d "isaac_ros_pose_estimation" ]; then
        git clone -b release-4.3 https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_pose_estimation.git isaac_ros_pose_estimation
    fi
    rosdep install --from-paths "${ISAAC_ROS_WS}/src/isaac_ros_pose_estimation/isaac_ros_foundationpose" --ignore-src -y
    
    cd "${ISAAC_ROS_WS}"
    colcon build --symlink-install --packages-up-to isaac_ros_foundationpose --base-paths "${ISAAC_ROS_WS}/src/isaac_ros_pose_estimation/isaac_ros_foundationpose"
}

install_bashrc_utils() {
    echo "Installing ROS aliases and functions to ~/.bashrc..."
    
    # Define the block to append using a Heredoc
    BASHRC_BLOCK=$(cat << 'EOF'

# ==========================================
# ROS & Development Utilities
# ==========================================

# Source ROS 2 and local workspace
alias sros='source /opt/ros/${ROS_DISTRO}/setup.bash && if [ -f "./install/setup.bash" ]; then source ./install/setup.bash; fi'

# Source Python virtual environment
senv() {
    if [ -f .venv/bin/activate ]; then
        source .venv/bin/activate
    else
        echo "No virtual environment found in the current directory."
    fi
}

# Build workspace with all available cores
ccb() {
    colcon build --parallel-workers $(nproc)
}

# Clean ROS workspace (all or specific package)
cros() {
    if [ -n "$1" ]; then
        rm -rf build/"$1" install/"$1" log/"$1"
        echo "Cleaned package: $1"
    else
        rm -rf build install log
        echo "Cleaned entire workspace."
    fi
}

# Kill all ROS 2, Gazebo, and RViz related processes
kros() {
    echo "Nuking ROS 2 / Gazebo / RViz related processes..."
    _kros_kill() {
        local p
        p=$(pgrep -f "$1" 2>/dev/null) || true
        [ -n "$p" ] && kill -9 $p 2>/dev/null
    }
    
    local patterns=(
        'ros2' 'apriltag_node' 'component_container' 'ros2_control_node'
        'static_transform_publisher' 'joint_state_publisher' 'robot_state_publisher'
        'controller_manager' 'move_group' 'rviz2' 'gz sim' 'gz_ros' 'ros_gz'
        'foxglove_bridge' 'z1_ctrl' 'ruby.*gz'
    )
    
    for _pat in "${patterns[@]}"; do
        _kros_kill "$_pat"
    done
    
    if [ -n "${ROS_DISTRO:-}" ]; then
        _kros_kill "/opt/ros/${ROS_DISTRO}/lib/"
    fi
    
    ros2 daemon stop 2>/dev/null || true
    echo "Done."
}

# Automatically source ROS on new terminal sessions
sros

# Qt Debugging (optional, useful for RViz/GUI issues)
export QT_DEBUG_PLUGINS=1

# ==========================================
EOF
)

    # Check if already installed to avoid duplicate entries
    if grep -q "ROS & Development Utilities" ~/.bashrc; then
        echo "The utilities are already installed in ~/.bashrc."
    else
        echo "$BASHRC_BLOCK" >> ~/.bashrc
        echo "Successfully appended to ~/.bashrc!"
    fi

    echo "Please run 'source ~/.bashrc' or open a new terminal to apply the changes."
}

echo "=========================================="
echo " Isaac ROS Setup Script"
echo "=========================================="
echo "Please select an option:"
echo "1) Install Isaac ROS packages from binary (apt)"
echo "2) Install Isaac ROS packages from source (git + colcon)"
echo "3) Install bashrc utilities (aliases, functions)"
echo "4) Install ALL (Binary + Bashrc utils)"
echo "5) Quit"
echo "=========================================="

read -p "Enter your choice [1-5]: " choice

case $choice in
    1)
        install_from_binary
        ;;
    2)
        install_from_source
        ;;
    3)
        install_bashrc_utils
        ;;
    4)
        install_from_binary
        install_bashrc_utils
        ;;
    5)
        echo "Exiting."
        exit 0
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac
