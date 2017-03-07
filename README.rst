
CID - FutoIn Continuous Integration & Delivery Tool - Reference Implementation
==============================================================================

Intro
-----

There are many continuous integration & delivery tools, but they are primarily
targeted at own infrastructure. The demand for a new meta-tool is to merge
many operation of different technologies like npm, composer, bundler, nvm,
rvm, php-build and others under a single tool for runtime setup, project
development, build, deployment and running.

*NOTE: current focus is on web projects, but support of other types is a far
target.*

Full theoretical details are defined as FutoIn Spec FTN16 available at:
https://github.com/futoin/specs/blob/master/draft/ftn16_cid_tool.md

Supported technologies & tools (so far):

* **cmake** (uses make in proper order)
* **docker** (experimental)
    - **docker-compose**
* **make**
* **node**
    - **npm**
    - **bower**
    - **grunt**
    - **grulp**
    - **nvm** (implicit)
* **php** - both system & any php-build supported
    - **composer**
    - **php-build** (implicit)
* **python** - system 2 & 3
    - **virtualenv**, venv is ignored due to issues with *ensurepip* package
    - **pip**
* **ruby** - both system & any rvm supported
    - **gen**
    - **bundler**
    - **rvm** (implicit)
* **scp** - for RMS

Tested on the following OSes:

* **ArchLinux**
    - latest
* **CentOS**
    - **7** with EPEL repository enabled
* **Debian**
    - **8 - Jessie**
    - **9 - Stretch**
* **Fedora**
    - **25**
* **Gentoo**
    - Well... CID does support emerge, but you are on your own here ;)
* **OpenSUSE**
    - **42.1 Leap**
* **Ubuntu**
    - **14.04 LTS - Trusty**
    - **16.04 LTS - Xenial**
    - **16.10 - Yakkety**
* **Other Linux**
    - it should work without issues, if system packages are installed manually

Setup
-----

**cid** is written in commonly available Python language supporting both 
Python versions 2.7 and 3+.

Run the following: ::

    pip install futoin-cid

If pip is not available then it's strongly suggested to install one first: ::

    easy_install pip

To allow cid automatically install system packages, please allow execution
of apt-get, dnf, zypper or yum in sudoers. Example: ::

    username ALL=(ALL) NOPASSWD: /usr/bin/apt-get install
    username ALL=(ALL) NOPASSWD: /usr/bin/apt-get install *
    
    username ALL=(ALL) NOPASSWD: /usr/bin/dnf install
    username ALL=(ALL) NOPASSWD: /usr/bin/dnf install *
    
    username ALL=(ALL) NOPASSWD: /usr/bin/zypper install
    username ALL=(ALL) NOPASSWD: /usr/bin/zypper install *
    
    username ALL=(ALL) NOPASSWD: /usr/bin/yum install
    username ALL=(ALL) NOPASSWD: /usr/bin/yum install *

*Note: there are duplications with asterisk as some OSes have patched sudo*

Usage
-----

Please see details in the FTN16 spec: ::

    cid tag <branch> [<next_version>] [--vcsRepo vcs_url] [--wcDir wc_dir]
    
    cid prepare [<vcs_ref>] [--vcsRepo vcs_url] [--wcDir wc_dir]
    
    cid build
    
    cid package
    
    cid check [--permissive]
    
    cid promote <package> <rms_pool> [--rmsRepo rms_url]
        [--rmsHash type_value]
       
    cid deploy vcstag [<vcs_ref>] [--vcsRepo vcs_url] [--redeploy]
        [--deployDir deploy_dir]
       
    cid deploy vcsref <vcs_ref> [--vcsRepo vcs_url] [--redeploy]
        [--deployDir deploy_dir]
       
    cid deploy [rms] <rms_pool> [<package>] [--rmsRepo rms_url]
        [--rmsHash type_value] [--redeploy] [--deployDir deploy_dir] [--build]
    
    cid run [<command>]
    
    cid ci_build <vcs_ref> <rms_pool> [--vcsRepo vcs_url] [--rmsRepo rms_url]
        [--permissive]
    
    cid tool exec <tool_name> [-- <tool_arg>...]
    
    cid tool (install|uninstall|update|test|env) [<tool_name>]

