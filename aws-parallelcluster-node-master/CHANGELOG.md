aws-parallelcluster-node CHANGELOG
===================================

This file is used to list changes made in each version of the aws-parallelcluster-node package.

2.5.0
-----

**ENHANCEMENTS**
- Slurm:
  - Add support for scheduling with GPU options. Currently supports the following GPU-related options: `—G/——gpus,
    ——gpus-per-task, ——gpus-per-node, ——gres=gpu, ——cpus-per-gpu`.
  - Add gres.conf and slurm_parallelcluster_gres.conf in order to enable GPU options. slurm_parallelcluster_gres.conf
    is automatically generated by node daemon and contains GPU information from compute instances. If need to specify
    additional GRES options manually, please modify gres.conf and avoid changing slurm_parallelcluster_gres.conf when
    possible.
  - Integrated GPU requirements into scaling logic, cluster will scale automatically to satisfy GPU/CPU requirements
    for pending jobs. When submitting GPU jobs, CPU/node/task information is not required but preferred in order to
    avoid ambiguity. If only GPU requirements are specified, cluster will scale up to the minimum number of nodes
    required to satisfy all GPU requirements.
  - Slurm daemons will now keep running when cluster is stopped for better stability. However, it is not recommended
    to submit jobs when the cluster is stopped.
  - Change jobwatcher logic to consider both GPU and CPU when making scaling decision for slurm jobs. In general,
    cluster will scale up to the minimum number of nodes needed to satisfy all GPU/CPU requirements.
- Reduce number of calls to ASG in nodewatcher to avoid throttling, especially at cluster scale-down.

**CHANGES**
- Increase max number of SQS messages that can be processed by sqswatcher in a single batch from 50 to 200. This
  improves the scaling time especially with increased ASG launch rates.
- Increase faulty node termination timeout from 1 minute to 5 in order to give some additional time to the scheduler
  to recover when under heavy load.

**BUG FIXES**
- Fix jobwatcher behaviour that was marking nodes locked by the nodewatcher as busy even if they had been removed
  already from the ASG Desired count. This was causing, in rare circumstances, a cluster overscaling.
- Better handling of errors occurred when adding/removing nodes from the scheduler config.
- Fix bug that was causing failures in sqswatcher when ADD and REMOVE event for the same host are fetched together.


2.4.1
-----

**ENHANCEMENTS**
- Torque:
  - process nodes added to or removed from the cluster in batches in order to speed up cluster scaling.
  - scale up only if required slots/nodes can be satisfied
  - scale down if pending jobs have unsatisfiable CPU/nodes requirements
  - add support for jobs in hold/suspended state (this includes job dependencies)
  - automatically terminate and replace faulty or unresponsive compute nodes
  - add retries in case of failures when adding or removing nodes
  - add support for ncpus reservation and multi nodes resource allocation (e.g. -l nodes=2:ppn=3+3:ppn=6)

**CHANGES**
- Drop support for Python 2. Node daemons now support Python >= 3.5.
- Torque: trigger a scheduling cycle every 1 minute when there are pending jobs in the queue. This is done in order
  to speed up jobs scheduling with a dynamic cluster size.

**BUG FIXES**
- Restore logic that was automatically adding compute nodes identity to known_hosts file.
- Slurm: fix issue that was causing the daemons to fail when the cluster is stopped and an empty compute nodes file
  is imported in Slurm config.
- Torque: fix command to disable hosts in the scheduler before termination.


2.4.0
-----

**ENHANCEMENTS**
- Dynamically fetch compute instance type and cluster size in order to support updates
- SGE:
  - process nodes added to or removed from the cluster in batches in order to speed up cluster scaling.
  - scale up only if required slots/nodes can be satisfied
  - scale down if pending jobs have unsatisfiable CPU/nodes requirements
  - add support for jobs in hold/suspended state (this includes job dependencies)
  - automatically terminate and replace faulty or unresponsive compute nodes
  - add retries in case of failures when adding or removing nodes
- Slurm:
  - scale up only if required slots/nodes can be satisfied
  - scale down if pending jobs have unsatisfiable CPU/nodes requirements
  - automatically terminate and replace faulty or unresponsive compute nodes
- Dump logs of replaced failing compute nodes to shared home directory

**CHANGES**
- SQS messages that fail to be processed are re-queued only 3 times and not forever
- Reset idletime to 0 when the host becomes essential for the cluster (because of min size of ASG or because there are
  pending jobs in the scheduler queue)
- SGE: a node is considered as busy when in one of the following states "u", "C", "s", "d", "D", "E", "P", "o".
  This allows a quick replacement of the node without waiting for the `nodewatcher` to terminate it.

**BUG FIXES**
- Slurm: add "BeginTime", "NodeDown", "Priority" and "ReqNodeNotAvail" to the pending reasons that trigger
  a cluster scaling
- Add a timeout on remote commands execution so that the daemons are not stuck if the compute node is unresponsive
- Fix an edge case that was causing the `nodewatcher` to hang forever in case the node had become essential to the
  cluster during a call to `self_terminate`.


2.3.1
-----

**BUG FIXES**
- `sqswatcher`: Slurm - Fix host removal


2.3.0
-----

**CHANGES**
- `sqswatcher`: Slurm - dynamically adjust max cluster size based on ASG settings
- `sqswatcher`: Slurm - use FUTURE state for dummy nodes to prevent Slurm daemon from contacting unexisting nodes
- `sqswatcher`: Slurm - dynamically change the number of configured FUTURE nodes based on the actual nodes that
  join the cluster. The max size of the cluster seen by the scheduler always matches the max capacity of the ASG.
- `sqswatcher`: Slurm - process nodes added to or removed from the cluster in batches. This speeds up cluster scaling
  which is able to react with a delay of less than 1 minute to variations in the ASG capacity.
- `sqswatcher`: Slurm - add support for job dependencies and pending reasons. The cluster won't scale up if the job
  cannot start due to an unsatisfied dependency.
- Slurm - set `ReturnToService=1` in scheduler config in order to recover instances that were initially marked as down
  due to a transient issue.
- `sqswatcher`: remove DynamoDB table creation
- improve and standardize shell command execution
- add retries on failures and exceptions

**BUG FIXES**
- `sqswatcher`: Slurm - set compute nodes to DRAIN state before removing them from cluster. This prevents the scheduler
  from submitting a job to a node that is being terminated.

2.2.1
-----

**CHANGES**
- `nodewatcher`: sge - improve logic to detect if a compute node has running jobs
- `sqswatcher`: remove invalid messages from SQS queue in order to process remaining messages
- `sqswatcher`: add number of slots to the log of torque scheduler
- `sqswatcher`: add retries in case aws request limits are reached

**BUG FIXES**
- `sqswatcher`: keep processing compute node termination until all scheduled jobs are terminated/cancelled.
  This allows to automatically remove dead nodes from the scheduler once all jobs are terminated.
- `jobwatcher`: better handling of error conditions and usage of fallback values
- `nodewatcher`: enable daemon when cluster status is `UPDATE_ROLLBACK_COMPLETE`

**TOOLING**
- Add a script to simplify node package upload when using `custom_node_package` option

2.1.1
-----

- China Regions, cn-north-1 and cn-northwest-1 support

2.1.0
-----

- China Regions, cn-north-1 and cn-northwest-1 support

2.1.0
-----

Bug Fixes:
- Don't schedule jobs on compute nodes that are terminating

2.0.2
-----

- Align version to main ParallelCluster package

2.0.0
-----

- Rename package to AWS ParallelCluster


1.6.0
-----

Bug fixes/minor improvements:

  - Changed scaling functionality to scale up and scale down faster.


1.5.4
-----

Bug fixes/minor improvements:

  - Upgraded Boto2 to Boto3 package.


1.5.2
-----

Bug fixes/minor improvements:

  - Fixed Slurm behavior to add CPU slots so multiple jobs can be scheduled on a single node, this also sets CPU as a consumable resource

1.5.1
-----

Bug fixes/minor improvements:

  - Fixed Torque behavior when scaling up from an empty cluster
  - Avoid Torque server restart when adding and removing compute nodes
