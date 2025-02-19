# Use Ubuntu as the base image
FROM ubuntu:22.04

# Install sudo since it's not preinstalled in minimal Ubuntu images
RUN apt-get update -y && apt-get install -y sudo

# Create a user named 'dev-container' with a home directory and set its default shell
RUN useradd -m -s /bin/bash dev-container \
    && mkdir -p /home/dev-container \
    && chown -R dev-container:dev-container /home/dev-container

# Allow 'dev-container' user to run sudo commands without a password
RUN echo "dev-container ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Install system dependencies and update apt
RUN apt-get update -y && \
    apt-get upgrade -y && \
    apt-get install -y \
    zsh \
    curl \
    python3 \
    python3-pip \
    python3-venv \
    jq \
    unzip \
    git \
    git-lfs \
    gcc \
    g++ \
    make \
    tar \
    libc6 \
    && apt-get clean

# Set Python3 as the default Python version
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1 && \
    update-alternatives --set python /usr/bin/python3

# Update pip and install dependencies
RUN python -m pip install --upgrade pip setuptools wheel

# Install Node.js 18.x
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean

# Install AWS CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && ./aws/install && rm -rf awscliv2.zip aws

# Install AWS CDK globally
RUN npm install -g aws-cdk

# Copy requirements.txt and install dependencies
COPY requirements.txt requirements.txt
RUN python -m pip install -r requirements.txt

# Switch to the 'dev-container' user to set up Oh-My-Zsh and its plugins
USER dev-container

# Oh-my-zsh & plugins
ARG ZSH_PATH=/home/dev-container/.oh-my-zsh/custom
ARG PLUGINS="aws ansible docker zsh-syntax-highlighting colored-man-pages zsh-autosuggestions"

RUN curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh | bash || true && \
    mkdir -p $ZSH_PATH/plugins && \
    git clone https://github.com/zsh-users/zsh-autosuggestions "$ZSH_PATH/plugins/zsh-autosuggestions" && \
    git clone https://github.com/zsh-users/zsh-syntax-highlighting.git "$ZSH_PATH/plugins/zsh-syntax-highlighting" && \
    git clone https://github.com/spaceship-prompt/spaceship-prompt.git "$ZSH_PATH/themes/spaceship-prompt" --depth=1 && \
    ln -s "$ZSH_PATH/themes/spaceship-prompt/spaceship.zsh-theme" "$ZSH_PATH/themes/spaceship.zsh-theme" && \
    sed -i '/^ZSH_THEME/c\ZSH_THEME="spaceship"' /home/dev-container/.zshrc && \
    sed -i '/^plugins=(/ s/)$/ '"$PLUGINS"')/' /home/dev-container/.zshrc
