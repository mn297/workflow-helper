echo 'source ~/anaconda3/etc/profile.d/conda.sh' >>~/.bashrc
conda create --name myenv python=3.12
conda activate myenv

pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
pip install gymnasium matplotlib numpy pandas seaborn "stable-baselines3[extra]" ale-py gym-anytrading tqdm scipy scikit-learn dask-ml yfinance stockstats wrds alpaca_trade_api exchange_calendars finrl rich open3d kagglehub ultralytics
