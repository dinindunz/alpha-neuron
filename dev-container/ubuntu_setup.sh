sudo whoami
pwd
sudo visudo
cat visudo
sudo visudo
sudo whoami
sudo apt install nvidia-cuda-toolkit
sudo apt install ~/Downloads/synergy-3.2.1-linux-noble-x64.deb
sudo apt install curl
sudo apt install docker.io
sudo groupadd docker
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg  && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list |  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' |  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sed -i -e '/experimental/ s/^#//g' /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo sed -i -e '/experimental/ s/^#//g' /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
sudo docker run -d -p 3000:8080 --gpus=all -v ollama:/root/.ollama -v open-webui:/app/backend/data --name open-webui --restart always ghcr.io/open-webui/open-webui:ollama
sudo apt install zsh
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting
git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
git clone https://github.com/spaceship-prompt/spaceship-prompt.git ~/.zsh/spaceship-prompt
ln -s ~/.zsh/spaceship-prompt/spaceship.zsh-theme ~/.oh-my-zsh/custom/themes/spaceship.zsh-theme
chsh -s /usr/bin/zsh
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
sudo docker run -d -p 9000:9000 -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/data  --name portainer --restart always portainer/portainer-ce:latest
code -r /home/dinindu/.ssh/gitkraken_rsa
code -r /home/dinindu/.ssh/gitkraken_rsa.pub
chmod 600 ~/.ssh/gitkraken_rsa
sudo apt install timeshift
sudo apt install fortune cowsay
sudo apt install fortune-mod
sudo apt install lolcat
code -r ~/.aws/config
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
sudo apt install openjdk-11-jdk
wget https://downloads.lightbend.com/scala/2.13.12/scala-2.13.12.deb
sudo dpkg -i scala-2.13.12.deb
sudo apt install nvtop
sudo dpkg -i lm-studio-*.deb
chmod +x LM-Studio-0.3.9-6-x64.AppImage
sudo apt install libfuse2 -y
./LM-Studio-0.3.9-6-x64.AppImage --no-sandbox