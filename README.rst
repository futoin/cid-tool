
CID - FutoIn Continuous Integration & Delivery Tool
==============================================================================

Intro
-----

There are many continuous integration & delivery tools, but they are primarily
targeted at own infrastructure. The demand for a new meta-tool is to merge
many operations of different technologies like npm, composer, bundler, nvm,
rvm, php-build and others under a single tool for runtime setup, project
development, build, deployment and running.

**Please use official documentation at https://futoin.org/docs/cid/**

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

* **erlang**

  - **elixir**
  - **mix**
  - **phoenix**

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

- **aws** - S3 for RMS, and the AWS CLI tool in general

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


Development
-----------

The tool has reached its major milestone for Continuous Delivery case and use at all
stages: local development env, staging and production.

A reference secure integration into provisioning system can be found here: https://github.com/codingfuture/puppet-cfweb

There is a strong concept and several evolutions passed across years. Therere still major milestones planned. The tool can be extended with additional technology support either through custom plugins
or directly in main source tree.

Notes for contributing:

1. :code:`./bin/cid run autopep8` - for code auto-formatting
2. :code:`./bin/cid check` - for static analysis
3. :code:`./tests/run_vagrant_all.sh [optional filters]` - to make sure nothing is broken
