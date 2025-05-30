## v1.7.0 (2025-04-17)

## v1.7.0rc3 (2025-04-17)

### Feat

- use srun when launching slurm tasks

### Fix

- import Launcher
- assert that the returned launcher is a launcher

## v1.7.0rc2 (2025-04-17)

### Feat

- use srun when launching slurm tasks

### Fix

- import Launcher
- assert that the returned launcher is a launcher

## v1.7.0rc2 (2025-04-11)

### Fix

- xp_file is changed into a Path if command line

## v1.7.0rc1 (2025-04-17)

### Feat

- use srun when launching slurm tasks

### Fix

- import Launcher
- assert that the returned launcher is a launcher

## v1.7.0rc2 (2025-04-11)

### Fix

- xp_file is changed into a Path if command line

## v1.7.0rc1 (2025-04-08)

### Fix

- handles non resources

## v1.7.0rc0 (2025-04-08)

### Feat

- dynamic outputs and field factory

### Fix

- npm audit
- removed temporarly dynamic output
- wheel includes server data files
- launchers.py is a resource

## v1.6.2 (2025-01-24)

### Fix

- python path is now propagated to the tasks

## v1.6.1 (2025-01-22)

### Fix

- **cli.py**: Python path should be modified including when running the experiments

## v1.6.0 (2025-01-16)

### Feat

- python path and module in experiments

### Refactor

- pre-commit commitizen update

## v1.5.14 (2024-11-05)

### Fix

- when fabric is not there, use placeholders

## v1.5.13 (2024-10-23)

### Fix

- js vulnerabilities fix

## v1.5.11 (2024-09-13)

### Fix

- python 3.12 compatibility (but without ssh)
- no dependencies for loaded configurations
- fabric is now optional

## v1.5.10 (2024-09-02)

### Feat

- include jobs not in experiments
- include jobs not in experiments

## v1.5.9 (2024-07-28)

### Fix

- bug in setting workspace env

## v1.5.8 (2024-07-27)

### Fix

- andles better null process
- use a better way to load the XP file

### Refactor

- removed the launchers.yaml support

## v1.5.7 (2024-05-31)

### Feat

- better job interactions

### Fix

- bug when no settings.yaml file
- set init tasks before job creation
- removed extra logging information
- wrong information reported
- wrong test for running/done tasks

### Refactor

- change the cli source dir

## v1.5.6 (2024-05-10)

### Fix

- bug in environment

## v1.5.5 (2024-05-10)

### Fix

- bugs in normal task exit

### Refactor

- change run-experiment parameters
- removed unused environments

## v1.5.4 (2024-03-06)

### Fix

- get back to sys.exit

## v1.5.3 (2024-03-06)

### Fix

- force exit with multiprocessing

## v1.5.2 (2024-03-06)

### Fix

- multiple launchers

## v1.5.1 (2024-02-29)

### Feat

- handles properly mp.spawn
- requirements can now include a disjunction
- environment can be defined in the settings

### Fix

- **slurm**: Check if slurm process is alive before returning it
- really using the workspace directory

## v1.5.0 (2024-02-26)

### Feat

- uses job failure status
- HandledException to shorten error stack trace

### Fix

- Deprecate YAML defined launchers
- added pre/post yaml options
- better error messages
- support python 3.12 pathlib
- **typinutils**: test for optional
- _collect_parameters is in Python 3.11
- **types**: accept generics as Param (but no real validation)
- **ConfigurationBase**: Documentation and new fields to describe an experiment
- process YAML file in the right order
- Configuration must be OmegaConf to be transformed

### Refactor

- Use XPMValue and XPMConfig to distinguish configurations and values

## v1.4.3 (2023-12-21)

### Fix

- set id as MISSING

## v1.4.2 (2023-12-21)

### Fix

- parent should be really optional

## v1.4.1 (2023-12-19)

### Feat

- decorator class method for experiment helpers
- representation of identifier as hex string
- load task from directory

### Fix

- identifier is a method not a property

## v1.4.0 (2023-12-16)

### Feat

- run-experiment cli

## v1.3.6 (2023-12-12)

### Feat

- Saving/Loading from experiments

## v1.3.5 (2023-12-08)

### Feat

- access run mode from experiment

## v1.3.4 (2023-12-07)

### Feat

- Test for falsy documented

## v1.3.3 (2023-12-06)

## v1.3.2 (2023-11-28)

### Feat

- utility function to format time for SLURM

## v1.3.1 (2023-11-27)

### Fix

- bad assert test

## v1.3.0 (2023-11-24)

### Feat

- launchers.py specification file
- Serialization for arbitrary data structures

## v1.2.3 (2023-10-04)

### Fix

- task identifier and reload

## v2.0.0 (2023-10-03)

### Fix

- task identifier and reload

## v1.2.1 (2023-10-03)

### Feat

- workspace settings

## v1.2.0 (2023-10-03)

### Feat

- init tasks

## v1.1.2 (2023-08-28)

### Fix

- undocumented produces more information

## v1.1.1 (2023-10-03)

### Feat

- undocumented in sphinx documentation
- Added decorator (NOOP) for config only methods

## v1.1.0 (2023-10-03)

### Feat

- Generic documentation checker (for use in automated tests)
- improved check documentation command

## v1.0.0 (2023-10-03)

### Feat

- List experiments
- **documentation**: Checks for undocumented configuration objects in a package

## v0.30.0 (2023-10-03)

### Feat

- **configuration**: Add access to pre-task and dependency copying

## v0.29.11 (2023-10-03)

### Fix

- more slurm fixes

## v0.29.10 (2023-10-03)

### Fix

- max duration QoS was ignored

## v0.29.9 (2023-10-03)

### Fix

- more fine-grained SLURM configuration
- blank line after job information

## v0.29.8 (2023-10-03)

### Fix

- **slurm**: Better SLURM launcher finder

## v0.29.7 (2023-10-03)

## v0.29.6 (2023-10-03)

### Fix

- cleaned up the instance() mode

## v0.29.5 (2023-10-03)

### Fix

- cleaned up the instance() mode

## v0.29.4 (2023-10-03)

### Fix

- better instance()

## v0.29.3 (2023-10-03)

### Fix

- identifiers

## v0.29.2 (2023-10-03)

### Fix

- pre-task are properly handled

## v0.29.1 (2023-10-03)

### Fix

- exception thrown when adding pre-task to a sealed config

## v0.29.0 (2023-10-03)

### Fix

- pre task dependencies are taken into account

## v0.28.0 (2023-10-03)

### BREAKING CHANGE

- - subparam were removed (should be replaced by something more stable)
- serialiazed configurations were removed (too much trouble too)

### Feat

- show dependencies when simulating
- removed config wrapper
- easier path LW task access
- **Lightweight-pre-tasks**: Lightweight pre-tasks allow code to be executed to modify objects

### Fix

- bug in dependency tracking

## v0.27.0 (2023-10-03)

### Feat

- Expose the unwrap function

### Fix

- Removes unnecessary server logs

## v0.26.0 (2023-10-03)

### Fix

- Fix submit hooks (and document them)

## v0.25.0 (2023-10-03)

## v0.24.0 (2023-10-03)

### Feat

- serialized configurations

### Fix

- requirement for fabric
- add gevent-websocket for supporting websockets

### Refactor

- Changed TaskOutput to ConfigWrapper

## v0.23.0 (2023-10-03)

### Feat

- submit hooks to allow e.g. changing the environment variables

## v0.22.0 (2023-10-03)

### Feat

- tags as immutable and hashable dicts

### Fix

- corrected service status update for servers
- improved server

## v0.21.0 (2023-10-03)

### Feat

- When an experiment fails, display the path to stderr
- service proxying

### Fix

- JS vulnerabilities fix
- Information message when locking experiment
- Improving slurm support
- Fix test bugs
- better handlign of services

### Refactor

- **server**: switched to flask and socketio for future evolutions of the server

## v0.20.0 (2023-10-03)

### Feat

- improvements for dry-run modes to show completed jobs

### Refactor

- more reliable identifier computation

## v0.19.2 (2023-10-03)

### Fix

- better identifier recomputation

## v0.19.1 (2023-10-03)

### Fix

- fix bugs with generate/dry-run modes

## v0.19.0 (2023-10-03)

### Feat

- allow using the old task identifier computation to fix params.json

## v0.18.0 (2023-10-03)

### BREAKING CHANGE

- New identifiers will be different in all cases - use the deprecated command to recompute identifiers for old experiments
- For any task output which is different than the task itself, the identifier will change

### Feat

- **configuration**: re-use computed sub-configuration identifiers

### Fix

- **server**: fix some display bugs in the UI
- **configuration**: fixed more bugs with identifiers
- **configuration**: fixed bugs with identifiers
- **configuration**: serialize the task to recompute exactly the identifier

### Refactor

- removed jsonstreams dependency

## v0.16.0 (2023-10-03)

### Feat

- **server**: web services for experiment server

## v0.15.1 (2023-10-03)

### Fix

- wrong indent
