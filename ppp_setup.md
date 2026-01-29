 
	
<!-- 1 -->
sudo pkill pppd || true 

sudo pkill socat || true 

sudo rm -f /tmp/ttyA /tmp/ttyB 

 

 
<!-- 2 -->
sudo socat -d -d \ 

  pty,raw,echo=0,link=/tmp/ttyA \ 

  pty,raw,echo=0,link=/tmp/ttyB 

 

 
<!-- 3 -->
sudo pppd /tmp/ttyA 115200 \ 

  10.10.10.1:10.10.10.2 \ 

  noauth local debug nodetach nocrtscts nodefaultroute \ 

  persist maxfail 0 

 
<!-- 4 -->
sudo pppd /tmp/ttyB 115200 \ 

  10.10.10.2:10.10.10.1 \ 

  noauth local debug nodetach nocrtscts nodefaultroute \ 

  persist maxfail 0 

 

 
<!-- 5 -->
ip -br addr show ppp0 ppp1 

ip addr show ppp0 

ip addr show ppp1 

 

 