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
#                           File: SOFASonix.py
#                           Project: SOFASonix
#                           Author: I.Laghidze
#                           License: BSD 3
#
# =============================================================================

import netCDF4
import numpy as np
import json
import sqlite3
import pandas as pd
import datetime
import os
from .SOFASonixField import SOFASonixField
from .SOFASonixError import SOFAError, SOFAFieldError


class SOFASonix(object):
    APIName = "SOFASonix"
    APIVersion = "1.0.6"
    DBFile = "ss_db.db"

    def __init__(self, conv,
                 sofaConventionsVersion=False,
                 version=False,
                 load=False,
                 **dims):
        # Create DB Path
        try:
            cwdpath = os.path.dirname(os.path.realpath(__file__))
        except NameError:
            cwdpath = os.path.dirname(os.path.realpath('__file__'))
        finally:
            self.dbpath = "{}/{}".format(cwdpath, SOFASonix.DBFile)

        # Return convention data if valid params supplied.
        self.convention = self._getConvention(conv, sofaConventionsVersion,
                                              version)
        self.modified = False  # Check whether convention has been modified

        # Get dimensions
        self.dims = json.loads(self.convention.pop("dimensions"))

        # Override dimensions if provided
        [self.setDim(dim.upper(), dims[dim]) for dim in dims]

        # Get convention parameters
        self.params = self._getParams(self.convention["id"])

        # Assign application information
        self.getParam("GLOBAL:APIName",
                      True).value = SOFASonix.APIName
        self.getParam("GLOBAL:APIVersion",
                      True).value = SOFASonix.APIVersion

        # Check if creating new SOFA file or loading an existing one
        if(load is False):
            # Attempt to automatically fill date fields if they exist
            try:
                # Date timestamps
                self.getParam("GLOBAL:DateCreated", True).value = self._time()
                # Date modified - Updated on SAVE
                self.getParam("GLOBAL:DateModified", True).value = self._time()
            except SOFAFieldError:
                pass

    def __setattr__(self, name, value):
        # Quick set dimensions if supplied.
        if (name[0] == "_"):
            self.setDim(name.strip("_"), value)
        else:
            # Quick set parameters if supplied.
            params = {i.getShorthandName().lower(): i
                      for i in self.flatten().values()}
            nameTrim = name.lower()

            if(hasattr(self, "params") and nameTrim in params):
                param = params[nameTrim]
                # Perform shorthand removal if value is None
                if(value is None):
                    self.deleteParam(param.name)
                else:
                    self.setParam(param.name, value)
            # Otherwise assign normally
            else:
                super(SOFASonix, self).__setattr__(name, value)

    def __getattr__(self, name):
        error = ("'{}' object has no attribute '{}'"
                 ).format(self.__class__.__name__, name)
        # Retrieve dimensiojs if exists
        if(name[0] == "_" and "dims" in self.__dict__):
            try:
                return self.getDim(name.strip("_"))
            except Exception:
                pass
        # Retrieve parameter if exists.
        elif("params" in self.__dict__):
            params = [i.replace(":", "_").replace(".",
                      "_").lower() for i in self.flatten()]
            nameTrim = name.lower()
            if(nameTrim in params):
                return self.getParam(list(self.flatten().keys())
                                     [params.index(nameTrim)])
        raise AttributeError(error)

    def _time(self):
        return datetime.datetime.now().replace(
            microsecond=0).isoformat().replace("T", " ")

    def _getData(self, query):
        try:
            db = sqlite3.connect(self.dbpath)
            cursor = db.cursor()
            cursor.execute(query)
            data = cursor.fetchall()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
        return data

    def _updateStrings(self):
        # Get all string parameter values
        strings = {k: i for k, i in self.flatten().items() if
                   (i.isType("string")
                   and not i.isEmpty())}
        stringSizes = [len(i.value) for i in strings.items()]

        # Get the largest string value and update dimension S
        if(len(stringSizes)):
            self.setDim("S", max(stringSizes)[-1])

        # Pad all string arrays
        for k in strings:
            amountToPad = self.getDim("S") - strings[k].value.shape[-1]
            if(amountToPad > 0):
                # Pad the appropriate amount of null characters to each string
                padamount = np.zeros((len(strings[k].shape), 2),
                                     dtype=np.int64)
                padamount[-1][-1] = amountToPad
                self.getParam(k, True).paddedValue = np.pad(strings[k].value,
                                                            amountToPad,
                                                            'constant')

    def _getConvention(self, conv, sofaConventionsVersion,
                       version):
        conventionData = self._getData("""SELECT convention_names.name as name,
                                                 conventions.id,
                                                 version,
                                                 spec_version,
                                                 standard,
                                                 dimensions,
                                                 data_group.name

                                                 FROM conventions

                                                 INNER JOIN data_group
                                                 on conventions.datagroup=
                                                 data_group.id
                                                 INNER JOIN convention_names
                                                 on conventions.convention=
                                                 convention_names.id

                                                 WHERE
                                                 lower(convention_names.name)
                                                 ='{}'
                            """.format(conv.lower()))

        # If supplied convention is in the database, check versions.
        if(conventionData):
            conventionName = conventionData[0][0]
            if(sofaConventionsVersion and version):
                try:
                    convention = conventionData[np.argwhere(
                            np.array([i[2] + i[3] for i in conventionData])
                            == sofaConventionsVersion + version)[0][0]]
                except Exception:
                    raise SOFAError(("Incompatible SOFAConventionsVersion ({})"
                                     " and spec version ({}) supplied. The "
                                     "following pairs are available for "
                                     "'{}':\n\n{}"
                                     ).format(sofaConventionsVersion,
                                              version,
                                              conventionName,
                                              "\n".join([("- Version: {}"
                                                          ", Spec Version: "
                                                          "{}").format(i[2],
                                                                       i[3])
                                                         for i in
                                                         conventionData])))
            elif(sofaConventionsVersion):
                try:
                    # Retrieve row indices with the supplied convention version
                    versionIndices = np.argwhere(np.array([i[2] for i in
                                                           conventionData])
                                                 == sofaConventionsVersion
                                                 )[:, 0]

                    # Strip invalid convention entries
                    validConventionData = [conventionData[i] for i
                                           in versionIndices]

                    # Get the convention data with the latest specVersion
                    convention = validConventionData[
                            np.argmax([i[3] for i in validConventionData])]

                except Exception:
                    available = np.unique([i[2] for i
                                           in conventionData]).astype(str)
                    raise SOFAError("Invalid SOFAConventionsVersion ({}). The "
                                    "following SOFAConventionsVersion values "
                                    "are available for '{}':\n\n- {}".format(
                                            sofaConventionsVersion,
                                            conventionName,
                                            "\n- ".join(available)))

            elif(version):
                try:
                    # Retrieve row indices with the supplied convention version
                    specVersionIndices = np.argwhere(np.array([i[3] for i in
                                                               conventionData])
                                                     == version)[:, 0]

                    # Strip invalid convention entries
                    validConventionData = [conventionData[i] for i
                                           in specVersionIndices]

                    # Get the convention ID with the latest convention version
                    convention = validConventionData[
                            np.argmax([i[2] for i in validConventionData])]

                except Exception:
                    available = np.unique([i[3] for i
                                           in conventionData]).astype(str)
                    raise SOFAError("Invalid spec version ({}). The following"
                                    " spec versions are available for "
                                    "'{}':\n\n- {}".format(
                                            version,
                                            conventionName,
                                            "\n- ".join(available)))
            else:
                # Assign latest SOFA version and Convention Version
                convention = conventionData[np.argmax([i[2] + i[3]
                                            for i in conventionData])]

        # Otherwise raise a ValueError and display available conventions.
        else:
            conventions = [k[0] for k in
                           self._getData("SELECT name FROM convention_names")]
            raise SOFAError(("Convention '{}' not found in conventions. "
                             "Please supply one of the following "
                             "conventions:\n\n- {}"
                             ).format(conv, "\n- ".join(conventions)))
        keys = ["name", "id", "SOFAConventionsVersion", "spec_version",
                "standard",
                "dimensions", "data_group"]
        return dict(zip(keys, convention))

    def _getUnits(self):
        units = dict(self._getData("""SELECT name, aliases FROM units"""))

        # Unserialize unit lists and add name
        for key, unitSet in units.items():
            units[key] = json.loads(unitSet)
            units[key].append(key)
        return units

    def _getParams(self, convention_id):
        parameters = self._getData("""SELECT field.name,
                                             value,
                                             ro,
                                             required,
                                             dimensions,
                                             description,
                                             parameter_type.name,
                                             parameter_class.name,
                                             properties
                                             FROM field
                                             INNER JOIN parameter_type
                                             on field.type = parameter_type.id
                                             INNER JOIN parameter_class
                                             on field.field_class
                                             = parameter_class.id
                                             WHERE convention={}
                                             """.format(int(convention_id)))

        units = self._getUnits()

        parsedParams = {}
        paramKeys = ["name", "value", "ro", "required", "dimensions",
                     "description", "type", "class", "properties"]
        for i in parameters:
            pi = dict(zip(paramKeys, i))
            pc = pi.pop("class")

            # Add parameter class as dictionary category
            if(pc not in parsedParams):
                parsedParams[pc] = {}

            # Unserialize data where necessary
            if(pi["type"] in ["double", "string"]):
                pi["value"] = np.array(json.loads(pi["value"])) \
                    if pi["value"] else np.array([])

            pi["dimensions"] = json.loads(pi["dimensions"])
            properties = json.loads(pi.pop("properties"))

            # Create a SOFASonixField object
            name = pi.pop("name")
            fieldParams = {}
            fieldParams.update(pi)
            fieldParams.update(properties)
            parsedParams[pc][name] = SOFASonixField(self, name, pc, units,
                                                    fieldParams)

        return parsedParams

    def attributes(self):
        for key, parameter in self.flatten().items():
            if (not parameter.isReadOnly() and
                    parameter.isType("attribute") and
                    not parameter.isTimestamp()):
                value = parameter.value
                text = "Parameter: '{}' | Required: {}\n".format(
                        key, "Yes" if parameter.isRequired() else "No")
                if (value):
                    text += ("Current value (leave "
                             "blank to preserve): \n{}\n").format(value)
                paramInput = input(text)
                if(paramInput == "" and value):
                    continue
                else:
                    self.setParam(key, str(paramInput))

    def flatten(self):
        flat = {}
        if(hasattr(self, "params")):
            {flat.update(category) for category in self.params.values()}
        return flat

    @staticmethod
    def load(file):
        raw = netCDF4.Dataset(file, "r", "NETCDF4")
        # Try to find a convention
        try:
            convention = raw.SOFAConventions
            version = float(raw.SOFAConventionsVersion)
            specversion = float(raw.Version)
        except Exception:
            raise SOFAError("Invalid SOFA file. No convention specified.")

        # Create a convention file.
        sofa = SOFASonix(convention, version, specversion, load=True)

        # Set dimensions if applicable
        for dim in raw.dimensions:
            if(dim in sofa.dims.keys()):
                sofa.setDim(dim, len(raw.dimensions[dim]), force=True)

        # Populate with datasets and attributes - single dimension (sufficient)
        for key in raw.variables:
            # Empty check
            if(raw[key].shape is not None):
                dat = np.array(raw[key][:].tolist())
                sofa.setParam(key, dat, force=True)
            # Check for attributes
            for attr in raw[key].ncattrs():
                attribute = getattr(raw[key], attr)
                if(attribute):
                    paramName = "{}:{}".format(key, attr)
                    try:
                        sofa.setParam(paramName,
                                      attribute,
                                      force=True)
                    except Exception as e:
                        raise Exception(e)

        # Match dimension strings for unclassed params
        if("__unclassed" in sofa.params):
            for param in sofa.params["__unclassed"].values():
                param._matchDims()

        # Now set global attributes
        for attr in raw.ncattrs():
            # Empty check
            attribute = getattr(raw, attr)
            if(attribute):
                try:
                    sofa.setParam("GLOBAL:{}".format(attr),
                                  attribute,
                                  force=True)
                except Exception as e:
                    raise Exception(e)

        # If modified (foreign parameters), add modified to convention name
        if(sofa.modified):
            sofa.getParam("GLOBAL:SOFAConventions").value += " (modified)"

        # Close h5py file and return SOFASonix object
        raw.close()
        return sofa

    def getDim(self, dim):
        dim = dim.upper()
        if(dim in self.dims):
            return self.dims[dim]["value"]
        else:
            raise SOFAError("Dimension '{}' does not exist")

    def setDim(self, dim, value, force=False):
        dim = dim.upper()
        if(dim in self.dims):
            if (self.dims[dim]["ro"] and force is False):
                raise SOFAError("Dimension '{}' is read-only.".format(dim))
            else:
                error = ("Invalid dimensions for '{}'. Please"
                         " supply a positive integer").format(dim)
                try:
                    numeric = int(value)
                    if(numeric < 0):
                        raise SOFAError(error)
                    self.dims[dim]["value"] = numeric
                except Exception:
                    raise SOFAError(error)
        else:
            raise SOFAError("Dimension '{}' doesn't exist".format(dim))

    def getParam(self, key, obj=False):
        params = self.flatten()
        if key in params:
            if(obj):
                return params[key]
            else:
                return params[key].value
        else:
            raise SOFAFieldError("Field '{}' was not found".format(key))

    def setParam(self, key, value, force=False):
        params = self.flatten()
        if key in params:
            param = params[key]
            if(not param.isReadOnly() or force):
                # Attribute
                if(param.isType("attribute")):
                    param.value = str(value)
                # Dealing with STRING (placeholder)
                elif(param.isType("string")):
                    if(type(value) in [list, np.ndarray]):
                        length = len(value) if type(value) == list\
                            else value.size
                        if(length):
                            if(type(value) == list):
                                # Check if all elements are strings
                                allStrings = all([type(v) == str
                                                  for v in value])
                                if(not allStrings):
                                    raise SOFAFieldError(("Submitted list data"
                                                          " for '{}' must only"
                                                          " contain strings"
                                                          ).format(key))

                                # Create a numpy array with nullspaces
                                maxS = max(map(len, value))
                                # Create an array to store the values
                                stringArray = np.zeros((len(value), maxS),
                                                       dtype=np.string_)
                                # Append values
                                for i in value:
                                    iv = list(i)
                                    stringArray[:len(iv)] = iv

                                # Store string array
                                param.value = stringArray
                                param.paddedValue = stringArray

                            # Otherwise assume a character array
                            else:
                                if(value.dtype != "S1"):
                                    raise SOFAFieldError(("Array submitted for"
                                                          " parameter '{}'"
                                                          " must be a "
                                                          "character array of "
                                                          "dtype 'S1'"
                                                          ).format(key))
                                param.value = value
                                param.paddedValue = stringArray

                        else:
                            raise SOFAFieldError(("Empty array or list "
                                                  "submitted for parameter "
                                                  "'{}'").format(key))
                        # Update dimension S and pad all character arrays
                        self._updateStrings()
                    else:
                        raise SOFAFieldError(("Parameter '{}' of type string "
                                              "must either have a list of "
                                              "strings or a numpy character"
                                              "array.").format(key))
                # Double
                elif(param.isType("double")):
                    if(type(value) in [list, np.ndarray]):
                        value = np.array(value)
                        # Check if array is numeric
                        if(np.issubdtype(value.dtype, np.number)):
                            # Check number of dimensions
                            param.checkDimensionsLength(value)

                            # Add value if length has passed
                            param.value = value

                            # Check if parameter defines dimensions
                            for i, dim in enumerate(param.dimensions[0]):
                                # If lowercase, define dim (assumption [0])
                                if(dim.lower() == dim):
                                    print(("Setting dimension '{}' from "
                                           "parameter '{}'"
                                           ).format(dim, param.name))
                                    # Bypass any exceptions if dim is RO
                                    try:
                                        self.setDim(dim, value.shape[i],
                                                    force=force)
                                    except Exception:
                                        pass
                        else:
                            raise SOFAFieldError(("Parameter '{}' of type "
                                                  "'double' cannot contain "
                                                  "non-numeric list data."
                                                  ).format(key))
                    else:
                        raise SOFAFieldError(("Parameter '{}' is of type "
                                              "'double'. Only python lists "
                                              "and numpy arrays are valid "
                                              "inputs.").format(key))
                else:
                    raise SOFAFieldError("Invalid parameter type for '{}'"
                                         .format(key))
            else:
                raise SOFAFieldError(("Cannot edit parameter '{}'. "
                                      "Read only.").format(key))
        # Force insertion of foreign parameter -- use for load ONLY
        elif force:
            print("Inserting foreign parameter: '{}'".format(key))
            # Python2 fix
            try:
                basetype = unicode
            except NameError:
                basetype = str

            # Find out parameter type
            if(type(value) in [str, basetype, bytes]):
                inputType = "attribute"
                inputDims = 0
            else:
                # Disable dims check unless _matchDims() is called on param
                inputDims = 0
                try:
                    value = np.array(value)
                except Exception:
                    raise SOFAFieldError("""Invalid parameter input. Please "
                                         "insert a valid string, list or "
                                         "numpy array.""")
                # Check if character array or numerical
                if(np.issubdtype(value.dtype, np.string_)):
                    inputType = "string"
                else:
                    inputType = "double"
            # If an unclassed variable is introduced for the first time
            if("__unclassed" not in self.params):
                self.params["__unclassed"] = {}
                # Also append (modified) to convention name (switched off)
                self.modified = False
            params = {"type": inputType,
                      "value": value,
                      "properties": {"requires": 0,
                                     "value_restrictions": 0},
                      "required": 0,
                      "dimensions": inputDims,
                      "ro": 0}
            properties = params.pop("properties")
            fieldParams = {}
            fieldParams.update(params)
            fieldParams.update(properties)
            self.params["__unclassed"][key] = SOFASonixField(self, key,
                                                             "__unclassed",
                                                             self._getUnits(),
                                                             fieldParams)

        else:
            raise SOFAError("Invalid parameter supplied for convention: '{}'"
                            .format(self.convention["name"]))

    def deleteParam(self, param):
        deleteList = []
        # Search for parameters to remove
        for category in self.params.keys():
            for field in self.params[category].values():
                # Remove parameter
                if(field.name == param):
                    if(field.isRequired()):
                        raise SOFAFieldError("Parameter '{}' is a required"
                                             " parameter and cannot be "
                                             "removed!".format(field.name))
                    else:
                        deleteList.append([category, field.name])
                        print("Removed '{}'".format(field.name))
                # Remove any associated attributes if applicable
                if(field.name.startswith("{}:".format(param))):
                    if(field.isRequired()):
                        print("WARNING: Associated attribute '{}' is a "
                              "required parameter and cannot "
                              "be automatically removed!".format(field.name))
                    else:
                        print("Removed associated attribute '{}'"
                              .format(field.name))
                        deleteList.append([category, field.name])
        if(len(deleteList)):
            for pair in deleteList:
                del self.params[pair[0]][pair[1]]
        else:
            print("No parameter '{}' found to delete.".format(param))

    def validate(self, category=False):
        params = self.params[category].items() if category else\
            self.flatten().items()
        for key, param in params:
            # Run required check]
            param.checkRequiredStatus()

            if(not param.isEmpty()):
                param.checkDimensions()
                param.checkRequirements()
                param.checkValueConstraints()

    def export(self, filename):
        # Perform field-by-field validation
        for category in self.params:
            self.validate(category)

        # Set new DateModified value if it exists
        try:
            self.getParam("GLOBAL:DateModified", True).value = self._time()
        except SOFAFieldError:
            pass

        # Create file and attempt saving.
        file = netCDF4.Dataset("{}.sofa".format(filename), "w",
                               format="NETCDF4")

        try:
            # Create dimensions
            for dim in self.dims.keys():
                file.createDimension(dim, self.dims[dim]["value"])

            attributes = self.flatten()
            # Extract doubles.
            doubles = {k: attributes.pop(k) for k in list(attributes.keys())
                       if attributes[k].isType("double")}

            # Extract strings
            strings = {k: attributes.pop(k) for k in list(attributes.keys())
                       if attributes[k].isType("string")}

            # Create all doubles first.
            for key, element in doubles.items():
                if(not element.isEmpty()):
                    var = file.createVariable(key, "f8",
                                              element.getDimensions())
                    var[:] = element.value

            # Create strings
            for key, element in strings.items():
                if(not element.isEmpty()):
                    var = file.createVariable(key, "S1",
                                              element.getDimensions())
                    var[:] = element.paddedValue

            # Create attributes
            for key, element in attributes.items():
                variable, attrname = key.split(":") if (":" in key)\
                    else ["global", key]
                # For global attributes, create in root
                if(key in self.params["global"] or
                   variable.lower() == "global"):
                    setattr(file, attrname, element.value)
                # Otherwise create the attribute within the variable
                else:
                    setattr(file[variable], attrname, element.value)
            file.close()
        except Exception:
            # Close file if errors encountered and re-raise exception.
            file.close()
            raise

    def view(self):
        cols = ["Shorthand", "Type", "Value", "RO", "M", "Dims"]
        rows = []
        params = self.flatten()
        for i in params:
            pi = params[i]
            value = "{} Array".format(pi.value.shape) if \
                (pi.isType("double") or pi.isType("string")) else pi.value
            rows.append([".{}".format(pi.getShorthandName()),
                         pi.type[0].upper(),
                         value,
                         pi.isReadOnly(),
                         pi.isRequired(),
                         str(pi.dimensions) if pi.dimensions else "_"])
        pd.set_option('display.max_colwidth', 40)
        pd.set_option('display.expand_frame_repr', False)

        df = pd.DataFrame(rows, columns=cols)
        print(df)
