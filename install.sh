#!/bin/bash -ex

echo "installing homebrew"
ruby -e "$(curl -fsSL https://raw.github.com/Homebrew/homebrew/go/install)"

echo "Installing Packages with Homebrew"
brew install ack autoconf automake curl \
    coreutils brew-cask git libxml2 libxslt \
    libyaml libpng libtiff libffi node openssl \
    sqlite s3cmd zsh

echo "installing rvm + ruby"
curl -sSL https://get.rvm.io | bash -s stable --ruby

echo "install pip"
wget https://bootstrap.pypa.io/get-pip.py
sudo python get-pip.py

echo "install packages"
sudo pip install ansible boto
