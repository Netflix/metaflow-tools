import os
import subprocess
import json
import tempfile


def handler(event, context):
    env = dict(os.environ)
    env.update(event["env"])
    print(json.dumps(event))

    # Set it here so that lambda plugin can save it to metadata
    env['LAMBDA_REQUEST_ID'] = context.aws_request_id

    with tempfile.TemporaryDirectory() as tmp_dir:

        # Create virtual env. We can't just pip install system wide due to read-only
        # filesystem in Lambda runtime.
        rc = subprocess.call(
            args=[
                "/bin/sh",
                "-c",
                "python -m venv --system-site-packages " + os.path.join(tmp_dir, "env"),
            ]
        )
        assert rc == 0

        # Add env to $PATH
        env["PATH"] = os.path.join(tmp_dir, "env/bin") + ":" + env.get("PATH", "")

        # Run whatever we need to run
        p = subprocess.Popen(
            args=event["args"],
            env=env,
            bufsize=0,
            cwd=tmp_dir,
        )

        rc = p.wait()

        return {'return_code': rc}
