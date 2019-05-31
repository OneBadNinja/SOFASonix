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
#                           File: SOFASonixField.py
#                           Project: SOFASonix
#                           Author: I.Laghidze
#                           License: BSD 3
#
# =============================================================================

from .SOFASonixError import SOFAFieldError, SOFAError
import numpy as np


class SOFASonixField:
    def __init__(self, parent, name, pclass, units, params):
        self.name = name
        self.parameter_class = pclass
        self.parent = parent
        self.units = units
        # Set parameters
        for key, value in params.items():
            setattr(self, key, value)
        # Create parameter for string data type
        # to store padded null valued arrays
        if(self.isType("string")):
            self.paddedValue = value

    def isType(self, type_str):
        return self.type.lower() == str(type_str).lower()

    def inClass(self, class_str):
        return self.parameter_class.lower() == str(class_str).lower()

    def isReadOnly(self):
        return True if self.ro else False

    def isRequired(self):
        return True if self.required else False

    def isTimestamp(self):
        return True if self.timestamp else False

    def isEmpty(self):
        size = len(self.value) if self.isType("attribute") or\
            self.isType("string") else self.value.size
        return True if size == 0 else False

    def checkRequiredStatus(self):
        if(self.isEmpty() and self.isRequired()):
            raise SOFAFieldError(("'{}' is a required parameter."
                                  ).format(self.name))

    def checkRequirements(self):
        if(self.requires):
            if(self.requires["type"] == "regular"):
                # Check if all required fields have been filled in
                for field in self.requires["fields"]:
                    if(self.parent.getParam(field, True).isEmpty()):
                        raise SOFAFieldError(("'{}' requires '{}' to be "
                                              "filled in"
                                              ).format(self.name, field))

            elif(self.requires["type"] == "conditional"):
                for value, fields in self.requires["fields"].items():
                    if(self.value.lower() == value.lower()):
                        for field in fields:
                            if(self.parent.getParam(field, True).isEmpty()):
                                raise SOFAFieldError(("'{}' requires '{}' to "
                                                      "be filled in if its "
                                                      "value is {}"
                                                      ).format(self.name,
                                                               field,
                                                               self.value))
            else:
                raise SOFAFieldError(("Invalid requirements type for "
                                      "'{}'").format(self.name))

    def _matchUnitsHelper(self, values, restrictions):
        passed = False
        for valueSet in restrictions:
            if(len(valueSet) == len(values)):
                zipValues = zip(values, valueSet)
                # Assume a positive match
                match = all([v in self.units[c]
                             for v, c in zipValues])
                if(match):
                    # Validation has passed
                    passed = True
                    break
        return passed

    def _matchDims(self):
        if((self.isType("double") or self.isType("string"))
                and self.inClass("__unclassed") and not self.dimensions):
            # Try to match dimensions
            dimensions = ""
            for num in self.value.shape:
                for dim, dimParams in self.parent.dims.items():
                    if(dimParams["value"] == num):
                        dimensions += dim
                        # Only one dimension may correspond to each shape value
                        break
            if(len(dimensions) != len(self.value.shape)):
                raise SOFAError("Unable to import correct dimensions "
                                "for parameter {}".format(self.name))
            else:
                self.dimensions = [dimensions]

    def checkValueConstraints(self):
        if(self.value_restrictions):
            if(self.value_restrictions["type"] == "regular"):
                if(self.value.lower() not in
                   self.value_restrictions["values"]):
                    raise SOFAFieldError(("'{}' accepts only the following "
                                          "values:{}\nYou have: '{}'"
                                          ).format(self.name,
                                                   "\n- ".join(
                                                           self.
                                                           value_restrictions
                                                           ["values"]),
                                                   self.value))

            elif(self.value_restrictions["type"] == "units"):
                # Obtain restricted valueSets
                restrictions = self.value_restrictions["values"]
                # Split units by commas
                values = [i.strip() for i in self.value.split(",")]
                lengths = [len(i) for i in restrictions]

                # Valid units allowed - generate error message if needed
                validUnitSets = []
                for valueSet in restrictions:
                    validUnitSet = [self.units[v][0] for v in valueSet]
                    validUnitSets.append(", ".join(validUnitSet))
                errormsg = ("Units for '{}' can only be one of the following:"
                            "{}").format(self.name, "\n- ".join(validUnitSets))

                # Check whether the correct # of units have been supplied
                if(len(values) not in lengths):
                    raise SOFAFieldError(errormsg)
                else:
                    # Check if units are matched
                    passed = self._matchUnitsHelper(values, restrictions)
                    if(not passed):
                        raise SOFAFieldError(errormsg)

            elif(self.value_restrictions["type"] == "conditional_units"):
                # Obtain the parameter to check for the condition
                externalParam = self.parent.getParam(self.value_restrictions
                                                     ["conditional_field"],
                                                     True)
                try:
                    # See if the parameter value has units to be matched
                    idx = [i.lower() for i in self.value_restrictions["values"]
                           ].index(externalParam.value.lower())
                    key = list(self.value_restrictions["values"])[idx]

                    # Obtain restricted value sets
                    restrictions = self.value_restrictions["values"][key]

                    # Split units by commas
                    values = [i.strip() for i in self.value.split(",")]
                    lengths = [len(i) for i in restrictions]

                    # Valid units allowed - generate error message if needed
                    validUnitSets = []
                    for valueSet in restrictions:
                        validUnitSet = [self.units[v][0] for v in valueSet]
                        validUnitSets.append(", ".join(validUnitSet))
                    errormsg = ("Units for '{}' can only be one of the "
                                "following if '{}' is supplied as a value for"
                                "'{}':{}"
                                ).format(self.name,
                                         "\n- ".join(validUnitSets),
                                         key,
                                         externalParam.name)

                    # Check whether the correct # of units have been supplied
                    if(len(values) not in lengths):
                        raise SOFAFieldError(errormsg)
                    else:
                        # Check if units are matched
                        passed = self._matchUnitsHelper(values, restrictions)
                        if(not passed):
                            raise SOFAFieldError(errormsg)

                # If value of field is not in conditional_units, ignore
                except Exception:
                    pass

            else:
                raise SOFAFieldError(("Invalid value_restrictions type for "
                                      "'{}'").format(self.name))

    def checkDimensionsLength(self, prospective=False):
        value = prospective if(type(prospective) == np.ndarray
                               and prospective.size) else self.value
        shapeLength = len(value.shape)
        # Get dimension length
        dimensionsLength = len(self.dimensions[0])

        if(shapeLength != dimensionsLength):
            raise SOFAFieldError(("'{}' is expecting a {}-dimensional input "
                                  "({})\nYou supplied: {} dimensions"
                                  ).format(self.name, dimensionsLength,
                                           self.dimensions, shapeLength))

    def checkDimensions(self):
        if(self.isType("double") or self.isType("string")):
            # Check if not force-input without dimensions matching
            if(self.dimensions):
                # Check dimensions length check
                self.checkDimensionsLength()

                # Perform dimensions check
                match = False
                for dSet in self.dimensions:
                    values = [self.parent.getDim(dim) for
                              dim in dSet]
                    if(list(self.value.shape) == values):
                        match = True
                        break
                # If dimensions are not matched, raise exception
                if(not match):
                    raise SOFAFieldError(("Incorrect dimensions for '{}'\n"
                                          "Required: {}\n"
                                          "Current: {}"
                                          ).format(self.name, self.dimensions,
                                                   list(self.value.shape)))

    def getDimensions(self):
        for dimlist in self.dimensions:
            dims = [self.parent.getDim(d_i) for d_i in dimlist]
            if(dims == list(self.value.shape)):
                return [i.upper() for i in dimlist]
        raise ValueError("Cannot get dimensions")

    def getShorthandName(self):
        return self.name.replace(":", "_").replace(".", "_")
