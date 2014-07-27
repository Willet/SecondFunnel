# Ansible Deployments & Provisioning

## Requirements

`pip install --upgrade ansible boto`

- also make sure its not installed by `brew`, may need to `brew prune` it

The `willet-admin-master` key is needed for initial provisioning and AMI building.


## Vagrant
Vagrant should just work out of the box by running
`vagrant up` If ssh errors occur it is probably due to hostname issues.

Recommendation if you have this problem:

Add to your SSH config `~/.ssh/config`

```
Host *.amazonaws.com
  StrictHostKeyChecking no
  User willet

Host 127.0.0.1
  StrictHostKeyChecking no
```

You may also need to remove lines from your `~/.ssh/known_hosts` to resolve the issue.

## Running


### Before Runing Commands

`ssh-add` to add your personal ssh key

`ssh-add willet-admin-master_id_rsa` for the production key (not needed for deploy)

### Commands

#### Command: Deploy

Production: `ansible-playbook -i inventory webservers.yml -l production -t deploy`

Stage: `ansible-playbook -i inventory webservers.yml -l stage -t deploy`

#### Command: Build AMIs

Production: `ansible-playbook -i inventory webservers_ami.yml -e app_environment=production`

Stage: `ansible-playbook -i inventory webservers_ami.yml -e app_environment=stage`

#### Command: Provision & Deploy

Generally this only useful to verify, since you should be rebuilding the AMI if this is happening.

Production: `ansible-playbook -i inventory webservers.yml -l production`

Stage: `ansible-playbook -i inventory webservers.yml -l stage`
