# ExportSQLServer: SQL Server (Microsoft) export pluging for MySQL Workbench
# Copyright (C) 2015 Keith Martin
# Based on the following work:
# ExportSQLite: SQLite export plugin for MySQL Workbench
# Copyright (C) 2009 Thomas Henlich
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# this function is called first by MySQL Workbench core to determine number of plugins in this module and basic plugin info
# see the comments in the function body and adjust the parameters as appropriate
#

# import the wb module, where various utilities for working with plugins are defined
from wb import *
import grt
import mforms
from mforms import Utilities, FileChooser
import re

# create a module information descriptor. The variable name must be ModuleInfo
ModuleInfo = DefineModule(name= "ExportSQLServer", author= "Keith Martin", version="2015.07.23")


# export a function from this module, declaring its return and parameter types and then
# tell WB that it is a plugin to be shown in the Catalog submenu of the Plugins menu and takes the 
# catalog of the currently loaded model as input

@ModuleInfo.plugin("wb.catalog.util.exportSQLServer", caption= "Export SQL Server CREATE script", input= [wbinputs.currentCatalog()], pluginMenu= "Catalog")
@ModuleInfo.export(grt.INT, grt.classes.db_Catalog)

# function to go through all schemata in the catalog and export in SQL Server Format
def exportSQLServer(catalog):

    haveFKeys = 0
    version = grt.root.wb.info.version #  V.getGlobal("/wb/info/version")
    versionNumber = "%d.%d.%d" % (version.majorNumber, version.minorNumber, version.releaseNumber)
    print versionNumber
    if validateForSQLServerExport(catalog) != 0:
    	return 1

    #-- we don't have requestFileSave in <= 5.1
    #    path = Workbench:requestFileSave("Save as", "SQL Files (*.sql)|*.sql")
    filechooser = FileChooser(mforms.SaveFile)
    filechooser.set_extensions("SQL Files (*.sql)|*.sql", "sql")
    filechooser.set_title("Save Microsoft SQL Server Create File")
    # fileChooser.set_directory(self.logfile_path)
    if filechooser.run_modal():
        path = filechooser.get_path()
    else:
        YesNoBox("Exiting", "Cancel Chosen")
        return 0

    with open(path, "w+") as file:
        #file = io.open(path, "w+")
        if (file == None):
            YesNoBox("Error", "Cannot open file %s" % (path))
            return 1
        #end
      
        #--  if (not path:find("\.sql$")) then
        #-- truncate db file
        #--    file:close()
        #--    file = io.popen("SQLServer3 -batch -bail " .. path, "w")
        #--  end
      
        info = grt.root.wb.doc.info
        file.write(infoFormat("Creator", "MySQL Workbench %s /ExportSQLServer plugin %s" % (versionNumber, ModuleInfo.version)))
        file.write(infoFormat("Author", info.author))
        file.write(infoFormat("Caption", info.caption))
        file.write(infoFormat("Project", info.project))
        file.write(infoFormat("Changed", info.dateChanged))
        file.write(infoFormat("Created", info.dateCreated))
        file.write(infoFormat("Description", info.description))

        #-- loop over all catalogs in schema, find main schema
        #-- main schema is first nonempty schema or nonempty schema named "main"
        iMain = -1
        i = 0
        for schema in catalog.schemata:
            if (len(schema.tables) > 0):
                if (iMain < 0):
                    iMain = i
                #end
                if (schema.name == "dbo"):  # dbo is SQL Server's main schema.
                    iMain = i
                    break
                #end
            #end
            i += 1
        #end

        if (iMain > -1):
            if (exportSchema(file, catalog.schemata[iMain], True) != 0):
                print "Error writing schema %s\n" % (catalog.schemata[iMain].name)
                return 1
            #end
        #end

        i = 0
        for schema in catalog.schemata:
            uniqueId = 1
            if (i != iMain):
                if (exportSchema(file, schema, False) != 0):
                    print "Error writing schema %s\n" % (catalog.schemata[i].name)
                    return 1
                #end
            #end
            i += 1
        #end

    print "Export to %s  finished.\n" % (path)
    return 0
#end

# Debug = True


# if debug, then print messages to show what's happening.
def showMessage(message):
    Debug = False
    if Debug:
        print message
#end

# Class to create a Yes No Box, and return True on Yes...
class YesNoBoxClass(mforms.Form):
    def __init__(self, Title, Message):
        mforms.Form.__init__(self, None, mforms.FormDialogFrame)
        self.set_title(Title)
        box = mforms.newBox(False)
        self.set_content(box)
        box.set_padding(12)
        box.set_spacing(12)
        label = mforms.newLabel(Message)
        box.add(label, False, True)
        self.cancelButton = mforms.newButton()
        self.cancelButton.set_text("No")
        box.add_end(self.cancelButton, False, True)
        self.okButton = mforms.newButton()
        self.okButton.set_text("Yes")
        box.add_end(self.okButton, False, True)
        
    def run(self):
        return self.run_modal(self.okButton, self.cancelButton)
#End Class

def YesNoBox(Title, Message):
    form = YesNoBoxClass(Title, Message)
    return form.run()


# check uniqueness of schema, table and index names
# return 0 on success
# otherwise return 1 (the export process should abort)
def validateForSQLServerExport(obj):
  # local id, i, j, errName, haveErrors, schema, tbl, column, index
  id = {}
  haveErrors = False
  # Loop through all the schemas.
  for schema in obj.schemata: #for i = 1, grtV.getn(obj.schemata) do
    showMessage(str.format("Processing Schema {0} in function {1}", schema.name, "validateForSQLServerExport"))
    #schema = obj.schemata[i]
    if (schema.name in id): # then
      haveErrors = True
      if (YesNoBox("Name conflict", "There is a duplicate schemas name [%s].\nPlease rename one of them.\nSearch for more such errors?" % (schema.name))):
        return 1
      #end
    else:
      id[schema.name] = schema.name

  # do not continue looking for errors on schema name error
  if (haveErrors):
    return 1

  # Check for duplicates in Table Names.
  for schema in obj.schemata: #   for i = 1, grtV.getn(obj.schemata) do
    #schema = obj.schemata[i]
    id = {}
    for tbl in schema.tables: # for j = 1, grtV.getn(schema.tables) do
      showMessage(str.format("Processing Table {0} in function {1}", tbl.name, "validateForSQLServerExport"))
      #tbl = schema.tables[j]
      if (tbl.name == ""):
        haveErrors = True
        if (YesNoBox("Name Conflict", "Table [%s] in schema [%s] has no name.\nPlease rename.\nSearch for more such errors?" % (tbl.name, schema.name))): # if (Workbench:confirm("Name conflict", "Table " .. j .. " in schema \"" .. schema.name .. "\" has no name. Please rename.\nSearch for more such errors?") == 0): #then
          return 1
        #end
      #end
      if (tbl.name in id): #if (id[tbl.name]): #then
        haveErrors = True
        if (YesNoBox("Name Conflict", "Table [%s] appears at least twice in schema [%s].\nPlease rename.\nSearch for more such errors?" % (tbl.name, schema.name))):#if (Workbench:confirm("Name conflict", "Tables " .. id[tbl.name] .. " and " .. j .. " in schema \"" .. schema.name .. "\" have the same name \"" .. tbl.name .. "\". Please rename one of them.\nSearch for more such errors?") == 0): #then
          return 1
        #end

      else:
        id[tbl.name] = tbl.name
      #end
    #end
  #end
  
  if (haveErrors):
    return 1
  #end

  # Check all the column names
  for schema in obj.schemata: # for i = 1, grtV.getn(obj.schemata) do
    #schema = obj.schemata[i]
    for tbl in schema.tables: # for j = 1, grtV.getn(schema.tables) do
      # tbl = schema.tables[j]
      id = {}
      for column in tbl.columns: # for k = 1, grtV.getn(tbl.columns) do
        showMessage(str.format("Processing Column {0} in function {1}", column.name, "validateForSQLServerExport"))
        # column = tbl.columns[k]
        if (column.name == ""): # then
          haveErrors = True
          if (YesNoBox("Name conflict", "Column [%s] in table [%s].[%s] has no name.\nPlease Rename.\n\nSearch for more such errors?" % (column.name, schema.name, tbl.name))): # if (Workbench:confirm("Name conflict", "Column " .. k .. " in table \"" .. schema.name .. "\".\"" .. tbl.name .. "\" has no name. Please rename.\nSearch for more such errors?") == 0): #then
            return 1
          #end
        #end
        if (column.name in id):#if (id[column.name]): #then
          haveErrors = True
          if (YesNoBox("Name conflict", "Column [%s] in table [%s].[%s] exists more than once.\nPlease rename one of them.\n\nSearch for more such errors?" % (column.name, schema.name, tbl.name))): #if (Workbench:confirm("Name conflict", "Columns " .. id[column.name] .. " and " .. k .. " in table \"" .. schema.name .. "\".\"" .. tbl.name .. "\" have the same name \"" .. column.name .. "\". Please rename one of them.\nSearch for more such errors?") == 0): #then
            return 1
          #end
        else:
          id[column.name] = column.name
        #end
      #end
      
      # now check indices (except primary/unique)
      id = {}
      for index in tbl.indices: # for k = 1, grtV.getn(tbl.indices) do
        showMessage(str.format("Processing Index {0} in function {1}", index.name, "validateForSQLServerExport"))
        #index = tbl.indices[k]
        if (index.indexType == "INDEX"):# then
          if (index.name == ""):# then
            haveErrors = True
            if (YesNoBox("Name conflict", "Index [%s] on table [%s].[%s] has no name.\nPlease Rename.\n\nSearch for more such errors?" % (index.name, schema.name, tbl.name))): # if (Workbench:confirm("Name conflict", "Index " .. k .. " in table \"" .. schema.name .. "\".\"" .. tbl.name .. "\" has no name. Please rename.\nSearch for more such errors?") == 0): #then
              return 1
            #end
          #end
          if (index.name in id):
            haveErrors = True
            if (YesNoBox("Name conflict", "Index [%s] on table [%s].[%s] has another of the same name.\nPlease rename one of them.\n\nSearch for more such errors?" % (index.name, schema.name, tbl.name))): # if (Workbench:confirm("Name conflict", "Indices " .. id[index.name] .. " and " .. k .. " in table \"" .. schema.name .. "\".\"" .. tbl.name .. "\" have the same name \"" .. index.name .. "\". Please rename one of them.\nSearch for more such errors?") == 0): #then
              return 1
            #end
          else:
            id[index.name] = index.name
          #end
        #end
      #end
    #end
  #end
  
  if (haveErrors):# then
    return 1
  #end

  return 0

# hack: if comment starts with "Defer..." we make it a deferred FK
# could use member 'deferability' (WB has it), but there is no GUI for it
def isDeferred(fKey):
  return (fKey.comment.strip()[:5].lower() == "defer")
#end

# function to export the table definition to a file
def exportTable(file, dbName, schema, tbl):
    #local primaryKey, pKColumn, colComment
    showMessage(str.format("Processing Schema {0} and Table {1} in function {2}", schema.name, tbl.name, "exportTable"))
    # cannot create empty tables
    if (len(tbl.columns) > 0):
        if (dbName > ""):
            file.write("\n\nCREATE TABLE %s.%s.%s(\n%s" % (quoteIdentifier(dbName), quoteIdentifier(schema.name), quoteIdentifier(tbl.name), sCommentFormat(tbl.comment)))
        else:
            file.write("\n\nCREATE TABLE %s.%s(\n%s" % (quoteIdentifier(schema.name), quoteIdentifier(tbl.name), sCommentFormat(tbl.comment)))
        #end

        foundPrimaryKey = False
        primaryKey = None
        #-- find the primary key
        for index in tbl.indices:
            if (index.isPrimary == 1):
                primaryKey = index
                foundPrimaryKey = True
                break
            #end
        #end
    
        #-- is primary key single-column?
        pKColumn = None
        if (foundPrimaryKey & (len(primaryKey.columns) == 1)): # then
            pKColumn = primaryKey.columns[0].referencedColumn
        #end
    
        colComment = ""
        k = 0
        for column in tbl.columns: # do
            k += 1
            #local column, SQLServerType, length, check, flags
            check = ""
            #column = tbl.columns[k]
            if (column.simpleType):# then
                SQLServerType = column.simpleType.name
                flags = column.simpleType.flags
            else:
                SQLServerType = column.userType.name
                flags = column.flags
            #end
            length = column.length
            #-- for INTEGER PRIMARY KEY column to become an alias for the rowid
            #-- the type needs to be "INTEGER" not "INT"
            #-- we fix it for other columns as well
            if ((SQLServerType.find("INT") != -1) | (SQLServerType == "LONG")): # then
                SQLServerType = "INTEGER"
                length = -1
                #-- check flags for "unsigned"
                for flag in column.flags:# do
                    if (flag == "UNSIGNED"): # then
                        check = "%s>=0" % (quoteIdentifier(column.name))
                        break
                    #end
                #end
            #end
            if (SQLServerType.find("LONG") != -1): # then
                #-- This is probably a LONG VARCHAR type, so we need to STRIP the LONG, and ADD (MAX)...
                SQLServerType = "%s(MAX)" % (SQLServerType[5:29])
            #end
            #-- we even implement ENUM (because we can)
            if (SQLServerType == "ENUM"):# then
                SQLServerType = "VARCHAR(MAX)"
                if (column.datatypeExplicitParams):# then
                    check = str.format("{0} IN {1}", quoteIdentifier(column.name), column.datatypeExplicitParams)
                #end
            #end
            if (k > 1): # then
                file.write( ", %s \n" % (commentFormat(colComment)))
            #end
            file.write( " %s" % (quoteIdentifier(column.name)))

            if (SQLServerType.find("BOOL") != -1): # then
                #-- This is probably a BOOL or BOOLEAN, so we will replace it with BIT
                SQLServerType = "BIT"
            #end
            #-- type is optional in SQLServer
            if (SQLServerType != ""):
                file.write( " %s" % (SQLServerType))
            #end
            #-- for [VAR]CHAR and such types specify length
            #-- even though this is not used in MySQL
            if (length > 0): # then
                file.write( "( %s )" % (length))
            #end
            #-- Must specify single-column PKs as column-constraints
            #-- for AI/rowid behaviour
            if (column == pKColumn):# then
                file.write(" CONSTRAINT %s PRIMARY KEY " % (quoteIdentifier("pk_%s" % (tbl.name))))
                if (primaryKey.columns[0].descend == 1): #then
                    file.write(" DESC")
                #end
                #-- only PK columns can be AI in SQLServer
                if (column.autoIncrement == 1): #then
                    file.write(" IDENTITY(1,1)")
                #end
            #end
            #-- check for NotNull
            if (column.isNotNull == 1): #then
                file.write(" NOT NULL")
            else:
                file.write(" NULL")
            #end
      
            if (check != ""): #then
                file.write(" CHECK(%s)" % (check))
            #end
      
            if (column.defaultValue != ""): #then
                file.write(" DEFAULT %s" % (column.defaultValue))
            #end

            colComment = column.comment
        #end
    
        #-- for multicolumn PKs
        if ((primaryKey != None) & (pKColumn == None)): #then
            file.write(", %s\n CONSTRAINT %s PRIMARY KEY(%s)" % (commentFormat(colComment), quoteIdentifier("pk_%s" % (tbl.name)), printIndexColumns(primaryKey)))
            colComment = ""
        #end
    
        #-- put non-primary, UNIQUE Keys in CREATE TABLE as well (because we can)
        for index in tbl.indices: #) do
            #local index
            #index = tbl.indices[k]
            if (index != primaryKey and index.indexType == "UNIQUE"): #then
                file.write(", %s\n" % (commentFormat(colComment)))
                colComment = ""
                if (index.name != ""): #then
                    file.write("  CONSTRAINT %s \n  " % (quoteIdentifier(index.name)))
                #end
                file.write("  UNIQUE( %s )" % (printIndexColumns(index)))
            #end
        #end
    
        for fKey in tbl.foreignKeys:
            #local fKey
            #fKey = tbl.foreignKeys[k]
            haveFKeys = 1
            file.write( ", %s \n" % (commentFormat(colComment)))
            colComment = ""
            if (fKey.name != ""): #then
                file.write("  CONSTRAINT %s \n" % (quoteIdentifier(fKey.name)))
            #end
            file.write("  FOREIGN KEY(%s)\n" % (printFKColumns(fKey.columns)))
            file.write("    REFERENCES %s ( %s )" % (quoteIdentifier(fKey.referencedTable.name), printFKColumns(fKey.referencedColumns)))
            if ((fKey.deleteRule == "RESTRICT") | (fKey.deleteRule == "CASCADE") | (fKey.deleteRule == "SET NULL")): #then
                file.write("\n    ON DELETE %s" % (fKey.deleteRule))
            #end
            if ((fKey.updateRule == "RESTRICT") | (fKey.updateRule == "CASCADE") | (fKey.updateRule == "SET NULL")): #then
                file.write("\n    ON UPDATE %s" % (fKey.updateRule))
            #end
            if (isDeferred(fKey)): #then
                file.write(" DEFERRABLE INITIALLY DEFERRED")
            #end
        #end
    
        file.write("%s\n);\n" % (commentFormat(colComment)))

        if (tbl.comment.strip() != ""): #then
            file.write( "\nexec sys.sp_addextendedproperty @name=N'MS_Description', @value=N'%s', @level0type=N'SCHEMA', @level0name=N'%s', @level1type=N'TABLE',@level1name=N'%s';\n" % (tbl.comment.strip().replace("'","''"), schema.name, tbl.name))
        #end

        for column in tbl.columns:
            #local column, SQLServerType, length, check, flags
            check = ""
            #column = tbl.columns[k]
            if (column.comment.strip() != ""): #then
                file.write( "\nexec sys.sp_addextendedproperty @name=N'MS_Description', @value=N'%s', @level0type=N'SCHEMA', @level0name=N'%s', @level1type=N'TABLE',@level1name=N'%s', @level2type=N'COLUMN', @level2name=N'%s';\n" % (column.comment.strip().replace("'","''"), schema.name, tbl.name, column.name))
            #end
        #end
    
        #-- CREATE INDEX statements for
        #-- all non-primary, non-unique, non-foreign indexes 
        k = 0
        for index in tbl.indices: #) do
            k += 1
            #local index, indexName
            #index = tbl.indices[k]
            if (index.indexType == "INDEX"): #then
                indexName = "%s" % (index.name)
                if (index.name == ""): #then
                    indexName = "%s.index%d" % (tbl.name, k)
                    #--uniqueId = uniqueId + 1
                #end
                file.write( "CREATE INDEX %s%s ON %s.%s (" % (dbName, quoteIdentifier(indexName), quoteIdentifier(schema.name), quoteIdentifier(tbl.name)))
                file.write( "%s);\n" % (printIndexColumns(index)))
            #end
        #end

        #-- write the INSERTS (currently always)
        #local tableInserts
        if (type(tbl.inserts) is str): #then
            #-- old inserts, WB 5.1-
            tableInserts = tbl.inserts.replace("`", "'") # get rid of the mySQL special quotes.
        else:
            #-- new inserts, WB 5.2.10+
            tableInserts = tbl.inserts().replace("`", "'") # get rid of the mySQL special quotes.
        #end
        showMessage(str.format("tableInserts = <<<{0}>>>", tableInserts))
        for insert in re.split("[\r\n]", tableInserts): #.split("\r\n"): #string.gmatch(tableInserts, "[^\r\n]+"): # do
            if (len(insert) > 0):
                showMessage(str.format("insert = <<<{0}>>>", insert))
                insertStart = "insert into '%s' (" % (tbl.name)
                if (insert.lower().find(insertStart) != -1):
                    #-- WB 5.1- insert
                    columnsValues = insert[len(insertStart):]
                else:
                    #-- WB 5.2+ insert
                    insertStart = "insert into '%s'.'%s' (" % (schema.name, tbl.name)
                    if (insert.lower().find(insertStart.lower()) != -1): #then
                        columnsValues = insert[len(insertStart):]
                    else:
                        YesNoBox("Error", "Unrecognized command in insert\n%s\n" % (insert))
                        return 1
                    #end
                #end
                showMessage(str.format("columnsValues = <<<{0}>>>", columnsValues))
                lastColumn = 0
                k = 0
                for column in tbl.columns: #) do
                    columnName = singlequoteIdentifier(column.name)
                    if (columnsValues[0: len(columnName)] == columnName): #then
                        columnsValues = columnsValues[len(columnName):]
                        if (columnsValues[0:1] == ")"): #then
                            columnsValues = columnsValues[1:]
                            lastColumn = k
                            break
                        else:
                            if (columnsValues[0:2] == ", "): #then
                                columnsValues = columnsValues[2:]
                            else:
                                YesNoBox("Error", "Unrecognized character in column list %s" % (columnsValues))
                            #end
                        #end
                    else:
                        YesNoBox("Error", "Unrecognized column in inserts %s" % (insert))
                        return 1
                    #end
                    k += 1
                #end
                file.write( "INSERT INTO %s.%s (" % (quoteIdentifier(schema.name), quoteIdentifier(tbl.name)))
                for k  in range (0, lastColumn + 1):
                    if (k > 0): #then
                        file.write( ",")
                    #end
                    file.write(quoteIdentifier(tbl.columns[k].name))
                #end

                if (columnsValues[0:9].lower() != " values ("): #then
                    YesNoBox("Error", "Unrecognized SQL in insert %s" % (columnsValues))
                    return 1
                #end
                columnsValues = columnsValues[9:]

                file.write(") VALUES (")
                file.write( columnsValues ) # .replace("'", "''")) # this was causing doubled single quotes
                file.write( "\n")
            #end
    #end
    return 0
#end

def orderTables(file, dbName, schema, unOrdered, respectDeferredness):
    showMessage(str.format("Processing Schema {0} in function {1}", schema.name, "orderTables"))
    while True:
        haveOrdered = False
        showMessage(str.format("There are {0} records left in unOrdered in function {1}", len(unOrdered), "orderTables"))
        if (len(unOrdered) == 0):  # if there aren't any tables in the unOrdered list then there is nothing to do.
            break
        for tbl in schema.tables: #) do
            showMessage(str.format("Processing Table {0} in function {1}", tbl.name, "orderTables"))
            if (tbl in unOrdered):
                hasForwardReference = False
                for fKey in tbl.foreignKeys:
                    if ((fKey.referencedTable in unOrdered) & (fKey.referencedTable.name != tbl.name) & ((respectDeferredness & isDeferred(fKey)) == False)):
                        hasForwardReference = True
                        break
                    #end
                #end
                if (hasForwardReference == False):
                    if (exportTable(file, dbName, schema, tbl) != 0):
                        print "Error writing table %s \n"% (tbl.name)
                        return 1
                    #end
                    unOrdered.remove(tbl)
                    haveOrdered = True
                #end
            #end
        #end
        if haveOrdered:
            break
    showMessage(str.format("Leaving Schema {0} in function {1}", schema.name, "orderTables"))
    return 0
#end


def exportSchema(file, schema, isMainSchema):
    print "Schema %s has %d tables\n" % (schema.name, len(schema.tables))
    if (len(schema.tables) > 0):
        file.write("\n-- Schema: %s \n" % (schema.name))
        file.write(sCommentFormat(schema.comment))

        dbName = "" # this is a feature of SQLite where this code came from.
        if (isMainSchema == False):
            #dbName = "%s." % (quoteIdentifier(schema.name))
            #file.write('ATTACH "%s" AS %s; \n' % (safeFileName("%s.sdb" % (schema.name)), quoteIdentifier(schema.name)))
            file.write ("CREATE SCHEMA %s" % (quoteIdentifier(schema.name)))
        #end

        if (isMainSchema & (schema.name.lower() != "dbo")):
            file.write ("CREATE SCHEMA %s;" % (quoteIdentifier(schema.name)))

        #-- find a valid table order for inserts from FK constraints
        unOrdered = []
        for tbl in schema.tables:
            showMessage(str.format("Adding {0} to list in function {1}", tbl.name, "orderTables"))    
            unOrdered.append(tbl)
        #end
    
        #-- try treating deferred keys like non-deferred keys first for ordering
        if (orderTables(file, dbName, schema, unOrdered, False) != 0):
            print "Error ordering tables in schema %s \n" % (schema.name)
            return 1
        #end
        #-- now try harder (leave out deferred keys from determining an order)
        if (orderTables(file, dbName, schema, unOrdered, True) != 0):
            print "Error ordering tables in schema %s \n" % (schema.name)
            return 1
        #end
   
        #-- loop through all remaining tables, if any. Have circular FK refs. How to handle?
        for tbl in schema.tables:
            if (tbl in unOrdered):
                if (exportTable(file, dbName, schema, tbl) != 0):
                    print "Error writing table %s\n" % (tbl.name)
                    return 1
                #end
            #end
        #end
        #-- file:write("COMMIT;\n")
    #end
    return 0
#end

#-- get comma separated column list of an index
def printIndexColumns(index):
    s = ""
    i = 1;
    for column in index.columns:
        if (i > 1):
            s += ","
        #end
        s += quoteIdentifier(column.referencedColumn.name)
        if (column.descend == 1):
            s += " DESC"
        #end
        i += 1
    #end
    return s
#end

#-- get comma separated column/reference list of a foreign key
def printFKColumns(columns):
    s = ""
    i = 1;
    for column in columns:
        if (i > 1):
            s += ","
        #end
        s += quoteIdentifier(column.name)
        i += 1
    #end
    return s
#end

#-- get comma separated referenced column list of a foreign key
def printFKRefdColumns(fKey):
    s = ""
    i = 1
    for column in fKey.columns:
        if (i > 1):
            s += ", "
        #end
        s += quoteIdentifier(column.referencedColumn.name)
    #end
    return s
#end

#-- format a info field as SQL comment
def infoFormat(header, body):
    strippedBody = body.strip()
    if (strippedBody == ""):
        return ""
    else:
        if (strippedBody.find("\n") != -1):
            #-- multiline comment
            return str.format("-- %s\n--   %s\n", header,strippedBody.replace("\n","\n--   "))
        else:
            #-- single line
            return str.format("-- {0:<14}: {1}\n", header, strippedBody)
        #end
    #end
#end

def singlequoteIdentifier(id):
    return str.format("'{0}'", id.replace("[", "").replace("]",""))


#-- double quote identifer, replacing " by ""
def quoteIdentifier(id):
    return str.format("[{0}]", id.replace("[", "").replace("]",""))
#end

#-- create safe filename from identifer
def safeFileName(id):
    return re.sub("[/\\:%*%?""<>|%%]", "", id)
#:gsub(
#    '[/\\:%*%?"<>|%%]',
#    function(c) return string.format("%%%02x", string.byte(c)) end
#  )
#end

#-- format a schema or table comment as SQL comment
#-- table comments to be stored in SQLServer schema
def sCommentFormat(body):
    strippedBody = body.strip()
    if (strippedBody == ""):
        return ""
    else:
        #-- multiline comment
        return str.format("--   {0}\n", strippedBody.replace("\n","\n--   "))
    #end
#end

#-- format a column comment as SQL comment
#-- to be stored in SQLServer schema for user information
def commentFormat(body):
    strippedBody = body.strip()
    if (strippedBody == ""):
        return ""
    else:
        if (strippedBody.find("\n") != -1):
            #-- multiline comment
            return str.format("\n--  {0}",strippedBody.replace("\n","\n--   "))
        else:
            #-- single line
            return str.format("-- {0}", strippedBody)
        #end
    #end
#end

#exportSQLServer(grt.root.wb.doc.physicalModels[0].catalog)
