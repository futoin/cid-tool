CID - FutoIn Continuous Integration & Delivery Tool - Reference Implementation
==============================================================================

Intro
-----

There are many continuous integration & delivery tools, but they are primarily targeted at own
infrastructure. The demand for a new meta-tool is to merge many operation of different
technologies like npm, composer, bundle, nvm, rvm, php-build and others under a single tool for
runtime setup, project development, build, deployment and running.

*NOTE: current focus is on web projects, but support of other types is a far target.*

Full theoretical details are defined as FutoIn Spec FTN16 available at: https://github.com/futoin/specs/blob/master/draft/ftn16_cid_tool.md

Supported technologies & tools (so far):

* **node**
    - **npm**
    - **bower**
    - **grunt**
    - **grulp**
    - **nvm** (implicit)
* **php** - both system & any php-build supported
    - **composer**
    - **php-build** (implicit)
* **python** - system
* **ruby** - both system & any rvm supported
    - **gen**
    - **rvm** (implicit)
* **scp** - for RMS
    


Setup
-----

**cid** is written in commonly available Python language supporting both Python versions 2.7 and 3+.

Run the following:
    pip install futoin-cid

If pip is not available then it's strongly suggested to install one first:
    easy_install pip

Usage
-----

To be explained later:
    cid tag <branch> [<next_version>] [--vcsRepo vcs_url] [--wcDir wc_dir]

    cid prepare [<vcs_ref>] [--vcsRepo vcs_url] [--wcDir wc_dir]

    cid build

    cid package

    cid promote <package> <rms_pool> [--rmsRepo rms_url] [--rmsHash type_value]

    cid deploy [rms] <rms_pool> [<package>] [--rmsRepo rms_url] [--rmsHash type_value] [--redeploy] [--deployDir deploy_dir]

    cid deploy (vcstag|vcsref) <vcs_ref> [--vcsRepo vcs_url] [--redeploy] [--deployDir deploy_dir]

    cid run [<command>]

    cid ci_build <vcs_ref> <rms_pool> [--vcsRepo vcs_url] [--rmsRepo rms_url]

    cid tool exec <tool_name> [-- <tool_arg>...]

    cid tool (install|uninstall|update|test|env) [<tool_name>]
