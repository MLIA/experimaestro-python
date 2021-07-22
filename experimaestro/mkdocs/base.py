"""mkdocs plugin for documentation generation

See https://www.mkdocs.org/user-guide/plugins/ for plugin API documentation
"""

from collections import defaultdict
import functools
import re
from experimaestro.mkdocs.annotations import shoulddocument
import requests
from urllib.parse import urljoin
from experimaestro.core.types import ObjectType, Type
import mkdocs
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Set, Tuple, Type as TypingType
import importlib
import logging
import itertools
import inspect
import mkdocs.config.config_options as config_options
from mkdocs.structure.pages import Page as MkdocPage
from experimaestro.core.objects import Config
import json
from docstring_parser.parser import parse as docstringparse

MODULEPATH = Path(__file__).parent


def md_protect(s):
    return re.sub(r"""([*`_{}[\]])""", r"""\\\1""", s)


def relativepath(source: str, target: str):
    """Computes a relative path from source to target"""
    if source == target:
        return ""

    if source[-1] == "/":
        source = source[:-1]

    if target[-1] == "/":
        target = target[:-1]

    source_seq = source.split("/")
    target_seq = target.split("/")
    maxlen = min(len(source_seq), len(target_seq))

    i = 0
    while i < maxlen and target_seq[i] == source_seq[i]:
        i += 1

    path = [".."] * (len(source_seq) - i) + target_seq[i:]

    return "/".join(path)


class ObjectLatticeNode:
    objecttype: ObjectType
    parents: Set["ObjectLatticeNode"]
    children: Set["ObjectLatticeNode"]

    def __init__(self, objecttype):
        self.objecttype = objecttype
        self.children = set()
        self.parents = set()

    def __hash__(self):
        return self.objecttype.__hash__()

    def __eq__(self, other):
        return other.objecttype is self.objecttype

    def __repr__(self):
        if self.objecttype is None:
            return "ROOT"
        return f"node({self.objecttype.identifier})"

    def isAncestor(self, other):
        return issubclass(self.objecttype.configtype, other.objecttype.configtype)

    def add(self, node: "ObjectLatticeNode"):
        if self.objecttype == node.objecttype:
            assert id(self) == id(node)
            return

        added = False
        replace = set()
        for child in self.children:
            if node.isAncestor(child):
                # Add in child
                child.add(node)
                added = True
            elif child.isAncestor(node):
                # Replace child
                replace.add(child)

        # Replace children
        for child in replace:
            # Remove child
            child.parents.remove(self)
            self.children.remove(child)

            # Insert node
            self.children.add(node)
            child.parents.add(node)
            node.parents.add(self)
            added = True

        # No suitable parent found
        if not added:
            node.parents.add(self)
            self.children.add(node)

        return node

    def find(self, objecttype):
        if objecttype == self.objecttype:
            return self

        for child in self.children:
            node = child.find(objecttype)
            if node is not None:
                return node

    def topologicalOrder(
        self, current: List["ObjectLatticeNode"], cover: Set["ObjectLatticeNode"]
    ):
        for child in self.children:
            current.append(child)

        for child in self.children:
            child.topologicalOrder(current, cover)


class ObjectLattice:
    """Lattice of objects"""

    def __init__(self):
        self.node = ObjectLatticeNode(None)

    def add(self, objecttype: ObjectType):
        node = self.node.find(objecttype)
        if node is None:
            node = ObjectLatticeNode(objecttype)
            self.node.add(node)
        return node

    def topologicalOrder(self) -> List[ObjectLatticeNode]:
        current = []
        self.node.topologicalOrder(current, set())
        return current


class Configurations:
    def __init__(self):
        self.tasks = set()
        self.configs = set()

    def add(self, node: ObjectLatticeNode):
        s = self.tasks if node.objecttype.task is not None else self.configs
        s.add(node)

    def remove(self, node):
        s = self.tasks if node.objecttype.task is not None else self.configs
        s.remove(node)

    def __iter__(self) -> Iterator[ObjectLatticeNode]:
        return itertools.chain(self.configs, self.tasks)


class Documentation(mkdocs.plugins.BasePlugin):
    RE_SHOWCLASS = re.compile(r"::xpm::([^ \n]+)")

    config_scheme = (
        ("name", config_options.Type(str, default="Tasks and configurations")),
        ("modules", config_options.Type(list)),
        ("external", config_options.Type(list)),
        ("init", config_options.Type(list)),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # path to sets of XPM types
        self.configurations: Dict[str, Configurations] = defaultdict(
            lambda: Configurations()
        )

        # Maps XPM types to markdown paths
        self.type2path = {}

        self.lattice = ObjectLattice()

    def on_config(self, config, **kwargs):
        # Import modules in init
        for module_name in self.config.get("init") or []:
            importlib.import_module(module_name)

        # Include documentation pages in config
        self.parsed = {}
        self.external = {}
        self.baseurl = config["site_url"]

        for item in self.config.get("external") or []:
            module_name, url = next(iter(item.items()))
            logging.info("Loading external mappings from %s", url)
            baseurl = str(urljoin(url, "."))
            mappings = requests.get(url).json()
            for module, path in mappings.items():
                self.external[module] = f"{baseurl}{path}"

        # Retrieve all configurations and tasks
        processed = set()
        for name_packagename in self.config["modules"]:
            md_path, module_names = next(iter(name_packagename.items()))
            path_cfgs = self.configurations[md_path]

            if md_path.endswith(".md"):
                md_path = md_path[:-3]

            for module_name in module_names:
                package = importlib.import_module(module_name)
                basepath = Path(package.__path__[0])

                for path in basepath.rglob("*.py"):
                    parts = list(path.relative_to(basepath).parts)
                    if parts[-1] == "__init__.py":
                        parts = parts[:-1]
                    elif parts[-1].endswith(".py"):
                        parts[-1] = parts[-1][:-3]

                    fullname = (
                        f"""{module_name}.{".".join(parts)}""" if parts else module_name
                    )

                    # Avoid to re-parse
                    if fullname in self.parsed:
                        continue
                    self.parsed[fullname] = f"{md_path}.html"

                    try:
                        module = importlib.import_module(fullname)
                        for _, member in inspect.getmembers(
                            module,
                            lambda t: inspect.isclass(t) and issubclass(t, Config),
                        ):
                            # Only include members of the module
                            if member.__module__ != fullname:
                                continue

                            xpmtype = member.__getxpmtype__()
                            if xpmtype in processed:
                                continue

                            processed.add(xpmtype)

                            node = self.lattice.add(xpmtype)
                            path_cfgs.add(node)

                            # Register on which page the type is defined
                            self.type2path[
                                f"{member.__module__}.{member.__qualname__}"
                            ] = f"{md_path}.html"

                            member.__xpmtype__.__initialize__()

                    except Exception as e:
                        logging.exception(
                            "Error while reading definitions file %s: %s", path, e
                        )
        return config

    def on_post_build(self, config):
        mapping_path = Path(config["site_dir"]) / "experimaestro-mapping.json"
        logging.info("Writing mapping file %s", mapping_path)
        with mapping_path.open("wt") as fp:
            json.dump(self.parsed, fp)

    def showlink(self, location, m: re.Match):
        """Show a link to the documentation"""
        return self.getlink(location, m.group(1).strip())

    def showclass(self, location, m: re.Match, page: MkdocPage, cfgs: Configurations):
        """Show a class and its descendants"""

        # Search for the class
        classname = m.group(1)
        node = None
        for _node in cfgs:
            basetype = _node.objecttype.basetype
            if f"{basetype.__module__}.{basetype.__qualname__}" == classname:
                node = _node
                break

        if node is None:
            return f"<div class='error'>Cannot find {classname}</div>"

        # Now, sort according to descendant/ascendant relationship or name
        nodes = set()
        for _node in cfgs:
            if issubclass(_node.objecttype.configtype, node.objecttype.configtype):
                nodes.add(_node)

        # Removes so they are not generated twice
        for node in nodes:
            try:
                cfgs.remove(node)
            except Exception:
                logging.error("Cannot remove %s", node)

        # objecttypes.sort(key=functools.cmp_to_key(lambda a, b: if issubclass(a.objecttype, b.objecttype)))
        lines = []
        self.build_doc(page, lines, nodes)
        return "".join(lines)

    def _getlink(self, url, qualname: str) -> Tuple[str, Optional[str]]:
        """Get a link given a qualified name"""

        # Use an internal reference
        md_path = self.type2path.get(qualname, None)
        if md_path:
            return qualname, f"{relativepath(url, md_path)}#{qualname}"

        # Try to get an external reference
        module_name = qualname[: qualname.rfind(".")]
        baseurl = self.external.get(module_name, None)

        return qualname, f"{baseurl}#{qualname}" if baseurl else None

    def getlink(self, url, qualname: str):
        """Get a link given a qualified name"""
        qualname, href = self._getlink(url, qualname)
        if href:
            return f"[{qualname}]({href})"
        return qualname

    def getConfigLink(self, pageURL: str, config: TypingType):
        return self._getlink(pageURL, f"{config.__module__}.{config.__qualname__}")

    def build_doc(
        self, page: MkdocPage, lines: List[str], nodes: List[ObjectLatticeNode]
    ):
        """Build the documentation for a list of configurations"""

        # Sort
        # lattice = ObjectLattice()
        # for node in nodes:
        #     lattice.add(node.objecttype)

        # sortednodes = lattice.topologicalOrder()

        for node in nodes:
            xpminfo = node.objecttype
            fullqname = (
                f"{xpminfo.objecttype.__module__}.{xpminfo.objecttype.__qualname__}"
            )
            lines.extend(
                (
                    f"""### {xpminfo.title} <span id="{fullqname}"> </span>\n\n""",
                    f"""`from {xpminfo.objecttype.__module__} import {xpminfo.objecttype.__name__}`\n\n""",
                )
            )

            if xpminfo.description:
                lines.extend((xpminfo.description, "\n\n"))

            # Add parents
            parents = list(xpminfo.parents())
            if parents:
                lines.append("*Parents*: ")
                lines.append(
                    ", ".join(
                        self.getlink(page.url, parent.fullyqualifiedname())
                        for parent in parents
                    )
                )
                lines.append("\n\n")

            if node.children:
                lines.append("*Children*: ")
                lines.append(
                    ", ".join(
                        self.getlink(page.url, child.objecttype.fullyqualifiedname())
                        for child in node.children
                    )
                )
                lines.append("\n\n")

            for name, argument in xpminfo.arguments.items():

                if isinstance(argument.type, ObjectType):
                    basetype = argument.type.basetype
                    typestr = self.getlink(
                        page.url, f"{basetype.__module__}.{basetype.__qualname__}"
                    )
                else:
                    typestr = argument.type.name()

                lines.append("- ")
                if argument.generator:
                    lines.append(" [*generated*] ")
                elif argument.constant:
                    lines.append(" [*constant*] ")
                lines.append(f"**{name}** ({typestr})")
                if argument.help:
                    lines.append(f"\n  {argument.help}")
                lines.append("\n\n")

            methods = [
                member
                for key, member in inspect.getmembers(
                    xpminfo.objecttype,
                    predicate=lambda member: inspect.isfunction(member)
                    and shoulddocument(member),
                )
            ]

            if methods:
                lines.append("**Methods**\n\n")
                for method in methods:
                    parseddoc = docstringparse(method.__doc__)
                    lines.append(
                        f"""- {md_protect(method.__name__)}() *{parseddoc.short_description}*\n"""
                    )

    def on_page_markdown(self, markdown, page: MkdocPage, **kwargs):
        """Generate markdown pages"""
        path = page.file.src_path

        cfgs = self.configurations.get(path, None)
        if cfgs is None:
            return markdown

        markdown = Documentation.RE_SHOWCLASS.sub(
            lambda c: self.showclass(page.url, c, page, cfgs), markdown
        )

        lines = [
            markdown,
            "<style>",
            (MODULEPATH / "style.css").read_text(),
            "</style>\n",
            "<div><hr></div>",
            "*Documentation generated by experimaestro*\n",
        ]

        if cfgs.configs:
            lines.extend(["## Configurations\n\n"])
            self.build_doc(page, lines, cfgs.configs)

        if cfgs.tasks:
            lines.extend(["## Tasks\n\n"])
            self.build_doc(page, lines, cfgs.tasks)

        return "".join(lines)
