
Vagrant.configure("2") do |config|
    config.vm.box_check_update = false
  
    config.vm.provider "virtualbox" do |v|
        v.linked_clone = true
        v.memory = 320
        v.cpus = 2
        if ENV['VAGRANT_GUI']
            v.gui = 1
        end
    end
    
    # make sure present on all boxes
    config.vm.synced_folder ".", "/vagrant", type: "rsync", rsync__exclude: ".git/", create: true, group: 'root'
    
    config.vm.provision "shell", inline: <<-SHELL
which apt-get && (sudo apt-get install -y \
    python3-minimal \
    python-nose python3-nose \
    python-docopt python3-docopt \
    || exit 1)
which yum && ( \
    sudo yum -y install epel-release && \
    sudo yum -y install python34 \
        python34-nose python-nose \
        python-docopt && \
    easy_install-3.4 pip && \
    sudo pip3 install docopt \
    || exit 1)
which zypper && ( \
    sudo zypper install -y python3 \
        python-nose python3-nose \
        python-docopt python3-docopt \
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
        #'centos_5' => 'bento/centos-5.11',
        #'centos_6' => 'centos/6',
        'centos_7' => 'centos/7',
        'opensuse_leap' => 'bento/opensuse-leap-42.1',
    }.each do |name, box|
        config.vm.define('cid_' + name) do |node|
            node.vm.box = box
            
            if box.split('/')[0] == 'centos'
                dist_controller = 'IDE'
            else
                dist_controller = 'SATA Controller'
            end
            
            node.vm.provider "virtualbox" do |v|
                v.customize [
                    "storagectl", :id,
                    "--name", dist_controller,
                    "--hostiocache", "on"
                ]
            end
        end
    end
end
