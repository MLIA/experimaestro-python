# --- Task and types definitions

from pathlib import Path
import pytest
import signal

from experimaestro import *
from experimaestro.scheduler import JobState

from .utils import TemporaryDirectory, TemporaryExperiment, is_posix

from .tasks import *
from . import restart


def test_simple_task():
    with TemporaryDirectory(prefix="xpm", suffix="helloworld") as workdir:
        assert isinstance(workdir, Path)
        with TemporaryExperiment("helloworld", workdir=workdir, maxwait=2):
            # Submit the tasks
            hello = Say(word="hello").submit()
            world = Say(word="world").submit()

            # Concat will depend on the two first tasks
            concat = Concat(strings=[hello, world]).submit()

        assert concat.__xpm__.job.state == JobState.DONE
        assert Path(concat.stdout()).read_text() == "HELLO WORLD\n"


def test_not_submitted():
    """A not submitted task should not be accepted as an argument"""
    with TemporaryExperiment("helloworld", maxwait=2):
        hello = Say(word="hello")
        with pytest.raises(ValueError):
            Concat(strings=[hello])


def test_fail():
    """Failing task... should fail"""
    with TemporaryExperiment("failing", maxwait=2):
        fail = Fail().submit()
        fail.touch()

    assert fail.__xpm__.job.wait() == JobState.ERROR


def test_foreign_type():
    """When the argument real type is in an non imported module"""
    with TemporaryExperiment("foreign_type", maxwait=2):
        # Submit the tasks
        from .tasks2 import ForeignClassB2

        b = ForeignClassB2(x=1, y=2)
        a = ForeignTaskA(b=b).submit()

        assert a.__xpm__.job.wait() == JobState.DONE
        assert a.stdout().read_text().strip() == "1"


def test_fail_dep():
    """Failing task... should cancel dependent"""
    with TemporaryExperiment("failingdep"):
        fail = Fail().submit()
        dep = FailConsumer(fail=fail).submit()
        fail.touch()

    assert fail.__xpm__.job.wait() == JobState.ERROR
    assert dep.__xpm__.job.wait() == JobState.ERROR


def test_unknown_attribute():
    """No check when setting attributes while executing"""
    with TemporaryExperiment("unknown"):
        method = SetUnknown().submit()

    assert method.__xpm__.job.wait() == JobState.DONE


def test_function():
    with TemporaryExperiment("function"):
        method = Method(a=1).submit()

    assert method.__xpm__.job.wait() == JobState.DONE


@pytest.mark.skip()
def test_done():
    """Checks that we do not run an already done job"""
    pass


def terminate(p):
    p.terminate()


def sigint(p):
    p.send_signal(signal.SIGINT)


TERMINATES_FUNC = [terminate]
if is_posix():
    TERMINATES_FUNC.append(sigint)


def restart_function(xp):
    restart.Restart().submit()


@pytest.mark.parametrize("terminate", TERMINATES_FUNC)
def test_restart(terminate):
    """Restarting the experiment should take back running tasks"""
    restart.restart(terminate, restart_function)


def test_submitted_twice():
    """Check that a job cannot be submitted twice within the same experiment"""
    with TemporaryExperiment("duplicate", maxwait=10) as xp:
        task1 = SimpleTask(x=1).submit()
        task2 = SimpleTask(x=1).submit()
        assert task1 is task2, f"{id(task1)} != {id(task2)}"


def test_configcache():
    """Test a configuration cache"""

    with TemporaryExperiment("configcache", maxwait=10) as xp:
        task = CacheConfigTask(data=CacheConfig()).submit()

    assert task.__xpm__.job.wait() == JobState.DONE
