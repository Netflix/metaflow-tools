import os
import re
import signal
import subprocess
import time
from collections import defaultdict, namedtuple
from threading import Thread

from .expiring_directory import (ExpiringDirectory, garbage_collect,
                                 refresh_timestamp)

NUM_LAST_LINES = 3

# TODO: FIX this
METAFLOW_STATUS_RE =\
    re.compile('.+? .+? '
               '\[(?P<run_id>.+?)/(?P<step>.+?)/(?P<task_id>.+?) .+?\] '
               ' ?(?P<body>.+)')

HOUR = 60 * 60
RUN_TTL = 7 * 24 * HOUR
RUNS_ROOT = 'runs'


class RunStatus(object):
    def __init__(self, tags):
        self.status = 'starting'
        self.run_id = None
        self.tags = tags
        self.current_step = 'starting'
        self.tasks = defaultdict(set)
        self.num_active_tasks = 0
        self.last_lines = []


Run = namedtuple('Run', ['id', 'proc', 'stdout', 'stderr', 'status'])

# MFBRunGroup assumes that one process controls one rungroup_id.
# It is not safe to have multiple processes making destructive
# updates in one rungroup_id concurrently. However, adding files
# with .add_indicator() and read-only operations, e.g. .read(),
# are safe in a multiprocess environment.


class MFBRunGroup(ExpiringDirectory):

    def __init__(self, rungroup_id, code=None, username=None):
        self.id = rungroup_id
        self.code = code
        self.username = username
        self.runs = []
        self.cleanup_threads = []
        super().__init__(RUNS_ROOT, self.id, RUN_TTL)
        self._makedirs(self.root)

    def __len__(self):
        return len(self.runs)

    @refresh_timestamp
    def add_indicator(self, indicator, body=''):
        with open(os.path.join(self.root, indicator), 'w') as f:
            f.write(body)

    @refresh_timestamp
    def has_indicator(self, indicator):
        return os.path.exists(os.path.join(self.root, indicator))

    @refresh_timestamp
    def pop_indicator(self, indicator):
        path = os.path.join(self.root, indicator)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    @garbage_collect
    @refresh_timestamp
    def add_run(self, run_id, args, tags):
        python, script_name = self.code.script_info()

        stdout = os.path.join(self.root, '%s.stdout' % run_id)
        stderr = os.path.join(self.root, '%s.stderr' % run_id)
        env = dict(os.environ)

        cmd = [python,
               script_name,
               '--no-pylint',
               '--package-suffixes',
               '',
               'run',
               '--with', 'batch'] + args

        for tag in tags:
            cmd.extend(('--tag', tag))

        proc = subprocess.Popen(cmd,
                                executable=python,
                                cwd=self.code.root,
                                stdout=open(stdout, 'wb'),
                                stderr=open(stderr, 'wb'),
                                env=env)

        self.runs.append(Run(id=run_id,
                             proc=proc,
                             stdout=open(stdout),
                             stderr=open(stderr),
                             status=RunStatus(tags)))

    def run_statuses(self):
        for run in self.runs:
            self._parse_logs(run)
            if run.status.status != 'cancelled':
                ret = run.proc.poll()
                if ret is None:
                    run.status.status = 'running'
                elif ret == 0:
                    run.status.status = 'done'
                else:
                    run.status.status = 'failed'
            yield run.id, run.status

    def _clean_line(self, line):
        m = METAFLOW_STATUS_RE.match(line)
        return m.group('body') if m else line.strip()

    def readlines(self, run_id, stream):
        with open(os.path.join(self.root, '%s.%s' % (run_id, stream))) as f:
            return list(map(self._clean_line, f.readlines()))

    def cancel(self):
        def cleanup(proc):
            # give the Metaflow process a chance to cleanup
            # after SIGINT. If it has not exited after 2 minutes,
            # we kill the process. We run this as a separate thread
            # so the user does not have to wait for the cleanup
            # process to finish.
            for i in range(120):
                time.sleep(1)
                if run.proc.poll() is not None:
                    return
            else:
                run.proc.kill()

        for run in self.runs:
            run.status.status = 'cancelled'
            run.proc.send_signal(signal.SIGINT)
            t = Thread(target=cleanup, args=(run.proc,))
            self.cleanup_threads.append(t)
            t.start()
        # wait for a few seconds, so we may capture some nice output
        # in the logs related to canceling
        time.sleep(5)

    def wait(self):
        for thread in self.cleanup_threads:
            thread.join()

    def _parse_logs(self, run):
        for stream in (run.stdout, run.stderr):
            for line in stream:
                m = METAFLOW_STATUS_RE.match(line)
                if line:
                    if len(run.status.last_lines) > NUM_LAST_LINES:
                        del run.status.last_lines[0]
                    if m:
                        run.status.last_lines.append(m.group('body'))
                    else:
                        run.status.last_lines.append(line.strip())
                if m:
                    run.status.run_id = m.group('run_id')
                    run.status.current_step = m.group('step')
                    run.status.tasks[m.group(2)].add(m.group('task_id'))
                    if line.endswith('Task is starting.\n'):
                        run.status.num_active_tasks += 1
                    elif line.endswith('Task finished successfully.\n'):
                        run.status.num_active_tasks -= 1
