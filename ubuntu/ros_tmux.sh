#!/bin/bash

# Check if the session exists
tmux has-session -t ros_session 2>/dev/null

# $? is a special variable that captures the exit code of the last command executed
if [ $? != 0 ]; then
  # Create a new session without attaching to it, and name it 'ros_session'
  tmux new-session -d -s ros_session

  # Run 'source' and 'roscore' in the first window
  tmux send-keys -t ros_session:0 'source /opt/ros/noetic/setup.bash; sleep 1; roscore' C-m

  # Give some time for roscore to start before creating new panes
  sleep 2

  # Create the panes (already explained in the previous answer)
  tmux split-window -h -t ros_session
  tmux send-keys -t ros_session:0.1 'source /opt/ros/noetic/setup.bash' C-m
  tmux split-window -v -t ros_session:0.0
  tmux send-keys -t ros_session:0.2 'source /opt/ros/noetic/setup.bash' C-m
  tmux split-window -v -t ros_session:0.1
  tmux send-keys -t ros_session:0.3 'source /opt/ros/noetic/setup.bash' C-m
fi

# Attach to the session, whether it was just created or already existed
tmux attach-session -t ros_session
