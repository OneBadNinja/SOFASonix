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
#                           File: MusicalInstrumentDirectivity_1.0_1.0.py
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

# Create SOFAFile object with the latest MusicalInstrumentDirectivity convention
sofa = SOFAFile("MusicalInstrumentDirectivity", sofaConventionsVersion=1.0, version=1.0)

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
sofa.GLOBAL_DateCreated = "2019-06-07 20:32:05"
sofa.GLOBAL_DateModified = "2019-06-07 20:32:05"
sofa.GLOBAL_Title = ""
sofa.GLOBAL_InstrumentType = ""
sofa.GLOBAL_InstrumentManufacturer = ""
sofa.GLOBAL_Musician = ""
sofa.GLOBAL_MusicianPosition = ""
sofa.N_LongName = "frequency"
sofa.N_Units = "hertz"
sofa.ListenerPosition_Type = "cartesian"
sofa.ListenerPosition_Units = "metre"
sofa.ReceiverPosition_Type = "cartesian"
sofa.ReceiverPosition_Units = "metre"
sofa.SourcePosition_Type = "spherical"
sofa.SourcePosition_Units = "degree, degree, metre"
sofa.SourcePosition_Definition = ""
sofa.SourceView_Type = "spherical"
sofa.SourceView_Units = "degree, degree, metre"
sofa.SourceView_Definition = ""
sofa.SourceUp_Type = "spherical"
sofa.SourceUp_Units = "degree, degree, metre"
sofa.SourceUp_Definition = ""
sofa.EmitterPosition_Type = "cartesian"
sofa.EmitterPosition_Units = "degree, degree, metre"

# ----- Non-Mandatory attributes -----
sofa.GLOBAL_ApplicationName = None
sofa.GLOBAL_ApplicationVersion = None
sofa.GLOBAL_History = None
sofa.GLOBAL_References = None
sofa.GLOBAL_Origin = None
sofa.EmitterDescription = None
sofa.TuningFrequency_LongName = None
sofa.TuningFrequency_Units = None


"""
=============================== Double Variables ==============================
"""

# ----- Mandatory double variables -----

# Needs dimensions N or NE
sofa.N = np.zeros(1)

# Needs dimensions IC
sofa.ListenerPosition = np.zeros(1)

# Needs dimensions rCI
sofa.ReceiverPosition = np.zeros(1)

# Needs dimensions IC
sofa.SourcePosition = np.zeros(1)

# Needs dimensions IC
sofa.SourceView = np.zeros(1)

# Needs dimensions IC
sofa.SourceUp = np.zeros(1)

# Needs dimensions eCI
sofa.EmitterPosition = np.zeros(1)

# Needs dimensions mREn
sofa.Data_Real = np.zeros(1)

# Needs dimensions MREN
sofa.Data_Imag = np.zeros(1)

# ----- Non-mandatory double variables -----

# Needs dimensions E
sofa.EmitterMidiNote = None

# Needs dimensions I or E
sofa.TuningFrequency = None


"""
=============================== Export ========================================
"""

# Save file upon completion
sofa.export("filename")
