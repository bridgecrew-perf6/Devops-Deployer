#!/bin/bash
apt-get update -y
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
apt install unzip
unzip awscliv2.zip
./aws/install

apt-get install openjdk-11-jdk -y

# BLD , BRANCH , CHEF_ROLE
aws s3 cp s3://majd-petclininc-artifacts/Artifacts/^CHEF_ROLE/^BRANCH/^BLD/spring-petclinic-2.4.2.jar /home/ubuntu/petclinic.jar
aws s3 cp s3://majd-petclininc-artifacts/Artifacts/application-mysql.properties /home/ubuntu/application-mysql.properties
echo -e '\n#!/bin/bash\njava -jar -Dspring.profiles.active=mysql /home/ubuntu/petclinic.jar --spring.config.location=/home/ubuntu/application-mysql.properties' > /home/ubuntu/run-app.sh

echo -e '\n[Unit]\nDescription=Deployer - PetClinic
\n[Service]
User=ubuntu
ExecStart=/bin/bash /home/ubuntu/run-app.sh
SuccessExitStatus=143
TimeoutStopSec=10
Restart=on-failure
RestartSec=5

\n[Install]
WantedBy=multi-user.target
' > /etc/systemd/system/petclinic.service

chmod +x /home/ubuntu/run-app.sh
systemctl daemon-reload	
systemctl enable petclinic.service
systemctl start petclinic
systemctl status petclinic