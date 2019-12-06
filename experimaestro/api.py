"""Old layer between the C API and experimaestro

TODO: re-organize
"""

import json
import sys
import inspect
import os.path as op
import os
import logging
from pathlib import Path, PosixPath
import re
from typing import Union, Dict, List, Set
import hashlib
import struct
from experimaestro.utils import logger

# --- Initialization

modulepath = Path(__file__).parent

class Typename():
    def __init__(self, name: str):
        self.name = name

    def __getattr__(self, key):
        return self(key)

    def __call__(self, key):
        return Typename(self.name + "." + key)

    def __str__(self):
        return self.name


def typename(name: Union[str, Typename]):
    if isinstance(name, Typename):
        return name
    return Typename(str(name))


class Argument:
    def __init__(self, name, type: "Type", required=None, help=None, generator=None, ignored=False, default=None):
        required = (default is None) if required is None else required
        if default is not None and required is not None and required:
            raise Exception("Argument '%s' is required but default value is given" % name)

        self.name = name
        self.help = help
        self.type = type
        self.ignored = ignored
        self.required = required
        self.default = default
        self.generator = generator

    def __repr__(self):
        return "argument[{name}:{type}]".format(**self.__dict__)

class TypeAttribute:
    def __init__(self, type, key):
        self.type = type
        self.path = [key]

class Type():
    DEFINED:Dict[type, "Type"] = {}

    def __init__(self, tn: Union[str, Typename], description=None): 
        if tn is None:
            tn = None
        elif isinstance(tn, str):
            tn = Typename(tn)
        self.typename = tn
        self.description = description
        self.arguments:Dict[str, Argument] = {}

    def __str__(self):
        return "Type({})".format(self.typename)

    def __repr__(self):
        return "Type({})".format(self.typename)

    def name(self):
        return str(self.typename)

    def addArgument(self, argument: Argument):
        self.arguments[argument.name] = argument

    def getArgument(self, key: str) -> Argument:
        return self.arguments[key]

    def isArray(self):
        return False


    @staticmethod
    def fromType(key):
        """Returns the Type object corresponding to the given type"""
        logger.debug("Searching for type %s", key)

        if key is None:
            return AnyType

        defined = Type.DEFINED.get(key, None)
        if defined:
            return defined

        if isinstance(key, Type):
            return key

        if isinstance(key, TypeProxy):
            return key()

        if isinstance(key, PyObject):
            return key.__class__.__xpm__
        
        if inspect.isclass(key) and issubclass(key, PyObject):
            return key.__xpm__

        raise Exception("No type found for %s", key)


class ObjectType(Type):
    """The type of PyObject"""

    REGISTERED:Dict[Typename, "PyObject"] = {}
    def __init__(self, objecttype: "PyObject", typename, description):
        super().__init__(typename, description)
        self.objecttype = objecttype

        if self.typename in ObjectType.REGISTERED:
            raise Exception("Experimaestro type %s is already declared" % self.typename)
        ObjectType.REGISTERED[self.typename] = objecttype

        self.task = None

    def validate(self, value):
        if not isinstance(value, PyObject):
            raise ValueError("%s is not an experimaestro type or task", value)
        if not isinstance(value, self.objecttype):
            raise ValueError("%s is not a subtype of %s")

        if self.task and not value.__xpm__.job:
            raise ValueError("The value must be submitted before giving it")
        return value


class TypeProxy: 
    def __call__(self) -> Type:
        """Returns the real type"""
        raise NotImplementedError()

def definetype(*types):
    def call(typeclass):
        instance = typeclass(types[0].__name__)
        for t in types:
            Type.DEFINED[t] = instance
    return call

@definetype(int)
class IntType(Type): 
    def validate(self, value):
        return int(value)

@definetype(str)
class StrType(Type): 
    def validate(self, value):
        return str(value)

@definetype(float)
class FloatType(Type): 
    def validate(self, value):
        return float(value)

@definetype(Path)
class PathType(Type): 
    def validate(self, value):
        return Path(value)

AnyType = Type("any")

class ArrayType(Type):  
    def __init__(self, type: Type):
        self.type = type

    def validate(self, value):
        if not isinstance(value, List):
            raise ValueError("value is not a list")

        return [self.type.validate(x) for x in value]


# --- XPM Objects

class HashComputer():
    OBJECT_ID = b'\x00'
    INT_ID = b'\x01'
    FLOAT_ID = b'\x02'
    STR_ID = b'\x03'
    PATH_ID = b'\x04'
    NAME_ID = b'\x05'
    NONE_ID = b'\x06'
    LIST_ID = b'\x06'

    def __init__(self):
        self.hasher = hashlib.sha256()

    def digest(self):
        return self.hasher.digest()

    def update(self, value):
        if value is None:
            self.hasher.update(NONE_ID)
        if isinstance(value, float):
            self.hasher.update(HashComputer.FLOAT_ID)
            self.hasher.update(struct.pack('!d', value))
        elif isinstance(value, int):
            self.hasher.update(HashComputer.INT_ID)
            self.hasher.update(struct.pack('!q', value))
        elif isinstance(value, str):
            self.hasher.update(HashComputer.STR_ID)
            self.hasher.update(value.encode("utf-8"))
        elif isinstance(value, list):
            self.hasher.update(HashComputer.LIST_ID)
            self.hasher.update(struct.pack('!d', len(value)))
            for x in value:
                self.update(x)
        elif isinstance(value, PyObject):
            xpmtype = value.__class__.__xpm__ # type: Type
            self.hasher.update(HashComputer.OBJECT_ID)
            self.hasher.update(xpmtype.typename.name.encode("utf-8"))
            arguments = sorted(xpmtype.arguments.values(), key=lambda a: a.name)
            for argument in arguments:
                argvalue = getattr(value, argument.name, None)
                if argument.ignored or argument.generator:
                    continue
                if argument.default and argument.default == argvalue:
                    # No update if same value
                    continue
                self.hasher.update(HashComputer.NAME_ID)
                self.update(argvalue)
            
        else:
            raise NotImplementedError("Cannot compute hash of type %s" % type(value))

class TypeInformation():
    """Holds experimaestro information for a PyObject (Type or Task)"""

    def __init__(self, pyobject):
        # The underlying pyobject and XPM type
        self.pyobject = pyobject
        self.xpmtype = self.pyobject.__class__.__xpm__ # type: ObjectType

        # Meta-informations
        self.tags = {}

        # State information
        self.job = None
        self.setting = False

        # Cached information
        self._identifier = None
        self._validated = False
        self._sealed = False

    def set(self, k, v, bypass=False):
        if self._sealed:
            raise AssertionError("Object is read-only")

        argument = self.xpmtype.arguments.get(k, None)
        if argument:
            # If argument, check the value
            if not bypass and argument.generator:
                raise AssertionError("Property %s is read-only" % (k))
            object.__setattr__(self.pyobject, k, argument.type.validate(v))
        else:
            object.__setattr__(k, v)

    def run(self):
        self.pyobject.execute()

    def init(self):
        self.pyobject._init()

    def validate(self):
        """Validate values and seal the values"""
        if not self._validated:
            self._validated = True
            for k, argument in self.xpmtype.arguments.items():
                if hasattr(self.pyobject, k):
                    value = getattr(self.pyobject, k)
                    if isinstance(value, PyObject):
                        value.__xpm__.validate()
                elif argument.required:
                    if not argument.generator:
                        raise ValueError("Value %s is required but missing", k)

    def seal(self, jobcontext: "experimaestro.job.Job"):
        """Seal the object, generating values when needed, before scheduling the associated job(s)"""
        if self._sealed:
            return

        for k, argument in self.xpmtype.arguments.items():
            if argument.generator:
                self.set(k, argument.generator(jobcontext), bypass=True)
        self._sealed = True

    @property
    def identifier(self):
        """Computes the unique identifier"""
        if self._identifier is None:
            hashcomputer = HashComputer()
            hashcomputer.update(self.pyobject)
            self._identifier = hashcomputer.digest()
        return self._identifier

    def updatedependencies(self, dependencies: Set["experimaestro.dependencies.Dependency"]):
        for argument in self.xpmtype.arguments.values():
            if isinstance(argument.type, ObjectType):
                if argument.type.task:
                    raise NotImplementedError(argument.type.task)
                else:
                    getattr(self.pyobject, argument.name).__xpm__.updatedependencies(dependencies)
                

    def submit(self, workspace, launcher):
        # --- Prepare the object
        if self.job:
            raise Exception("Task %s was already submitted" % self)
        if not self.xpmtype.task:
            raise ValueError("%s is not a task" % self.xpmtype)

        self.validate()

        # --- Submit the job
        from .scheduler import Job, Scheduler

        self.job = self.xpmtype.task(self.pyobject, launcher=launcher, workspace=workspace)
        self.seal(self.job)

        # --- Search for dependencies
        self.updatedependencies(self.job.dependencies)

        if Scheduler.CURRENT.submitjobs:
            Scheduler.CURRENT.submit(self.job)
        else:
            logger.warning("Simulating: not submitting task", self.xpmtype.task)
        


def clone(v):
    """Clone a value"""
    if isinstance(v, (str, float, int)):
        return v
    if isinstance(v, list):
        return [clone(x) for x in v]
    raise NotImplementedError("For type %s" % v)

class PyObjectMetaclass(type):
    def __getattr__(cls, key):
        """Access to a class field"""
        return cls.__xpm__.arguments[key]

class PyObject(metaclass=PyObjectMetaclass):
    """Base type for all objects in python interface"""

    def __init__(self, **kwargs):
        assert self.__class__.__xpm__, "No XPM type associated with this XPM object"

        # Add configuration
        self.__xpm__ = TypeInformation(self)

        # Initialize with arguments
        for k, v in kwargs.items():
            self.__setattr__(k, v)

        # Initialize with default arguments
        for k, v in self.__class__.__xpm__.arguments.items():
            if k not in kwargs and v.default is not None:
                self.__setattr__(k, clone(v.default))

    def __setattr__(self, name, value):
        if name != "__xpm__":
            return self.__xpm__.set(name, value)
        return super().__setattr__(name, value)

    def submit(self, *, workspace=None, launcher=None):
        """Submit this task"""
        self.__xpm__.submit(workspace, launcher)
        return self

    def tag(self, name, value):
        self.__xpm__.tags[name] = value

    def _init(self):
        """Prepare object after creation"""
        pass

    def _stdout(self):
        return self.__xpm__.job.stdout