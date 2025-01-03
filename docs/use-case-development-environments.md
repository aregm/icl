# How to create and maintain development environments

## Development environments for Triton XPU
A Triton XPU team grew fast to 20 developers.
The project required Intel GPUs to develop a Triton XPU code and run tests.
In the beginning, developers used a shared machine with a single GPU.
Each developer configured their own environment, installing user-level Python packages and system-level tools, such as gcc, clang and make.
Also, the project required GPU driver, level zero library, and oneAPI bundle, which needed to be installed system-wide.
Developers often updated system-level packages, which affected other developers on this machine.
The number of available GPUs was limited, so it was not possible to give each developer a physical machine with GPU.
With the help of ICL, we created several profiles for Triton XPU development environments and kept them updated with the required system-level dependencies.
As the result, the whole Triton XPU worked in sessions handled by 3 physical machines, each machine with a single GPU.
Reproducible, isolated sessions solved most of the existed issues and improved team's performance.

## Development environments are hard
Developers have to spend a considerable amount of time to prepare their development environments, installing system and project dependencies manually.
Such environments often go out of sync with the project requirements.
Sometimes there is a dedicated person or a team responsible for building dev environments and keeping them up to date.
One option is to provide a virtualized or containerized environments.
However, even in this case developers still need to know how to start a new environment, how and when to update the existing one.

## Profiles and sessions
A possible solution for this problem is to use profiles, named and versioned container images with additional configuration that are created and maintained by a professional team (devops team, build and release team).
Such profile contains system and project level dependencies. A developer selects a profile to start a new session.
All changes made by a developer in the session are persistent, however there is an option to use another profile for the existing session.
In this case, all user files are kept but the system and project dependencies come from the new profile.

## Access to a session
Developers can access their session via web interface (terminal, Jupyter, or VS Code), log in to the session via ssh, or use their local IDE (VS Code, Idea, Zed) in remote mode via ssh.

## Sharing and cloning sessions
Developers can provide access to their environments for other developers, make snapshots of their sessions, rollback to the existing snapshots, make a copy of the existing session to work in parallel with different profiles.

## Internal services
In a session, there are internal services such as shared volumes, workflow engine, image and package registries and so on.

## Multiple sessions
Developers can create more than one session for experiments and trying potential updates, or select different profiles for the existing session to work with the project with different sets of dependencies.

## Shared compute pool
A shared pool of machines is used to handle the sessions.
This enables more efficient consumption of hardware resources, allows executing workloads that require special hardware, more memory, or compute than any individual workstation can provide.

## Session persistence
More granular level to control what comes from the profile and what from the session.
In a common scenario, the home directory with all files is persisted in the session while the remaining files are from the profile.

## Creating new profiles
Developers to create their own profiles and make them available for other developers.
A developer can use an existing profile or a session, make update manually (install new dependencies) or define updates as a code.

## Keeping profiles up to date
DevOps team to automate making new profiles whenever update is required, potentially migrating the existing sessions to the new profiles without disturbing the development process.
 


