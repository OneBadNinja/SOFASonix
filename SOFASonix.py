import h5py
import numpy as np
import json
import sqlite3
import pandas as pd
import datetime
import os


class SOFASonix:
    APIName = "SOFASonix"
    APIVersion = "1.0"

    def __init__(self, conv, version=False, specVersion=False, load=False,
                 **dims):
        # Return convention data if valid params supplied.
        self.convention = self._getConvention(conv, version, specVersion)
        self.modified = False  # Check whether convention has been modified

        # Get dimensions
        self.dims = json.loads(self.convention.pop("dimensions"))

        # Override dimensions if provided
        [self.setDim(dim.upper(), dims[dim]) for dim in dims]

        # Get convention parameters
        self.params = self._getParams(self.convention["id"])

        # Assign application information
        self.params["global"]["APIName"].value = self.APIName
        self.params["global"]["APIVersion"].value = self.APIVersion

        # Check if creating new SOFA file or loading an existing one
        if(load is False):
            # Date timestamps
            self.params["global"]["DateCreated"].value = self._time()
            # Date modified - Updated on SAVE
            self.params["global"]["DateModified"].value = self._time()

    def __setattr__(self, name, value):
        # Quick set dimensions if supplied.
        if (name[0] == "_"):
            self.setDim(name.strip("_"), value)
        else:
            # Quick set parameters if supplied.
            params = [i.replace(":", "_").replace(".", "_").lower()
                      for i in self.flatten()]
            nameTrim = name.lower()

            if(hasattr(self, "params") and nameTrim in params):
                self.setParam(list(self.flatten().keys())
                              [params.index(nameTrim)], value)
            # Otherwise assign normally
            else:
                super().__setattr__(name, value)

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

    def _getData(self, query, dbfile="ss_db.db"):
        try:
            path = os.path.dirname(os.path.abspath("__file__"))
            db = sqlite3.connect("{}/{}".format(path, dbfile))
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

    def _getConvention(self, conv, version, specVersion):
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
            if(version and specVersion):
                try:
                    convention = conventionData[np.argwhere(
                            np.array([i[2] + i[3] for i in conventionData])
                            == version + specVersion)[0][0]]
                except Exception:
                    raise SOFAError(("Incompatible convention version ({}) "
                                     "and spec version ({}) supplied. The "
                                     "following pairs are available for "
                                     "'{}':\n\n{}"
                                     ).format(version,
                                              specVersion,
                                              conventionName,
                                              "\n".join([("- Version: {}"
                                                          ", Spec Version: "
                                                          "{}").format(i[2],
                                                                       i[3])
                                                         for i in
                                                         conventionData])))
            elif(version):
                try:
                    # Retrieve row indices with the supplied convention version
                    versionIndices = np.argwhere(np.array([i[2] for i in
                                                           conventionData])
                                                 == version)[:, 0]

                    # Strip invalid convention entries
                    validConventionData = [conventionData[i] for i
                                           in versionIndices]

                    # Get the convention data with the latest specVersion
                    convention = validConventionData[
                            np.argmax([i[3] for i in validConventionData])]

                except Exception:
                    available = np.unique([i[2] for i
                                           in conventionData]).astype(str)
                    raise SOFAError("Invalid convention version ({}). The "
                                    "following convention versions are "
                                    "available for '{}':\n\n- {}".format(
                                            version,
                                            conventionName,
                                            "\n- ".join(available)))

            elif(specVersion):
                try:
                    # Retrieve row indices with the supplied convention version
                    specVersionIndices = np.argwhere(np.array([i[3] for i in
                                                               conventionData])
                                                     == specVersion)[:, 0]

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
                                            specVersion,
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
        keys = ["name", "id", "version", "spec_version", "standard",
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

            # Remove global keyword from name if present
            if(pc == "global"):
                pi["name"] = pi["name"].replace("GLOBAL:", "")

            pi["dimensions"] = json.loads(pi["dimensions"])
            properties = json.loads(pi.pop("properties"))

            # Create a SOFASonixField object
            name = pi.pop("name")
            parsedParams[pc][name] = SOFASonixField(self, name, pc, units,
                                                    {**pi, **properties})

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

    def load(file):
        raw = h5py.File(file)
        # Try to find a convention
        try:
            convention = raw.attrs["SOFAConventions"].decode('utf-8')
            version = float(raw.attrs["SOFAConventionsVersion"].decode(
                    "utf-8"))
            specversion = float(raw.attrs["Version"].decode("utf-8"))
        except Exception:
            raise SOFAError("Invalid SOFA file. No convention specified.")

        # Create a convention file.
        sofa = SOFASonix(convention, version, specversion, load=True)

        # Populate with datasets and attributes - single dimension (sufficient)
        for key in raw.keys():
            # If datatype IR and dims are provided as doubles, set them.
            if (key in sofa.dims.keys() and
                    sofa.convention["data_group"] == "IR"):
                # Need to solve dimensions constraints
                sofa.setDim(key, raw[key][:].shape[0], force=True)
            # Otherwise set each double parameter.
            else:
                # Empty check
                if(raw[key].shape is not None):
                    sofa.setParam(key, raw[key][:], force=True)

        # Now set attributes
        for attr in raw.attrs.keys():
            # Empty check
            if(raw.attrs[attr].shape is not None):
                sofa.setParam(attr, raw.attrs[attr].decode('utf-8'),
                              force=True)

        # If modified (foreign parameters), add modified to convention name
        if(sofa.modified):
            sofa.params["global"]["SOFAConventions"]["value"] += " (modified)"

        # Close h5py file and return SimpleSOFA object
        raw.close()
        return sofa

    def getDim(self, dim):
        if(dim in self.dims):
            return self.dims[dim]["value"]
        else:
            raise SOFAError("Dimension '{}' does not exist")

    def setDim(self, dim, value, force=False):
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
                            param.value = value
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
        # Force insertion of foreign parameter
        elif force:
            print("Inserting foreign parameter: '{}'".format(key))
            # Find out parameter type
            if(type(value) == str):
                inputType = "attribute"
                inputDims = 0
            else:
                inputType = "double"
                try:
                    value = np.array(value)
                    inputDims = value.shape
                except Exception:
                    raise SOFAFieldError("""Invalid parameter input. Please "
                                         "insert a valid string, list or "
                                         "numpy array""")
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
            self.params["__unclassed"][key] = SOFASonixField(self, key,
                                                             "__unclassed",
                                                             self._getUnits(),
                                                             {**params,
                                                              **properties})

        else:
            raise SOFAError("Invalid parameter supplied for convention: '{}'"
                            .format(self.convention["name"]))

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

    def export(self, filename, dims=True):
        # Perform field-by-field validation
        for category in self.params:
            self.validate(category)

        # Set new DateModified value
        self.params["global"]["DateModified"].value = self._time()

        # Create file and attempt saving.
        file = h5py.File("{}.sofa".format(filename), "w")

        try:
            attributes = self.flatten()
            # Extract doubles.
            doubles = {k: attributes.pop(k) for k in list(attributes.keys())
                       if attributes[k].isType("double")}
            # Extract strings
            strings = {k: attributes.pop(k) for k in list(attributes.keys())
                       if attributes[k].isType("string")}

            dsets = {}

            # Create all doubles first.
            for key, element in doubles.items():
                value = h5py.Empty("float64") if element.isEmpty() \
                    else element.value
                dsets[key] = file.create_dataset(key, data=value)

            # Create strings
            for key, element in strings.items():
                value = h5py.Empty("S1") if element.isEmpty() else\
                    element.z
                dsets[key] = file.create_dataset(key, data=value, dtype="S1")

            # Create parameters for dimensions
            if(dims and self.convention["data_group"] == "IR"):
                for k, i in self.dims.items():
                    file.create_dataset(k, data=np.zeros(i["value"]))

            # Create attributes
            for key, element in attributes.items():
                variable, attrname = key.split(":") if ":" in key \
                    else ("", key)

                value = np.string_(element.value)

                # For global attributes, create in root
                if(variable == ""):
                    file.attrs[attrname] = value
                # Otherwise create the attribute within the variable
                else:
                    dsets[variable].attrs[attrname] = value
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
            rows.append([".{}".format(i.replace(":", "_").replace(".", "_")),
                         pi.type[0].upper(),
                         value,
                         pi.isReadOnly(),
                         pi.isRequired(),
                         str(pi.dimensions) if pi.dimensions else "_"])
        pd.set_option('display.max_colwidth', 40)
        pd.set_option('display.expand_frame_repr', False)

        df = pd.DataFrame(rows, columns=cols)
        print(df)


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

    def checkDimensions(self):
        if(self.isType("double") or self.isType("string")):
            match = False
            for dSet in self.dimensions:
                values = [self.parent.getDim(dim) for dim in dSet]
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


class SOFAError(Exception):
    pass


class SOFAFieldError(Exception):
    pass
