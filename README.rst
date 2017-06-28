
CID - FutoIn Continuous Integration & Delivery Tool
==============================================================================

Intro
-----

There are many continuous integration & delivery tools, but they are primarily
targeted at own infrastructure. The demand for a new meta-tool is to merge
many operations of different technologies like npm, composer, bundler, nvm,
rvm, php-build and others under a single tool for runtime setup, project
development, build, deployment and running.

*NOTE: current focus is on web projects, but other types are supported as well.*

Full theoretical details are defined as FutoIn Spec FTN16 available at:
https://github.com/futoin/specs/blob/master/draft/ftn16_cid_tool.md

Features
~~~~~~~~

* Single tool for development, testing and production
* Intelligent automation of human-like behavior
* Automatic detection & setup of all tool dependencies
* Resource limit auto-detection & distribution
* Rolling deployments for zero downtime
* Container-friendly
* Technology-neutral
* Easily extendable & portable
* Fine tune of all aspects

Supported technologies & tools (so far):
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*Note: please use* **cid tool list** *and* **cid tool describe $tool** *for details.*

* **cmake**
* **docker**

  - **docker-compose**
    
* **go**

  - **gvm**
    
* **java** for runtime (uses Zulu JDK unless overridden)

  - **ant**
  - **gradle**
  - **jdk** for development (uses Zulu JDK unless overridden)
  - **maven**
  - **sdkman** for SDK management (besides JRE & JDK)

* **jfrog** - JFrog CLI
    
* **make**
* **nginx** - true web server for development, testing & production
* **node**

  - **npm**
  - **bower**
  - **grunt**
  - **gulp**
  - **nvm** (implicit)
    
* **php** - system, php-build supported and binary builds (Sury, SCL)

  - **composer**
  - **php-build** (implicit)
    
* **python** - system 2 & 3

  - **virtualenv**, venv is ignored due to issues with *ensurepip* package
  - **pip**
  - **twine** - as limited RMS tool
  - **uwsgi** - to run application behind nginx (or other web server)
    
* **ruby** - system, rvm supported and binary builds (Brightbox, SCL)

  - **gen**
  - **bundler**
  - **rvm** (implicit)
    
* **rust**

  - **rustup**
  - **cargo**
    
* **scala**

  - **sbt** - Simple Build Tools for Scala


Supported Version Control Systems(VCS):
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Git**
* **Mercurial**
* **Subversion**


Supported Release Management Systems (RMS):
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **archiva** - supporting non-Maven layout through WebDAV.

  - Always tested in standard cycle.

- **artifactory** - only Pro version as OSS is very limited for automation.

  - NOT tested in standard test cycle as JFrog did not provide license for development.

- **nexus** - only v2 as v3 lacks complete REST API yet.

  - Always tested in standard cycle.

- **scp** - SSH-based secure copy.

  - Always tested in standard cycle.

- **svn** - Subversion is quite suitable for Production release builds,
  but please **avoid using it for snapshots**.
  
  - Always tested in standard cycle.

- **twine** - Upload only to Python Package Index.

  - Promotion between repos is not supported.

- Not implemented, but planned:

  - Nexus v3 - after sane REST API is implemented.

Tested on the following OSes:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **AlpineLinux**

  - There are known incompatibilities with glibc-based binaries.

* **ArchLinux**

  - latest
    
* **CentOS**

  - **7**
    
* **Debian**

  - **8 - Jessie**
  - **9 - Stretch**
    
* **Fedora**

  - **25**
  
* **Gentoo**

  - Well... CID does support emerge, but you are on your own here ;)
    Not included in standard test cycle.
    
* **macOS**

  - **Sierra**
  - Test hardware is:

  .. image:: https://images1-focus-opensocial.googleusercontent.com/gadgets/proxy?container=focus&refresh=3600&resize_h=100&url=https://www.macstadium.com/content/uploads/2016/07/Powered_by_MacStadium_Logo-1.png
     :align: right
     :target: https://www.macstadium.com/
    
* **OpenSUSE**

  - **42.1 Leap**
    
* **Oracle Linux**

  - **7** - supported as CentOS. Not included in standard test cycle.
    
* **RedHat Enterprise Linux**

  - **7** - supported as CentOS. Not included in standard test cycle.
    
* **Ubuntu**

  - **14.04 LTS - Trusty**
  - **16.04 LTS - Xenial**
  - **16.10 - Yakkety**
  - **17.04 - Zesty**
    
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

For best user experience, it's suggested to allow system package installation (only)
through sudo without password. It should minimize impact on security.

A convenient OS-agnostic way is to do it this way: ::

    cid sudoers | sudo tee -a /etc/sudoers

One obvious drawback is management of package trusted signing keys. It can be disabled.
Then please run the following command instead: ::

    cid sudoers --skip-key-management | sudo tee -a /etc/sudoers

Typical use cases
-----------------

1. Prepare project for development: ::

    cid prepare master --vcsRepo=git:user@host:git/repo.git
    # create VCS working copy with specified VCS ref
    # auto-detects tools and executes:
    #  npm install, composer install, bundle install, etc.

2. Prepare project for release: ::

    cid tag master
    # updates auto-detected files like package.json
    # creates tags
    # "patch" version increment is the default behavior

3. Release builds on CI server: ::

    cid ci_build v1.0.0 Releases --vcsRepo=git:user@host:git/repo.git \
        --rmsRepo=svn:user@host/rms

4. Nightly builds on CI server: ::

    cid ci_build master Nightly --vcsRepo=git:user@host:git/repo.git \
        --rmsRepo=scp:user@host

5. Production-like execution environment in development: ::

    cid devserve
    # PHP-FPM, Ruby rack, Python WSGI, nginx... Doesn't matter - it knows how!

6. Staging deployment from VCS: ::

    cid deploy vcsref master --vcsRepo=git:user@host:git/repo.git \
        --deployDir=/www/staging \
        --limit-memory=1G
    # resource limits are preserved across runs, if not overridden

7. Production deployment from RMS: ::

    cid deploy rms Releases --rmsRepo=svn:user@host/rms \
        --deployDir=/www/prod \
        --limit-memory=8G \
        --limit-cpus=4
    # resource limits are preserved across runs, if not overridden

8. Alter resource limits before or after deployment: ::

    cid deploy setup
        --deployDir=/www/prod \
        --limit-memory=16G

9. Execution of deployed project: ::

    cid service master --deployDir=/www/prod

10. Use any supported tool without caring for setup & dependencies: ::

     cid tool exec dockercompose -- ...
     # ensures:
     # * setup of system Docker
     # * setup of virtualenv
     # * setup of pip
     # * setup of docker-compoer via pip into virtualenv
     # actually, executes

Usage
-----

Please see details in the FTN16 spec: ::

    cid init [<project_name>] [--vcsRepo=<vcs_repo>]
        [--rmsRepo=<rms_repo>] [--permissive]
        Initialize futoin.json with automatically detected data.
        
        If <project_name> is omitted and not known from
        auto-detection then basename of containing folder is used.
        
    cid tag <branch> [<next_version>] [--vcsRepo=<vcs_repo>] [--wcDir=<wc_dir>]
        Get the latest <branch>.
        Update source for release & commit.
        Create tag.
        
        Version must be in SEMVER x.y.z. format: http://semver.org/
        
        If <next_version> is omitted, the PATCH version part is incremented.
        
        If <next_version> is one of 'patch', 'minor' or 'major then
        the specified version part is incremented and all smaller parts are
        set to zero.
        
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
    
    cid promote <rms_pool> <packages>... [--rmsRepo=<rms_repo>]
        Promote package to Release Management System (RMS) or manage
        package across RMS pools.

        
    cid deploy ...
        Common arguments for deploy family of commands:
        [--deployDir=<deploy_dir>] - target folder, CWD by default.
        [--runtimeDir=<runtime_dir>] - target runtime data folder,
          <deploy_dir>/.runtime by default.
        [--tmpDir=<tmp_dir>] - target temporary data folder,
          <deploy_dir>/.tmp by default.
        [--limit-memory=<mem_limit>] - memory limit with B, K, M or G postfix.
        [--limit-cpus=<cpu_count>] - max number of CPU cores to use.
        [--listen-addr=<address>] - address to use for IP services
        [--user=<user>] - user name to run services.
        [--group=<group>] - user name to run services.
        
    cid deploy setup
        Prepare directory for deployment. Allows adjusting futoin.json
        before actual deployment is done to define limits once or add
        project settings overrides. Allows adjusting settings for next
        deployment. Not necessary otherwise.
       
    cid deploy vcstag [<vcs_ref>] [--vcsRepo=<vcs_repo>] [--redeploy]
        Deploy from VCS tag.
       
    cid deploy vcsref <vcs_ref> [--vcsRepo=<vcs_repo>] [--redeploy]
        Deploy from VCS branch.
       
    cid deploy rms <rms_pool> [<package>] [--rmsRepo=<rms_repo>] [--build]
        Deploy from RMS.
       
    cid deploy set-action <name> <actions>... [--deployDir=<deploy_dir>]
        Override .action in deployment config.
       
    cid deploy set-persistent <paths>... [--deployDir=<deploy_dir>]
        Add .persistent paths in deployment config.
       
       
    cid migrate
        Runs data migration tasks.

        Provided for overriding default procedures in scope of
        deployment procedure.
    
    cid run
        Run all configured .entryPoints.
    
    cid run <command>
        Checks if <command> is present in .entryPoints or in .actions
        then runs it.
    
    cid ci_build <vcs_ref> [<rms_pool>] [--vcsRepo=<vcs_repo>]
        [--rmsRepo=<rms_repo>] [--permissive] [--debug] [--wcDir=<wc_dir>]
        Run prepare, build and package in one run.
        if <rms_pool> is set then also promote package to RMS.
    
    
    cid tool ...
        Family tool-centric commands.
    
    cid tool exec <tool_name> [-- <tool_arg>...]
        Execute <tool_name> binary with provided arguments.
        Tool and all its dependencies are automatically installed.
        Note: not all tools support execution.
    
    cid tool (install|uninstall|update) [<tool_name>] [<tool_version>]
        Manage tools.
        Note: not all tools support all kinds of actions.
    
    cid tool test [<tool_name>]
        Test if tool is installed.

    cid tool env [<tool_name>]
        Dump tool-specific environment variables to be set in shell
        for execution without CID.
        Tool and all its dependencies are automatically installed.

    cid tool (prepare|build|check|package|migrate) <tool_name> [<tool_version>]
        Run standard actions described above only for specific tool.
        Tool and all its dependencies are automatically installed.
        Note: auto-detection is skipped and tool is always run.
    
    cid tool list
        Show a list of supported tools.

    cid tool describe <tool_name>
        Show tool's detailed description.
        
    cid tool detect
        Show list of auto-detected tools for current project
        with possible version numbers.

        
    cid vcs ...
        Abstract VCS helpers for CI environments & scripts.
        They are quite limited for daily use.
        
    cid vcs checkout [<vcs_ref>] [--vcsRepo=<vcs_repo>] [--wcDir=<wc_dir>]
        Checkout specific VCS ref.
        
    cid vcs commit <commit_msg> [<commit_files>...] [--wcDir=<wc_dir>]
        Commit all changes or specific files with short commit message.
    
    cid vcs merge <vcs_ref> [--no-cleanup] [--wcDir=<wc_dir>]
        Merge another VCS ref into current one. Abort on conflict.
        Automatic cleanup is done on abort, unless --no-cleanup.

    cid vcs branch <vcs_ref> [--wcDir=<wc_dir>]
        Create a new branch from current checkout VCS ref.
        
    cid vcs delete <vcs_ref> [--vcsRepo=<vcs_repo>] [--cacheDir=<cache_dir>]
        [--wcDir=<wc_dir>]
        Delete branch.
        
    cid vcs export <vcs_ref> <dst_dir> [--vcsRepo=<vcs_repo>]
        [--cacheDir=<cache_dir>] [--wcDir=<wc_dir>]
        Export VCS ref into folder.

    cid vcs tags [<tag_pattern>] [--vcsRepo=<vcs_repo>]
        [--cacheDir=<cache_dir>] [--wcDir=<wc_dir>]
        List tags with optional pattern for filtering.

    cid vcs branches [<branch_pattern>] [--vcsRepo=<vcs_repo>]
        [--cacheDir=<cache_dir>] [--wcDir=<wc_dir>]
        List branches with optional pattern for filtering.

    cid vcs reset [--wcDir=<wc_dir>]
        Revert all local changes, including merge conflicts.
        
    cid vcs ismerged <vcs_ref> [--wcDir=<wc_dir>]
        Check if branch is merged into current branch.

        
    cid rms ...
        Abstract RMS helpers for CI environments & scripts.
        They are quite limited for daily use.
        
    cid rms list <rms_pool> [<package_pattern>] [--rmsRepo=<rms_repo>]
        List package in specified RMS pool with optional pattern.
        
    cid rms retrieve <rms_pool> <packages>... [--rmsRepo=<rms_repo>]
        Retrieve package(s) from the specified RMS pool.
        
    cid rms pool create <rms_pool> [--rmsRepo=<rms_repo>]
        Ensure RMS pool exists. Creates, if missing.
        It may require admin privileges!

    cid rms pool list [--rmsRepo=<rms_repo>]
        List currently available RMS pools.
        
        
    cid devserve [--wcDir=<wc_dir>] [*generic deploy options*]
        Create temporary deployment directory and use working directory as "current".
        Re-balance services.
        Then act like "cid service list" and "cid service master".


    cid service ...
        Service execution helpers.

    cid service master [--deployDir=<deploy_dir>]
        [--adapt [*generic deploy options*]]
        Re-balance services, if --adapt.
        Run all entry points as children.
        Restarts services on exit.
        Has 10 second delay for too fast to exit services.
        Supports SIGTERM for clean shutdown.
        Supports SIGHUP for reload of service list & the services themselves.
    
    cid service list [--deployDir=<deploy_dir>]
        [--adapt [*generic deploy options*]]
        Re-balance services, if --adapt.
        List services in the following format:
        <entry point> <TAB> <instance ID> <TAB> <socket type> <TAB> <socket address>

    cid service exec <entry_point> <instance_id> [--deployDir=<deploy_dir>]
        Helper for system init to execute pre-configured service.
        
    cid service stop <entry_point> <instance_id> <pid> [--deployDir=<deploy_dir>]
        Helper for system init to gracefully stop pre-configured service.
        
    cid service reload <entry_point> <instance_id> <pid> [--deployDir=<deploy_dir>]
        Helper for system init to gracefully reload pre-configured service.
        Note: if reload is not supported then reload acts as "stop" to force restart.
        
    cid sudoers [<sudo_entity>] [--skip-key-management]
        Output ready sudoers entries specific to current OS.
        Current user is used by default, unless overridden.
        Only repository adding and package installation is allowed.
        For better security, it's possible to disable trusted signing key management
        with --skip-key-management.
        
    cid build-dep <build_dep>...
        Require specific development files to be installed, e.g.: openssl, mysqlclient,
        postgresql, imagemagick, etc.

Excplicit futoin.json example
-----------------------------

futoin.json is not strictly required, but it allows to use full power of CID.

.. code-block:: json

    {
      "name": "example-package",
      "version": "0.4.2",
      "actions": {
        "custom_script": [ "run some item" ]
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
      "entryPoints": {
        "app": {
          "tool": "python",
          "path": "app.py",
          "tune": {}
        }
      }
    }


Development
-----------

Current goal is to get a feature-complete tool. There is a strong concept,
but some parts of code became messy. Refactoring is postponed after feature
stabilization.

Notes for contributing:

1. `./bin/cid run autopep8` - for code auto-formatting
2. `./bin/cid check` - for static analysis
3. `./tests/run_vagrant_all.sh [optional filters]` - to make sure nothing is broken
