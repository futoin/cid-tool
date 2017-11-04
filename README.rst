
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
* Multiple entry points per project
* Rolling deployments with zero downtime
* Container-friendly
* Technology-neutral
* Easily extendable & portable
* Fine tune of all aspects
* Easy integration with provisioning systems with centralized tool setup

Supported technologies & tools (so far):
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*Note: please use* **cid tool list** *and* **cid tool describe $tool** *for details.*

* **cmake**
* **docker**

  - **docker-compose**
    
* **flyway**
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
* **liquibase**
* **nginx** - true web server for development, testing & production
* **node**

  - **npm**
  - **bower**
  - **grunt**
  - **gulp**
  - **nvm** (implicit)
  - **yarn** - uses npm for own install, but disables one for processing
  - **webpack**
    
* **php** - system, php-build supported and binary builds (Sury, SCL)

  - **composer**
  - **php-build** (implicit)
    
* **python** - system 2 & 3

  - **virtualenv**, venv is ignored due to issues with *ensurepip* package
  - **pip**
  - **twine** - as limited RMS tool
  - **uwsgi** - to run application behind nginx (or other web server)
    
* **ruby** - system, rvm supported and binary builds (Brightbox, SCL)

  - **gem**
  - **bundler**
  - **rvm** (implicit)
  - **puma** - to run application behind nginx (or other web server)
    
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
     :height: 100px
     :target: https://www.macstadium.com/
    
* **OpenSUSE**

  - **42.2 Leap**
  - There are known issues with some tools due to lack of community support.
    
* **Oracle Linux (OL)**

  - **7**
    
* **RedHat Enterprise Linux (RHEL)**

  - **7**

* **SUSE Linux Enterprise Server (SLES)**

  - **12**
  - *Note: only occasionally tested due to lack of suitable license*

* **Ubuntu**

  - **14.04 LTS - Trusty**
  - **16.04 LTS - Xenial**
  - **17.04 - Zesty**
    
* **Other Linux**

  - it should work without issues, if system packages are installed manually.

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

As alternative, you can set :code:`export CID_INTERACTIVE_SUDO=1` environment variable
to run :code:`sudo` in interactive mode. It is disabled by default to avoid hanging
in unattended use.

Another production approach is create a special user account e.g. "futoin" which
has sudo capabilities and allow all other users to sudo-run a special callback file
configured through :code:`.env.externalSetup` option in global /etc/futoin/futoin.json.
Callback example: https://github.com/codingfuture/puppet-cfweb/blob/master/files/cf_cid_callback.sh

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
    # See "Resource limits auto-detection" section for more info.
    # Public services listen on 0.0.0.0, unless overridden.
    # UNIX sockets are preferred for internal communications.

7. Production deployment from RMS: ::

    cid deploy rms Releases --rmsRepo=svn:user@host/rms \
        --deployDir=/www/prod \
        --limit-memory=8G \
        --limit-cpus=4
    # Auto-detection & distribution of resources as stated above.
    # Forced resource limits are preserved per deployment across runs, if not overridden

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

Resource limits auto-detection
------------------------------

All resource limits are container-friendly (e.g. Docker) and
automatically detected based on the following:

* RAM:

  1. :code:`--limit-memory` option is used, if present.
  2. cgroup memory limit is used, if less than amount of RAM.
  3. half of RAM is used otherwise.
  4. Memory units: one of B, K, M, G postfixes is required. Example: 1G, 1024M, 1048576K, 1073741824B

* CPU count:

  1. :code:`--limit-cpus` option is used, if present.
  2. cgroup CPU count is used, if present.
  3. all detected CPU cores are used otherwise.

* Max clients:

  * Auto-detected based on available memory and entry point configuration of :code:`.connMemory`.
  * Can be used by load balancers and reverse-proxy servers.

* File descriptor limit - auto-detected based on max clients and configured
  file descriptor count per client.
  
* Instance count per entry point:

  1. if not :code:`scalable` then only single instance is configured.
  2. if not :code:`multiCore` then:

     * get theoretical maximum of instances based on doubled :code:`.minMemory`
     * get CPU limit count
     * use :code:`maxInstances` configuration, if any.
     * use the least value of detected above.

  3. otherwise, configure one instance.



Resource distribution & Entry Point instance auto-configuration
---------------------------------------------------------------

Entry points are expected to be set in project :code:`futoin.json` manifest. However,
they can be set and/or tuned in deployment configuration as well.

Please note that "Application Entry Point" != "Application Instance". The first one generally defines
application, the second one is automatically derived & auto-configured in deployment based
on actual resource & configuration constraints.

Based on overall resource limits per deployment, the resources are automatically distributed across
entry points based on the following constraints:

* :code:`.minMemory` - minimal memory per instance without connections
* :code:`.connMemory` - extra memory per one connection
* :code:`.connFD = 16` - file descriptors per connection
* :code:`.internal = false` - if true, then resource is not exposed
* :code:`.scalable = true` - if false then it's not allowed to start more than one instance globally
* :code:`.reloadable = false` - if true then reload WITHOUT INTERRUPTION is supported
* :code:`.multiCore = true` - if true then single instance can span multiple CPU cores
* :code:`.exitTimeoutMS = 5000` - how many milliseconds to wait after SIGTERM before sending SIGKILL
* :code:`.cpuWeight = 100` - arbitrary positive integer
* :code:`.memWeight = 100` - arbitrary positive integer
* :code:`.maxMemory` - maximal memory per instance (for very specific cases)
* :code:`.maxTotalMemory` - maximal memory for all instances (for very specific cases)
* :code:`.maxInstances` - limit number of instances per deployment
* :code:`.socketTypes` = ['unix', 'tcp', 'tcp6'] - supported listen socket types
* :code:`.socketProtocol` = one of ['http', 'fcgi', 'wsgi', 'rack', 'jsgi', 'psgi']
* :code:`.debugOverhead` - extra memory per instance in "dev" deployment
* :code:`.debugConnOverhead` - extra memory per connection in "dev" deployment
* :code:`.socketType` - generally, for setup in deployment config
* :code:`.socketPort` - default/base port to assign to service (optional)
* :code:`.maxRequestSize` - maximal size of single request (mostly applicable to HTTP request)

*Note: each tool has own reasonable defaults which can be tunes per entry point.*


Zero-downtime deployment approach
---------------------------------

This approach is used for classical, container and development deployments.
However, actual zero-downtime benefit is assumed for "classical" non-container
production case.

Step-by-step:

* a clean target folder is required for safety reasons due to automatic cleanup,
* deploy lock is taken on target folder,
* target package:

  * if :code:`devserve` is used, the actual working copy is symlinked
  * if :code:`vcsref` or :code:`vcsref` then local VCS cache is maintained for bandwidth efficiency
  * otherwise, last used RMS package is cached

* target version auto-detection:

  * if :code:`vcsref` is used then the latest revision is always used.
  * if precise version is set - it is used for deployment
  * if partial package mask is set - it is used with shell-like match filtering
  * for :code:`rms` a list of available packages is retrieved efficient way
  * for :code:`vcstag` a list of available tags is retrieved efficient way
  * the retrieved list of candidates is sorted in natural order (decimal numbers are assumed)
  * the latest one (greatest by order) is used

* persistent data:

  * :code:`persistent` configuration is used to setup read-write persistent paths.
  * read-write location root is set to :code:`{deployment root}/persistent/` by default.
  * if specified file or directory exists in package, it is forcibly copied to read-write location (!).
  * otherwise, a folder is created in read-write location with symlink from target folder.
  * it's expected that persistent folder is subject for backup procedures.

* a temporary folder under deployment root is used,

* the actions are executed:

  * actions can be hooked both in project and deployment configuration:

    * :code:`.actions` is a map of named actions to string or list of commands.
    * Standard actions match some of command names: "prepare", "build", "migrate", etc.
    * :code:`@cid` in the beginning of command is treated as CID invocation. Example: :code:`@cid build-dep openssl`
    * :code:`@default` as command executes the default behavior. For deployment config it executes project-specified action configuration.
    * If command matches any of other defined actions then it is executed with recursion of this logic.
    * *Note: there is recursion protection other than program stack size.*
    * See :code:`cid deploy set action` for easy scripting instead of direct JSON manipulations.

  * if VCS deployment or forced with :code:`--build` option
  
    * :code:`cid prepare` - suitable for extra setup
    * :code:`cid build`

  * :code:`cid migrate` - suitable for auto-configuration & database migrations
  
* all files and directories are set read-only for security & data safety purposes (enforce persistent locations),
* temporary folder is renamed to package name without extension, VCS tag or VCS branch with revision name,
* :code:`current` symlink is set to above,
* if running :code:`cid service master` is detected then it is refreshed,

  * *note: very slight delay may occur which expected to be smoothed by load balancer*?

* deployment folder is cleaned out of any not expected files and folder (cleanup of old versions & misc.),

  * *note: there are some extra files & folders like .tmp, .runtime, .futoin-deploy.lock, etc.*,

* deploy lock is released,
* at any point, if something goes wrong the procedure is aborted leaving previous version running as is.


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
        
    cid deploy set tools <tools>... [--deployDir=<deploy_dir>]
        Overrides .tools in deployment config.
        
    cid deploy set tooltune <tool> {<set_name=value>...|<del_name>|<inline_json>} [--deployDir=<deploy_dir>]
        Pverrode .toolTune in deployment config.
       
    cid deploy set action <name> <actions>... [--deployDir=<deploy_dir>]
        Override .action in deployment config.
       
    cid deploy set persistent <paths>... [--deployDir=<deploy_dir>]
        Add .persistent paths in deployment config.
       
    cid deploy set entrypoint <name> <tool> <path> {<set_name=value>...|<del_name>|<inline_json>} [--deployDir=<deploy_dir>]
        Set entry point configuration in deployment.
       
    cid deploy set env <variable> [<value>] [--deployDir=<deploy_dir>]
        Set or remote environment config .env entries.
       
    cid deploy set webcfg <variable> [<value>] [--deployDir=<deploy_dir>]
    cid deploy set webcfg mounts <route>[=<app>] [--deployDir=<deploy_dir>]
        Set or remove .webcfg entries.

    cid deploy set webmount <web_path> [<json>] [--deployDir=<deploy_dir>]
        Set complex web mount point configuration.

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
    
    cid tool exec <tool_name> [<tool_version>] [-- <tool_arg>...]
        Execute <tool_name> binary with provided arguments.
        Tool and all its dependencies are automatically installed.
        Note: not all tools support execution.

    cid tool envexec <tool_name> [<tool_version>] [-- <command>...]
        Execute arbitrary command with environment of specified tool.

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
        
    cid vcs clean [--wcDir=<wc_dir>]
        Remove unversioned files and directories, including ignored.
        
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
        
    cid build-dep [<build_dep>...]
        Require specific development files to be installed, e.g.: openssl, mysqlclient,
        postgresql, imagemagick, etc.
        Without parameters lists available deps.

Excplicit :code:`futoin.json` examples
--------------------------------------

:code:`futoin.json` is not strictly required, but it allows to use full power of CID.
Below is real-world application configuration examples.

1. Dynamic PHP website
~~~~~~~~~~~~~~~~~~~~~~
.. code-block:: json

    {
        "vcs": "git",
        "vcsRepo": "git@...",
        "name": "...",
        "version": "2.0.0",
        "entryPoints": {
            "backend": {
                "tool": "phpfpm",
                "path": "web/index.php",
                "tune": {
                    "internal": true
                }
            },
            "webserver": {
                "tool": "nginx",
                "path": "web"
            }
        },
        "webcfg": {
            "root": "web",
            "mounts": {
                "/": {
                    "app": "backend",
                    "static": true,
                    "tune": {
                        "pattern": true,
                        "gzip": true,
                        "staticGzip": true
                    }
                }
            }
        }
    }


2. Static web page with small API for contact form built using :code:`webpack`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. code-block:: json

    {
        "vcs": "git",
        "vcsRepo": "git@...",
        "name": "...",
        "version": "1.0.16",
        "entryPoints": {
            "backend": {
                "tool": "node",
                "path": "server.js",
                "tune": {
                    "internal": true,
                    "scalable": false
                }
            },
            "frontend": {
                "tool": "nginx",
                "path": "webroot",
                "tune": {
                    "config": {
                        "http": {
                            "server": {
                                "rewrite '^/([a-z]{2})/$'": "/index.$1.html last",
                                "location = /": {
                                    "return": "302 /en/"
                                }
                            }
                        }
                    }
                }
            }
        },
        "webcfg": {
            "root": "webroot",
            "mounts": {
                "/": {
                    "tune": {
                        "pattern": false,
                        "gzip": true,
                        "staticGzip": true
                    }
                },
                "/api/": "backend",
                "~ \"^/index\\.[a-z]{2}\\.html$\"": {
                    "tune": {
                        "pattern": false,
                        "gzip": true,
                        "staticGzip": true,
                        "expires": "epoch"
                    }
                },
                "^~ /img/": {
                    "tune": {
                        "pattern": false
                    }
                },
                "^~ /fonts/": {
                    "tune": {
                        "pattern": false
                    }
                },
                "^~ /icons-": {
                    "tune": {
                        "pattern": false
                    }
                }
            }
        },
        "actions": {
            "upgrade-deps": "@cid tool exec yarn -- upgrade --latest",
            "build": "@cid tool exec node -- ./node_modules/.bin/webpack"
        }
    }

3. Deploy of Redmine without embedded :code:`futoin.json`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. code-block:: bash

    # select deploy root
    DEPLOY_DIR=/target-empty-dir-or-existing-deployment
    mkdir $DEPLOY_DIR
    cd $DEPLOY_DIR
    
    # initialize with safety placeholders first
    cid deploy setup 
    
    # require Ruby 2.3 instead of latest
    cid deploy set env rubyVer '2.3'
    
    # hook standard prepare action
    cid deploy set action prepare app-config database-config app-install
    
    # set custom-named actions for easy management
    cid deploy set action app-config \
        'cp config/configuration.yml.example config/configuration.yml' \
        'rm -rf tmp && ln -s ../.tmp tmp'

    # assume, database config is put in deploy root (after 'cid deploy setup')
    cid deploy set action database-config \
        'ln -s ../../.database.yml config/database.yml'
    cat >.database.yml <<EOT
    production:
        adapter: mysql2
        database: redmine
        host: localhost
        username: redmine
        password: redmine
        encoding: utf8
    EOT
        
    # Standard Redmine HOWTO:
    cid deploy set action app-install \
        '@cid build-dep ruby mysql-client imagemagick tzdata libxml2' \
        '@cid tool exec bundler -- install --without "development test"'

    # hook standard migrate action
    cid deploy set action migrate \
        '@cid tool exec bundler -- exec rake generate_secret_token' \
        '@cid tool exec bundler -- exec rake db:migrate RAILS_ENV=production' \
        '@cid tool exec bundler -- exec rake redmine:load_default_data RAILS_ENV=production REDMINE_LANG=en'

    # Add persistent locations
    cid deploy set persistent  files log
    
    # Configure entry points
    cid deploy set entrypoint  web nginx public socketType=tcp
    cid deploy set entrypoint  app puma config.ru internal=1

    # Configure web paths
    cid deploy set webcfg root public
    cid deploy set webcfg main app
    cid deploy set webmount '/' '{"static": true}'

For example, it can run with :code:`cid service master --deployDir=$DEPLOY_DIR` in container.

For more advanced integration, provisioning system should examine :code:`.futoin.merged.json`
to configure :code:`systemd` (or other) services with per-instance limits. Such instance
can be launched through :code:`cid service exec <name> <instance>`.

More advanced example can be found here: https://github.com/codingfuture/puppet-cfwebapp/blob/master/manifests/redmine.pp

Development
-----------

The tool has reached its major milestone for Continuous Delivery case and use at all
stages: local development env, static and production.

A reference secure integration into provisioning system can be found here: https://github.com/codingfuture/puppet-cfweb

There is a strong concept and several evolutions passed across years. Therere still major milestones planned. The tool can be extended with additional technology support either through custom plugins
or directly in main source tree.

Notes for contributing:

1. :code:`./bin/cid run autopep8` - for code auto-formatting
2. :code:`./bin/cid check` - for static analysis
3. :code:`./tests/run_vagrant_all.sh [optional filters]` - to make sure nothing is broken
