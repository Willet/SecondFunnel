# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
    config.vm.box = "trusty64"
    config.vm.box_url = "https://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-amd64-vagrant-disk1.box"

    config.ssh.username = 'vagrant'
    config.ssh.forward_agent = true
    config.vm.network :public_network
    config.vm.network :forwarded_port, guest: 80, host: 8000
    config.vm.synced_folder ".", "/opt/secondfunnel/app", :mount_options => ["uid=1002,gid=1002"]

    config.vm.provider "virtualbox" do |v|
      v.memory = 2048
      v.cpus = 1
      v.gui = true
      # see https://github.com/mitchellh/vagrant/issues/391 (ssh issues on reload)
      v.customize ["modifyvm", :id, "--natnet1", "192.168/16"] # setup nat networking
      v.customize ["modifyvm", :id, "--rtcuseutc", "on"] # fix clocks for DHCP
      v.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
      v.customize ["modifyvm", :id, "--natdnsproxy1", "on"]
    end

    config.vm.provision "shell" do |shell|
        shell.privileged = true
        shell.inline = "perl -p -i -e 's/post-up route del default dev \\$IFACE/post-up  route del default dev \\$IFACE || true/g' /etc/network/interfaces"
    end

    config.vm.provision "ansible" do |ansible|
        ansible.playbook = "ansible/webservers.yml"
        ansible.groups = {
          "vagrant" => ["default"],
          "webservers" => ["default"]
        }
    end
end
