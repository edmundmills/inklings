import subprocess

from django.core.management.commands.runserver import \
    Command as RunServerCommand


class Command(RunServerCommand):
    def execute(self, *args, **kwargs):
        self.start_webpack_watcher()
        super(Command, self).execute(*args, **kwargs)

    def start_webpack_watcher(self):
        subprocess.run(["pkill", "-f", "webpack --watch"], check=False)
        subprocess.Popen(["npm", "run", "watch"])