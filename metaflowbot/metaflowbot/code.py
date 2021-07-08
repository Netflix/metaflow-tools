import inspect
import json
import os
import subprocess
import sys
import tempfile

from metaflow import Run, namespace

from .expiring_directory import (ExpiringDirectory, garbage_collect,
                                 refresh_timestamp)

HOUR = 60 * 60
FLOW_APPLY_TIMEOUT = 2 * 60
CODE_TTL = 7 * 24 * HOUR
CODE_ROOT = 'code'

# a key feature of MFBCode is that it is safe to use
# in multiple concurrent processes that deal with the
# same run.
class MFBCode(ExpiringDirectory):

    def __init__(self, run_pathspec):
        self.flow_name = run_pathspec.split('/')[0]
        self.pathspec = run_pathspec
        self.id = run_pathspec.replace('/', '_')
        super().__init__(CODE_ROOT, self.id, CODE_TTL)

    @garbage_collect
    @refresh_timestamp
    def load(self):
        if not self.is_cached:
            self._download_and_extract(self.pathspec)
        return self

    @refresh_timestamp
    def flowspec_apply(self, func):

        def get_flow():

            import importlib
            import inspect
            import sys

            from metaflow import FlowSpec

            # We don't want to start executing the flow
            # if the user's code instantiates it. We
            # ensure this by monkey-patching FlowSpec.
            class NoopFlowSpec(object):
                pass
            sys.modules['metaflow'].FlowSpec = NoopFlowSpec

            mod = importlib.import_module(MODULE_NAME)
            for name in dir(mod):
                if name != 'FlowSpec':
                    attr = getattr(mod, name)
                    if inspect.isclass(attr) and issubclass(attr, NoopFlowSpec):
                        return attr

        def format_func(func):
            lines, _ = inspect.getsourcelines(func)
            indent = lines[0].index('def')
            return ''.join(l[indent:] for l in lines)

        python, script_name = self.script_info()
        with tempfile.NamedTemporaryFile(dir=self.root,
                                         prefix='.flow_apply.',
                                         mode='w') as tmp:
            # we need to write the function output to a file instead
            # of capturing it on stdout, since the user's module may
            # output anything on stdout/stderr
            tmp.write('\n'.join([\
                'import json',
                'MODULE_NAME = "{module_name}"',
                '{get_flow}',
                '{user_func}',
                'with open("{tmp}.out", "w") as f:',
                '    json.dump({user_func_name}(get_flow()), f)'])\
                .format(module_name=script_name.split('.')[0],
                        get_flow=format_func(get_flow),
                        user_func=format_func(func),
                        tmp=tmp.name,
                        user_func_name=func.__name__))
            tmp.flush()
            subprocess.check_call([python, tmp.name],
                                  cwd=self.root,
                                  stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL,
                                  timeout=FLOW_APPLY_TIMEOUT)
            output = '%s.out' % tmp.name
            try:
                with open(output) as f:
                    return json.load(f)
            finally:
                try:
                    os.unlink(output)
                except:
                    pass

    def script_info(self):
        with open(os.path.join(self.root, 'INFO')) as f:
            info = json.load(f)
            python = 'python%s' % info['python_version'][0]
            script_name = info['script']
            return python, script_name

    def _download_and_extract(self, run_pathspec):
        path = tempfile.mkdtemp(prefix=self.id + '.', dir=CODE_ROOT)
        namespace(None)
        Run(run_pathspec).code.tarball.extractall(path=path)
        done = path + '.DONE'
        os.symlink(os.path.basename(path), done)
        os.rename(done, self.root)

if __name__ == '__main__':
    def test_func(x):
        return {'foo': str(x)}
    print(MFBCode('HelloFlow/671').load().flowspec_apply(test_func))
