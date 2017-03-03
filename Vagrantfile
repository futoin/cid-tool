
Vagrant.configure("2") do |config|
    config.vm.box_check_update = false
  
    config.vm.provider "virtualbox" do |v|
        v.linked_clone = true
        v.memory = 512
        v.cpus = 2
        if ENV['VAGRANT_GUI']
            v.gui = 1
        end
    end
    
    # make sure present on all boxes
    config.vm.synced_folder ".", "/vagrant", type: "rsync", rsync__exclude: ".git/", create: true, group: 'root'
    
    config.vm.provision "shell", inline: <<-SHELL
which apt-get && ( \
    apt-get update && \
    apt-get install -y \
    python3-minimal \
    python-nose python3-nose \
    python-docopt python3-docopt \
    || exit 1)
which yum && ( \
    yum install -y epel-release; \
    yum install -y python34 python34-setuptools; \
    easy_install-3.4 pip; \
    pip3.4 install docopt nose; \
    ( \
        yum install -y python-setuptools; \
        which easy_install-2.7 && (
            easy_install-2.7 pip; \
            pip2.7 install docopt nose \
        ) || (
            yum install -y centos-release-scl; \
            yum install -y python27; \
            source /opt/rh/python27/enable; \
            easy_install-2.7 pip; \
            pip2.7 install docopt nose \
        )
    )
    )
which zypper && ( \
    zypper install -y python3 \
        python-nose python3-nose \
        python-docopt python3-docopt \
    || exit 1)
true
    SHELL
    
    {
        'debian_jessie' => 'debian/jessie64',
        'ubuntu_xenial' => 'bento/ubuntu-16.04',
        'centos_7' => 'centos/7',
        'opensuse_leap' => 'bento/opensuse-leap-42.1',
        
        'debian_stretch' => 'fujimakishouten/debian-stretch64',
        'ubuntu_trusty' => 'bento/ubuntu-14.04',
        'ubuntu_yakkety' => 'bento/ubuntu-16.10', # non-LTS
        #'ubuntu_zesty' => 'bento/ubuntu-17.04', # non-LTS
        #'centos_6' => 'centos/6', # too old
    }.each do |name, box|
        config.vm.define('cid_' + name) do |node|
            node.vm.box = box
            
            if box.split('/')[0] == 'centos'
                dist_controller = 'IDE'
                
                config.vm.provision "shell", inline: <<-SHELL
sudo cat > /etc/yum.repos.d/wandisco-svn.repo <<EOC
[WANdiscoSVN]
name=WANdisco SVN Repo 1.9
enabled=1
baseurl=http://opensource.wandisco.com/centos/#{box.split('/')[1]}/svn-1.9/RPMS/$basearch/
gpgcheck=1
gpgkey=http://opensource.wandisco.com/RPM-GPG-KEY-WANdisco
EOC
                SHELL
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
