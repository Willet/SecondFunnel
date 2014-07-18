# Ansible Deployments & Provisioning

## Requirements

`pip install --upgrade ansible`

- also make sure its not installed by `brew`, may need to `brew prune` it

Using `willet-admin-master` key is needed for initial provisioning.


## Running

### Before Runing Commands

`ssh-add` to add your personal ssh key

`ssh-add willet-admin-master_id_rsa` for the production key

### Commands

** Test - Provision & Deploy **

`ansible-playbook -i inventory webservers.yml -l stage`

** Test - Deploy **

`ansible-playbook -i inventory webservers.yml -l stage -t deploy`

** Production - Provision & Deploy **

`ansible-playbook -i inventory webservers.yml -l production`

**  Production - Deploy **

`ansible-playbook -i inventory webservers.yml -l production -t deploy`

