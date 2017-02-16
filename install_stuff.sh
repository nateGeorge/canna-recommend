# install script for ubuntu 16.04 server on AWS
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install python-minimal python-pip mongodb -y
pip install --upgrade pip

pip install --upgrade --no-cache-dir https://get.graphlab.com/GraphLab-Create/2.1/your email/your license key/GraphLab-Create-License.tar.gz
sudo pip install sklearn numpy pandas scipy pymongo spacy nltk bs4 selenium fake_useragent flask reqests ipython
python2 install_nltk_packages.py
sudo iptables -t nat -A OUTPUT -o lo -p tcp --dport 80 -j REDIRECT --to-port 10001
sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-ports 10001
sudo iptables -t nat -D PREROUTING 1
