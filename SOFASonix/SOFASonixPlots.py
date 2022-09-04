#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2022, D.Carvalho
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
#                           File: SOFASonixPlots.py
#                           Project: SOFASonix
#                           Author: D.Carvalho
#                           License: BSD 3
#
# =============================================================================

import matplotlib.pyplot as plt
import numpy as np


class SOFASonixPlots:
    def __init__(self, Obj_sofa,
                 plot_type,
                 title='',
                 verticalRange=2,
                 horizontalRange=2,
                 noisefloor=-50,
                 ear=[0, 1],
                 azim=0,
                 elev=0,
                 unwrap=False):
        '''
        Plot the most comon graphs in HRTF analysis

        Parameters
        ----------
        Obj_sofa : class object
            SOFAsonix SimpleFreeFieldHRIR.
        plot_type : string
            'MagHorizontal': surface plot of all the HRTFs magnitude in the horiontal plane
            'MagMedian':     surface plot of all the HRTFs magnitude in the median plane
            'spectrum':      magnitude spectra for a single position
            'time':          impulse response for a single position
            'phase':         phase response for a single position
        title : string, optional
            desired title for the plot figure. The default is ''.
        verticalRange : int, optional
            +/- the amplitude of the region to search for the median plane in
            case of 'MagMedian' plot type. The default is 2.
        horizontalRange : int, optional
            +/- the amplitude of the region to search for the horiontal plane in
            case of 'MagHorizontal' plot type. The default is 2.
        noisefloor : float, optional
            cuttoff amplitude in the surface plots. The default is -50 (dB).
        ear : list, optional
            Specifies which ears to plot, where [0] is left and [1] is right.
            The default is [0, 1].
        azim : float, optional
            Azimuth position (relevant for plot types ['spectrum', 'time', 'phase']).
            Nearest neighbor interpolation is applied. The default is 0.
        elev : float, optional
            Elevation position (relevant for plot types ['spectrum', 'time', 'phase']).
            Nearest neighbor interpolation is applied. The default is 0.
        phaseUnwrap : bool, optional
            Whether or not to unwrap the phase in the 'phase' plot. The default is False.

        '''
        self.Obj = Obj_sofa
        self.plot_type = plot_type.lower()
        self.title = title
        self.verticalRange = np.abs(verticalRange)
        self.horizontalRange = np.abs(horizontalRange)
        self.noisefloor = noisefloor
        self.ear = ear
        self.ear_label = ['left', 'right']
        self.azim = azim
        self.elev = elev
        self.unwrap = unwrap
        self.HRIRs = Obj_sofa.Data_IR
        self.pos = Obj_sofa.SourcePosition
        self.fs = Obj_sofa.Data_SamplingRate
        self.freqVec = np.fft.rfftfreq(self.HRIRs.shape[-1], 1 / self.fs)

        # call plots
        if self.plot_type == 'maghorizontal':
            self.mag_horizontal()
        elif self.plot_type == 'magmedian':
            self.mag_median()
        elif self.plot_type == 'spectrum':
            self.mag_spectrum()
        elif self.plot_type == 'time':
            self.IR_time()
        elif self.plot_type == 'phase':
            self.IR_phase()

    def mag_horizontal(self):
        # find horizontal plane
        idx_pos = np.where(np.logical_and(self.pos[:, 1] > -self.verticalRange,
                                          self.pos[:, 1] < self.verticalRange))
        posi = np.squeeze(self.pos[idx_pos, :2])

        for ch in self.ear:
            hM = np.squeeze(self.HRIRs[:, ch, :])
            M = np.squeeze(20 * np.log10(np.abs(np.fft.rfft(hM[idx_pos, :], axis=-1))))

            azi = np.sort(posi[:, 0], axis=0)
            i = np.argsort(posi[:, 0], axis=0)
            M = M[i, :]

            plt.figure()
            fig, ax = plt.subplots()
            ax.pcolormesh(self.freqVec, azi, M, shading='nearest', vmin=self.noisefloor)
            plt.ylim([0, 360])
            plt.xlabel('Frequency (Hz)')
            plt.ylabel('Azimuth (deg)')
            plt.title(self.title)
            plt.show()

    def mag_median(self):
        # find median plane
        idx_pos = np.where(np.logical_and(self.pos[:, 0] > -self.horizontalRange,
                                          self.pos[:, 0] < self.horizontalRange))
        posi = np.squeeze(self.pos[idx_pos, :2])

        for ch in self.ear:
            hM = np.squeeze(self.HRIRs[:, ch, :])  # left ear
            M = np.squeeze(20 * np.log10(np.abs(np.fft.rfft(hM[idx_pos, :], axis=-1))))

            ele = np.sort(posi[:, 1], axis=0)
            i = np.argsort(posi[:, 1], axis=0)
            M = M[i, :]

            plt.figure()
            fig, ax = plt.subplots()
            ax.pcolormesh(self.freqVec, ele, M, shading='nearest', vmin=self.noisefloor)
            plt.ylim([-90, 90])
            plt.xlabel('Frequency (Hz)')
            plt.ylabel('Elevation (deg)')
            plt.title(self.title)
            plt.show()

    def mag_spectrum(self):
        plt.figure()
        idx_pos = np.sqrt((self.pos[:, 0] - self.azim)**2 + (self.pos[:, 1] - self.elev)**2).argmin()
        for ch in self.ear:
            M = np.squeeze(20 * np.log10(np.abs(np.fft.rfft(self.HRIRs[idx_pos, ch, :], axis=-1))))

            plt.semilogx(self.freqVec, M, label=self.ear_label[ch])
            plt.xlim([20, 20000])
            plt.xlabel('Frequency (Hz)')
            plt.ylabel('Magitude (dB)')
            plt.title(self.title)
        plt.legend()
        plt.show()

    def IR_time(self):
        plt.figure()
        idx_pos = np.sqrt((self.pos[:, 0] - self.azim)**2 + (self.pos[:, 1] - self.elev)**2).argmin()
        for ch in self.ear:
            M1 = np.squeeze(self.HRIRs[idx_pos, ch, :])
            N = M1.shape[-1]
            tx = np.arange(0, N / self.fs, 1 / self.fs)

            plt.plot(tx, M1, label=self.ear_label[ch])
            plt.xlabel('Time (sec)')
            plt.ylabel('Amplitude')
            plt.title(self.title)
        plt.legend()
        plt.show()

    def IR_phase(self):
        plt.figure()
        idx_pos = np.sqrt((self.pos[:, 0] - self.azim)**2 + (self.pos[:, 1] - self.elev)**2).argmin()
        for ch in self.ear:
            if self.unwrap:
                M1 = np.squeeze(np.unwrap(np.angle(np.fft.rfft(self.HRIRs[idx_pos, ch, :], axis=-1))))
                ylabel = 'Phase (deg)'
            else:
                M1 = np.squeeze(np.angle(np.fft.rfft(self.HRIRs[idx_pos, ch, :], axis=-1), deg=True))
                ylabel = 'Phase (rad)'

            plt.semilogx(self.freqVec, M1, label=self.ear_label[ch])
            plt.xlim([20, 20000])
            plt.xlabel('Frequency (Hz)')
            plt.ylabel(ylabel)
            plt.title(self.title)
        plt.legend()
        plt.show()
