#!/bin/sh

# NOTE: this file is not copied to running instances!
# setup the below environment variables and set on AMI's
# within AWS Console

echo "
Host github.com
  ForwardAgent yes
  StrictHostKeyChecking no
" >> ~/.ssh/config

APP_ENVIRONMENT=production
PLAYBOOK=ansible/webservers.yml
TAGS=deploy
REPO_NAME=SecondFunnel
GIT_REPO=git@github.com:Willet/SecondFunnel.git
DEPLOY_KEY=/opt/secondfunnel/willet_deploy_key_id_rsa
GIT_BRANCH=dev
INVENTORY_FILE=~/ansible_local_inventory

# start the ssh-agent, and set it up in the current shell
eval `ssh-agent`

# add the deploy key to the running ssh-agent
ssh-add $DEPLOY_KEY

# add github.com as a known_hosts (so we can ansible-playbook against it)
ssh-keyscan -t rsa,dsa github.com 2>&1 | sort -u - ~/.ssh/known_hosts > ~/.ssh/tmp_hosts
cat ~/.ssh/tmp_hosts >> ~/.ssh/known_hosts

echo -e "[$APP_ENVIRONMENT]\nlocalhost" > $INVENTORY_FILE

# git clone the repo (for ansible playbooks),
# and then run the ansible playbook
cd ~/
git clone --branch $GIT_BRANCH --single-branch --depth 1 $GIT_REPO $REPO_NAME
cd $REPO_NAME
ansible-playbook -i $INVENTORY_FILE -e app_environment=$APP_ENVIRONMENT $PLAYBOOK -t $TAGS
cd ~/
rm -rf SecondFunnel $INVENTORY_FILE
