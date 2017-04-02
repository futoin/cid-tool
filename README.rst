
CID - The Manager of Managers - FutoIn Continuous Integration & Delivery Tool
==============================================================================

Intro
-----

There are many continuous integration & delivery tools, but they are primarily
targeted at own infrastructure. The demand for a new meta-tool is to merge
many operations of different technologies like npm, composer, bundler, nvm,
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
* **go**
    - **gvm**
* **java** for runtime (uses Zulu JDK unless overriden by javaBin)
    - **ant**
    - **gradle**
    - **jdk** for development (uses Zulu JDK unless overriden by jdkDir)
    - **maven**
    - **sdkman** for SDK management (besides JRE & JDK)
* **make**
* **node**
    - **npm**
    - **bower**
    - **grunt**
    - **gulp**
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
* **rust**
    - **rustup**
    - **cargo**
* **scala**
    **sbt** - Simple Build Tools for Scala
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
        Not included in standard test cycle.
* **OpenSUSE**
    - **42.1 Leap**
* **Oracle Linux**
    - **7** - supported as CentOS, but some packages (e.g. Docker) must be
        installed manually. Not included in standard test cycle.
* **RedHat Enterprise Linux**
    - **7** - see notes for Oracle Linux
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
    username ALL=(ALL) NOPASSWD: /usr/bin/apt-get update
    username ALL=(ALL) NOPASSWD: /usr/bin/apt-add-repository
    username ALL=(ALL) NOPASSWD: /usr/bin/apt-add-repository *
    # Potential security issue, you may want to install GPG keys manually
    username ALL=(ALL) NOPASSWD: /usr/bin/apt-key add
    username ALL=(ALL) NOPASSWD: /usr/bin/apt-key add *
    
    username ALL=(ALL) NOPASSWD: /usr/bin/dnf install
    username ALL=(ALL) NOPASSWD: /usr/bin/dnf install *

    username ALL=(ALL) NOPASSWD: /usr/bin/emerge
    username ALL=(ALL) NOPASSWD: /usr/bin/emerge *
    
    username ALL=(ALL) NOPASSWD: /usr/bin/pacman
    username ALL=(ALL) NOPASSWD: /usr/bin/pacman *

    username ALL=(ALL) NOPASSWD: /usr/bin/zypper install
    username ALL=(ALL) NOPASSWD: /usr/bin/zypper install *
    username ALL=(ALL) NOPASSWD: /usr/bin/zypper addrepo
    username ALL=(ALL) NOPASSWD: /usr/bin/zypper addrepo *
    
    username ALL=(ALL) NOPASSWD: /usr/bin/yum install
    username ALL=(ALL) NOPASSWD: /usr/bin/yum install *
    username ALL=(ALL) NOPASSWD: /usr/bin/yum-config-manager --add-repo
    username ALL=(ALL) NOPASSWD: /usr/bin/yum-config-manager --add-repo *
    
    # For dnf, yum and zypper
    # Potential security issue, you may want to install GPG keys manually
    username ALL=(ALL) NOPASSWD: /usr/bin/rpm --import
    username ALL=(ALL) NOPASSWD: /usr/bin/rpm --import *

*Note: there are duplications with asterisk as some OSes have patched sudo*

Usage
-----

Please see details in the FTN16 spec: ::

    cid tag <branch> [<next_version>] [--vcsRepo=<vcs_repo>] [--wcDir=<wc_dir>]
        Get the latest <branch>.
        Update source for release & commit.
        Create tag.
        If <next_version> is omitted, the smallest version part is incremented.
        Current version is determined by tools (e.g. from package.json)
    
    cid prepare [<vcs_ref>] [--vcsRepo=<vcs_repo>] [--wcDir=<wc_dir>]
        Retrieved the specific <vcs_ref>, if provided.
        --vcsRepo is required, if not in VCS working copy.
        Action depends on detected tools:
        * should clean up the project
        * should retrieve external dependencies
    
    cid build [--debug]
        Action depends on detected tools.
        Runs tool-specific build/compilation.
    
    cid package
        Action depends on detected tools.
        Runs tool-specific package.
        If package is not found then config.package folder is put into archive -
            by default it's '.' relative to project root.
    
    cid check [--permissive]
        Action depends on detected tools.
        Runs tool-specific test/validation.
    
    cid promote <package> <rms_pool> [--rmsRepo=<rms_repo>]
        [--rmsHash=<rms_hash>]
        Promote package to Release Management System (RMS) or manage
        package across RMS pools.
       
    cid deploy vcstag [<vcs_ref>] [--vcsRepo=<vcs_repo>] [--redeploy]
        [--deployDir=<deploy_dir>]
        Deploy from VCS tag.
       
    cid deploy vcsref <vcs_ref> [--vcsRepo=<vcs_repo>] [--redeploy]
        [--deployDir=<deploy_dir>]
        Deploy from VCS branch.
       
    cid deploy [rms] <rms_pool> [<package>] [--rmsRepo=<rms_repo>]
        [--rmsHash=<rms_hash>] [--redeploy] [--deployDir=<deploy_dir>]
        [--build]
        Deploy from RMS.
    
    cid run [<command>]
        Not implemented yet.
    
    cid ci_build <vcs_ref> <rms_pool> [--vcsRepo=<vcs_repo>]
        [--rmsRepo=<rms_repo>] [--permissive] [--debug]
        Run prepare, build and package in one run.
    
    cid tool exec <tool_name> [-- <tool_arg>...]
        Execute <tool_name> binary with provided arguments.
        Tool and all its dependencies are automatically installed.
        Note: not all tools support execution.
    
    cid tool (install|uninstall|update) [<tool_name>]
        Manage tools.
        Note: not all tools support all kinds of actions.
    
    cid tool test [<tool_name>]
        Test if tool is installed.

    cid tool env [<tool_name>]
        Dump tool-specific environment variables to be set in shell
        for execution without CID.
        Tool and all its dependencies are automatically installed.

    cid tool (prepare|build|check|package|migrate) <tool_name>
        Run standard actions described above only for specific tool.
        Tool and all its dependencies are automatically installed.
        Note: auto-detection is skipped and tool is always run.
    
    cid tool list
        Show a list of supported tools.

    cid tool describe <tool_name>
        Show tool's detailed description.
        
    cid init [<project_name>] [--vcsRepo=<vcs_repo>]
        [--rmsRepo=<rms_repo>] [--permissive]
        Initialize futoin.json with automatically detected data.
        
        If <project_name> is omitted and not known from
        auto-detection then basename of containing folder is used.

Excplicit futoin.json example
-----------------------------

futoin.json is not strictly required, but it allows to use full power of CID.

.. code-block:: json

    {
      "name": "example-package",
      "version": "0.4.2",
      "actions": {
        "package": []
      },
      "plugins": {
        "examplerelease": "some.project.specific.release",
        "examplehelper": "some.other.helpertool"
      },
      "vcs": "git",
      "tools": {
        "examplerelease": true,
        "python": "*",
        "node": "stable",
        "gradle": "*"
      },
      "toolTune" : {
        "gradle": {
          "package": "jar"
        }
      },
      "rms": "scp",
      "rmsRepo": "rms@somehost",
      "rmsPool": "ReleaseBuilds",
      "main": {
        "app": {
          "tool": "python",
          "path": "app.py",
          "tune": {}
        }
      }
    }


