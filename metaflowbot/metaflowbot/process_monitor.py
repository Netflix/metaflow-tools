from hashlib import sha1


def process_fingerprint_matches(fingerprint):
    pid, cmdhash = fingerprint.split(':')
    try:
        # if PID is not alive anymore, reading /proc/PID/cmdline
        # fails, so we return False. There's a theoretical possibility
        # that the PID is alive but it corresponds to a different
        # process than what we were monitoring originally. To guard
        # against this false positive, we check the hash of the process
        # command line, aka "process fingerprint".
        return process_fingerprint(pid) == fingerprint
    except:
        return False


def process_fingerprint(pid):
    path = '/proc/%s/cmdline' % pid
    with open(path, 'rb') as f:
        return '%s:%s' % (pid, sha1(f.read()).hexdigest())
