
Vagrant.configure("2") do |config|
  config.vm.box_check_update = false

  config.vm.provision "shell", inline: <<-SHELL
     apt-get update
     apt-get install -y apache2
  SHELL
  
    config.vm.provider "virtualbox" do |v|
        v.linked_clone = true
        v.memory = 320
        v.cpus = 2
        if ENV['VAGRANT_GUI']
            v.gui = 1
        end
        
        v.customize [
            "storagectl", :id,
            "--name", 'SATA Controller',
            "--hostiocache", "on"
        ]
    end
    
    # make sure present on all boxes
    config.vm.synced_folder ".", "/vagrant", type: "rsync", rsync__exclude: ".git/"
    
    config.vm.provision "shell", inline: <<-SHELL
which apt-get && (sudo apt-get install -y \
    python3-minimal \
    python-nose python3-nose \
    python-docopt python3-docopt \
    || exit 1)
which yum && ( \
    sudo yum install epel-release && \
    sudo yum install python34 \
        python34-nose python2-nose \
        python-docopt \
    || exit 1)
true
    SHELL

    
    {
        'debian_jessie' => 'debian/jessie64',
        'debian_stretch' => 'fujimakishouten/debian-stretch64',
        'ubuntu_trusty' => 'bento/ubuntu-14.04',
        'ubuntu_xenial' => 'bento/ubuntu-16.04',
        'ubuntu_yakkety' => 'bento/ubuntu-16.10', # non-LTS
        #'ubuntu_zesty' => 'bento/ubuntu-17.04', # non-LTS
        'centos_5' => 'centos/5',
        'centos_6' => 'centos/6',
        'centos_7' => 'centos/7',
    }.each do |name, box|
        config.vm.define('cid_' + name) do |node|
            node.vm.box = box
        end
    end
end
