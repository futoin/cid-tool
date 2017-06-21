
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
    
    config.vm.provision "shell", inline: <<-SHELL
which apt-get 2>/dev/null && apt-get update || true
which apk 2>/dev/null && apk update || true
    SHELL
    
    vms = {
        'rmshost' => 'debian/jessie64',
        'debian_stretch' => 'debian/stretch64',
        'ubuntu_xenial' => 'bento/ubuntu-16.04',
        'centos_7' => 'centos/7',
        'opensuse_leap' => 'bento/opensuse-leap-42.1',
        'fedora_25' => 'bento/fedora-25',
        'archlinux' => 'ogarcia/archlinux-x64',
        'alpinelinux' => 'maier/alpine-3.6-x86_64',

        # behaves similar to CentOS, but limited
        #'ol_7' => 'boxcutter/ol73',
        #'rhel_7' => 'iamseth/rhel-7.3',
        #'sles_12' => 'suse/sles12sp1',

        # not part of standard test cycle
        #'macos' => 'jhcook/macos-sierra',
        #'macos' => 'http://files.dryga.com/boxes/osx-sierra-0.3.1.box',
        #'funtoo' => 'tonyczeh/funtoo-generic64-pure64',
        #'gentoo' => 'cmiles/gentoo-amd64-minimal',

        # older versions
        'debian_jessie' => 'debian/jessie64',
        'ubuntu_trusty' => 'bento/ubuntu-14.04',
        #'ubuntu_yakkety' => 'bento/ubuntu-16.10', # non-LTS
        'ubuntu_zesty' => 'wholebits/ubuntu17.04-64', # non-LTS
        #'centos_6' => 'centos/6', # too old
    }
    
    vms.each do |name, box|
        config.vm.define('cid_' + name) do |node|
            node.vm.box = box
            
            group = 'root'
            
            if box.split('/')[0] == 'centos'
                dist_controller = 'IDE'
            elsif name == 'archlinux'
                dist_controller = 'IDE Controller'
                node.vm.provision 'shell', inline: 'sudo pacman -Syu --noconfirm'
                # requires vagrant-reload plugin
                node.vm.provision :reload
            elsif name == 'macos'
                dist_controller = 'SATA'
                group = 'staff'
            elsif name == 'sles_12'
                dist_controller = 'SCSI'
            else
                dist_controller = 'SATA Controller'
            end
            
            if ['ubuntu_trusty', 'centos_7', 'debian_stretch', 'alpinelinux'].include? name
                nic_type = '82540EM'
            else
                nic_type = 'virtio'
            end
            
            node.vm.provider "virtualbox" do |v|
                v.customize [
                    "storagectl", :id,
                    "--name", dist_controller,
                    "--hostiocache", "on"
                ]
            end
            
            node.vm.synced_folder ".", "/vagrant", type: "rsync", rsync__exclude: ".git/", create: true, group: group
            
            if name == 'rmshost'
                node.vm.provider "virtualbox" do |v|
                    v.memory = 2048
                end
                
                node.vm.provision "shell", inline: <<-SHELL
                    cd /vagrant && sudo -H -u vagrant /vagrant/tests/run.sh rmshost
                SHELL
                
                node.vm.network(
                    "private_network",
                    adapter: 2,
                    ip: "10.11.1.11",
                    netmask: "24",
                    nic_type: nic_type,
                    virtualbox__intnet: "ciddmz",
                    auto_config: true
                )
            else
                host_addr = 100 + vms.keys().index(name)
            
                node.vm.network(
                    "private_network",
                    adapter: 2,
                    ip: "10.11.1.#{host_addr}",
                    netmask: "255.255.255.0",
                    nic_type: nic_type,
                    virtualbox__intnet: "ciddmz",
                    auto_config: true
                )
                
                node.vm.provision "shell", run: "always", inline: <<-SHELL
                    ip addr  | grep DOWN | cut -d ' ' -f2 | tr ':' ' ' | xargs -n1 --no-run-if-empty ifup
                SHELL
            end
        end
    end
end
