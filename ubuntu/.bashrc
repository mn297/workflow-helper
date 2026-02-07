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

ROS_DISTRO="jazzy"
# ROS_DISTRO="humble"

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
ccb() {
	colcon build --symlink-install --parallel-workers $(nproc)
}
cros() {
	if [ -n "$1" ]; then
		rm -rf build/"$1" install/"$1" log/"$1"
	else
		rm -rf build install log
	fi
}
sros

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
