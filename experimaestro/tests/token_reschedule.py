if __name__ == "__main__":
    import sys
    import logging
    from pathlib import Path
    import time

    from experimaestro.scheduler import JobState
    from experimaestro.tests.utils import TemporaryExperiment, TemporaryDirectory, timeout
    from experimaestro.tests.task_tokens import TokenTask

    workdir, x, lockingpath, readypath, timepath = sys.argv[1:]
    with TemporaryExperiment("reschedule%s" % x, workdir=workdir) as xp:
        logging.info("Reschedule with token [%d]: starting task in %s", x, workdir)
        token = xp.workspace.connector.createtoken("test-token-reschedule", 1)
        task = (
            TokenTask(path=lockingpath, x=x)
            .add_dependencies(token.dependency(1))
            .submit()
        )
        logging.info("Waiting for task to be scheduled")
        while task.job.state == JobState.UNSCHEDULED:
            time.sleep(0.01)

        Path(readypath).write_text("hello")
        logging.info("Reschedule with token [%d]: ready", x)

    logging.info("Reschedule with token [%d]: finished", x)
    Path(timepath).write_text(Path(task.stdout()).read_text())