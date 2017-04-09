
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
which apt-get && apt-get update || true
    SHELL
    
    {
        'debian_jessie' => 'debian/jessie64',
        'ubuntu_xenial' => 'bento/ubuntu-16.04',
        'centos_7' => 'centos/7',
        'opensuse_leap' => 'bento/opensuse-leap-42.1',
        'fedora_25' => 'bento/fedora-25',
        #'funtoo' => 'tonyczeh/funtoo-generic64-pure64',
        #'gentoo' => 'cmiles/gentoo-amd64-minimal',
        'archlinux' => 'ogarcia/archlinux-x64',
        # behaves similar to CentOS, but limited
        #'ol_7' => 'boxcutter/ol73',
        # not part of standard test cycle
        #'macos' => 'jhcook/macos-sierra',
        #'macos' => 'http://files.dryga.com/boxes/osx-sierra-0.3.1.box',
        
        'debian_stretch' => 'fujimakishouten/debian-stretch64',
        'ubuntu_trusty' => 'bento/ubuntu-14.04',
        'ubuntu_yakkety' => 'bento/ubuntu-16.10', # non-LTS
        #'ubuntu_zesty' => 'bento/ubuntu-17.04', # non-LTS
        #'centos_6' => 'centos/6', # too old
    }.each do |name, box|
        config.vm.define('cid_' + name) do |node|
            node.vm.box = box
            
            group = 'root'
            
            if box.split('/')[0] == 'centos'
                dist_controller = 'IDE'
            elsif name == 'archlinux'
                dist_controller = 'IDE Controller'
            elsif name == 'macos'
                dist_controller = 'SATA'
                group = 'staff'
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
            
            node.vm.synced_folder ".", "/vagrant", type: "rsync", rsync__exclude: ".git/", create: true, group: group
        end
    end
end
