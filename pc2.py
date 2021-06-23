#!/usr/bin/python3
import os
import sys
from subprocess import call, check_output
import logging
logging.basicConfig(level=logging.DEBUG, filename='archivo.log', format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
logger = logging.getLogger('pc2')
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)



# Configuracion de las bbdd.

def bbdd():
	fin= open("pc2.cfg", 'r') # out file
	nservidores = int(fin.readlines()[0][0]) #Toma el valor del numero de servidores para utilizarlo en el bucle posteriormente
	fin.close()
	#BBDD
	logger.debug('%s - Comenzando la configuración de las bases de datos'%("BBDD"))
	cmd_line = "sudo lxc-attach --clear-env -n bbdd -- bash -c \" apt -y update; apt -y install mariadb-server ; sed -i -e 's/bind-address.*/bind-address=0.0.0.0/' -e 's/utf8mb4/utf8/' /etc/mysql/mariadb.conf.d/50-server.cnf ; systemctl restart mysql\""
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n bbdd -- mysqladmin -u root password xxxx"
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n bbdd -- mysql -u root --password='xxxx' -e \"CREATE USER 'quiz' IDENTIFIED BY 'xxxx';\""
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n bbdd -- mysql -u root --password='xxxx' -e \"CREATE DATABASE quiz;\""
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n bbdd -- mysql -u root --password='xxxx' -e \"GRANT ALL PRIVILEGES ON quiz.* to 'quiz'@'localhost' IDENTIFIED by 'xxxx';\""
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n bbdd -- mysql -u root --password='xxxx' -e \"GRANT ALL PRIVILEGES ON quiz.* to 'quiz'@'%' IDENTIFIED by 'xxxx';\""
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n bbdd -- mysql -u root --password='xxxx' -e \"FLUSH PRIVILEGES;\""
	call (cmd_line, shell=True)
	logger.debug('%s - Bases de datos configuradas'%("BBDD"))

# Configuracion NAS.

def nas():
	logger.debug('%s - Configurando el nas'%("NAS"))
	cmd_line = "sudo lxc-attach --clear-env -n nas1 -- gluster peer probe 20.20.4.22"
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nas1 -- gluster peer probe 20.20.4.23"
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nas1 -- sleep 5"
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nas1 -- gluster peer status"
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nas1 -- gluster volume create nas replica 3 transport tcp 20.20.4.21:/nas 20.20.4.22:/nas 20.20.4.23:/nas force"
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nas1 -- gluster volume start nas"
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nas1 -- gluster volume info"
	call (cmd_line, shell=True)
	for i in [1,2,3]:
		cmd_line = "sudo lxc-attach --clear-env -n nas"+str(i)+" -- gluster volume set nas network.ping-timeout 5"
		call (cmd_line, shell=True)
	logger.debug('%s - NAS configurado'%("NAS"))

# Configuracion servidores

def serv():
	fin= open("pc2.cfg", 'r') # out file
	nservidores = int(fin.readlines()[0][0]) #Toma el valor del numero de servidores para utilizarlo en el bucle posteriormente
	fin.close()
	#APLICACION SERVIDORES
	logger.debug('%s - Configurando los servidores'%("SERV"))
	for i in range (1,nservidores+1):
		cmd_line = "sudo lxc-attach --clear-env -n s"+str(i)+" -- apt-get update -y"
		call (cmd_line, shell=True)
		cmd_line = "sudo lxc-attach --clear-env -n s"+str(i)+" -- apt-get install install git -y"
		call (cmd_line, shell=True)
		cmd_line = "sudo lxc-attach --clear-env -n s"+str(i)+" -- apt-get install curl -y"
		call (cmd_line, shell=True)
		cmd_line = "sudo lxc-attach --clear-env -n s"+str(i)+" -- bash -c \" curl -sL https://deb.nodesource.com/setup_14.x | sudo -E bash -; sudo apt-get -y install nodejs \" "
		call (cmd_line, shell=True)
		cmd_line = "sudo lxc-attach --clear-env -n s"+str(i)+" -- git clone https://github.com/CORE-UPM/quiz_2021.git"
		call (cmd_line, shell=True)
		cmd_line = "sudo lxc-attach --clear-env -n s"+str(i)+" -- bash -c \" cd quiz_2021 ; sed -i '29d' ./app.js \" "
		call (cmd_line, shell=True)
		cmd_line = "sudo lxc-attach --clear-env -n s"+str(i)+" -- bash -c \" cd quiz_2021 ; mkdir -p public/uploads ; npm install ; npm install forever ; npm install mysql2  \" "
		call (cmd_line, shell=True)
		cmd_line = "sudo lxc-attach --clear-env -n s"+str(i)+" -- bash -c \" cd quiz_2021 ; mount -t glusterfs 20.20.4.21:/nas public/uploads  \" "
		call (cmd_line, shell=True)
		cmd_line='sudo lxc-attach --clear-env -n s'+str(i)+' -- sed -i "s/Welcome to Quiz/Welcome to Quiz s"'+str(i)+'"/" /quiz_2021/views/index.ejs'
		call (cmd_line, shell=True)
		logger.debug('%s - Servidor s%s configurado'%("SERV", str(i)))

	
		if i == 1:
			cmd_line = "sudo lxc-attach --clear-env -n s1 -- bash -c \" cd quiz_2021; export QUIZ_OPEN_REGISTER=yes ; export DATABASE_URL=mysql://quiz:xxxx@20.20.4.31:3306/quiz ; npm run-script migrate_env \" "
			call (cmd_line, shell=True)
			cmd_line = "sudo lxc-attach --clear-env -n s1 -- bash -c \" cd quiz_2021; export QUIZ_OPEN_REGISTER=yes ; export DATABASE_URL=mysql://quiz:xxxx@20.20.4.31:3306/quiz ; npm run-script seed_env \" "
			call (cmd_line, shell=True)

		cmd_line = "sudo lxc-attach --clear-env -n s"+str(i)+" -- bash -c \" cd quiz_2021; export QUIZ_OPEN_REGISTER=yes ; export DATABASE_URL=mysql://quiz:xxxx@20.20.4.31:3306/quiz ; ./node_modules/forever/bin/forever start ./bin/www \" "
		call (cmd_line, shell=True)


# Configuracion balanceador.

def lb():
	logger.debug('%s - Configurando balanceador'%("LB"))
	HaProxy()
	cmd_line = "sudo lxc-attach --clear-env -n lb -- bash -c \" apt update ; apt -y install haproxy \" "
	call (cmd_line, shell=True)
	cmd_line = "sudo /lab/cdps/bin/cp2lxc haproxy.cfg /var/lib/lxc/lb/rootfs/etc/haproxy"
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n lb -- bash -c \"sudo systemctl restart haproxy \" "
	call (cmd_line, shell=True)
	logger.debug('%s - Balanceador configurado'%("LB"))

# Configuración de HaProxy con mejorada incluida.

def HaProxy():
	logger.debug('%s - Configurando el fichero HAproxy'%("LB"))
	fin= open("pc2.cfg", 'r') # out file
	nservidores = int(fin.readlines()[0][0]) #Toma el valor del numero de servidores para utilizarlo en el bucle posteriormente
	fin.close()
	fout = open("haproxy.cfg",'w')
	fout.write("global\n")
	fout.write("\tlog /dev/log	local0\n")
	fout.write("\tlog /dev/log	local1 notice\n")
	fout.write("\tchroot /var/lib/haproxy\n")
	fout.write("\tstats socket /run/haproxy/admin.sock mode 660 level admin expose-fd listeners\n")
	fout.write("\tstats timeout 30s\n")
	fout.write("\tuser haproxy\n")
	fout.write("\tgroup haproxy\n")
	fout.write("\tdaemon\n")
	fout.write("\n")
	fout.write("\tca-base /etc/ssl/certs\n")
	fout.write("\tcrt-base /etc/ssl/private\n")
	fout.write("\n")
	fout.write("\tssl-default-bind-ciphers ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:RSA+AESGCM:RSA+AES:!aNULL:!MD5:!DSS\n")
	fout.write("\tssl-default-bind-options no-sslv3\n")
	fout.write("\n")
	fout.write("defaults\n")
	fout.write("\tlog	global\n")
	fout.write("\tmode	http\n")
	fout.write("\toption	httplog\n")
	fout.write("\toption	dontlognull\n")
	fout.write("\ttimeout connect 5000\n")
	fout.write("\ttimeout client  50000\n")
	fout.write("\ttimeout server  50000\n")
	fout.write("\terrorfile 400 /etc/haproxy/errors/400.http\n")
	fout.write("\terrorfile 403 /etc/haproxy/errors/403.http\n")
	fout.write("\terrorfile 408 /etc/haproxy/errors/408.http\n")
	fout.write("\terrorfile 500 /etc/haproxy/errors/500.http\n")
	fout.write("\terrorfile 502 /etc/haproxy/errors/502.http\n")
	fout.write("\terrorfile 503 /etc/haproxy/errors/503.http\n")
	fout.write("\terrorfile 504 /etc/haproxy/errors/504.http\n")
	fout.write("\n")
	fout.write("\n")
	fout.write("frontend lb \n")
	fout.write("\tbind *:80\n")
	fout.write("\tmode http\n")
	fout.write("\tdefault_backend webservers\n")
	fout.write("\n")
	fout.write("backend webservers\n")
	fout.write("\tmode http\n")
	fout.write("\tbalance roundrobin\n")
	for i in range(1,3):
		fout.write("\tserver s"+str(i)+ " 20.20.3.1"+str(i)+ ":3000 check weight 40\n")
	if nservidores == 4:
		fout.write("\tserver s3 20.20.3.13:3000 check weight 10\n")
		fout.write("\tserver s4 20.20.3.14:3000 check weight 10\n")
	else:
		fout.write("\tserver s3 20.20.3.13:3000 check weight 20\n")
	fout.write("listen stats\n")
	fout.write("\tbind :8001\n")
	fout.write("\tstats enable\n")
	fout.write("\tstats uri /\n")
	fout.write("\tstats hide-version\n")
	fout.write("\tstats auth admin:cdps\n")

# Configuracion del firewall

def fw():
	call(["chmod","+x","fw.fw"])
	cmd_line = "sudo /lab/cdps/bin/cp2lxc fw.fw /var/lib/lxc/fw/rootfs/root"
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n fw -- /root/fw.fw"
	call (cmd_line, shell=True)
	logger.debug('%s - Firewall configurado'%("Firewall"))

# Configuracion del servidor de gestión mediante par de claves pública/privada.

def gestion():
	if not os.path.exists('/mnt/tmp/pc2/ges_rsa'):
		call('ssh-keygen -t rsa -N "" -f "/mnt/tmp/pc2/ges_rsa"', shell=True)

	logger.debug('%s - Nuevas claves generadas para conectarse al servidor de gestión'%("Gestion"))

	key = check_output('cat /mnt/tmp/pc2/ges_rsa.pub', shell=True)
	key = key.decode('utf-8')
	cmd_line='sudo lxc-attach --clear-env -n ges -- mkdir /root/.ssh'
	call(cmd_line, shell=True)
	cmd_line = "sudo /lab/cdps/bin/cp2lxc ges_rsa /var/lib/lxc/c1/rootfs/root"
	call (cmd_line, shell=True)
	cmd_line = "sudo /lab/cdps/bin/cp2lxc ges_rsa /var/lib/lxc/c2/rootfs/root"
	call (cmd_line, shell=True)
	cmd_line='sudo lxc-attach --clear-env -n ges -- bash -c "echo \'{key}\' >> /root/.ssh/authorized_keys"'.format(key=key)
	call(cmd_line, shell=True)
	cmd_line='sudo lxc-attach --clear-env -n ges -- sed -i "s/#PasswordAuthentication yes/PasswordAuthentication no/" /etc/ssh/sshd_config'
	call(cmd_line, shell=True)
	cmd_line='sudo lxc-attach --clear-env -n ges -- service ssh restart'
	call(cmd_line, shell=True)
	logger.debug('%s - Servidor configurado'%("Gestion"))



# Configuracion servidor Nagios.

def nagios():
	logger.debug('%s - Configurando servidor Nagios '%("Nagios"))
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- apt-get update -y"
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- apt-get install git -y"
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- apt-get install -y autoconf gcc libc6 make wget unzip apache2 php libapache2-mod-php7.2 libgd-dev"
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- apt-get install libapache2-mod-php -y"
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- apt-get install curl"
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- apt-get install -y autoconf gcc libc6 libmcrypt-dev make libssl-dev wget bc gawk dc build-essential snmp libnet-snmp-perl gettext"
	call (cmd_line, shell=True)
	logger.debug('%s - Se han configurado las dependencias '%("Nagios"))
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- openssl s_client -showcerts -connect github.com:443"
	call (cmd_line, shell=True)
	logger.debug('%s - Se ha establecido el certificado SSL con github '%("Nagios"))
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- bash -c \" cd /tmp ; wget -O nagioscore.tar.gz https://github.com/NagiosEnterprises/nagioscore/archive/nagios-4.4.5.tar.gz \" "
	call (cmd_line, shell=True)
	logger.debug('%s - Se ha descargado el paquete de Nagios '%("Nagios"))
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- bash -c \" cd /tmp ; tar xzf nagioscore.tar.gz \" "
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- bash -c \" cd /tmp/nagioscore-nagios-4.4.5/ ; sudo ./configure --with-httpd-conf=/etc/apache2/sites-enabled \" "
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- bash -c \" cd /tmp/nagioscore-nagios-4.4.5/ ; sudo make all \" "
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- bash -c \" cd /tmp/nagioscore-nagios-4.4.5/ ; sudo make install-groups-users \" "
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- bash -c \" cd /tmp/nagioscore-nagios-4.4.5/ ; sudo usermod -a -G nagios www-data \" "
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- bash -c \" cd /tmp/nagioscore-nagios-4.4.5/ ; sudo make install \" "
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- bash -c \" cd /tmp/nagioscore-nagios-4.4.5/ ; sudo make install-daemoninit \" "
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- bash -c \" cd /tmp/nagioscore-nagios-4.4.5/ ; sudo make install \" "
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- bash -c \" cd /tmp/nagioscore-nagios-4.4.5/ ; sudo make install-commandmode \" "
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- bash -c \" cd /tmp/nagioscore-nagios-4.4.5/ ; sudo make install-config \" "
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- bash -c \" cd /tmp/nagioscore-nagios-4.4.5/ ; sudo make install-webconf \" "
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- bash -c \" cd /tmp/nagioscore-nagios-4.4.5/ ; sudo a2enmod rewrite \" "
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- bash -c \" cd /tmp/nagioscore-nagios-4.4.5/ ; sudo a2enmod cgi \" "
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- bash -c \" cd /tmp/nagioscore-nagios-4.4.5/ ; echo \"hola\" | htpasswd -c -i /usr/local/nagios/etc/htpasswd.users nagiosadmin \" "
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- bash -c \" cd /tmp ; wget --no-check-certificate -O nagios-plugins.tar.gz https://github.com/nagios-plugins/nagios-plugins/archive/release-2.2.1.tar.gz \" "
	call (cmd_line, shell=True)
	logger.debug('%s - Se han descargado los plugins de Nagios '%("Nagios"))
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- bash -c \" cd /tmp ; tar zxf nagios-plugins.tar.gz \" "
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- bash -c \" cd /tmp/nagios-plugins-release-2.2.1/ ; sudo ./tools/setup \" "
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- bash -c \" cd /tmp/nagios-plugins-release-2.2.1/ ; sudo ./configure \" "
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- bash -c \" cd /tmp/nagios-plugins-release-2.2.1/ ; sudo make \" "
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- bash -c \" cd /tmp/nagios-plugins-release-2.2.1/ ; sudo make install \" "
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- sudo systemctl restart apache2.service"
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- sudo systemctl start nagios.service"
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- mkdir /usr/local/nagios/etc/servers"
	call (cmd_line, shell=True)
	cmd_line = "sudo /lab/cdps/bin/cp2lxc ./nagios/s1.cfg /var/lib/lxc/nagios/rootfs/usr/local/nagios/etc/servers/"
	call (cmd_line, shell=True)
	cmd_line = "sudo /lab/cdps/bin/cp2lxc ./nagios/s2.cfg /var/lib/lxc/nagios/rootfs/usr/local/nagios/etc/servers/"
	call (cmd_line, shell=True)
	cmd_line = "sudo /lab/cdps/bin/cp2lxc ./nagios/s3.cfg /var/lib/lxc/nagios/rootfs/usr/local/nagios/etc/servers/"
	call (cmd_line, shell=True)
	cmd_line = "sudo /lab/cdps/bin/cp2lxc ./nagios/s4.cfg /var/lib/lxc/nagios/rootfs/usr/local/nagios/etc/servers/"
	call (cmd_line, shell=True)
	cmd_line = "sudo /lab/cdps/bin/cp2lxc ./nagios/nas1.cfg /var/lib/lxc/nagios/rootfs/usr/local/nagios/etc/servers/"
	call (cmd_line, shell=True)
	cmd_line = "sudo /lab/cdps/bin/cp2lxc ./nagios/nas2.cfg /var/lib/lxc/nagios/rootfs/usr/local/nagios/etc/servers/"
	call (cmd_line, shell=True)
	cmd_line = "sudo /lab/cdps/bin/cp2lxc ./nagios/nas3.cfg /var/lib/lxc/nagios/rootfs/usr/local/nagios/etc/servers/"
	call (cmd_line, shell=True)
	cmd_line = "sudo /lab/cdps/bin/cp2lxc ./nagios/bbdd.cfg /var/lib/lxc/nagios/rootfs/usr/local/nagios/etc/servers/"
	call (cmd_line, shell=True)
	cmd_line = "sudo /lab/cdps/bin/cp2lxc ./nagios/fw.cfg /var/lib/lxc/nagios/rootfs/usr/local/nagios/etc/servers/"
	call (cmd_line, shell=True)
	cmd_line = "sudo /lab/cdps/bin/cp2lxc ./nagios/lb.cfg /var/lib/lxc/nagios/rootfs/usr/local/nagios/etc/servers/"
	call (cmd_line, shell=True)
	cmd_line = "sudo /lab/cdps/bin/cp2lxc ./nagios/nagios.cfg /var/lib/lxc/nagios/rootfs/usr/local/nagios/etc/"
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- sudo systemctl restart apache2.service"
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- sudo systemctl restart nagios.service"
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nagios -- sudo systemctl start nagios.service"
	call (cmd_line, shell=True)
	logger.debug('%s - Servidor Nagios configurado'%("Nagios"))

# Configuracion del servidor de logs

def logs():
	logger.debug('%s - Configurando servidor de logs '%("LOGS"))
	cmd_line = "sudo lxc-attach --clear-env -n logs -- apt-get update -y"
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n logs -- apt-get install lsof -y"
	call (cmd_line, shell=True)
	cmd_line = "sudo /lab/cdps/bin/cp2lxc ./logs/servidor/rsyslog.conf /var/lib/lxc/logs/rootfs/etc/rsyslog.conf"
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n logs -- mkdir /var/log/mislogs"
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n logs -- chown syslog:syslog /var/log/mislogs"
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n logs -- service rsyslog restart"
	call (cmd_line, shell=True)
	cmd_line = "sudo /lab/cdps/bin/cp2lxc ./logs/clientes/rsyslog.conf /var/lib/lxc/bbdd/rootfs/etc/rsyslog.conf"
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n bbdd -- service rsyslog restart"
	call (cmd_line, shell=True)
	cmd_line = "sudo /lab/cdps/bin/cp2lxc ./logs/clientes/rsyslog.conf /var/lib/lxc/nas1/rootfs/etc/rsyslog.conf"
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nas1 -- service rsyslog restart"
	call (cmd_line, shell=True)
	cmd_line = "sudo /lab/cdps/bin/cp2lxc ./logs/clientes/rsyslog.conf /var/lib/lxc/nas2/rootfs/etc/rsyslog.conf"
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nas2 -- service rsyslog restart"
	call (cmd_line, shell=True)
	cmd_line = "sudo /lab/cdps/bin/cp2lxc ./logs/clientes/rsyslog.conf /var/lib/lxc/nas3/rootfs/etc/rsyslog.conf"
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n nas3 -- service rsyslog restart"
	call (cmd_line, shell=True)
	cmd_line = "sudo /lab/cdps/bin/cp2lxc ./logs/clientes/rsyslog.conf /var/lib/lxc/s1/rootfs/etc/rsyslog.conf"
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n s1 -- service rsyslog restart"
	call (cmd_line, shell=True)
	cmd_line = "sudo /lab/cdps/bin/cp2lxc ./logs/clientes/rsyslog.conf /var/lib/lxc/s2/rootfs/etc/rsyslog.conf"
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n s2 -- service rsyslog restart"
	call (cmd_line, shell=True)
	cmd_line = "sudo /lab/cdps/bin/cp2lxc ./logs/clientes/rsyslog.conf /var/lib/lxc/s3/rootfs/etc/rsyslog.conf"
	call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n s3 -- service rsyslog restart"
	call (cmd_line, shell=True)
	fin= open("pc2.cfg", 'r') # out file
	nservidores = int(fin.readlines()[0][0]) #Toma el valor del numero de servidores para utilizarlo en el bucle posteriormente
	fin.close()
	if nservidores == 4:
		cmd_line = "sudo /lab/cdps/bin/cp2lxc ./logs/clientes/rsyslog.conf /var/lib/lxc/s4/rootfs/etc/rsyslog.conf"
		call (cmd_line, shell=True)
		cmd_line = "sudo lxc-attach --clear-env -n s4 -- service rsyslog restart"
		call (cmd_line, shell=True)
	cmd_line = "sudo lxc-attach --clear-env -n logs -- service rsyslog restart"
	call (cmd_line, shell=True)
	logger.debug('%s - Servidor de logs configurado '%("LOGS"))


# OPERACIONES 

if len(sys.argv) > 1:
	operacion = sys.argv[1]
	servidores = [1,2,3]
	if operacion == "crear":
		def nuevoServidor():
			servidores.append(4)
			call(["sudo","vnx","-f","s4.xml","--create"])
		call(["sudo","vnx","-f","pc2.xml","--create"])
		logger.debug('%s - Escenario base creado'%("ESCENARIO"))
		if len(sys.argv) == 3:
			if sys.argv[2] == "s4":
				nuevoServidor()
				logger.debug('%s - Añadido el servidor s4 al escenario'%("ESCENARIO"))
		else:
			logger.debug('%s - Se ha optado por la configuracion por defecto'%("ESCENARIO"))
		# Numero de servidores en pc2.cfg 
		fout = open("pc2.cfg", 'w')
		fout.write(str(len(servidores)))
		fout.close()
	
	if operacion == "arrancar":
		call(["sudo","vnx","-f","pc2.xml","--start"])
		logger.debug('%s - Escenario base arrancado'%("ESCENARIO"))
		fin= open("pc2.cfg", 'r') # out file
		nservidores = int(fin.readlines()[0][0]) #Toma el valor del numero de servidores para utilizarlo en el bucle posteriormente
		fin.close()
		if nservidores == 4:
			call(["sudo","vnx","-f","s4.xml","--start"])
			logger.debug('%s - Arrancado el servidor s4'%("ESCENARIO"))

	if operacion == "parar":
		call(["sudo","vnx","-f","pc2.xml","--shutdown"])
		logger.debug('%s - Maquinas del escenario base paradas'%("ESCENARIO"))
		fin= open("pc2.cfg", 'r') # out file
		nservidores = int(fin.readlines()[0][0]) #Toma el valor del numero de servidores para utilizarlo en el bucle posteriormente
		fin.close()
		if nservidores == 4:
			call(["sudo","vnx","-f","s4.xml","--shutdown"])
			logger.debug('%s - Servidor s4 parado'%("ESCENARIO"))

	if operacion == "destruir":
		call(["sudo","vnx","-f","pc2.xml","--destroy"])
		logger.debug('%s - Maquinas del escenario base destruidas'%("ESCENARIO"))
		fin= open("pc2.cfg", 'r') # out file
		nservidores = int(fin.readlines()[0][0]) #Toma el valor del numero de servidores para utilizarlo en el bucle posteriormente
		fin.close()
		if nservidores == 4:
			call(["sudo","vnx","-f","s4.xml","--destroy"])
			logger.debug('%s - Servidor s4 destruido'%("ESCENARIO"))

	if operacion == "configuracionbasica":
		bbdd()
		nas()
		serv()
		lb()
		fw()
		logger.debug('%s - Escenario basico configurado'%("ESCENARIO"))

	if operacion == "nagios":
		nagios()

	if operacion == "gestion":
		gestion()

	if operacion == "logs":
		logs()

		



