# Mypy support
from mypy.plugin import Plugin

class ExperimaestroPlugin(Plugin):
    def get_type_analyze_hook(self, fullname: str):
        # see explanation below
        ...
    def get_type_analyze_hook(self, fullname):
        if fullname == "experimaestro.annotations.Param":
            print("Yo", fullname)

def plugin(version: str):
    # ignore version argument if the plugin works with all mypy versions.
    return ExperimaestroPlugin