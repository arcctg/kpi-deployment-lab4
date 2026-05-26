Vagrant.configure("2") do |config|
  config.vm.box = "debian/bookworm64"

  config.vm.network "forwarded_port", guest: 80, host: 8080

  config.vm.provider "virtualbox" do |vb|
    vb.memory = 1024
    vb.cpus = 1
  end

  config.vm.provider "vmware_desktop" do |vmw|
    vmw.memory = 1024
    vmw.cpus = 1
  end

  config.vm.provision "shell",
    inline: "apt-get update -qq && apt-get install -y -qq python3"

  config.vm.provision "shell", path: "provision.py"
end
