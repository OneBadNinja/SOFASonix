#!/usr/bin/env python
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
#                           File: FreeFieldDirectivityTF_1.0_0.1.py
#                           Project: SOFASonix
#                           Author: I.Laghidze
#                           License: BSD 3
#
# =============================================================================

from SOFASonix import SOFAFile
import numpy as np

"""
=============================== Initial Config ================================
"""

# Create SOFAFile object with the latest FreeFieldDirectivityTF convention
sofa = SOFAFile("FreeFieldDirectivityTF", version=0.1, specVersion=1.0)

# Set dimensions
sofa._M = 100
sofa._N = 1024
sofa._R = 2
sofa._E = 4

# View parameters of convention
sofa.view()


"""
=============================== Attributes ====================================
"""

# ----- Mandatory attributes -----
sofa.GLOBAL_AuthorContact = ""
sofa.GLOBAL_Comment = ""
sofa.GLOBAL_License = "No license provided, ask the author for permission"
sofa.GLOBAL_Organization = ""
sofa.GLOBAL_RoomType = "free field"
sofa.GLOBAL_DateCreated = "2019-06-01 19:38:27"
sofa.GLOBAL_DateModified = "2019-06-01 19:38:27"
sofa.GLOBAL_Title = ""
sofa.GLOBAL_InstrumentType = ""
sofa.GLOBAL_InstrumentManufacturer = ""
sofa.GLOBAL_Musician = ""
sofa.ListenerPosition_Type = "cartesian"
sofa.ListenerPosition_Units = "metre"
sofa.ListenerView_Type = "spherical"
sofa.ListenerView_Units = "degree, degree, metre"
sofa.ListenerUp_Type = "spherical"
sofa.ListenerUp_Units = "degree, degree, metre"
sofa.ReceiverPosition_Type = "cartesian"
sofa.ReceiverPosition_Units = "metre"
sofa.SourcePosition_Type = "cartesian"
sofa.SourcePosition_Units = "metre"
sofa.SourcePosition_Reference = ""
sofa.SourceView_Type = "spherical"
sofa.SourceView_Units = "degree, degree, metre"
sofa.SourceView_Reference = ""
sofa.SourceUp_Type = "spherical"
sofa.SourceUp_Units = "degree, degree, metre"
sofa.SourceUp_Reference = ""
sofa.EmitterPosition_Type = "cartesian"
sofa.EmitterPosition_Units = "degree, degree, metre"
sofa.N_LongName = "frequency"
sofa.N_Units = "Hertz"

# ----- Non-Mandatory attributes -----
sofa.GLOBAL_ApplicationName = None
sofa.GLOBAL_ApplicationVersion = None
sofa.GLOBAL_History = None
sofa.GLOBAL_References = None
sofa.GLOBAL_Origin = None
sofa.MIDINoteDescription = None


"""
=============================== Double Variables ==============================
"""

# ----- Mandatory double variables -----

# Needs dimensions N
sofa.N = np.zeros(1)

# Needs dimensions IC or MC
sofa.ListenerPosition = np.zeros(1)

# Needs dimensions IC or MC
sofa.ListenerView = np.zeros(1)

# Needs dimensions IC or MC
sofa.ListenerUp = np.zeros(1)

# Needs dimensions rCI or rCM
sofa.ReceiverPosition = np.zeros(1)

# Needs dimensions IC or MC
sofa.SourcePosition = np.zeros(1)

# Needs dimensions IC or MC
sofa.SourceView = np.zeros(1)

# Needs dimensions IC or MC
sofa.SourceUp = np.zeros(1)

# Needs dimensions eCI
sofa.EmitterPosition = np.zeros(1)

# Needs dimensions mRn
sofa.Data_Real = np.zeros(1)

# Needs dimensions MRN
sofa.Data_Imag = np.zeros(1)

# ----- Non-mandatory double variables -----

# Needs dimensions I or M
sofa.MIDINote = None

# Needs dimensions I or M
sofa.TuningFrequency = None


"""
=============================== Export ========================================
"""

# Save file upon completion
sofa.export("filename")
