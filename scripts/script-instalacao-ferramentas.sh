#!/bin/bash

# O char '#' é utilizado para comentários no bash e em scripts em bash
# - Eu vou colocar os comentários após os comandos, mas é costume aparecer antes
# - Para cada comando tem um "|| exit 1", somente para forçar o script a terminar
#   a execução de tudo, caso algum dos comandos retorne algum erro na sua
#   execução.

versao=$(lsb_release -sr)
echo " [+] Versão do sistema: $versao"

if [[ "$versao" != "22.04" ]]
then
	echo " [!] Esse sistema não é 22.04"
	exit 1
fi

echo " [+] Instalando ferramentas para o usuario $USER"
echo "     [+] Update do apt"
sudo apt-get -qq update || exit 1
# -qq é uma flag para não ficar imprimindo muita informação na tela

echo " [+] Instalando build-essentials"
sudo apt-get -qq install build-essential -y || exit 1
# build-essential é o equivalente a instalar:
# - dpkg-dev: Pacote de ferramentas debian (https://packages.ubuntu.com/focal/dpkg-dev)
# - make: Utilitário de organização para compilação
# - libc6-dev: Cabeçalhos de arquivos e bibliotecas de desenvolvimento da libc
# - gcc e g++: Compiladores de C e C++

echo " [+] Instalando docker e docker-compose"
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --batch --yes --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get -qq update || exit 1
sudo apt-get -qq install docker-ce -y || exit 1
sudo update-alternatives --set iptables /usr/sbin/iptables-legacy || exit 1
sudo service docker start || exit 1
sudo curl -L https://github.com/docker/compose/releases/download/v2.4.1/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose || exit 1
sudo chmod +x /usr/local/bin/docker-compose || exit 1

echo "     [+] Inserindo o usuário atual ao grupo docker (para não precisar digitar sudo toda vez)"
sudo usermod -aG docker $USER || exit 1 

echo " [+] Apontando python para python3"
sudo apt-get -qq install python-is-python3 -y
# Esse é um pacote que simplesmente cria links simbólicos de python3 para python, pra não precisar digitar python3 ou python3.10

echo " [+] Instalando o gdb"
sudo apt-get -qq install gdb valgrind -y

echo " [+] Instalando o pip"
curl -sS https://bootstrap.pypa.io/get-pip.py | sudo python
sudo pip install pwntools 

echo " [+] Instalando o gef"
wget -O ~/.gdbinit-gef.py -q https://gef.blah.cat/py || exit 1
echo source ~/.gdbinit-gef.py >> ~/.gdbinit || exit 1

echo " [+] Término das instalações."
echo '     [+] Para aplicar alguma das modificações, finalize o wsl e '
echo '         inicie de novo ("wsl --shutdown"). Serviços também precisam '
echo '         ser inicializados (docker, por exemplo).'