from .SOFASonix import SOFASonix


def SOFATemplate(convention,
                 sofaConventionsVersion=False,
                 version=False,
                 path=False,
                 useNone=True,
                 testMode=False):
    # Create SOFAFile
    sofa = SOFASonix(convention, sofaConventionsVersion, version)
    convention = sofa.global_sofaconventions

    # Obtain parameters and sort by attributes, doubles and strings
    attributes = sofa.flatten()

    # Extract doubles.
    doubles = {k: attributes.pop(k) for k in list(attributes.keys())
               if attributes[k].isType("double")}

    # Extract strings
    strings = {k: attributes.pop(k) for k in list(attributes.keys())
               if attributes[k].isType("string")}

    # Create file and begin writing
    if(path):
        name = "{}.py".format(path)
    else:
        name = "{}_{}_{}.py".format(convention, sofa.GLOBAL_Version,
                                    sofa.GLOBAL_SOFAConventionsVersion)
    file = open(name, "w")

    # Write Licensing Info
    file.write("""#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2018, I.Laghidze
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of SOFASonix nor the names of its contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# =============================================================================
#
#                           File: {}
#                           Project: SOFASonix
#                           Author: I.Laghidze
#                           License: BSD 3
#
# =============================================================================

""".format(name.split("/")[-1]))


    headerString = """from SOFASonix import SOFAFile
import numpy as np

\"""
=============================== Initial Config ================================
\"""

# Create SOFAFile object with the latest {} convention
sofa = SOFAFile("{}", sofaConventionsVersion={}, version={})
""".format(convention, convention,
           sofa.GLOBAL_SOFAConventionsVersion, sofa.GLOBAL_Version)

    file.write(headerString)
    file.write("\n# Set dimensions\n")

    # Default dimensions
    dims = {"M": 100, "N": 1024, "R": 2, "E": 4}

    for dim in dims:
        if(not sofa.dims[dim]["ro"]):
            file.write("sofa._{} = {}\n".format(dim, dims[dim]))

    # Add view parameters code
    file.write("""
# View parameters of convention
sofa.view()
""")

    # Create attributes separator
    file.write("""\n\n\"\"\"
=============================== Attributes ====================================
\"\"\"\n""")

    # Generate mandatory attributes
    file.write("\n# ----- Mandatory attributes -----\n")
    for key, ai in attributes.items():
        if(not ai.isReadOnly() and ai.isRequired()):
            if(ai.value):
                file.write("sofa.{} = \"{}\"".format(ai.getShorthandName(),
                           ai.value))
            else:
                if(testMode):
                    file.write("sofa.{} = \"TestMode\"".format(ai.getShorthandName()))
                else:
                    file.write("sofa.{} = \"\"".format(ai.getShorthandName()))
            file.write("\n")

    # Generate non-mandatory attributes
    file.write("\n# ----- Non-Mandatory attributes -----\n")
    for key, ai in attributes.items():
        if(not ai.isReadOnly() and not ai.isRequired()):
            if(useNone):
                file.write("sofa.{} = None".format(ai.getShorthandName(),
                           ai.value))
            else:
                if(ai.value):
                    file.write("sofa.{} = \"{}\"".format(ai.getShorthandName(),
                               ai.value))
                else:   
                    if(testMode):
                        file.write("sofa.{} = \"TestMode\"".format(ai.getShorthandName()))
                    else:
                        file.write("sofa.{} = \"\"".format(ai.getShorthandName()))
            file.write("\n")

    if(strings):
        # Create strings separator
        file.write("""\n\n\"""
=============================== String Variables ==============================
\"""\n""")

        # Generate mandatory strings
        file.write("\n# ----- Mandatory string variables -----\n")
        for key, si in strings.items():
            if(not si.isReadOnly() and si.isRequired()): 
                file.write("\n# Needs dimensions {}\n".format(" or ".join(si.dimensions)))
                if(testMode):
                    dims = ", ".join(["sofa._{}".format(i) for i in si.dimensions[0]])
                    file.write("sofa.{} = np.zeros(({}))".format(si.getShorthandName(), dims))
                else:
                    file.write("sofa.{} = np.zeros(1)".format(si.getShorthandName()))
                file.write("\n")

        # Generate non-mandatory strings
        file.write("\n# ----- Non-mandatory string variables -----\n")
        for key, si in strings.items():
            if(not si.isReadOnly() and not si.isRequired()):
                file.write("\n# Needs dimensions {}\n".format(" or ".join(si.dimensions)))
                if(useNone):
                    file.write("sofa.{} = None".format(si.getShorthandName()))
                else:
                    if(testMode):
                        dims = ", ".join(["sofa._{}".format(i) for i in si.dimensions[0]])
                        file.write("sofa.{} = np.zeros(({}))".format(si.getShorthandName(), dims))
                    else:
                        file.write("sofa.{} = np.zeros(1)".format(si.getShorthandName()))
                file.write("\n")

    # Create doubles separator
    file.write("""\n\n\"""
=============================== Double Variables ==============================
\"""\n""")

    # Generate mandatory doubles
    file.write("\n# ----- Mandatory double variables -----\n")
    for key, di in doubles.items():
        if(not di.isReadOnly() and di.isRequired()):
            file.write("\n# Needs dimensions {}\n".format(" or ".join(di.dimensions)))
            if(testMode):
                dims = ", ".join(["sofa._{}".format(i) for i in di.dimensions[0]])
                file.write("sofa.{} = np.zeros(({}))".format(di.getShorthandName(), dims))
            else:
                file.write("sofa.{} = np.zeros(1)".format(di.getShorthandName()))
            file.write("\n")

    # Generate non-mandatory doubles
    file.write("\n# ----- Non-mandatory double variables -----\n")
    for key, di in doubles.items():
        if(not di.isReadOnly() and not di.isRequired()):
            file.write("\n# Needs dimensions {}\n".format(" or ".join(di.dimensions)))
            if(useNone):
                file.write("sofa.{} = None".format(di.getShorthandName()))
            else:
                if(testMode):
                    dims = ", ".join(["sofa._{}".format(i) for i in di.dimensions[0]])
                    file.write("sofa.{} = np.zeros(({}))".format(di.getShorthandName(), dims))
                else:
                    file.write("sofa.{} = np.zeros(1)".format(di.getShorthandName()))
            file.write("\n")

    # Create export separator
    file.write("""\n\n\"""
=============================== Export ========================================
\"""\n""")
    # Finally, create save file statement
    file.write("""
# Save file upon completion
sofa.export("filename")\n""")
