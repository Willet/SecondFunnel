#!/bin/sh

# NOTE: this file is not copied to running instances!
# setup the below environment variables and set on AMI's
# within AWS Console

APP_ENVIRONMENT=production  # alternative: stage
GIT_BRANCH=master           # alternative: dev
#APP_ENVIRONMENT=stage
#GIT_BRANCH=dev
PLAYBOOK=ansible/webservers.yml
TAGS=deploy
REPO_NAME=SecondFunnel
GIT_REPO=git@github.com:Willet/SecondFunnel.git
DEPLOY_KEY=/opt/secondfunnel/willet_deploy_key_id_rsa
INVENTORY_FILE=~/ansible_local_inventory

# start the ssh-agent, and set it up in the current shell
eval `ssh-agent`

# add the deploy key to the running ssh-agent
ssh-add $DEPLOY_KEY

# create temporary environment file
echo -e "[$APP_ENVIRONMENT]\nlocalhost" > $INVENTORY_FILE

# git clone the repo (for ansible playbooks),
# and then run the ansible playbook against the localhost
cd ~/
git clone --branch $GIT_BRANCH --single-branch --depth 1 $GIT_REPO $REPO_NAME
cd $REPO_NAME
ansible-playbook -i $INVENTORY_FILE -e app_environment=$APP_ENVIRONMENT $PLAYBOOK -t $TAGS
cd -

# cleanup
rm -rf $REPO_NAME $INVENTORY_FILE
