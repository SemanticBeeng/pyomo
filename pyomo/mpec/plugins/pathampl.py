#  _________________________________________________________________________
#
#  Pyomo: Python Optimization Modeling Objects
#  Copyright (c) 2008 Sandia Corporation.
#  This software is distributed under the BSD License.
#  Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
#  the U.S. Government retains certain rights in this software.
#  For more information, see the Pyomo README.txt file.
#  _________________________________________________________________________


import re
import os
import copy

import pyutilib.services
import pyutilib.common
import pyutilib.common
import pyutilib.misc

import pyomo.misc.plugin
from pyomo.opt.base import *
from pyomo.opt.base.solvers import _extract_version
from pyomo.opt.results import *
from pyomo.opt.solver import *

import logging
logger = logging.getLogger('pyomo.solvers')

try:
    unicode
except:
    basestring = str


class PATHAMPL(SystemCallSolver):
    """An interface to the PATH MCP solver."""

    pyomo.misc.plugin.alias('path', doc='Nonlinear MCP solver')

    def __init__(self, **kwds):
        #
        # Call base constructor
        #
        kwds["type"] = "path"
        SystemCallSolver.__init__(self, **kwds)
        #
        # Setup valid problem formats, and valid results for each problem format
        # Also set the default problem and results formats.
        #
        self._valid_problem_formats=[ProblemFormat.nl]
        self._valid_result_formats = {}
        self._valid_result_formats[ProblemFormat.nl] = [ResultsFormat.sol]
        self.set_problem_format(ProblemFormat.nl)
        #
        # Define solver capabilities, which default to 'None'
        #
        self._capabilities = pyutilib.misc.Options()
        self._capabilities.linear = True

    def _default_results_format(self, prob_format):
        return ResultsFormat.sol

    def executable(self):
        executable = pyutilib.services.registered_executable("pathampl")
        if executable is None:
            logger.warning("Could not locate the 'pathampl' executable, which is required for solver %s" % self.name)
            self.enable = False
            return None
        return executable.get_path()

    def version(self):
        """
        Returns a tuple describing the solver executable version.
        """
        solver_exec = self.executable()
        if solver_exec is None:
            return _extract_version('')
        results = pyutilib.subprocess.run( [solver_exec, '-v'], timelimit=1 )
        return _extract_version(results[1])

    def create_command_line(self, executable, problem_files):
        assert(self._problem_format == ProblemFormat.nl)
        assert(self._results_format == ResultsFormat.sol)
        #
        # Define log file
        #
        if self.log_file is None:
            self.log_file = pyutilib.services.TempfileManager.create_tempfile(suffix="_pathampl.log")
        fname = problem_files[0]
        if '.' in fname:
            tmp = fname.split('.')
            if len(tmp) > 2:
                fname = '.'.join(tmp[:-1])
            else:
                fname = tmp[0]
        self.soln_file = fname+".sol"
        #
        # Define results file
        #
        self.results_file = self.soln_file
        #
        # Define command line
        #
        env=copy.copy(os.environ)
        cmd = [executable, problem_files[0], '-AMPL']
        if self._timer:
            cmd.insert(0, self._timer)
        # 
        opt=[]
        for key in self.options:
            if key is 'solver':
                continue
            if isinstance(self.options[key],basestring) and ' ' in self.options[key]:
                opt.append(key+"=\""+str(self.options[key])+"\"")
                cmd.append(str(key)+"="+str(self.options[key]))
            else:
                opt.append(key+"="+str(self.options[key]))
                cmd.append(str(key)+"="+str(self.options[key]))
        #
        # Merge with any options coming in through the environment
        #
        envstr = "pathampl_options"
        env[envstr] = " ".join(opt)
        #
        return pyutilib.misc.Bunch(cmd=cmd, log_file=self.log_file, env=env)


pyutilib.services.register_executable(name="pathampl")