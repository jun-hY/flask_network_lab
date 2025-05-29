#!/bin/bash

echo "root:network" | chpasswd

# archive 서버 변경
sed -i 's|http://archive.ubuntu.com|http://mirror.kakao.com/ubuntu|g' /etc/apt/sources.list
sed -i 's|http://security.ubuntu.com|https://security.ubuntu.com|g' /etc/apt/sources.list

# apt-get update
apt-get update

# shellinabox 설치
apt-get install -y shellinabox

# supervisor 설치
apt-get install -y supervisor

# 디렉토리 보장
mkdir -p /etc/supervisor/conf.d

echo 'export PATH=$PATH:/sbin:/usr/sbin' >> /root/.bashrc

# shellinabox supervisor 설정 생성
echo '[program:shellinabox]
command=/usr/bin/shellinaboxd --no-beep -t --user=root --group=root -s /:root:root:/:/bin/bash
autostart=true
autorestart=true
startsecs=5
stdout_logfile=/var/log/shellinabox.out.log
stderr_logfile=/var/log/shellinabox.err.log
' > /etc/supervisor/conf.d/shellinabox.conf

# supervisorctl shellinabox 실행
exec /usr/bin/supervisord -n