#!/usr/bin/env python3

import sys, os
from pprint import pprint

GCODE_COMMENT_CHAR=";"

def gcode_parseline(line, lineno):
  code = ""
  comment = ""

  in_comment = False
  for c in line:
    if c == GCODE_COMMENT_CHAR:
      in_comment = True
      continue

    if not in_comment:
      code+=c
    else:
      comment+=c

  code = code.strip()

  if code:
    tokens = code.split(" ")

    return {
      "lineno": lineno,
      "cmd": tokens[0],
      "args": tokens[1:],
      "comment": comment
    }
  else:
    return {
      "lineno": lineno,
      "cmd": "",
      "args": [""],
      "comment": comment
    }

def gcode_query(gcode, query):
  for key in query:
    if gcode[key] != query[key]:
      return False

  return True

def gcode_tostr(gcode):
  gcode_tokens = [gcode["cmd"], *gcode["args"]]

  gcode_str = " ".join(gcode_tokens)
  gcode_str += " "+GCODE_COMMENT_CHAR+gcode["comment"]

  return gcode_str

def gcode_find(gcode_doc, term, query={}):
  candidates = []
  for i, line in enumerate(gcode_doc):
    if term in line:
      candidates += [gcode_parseline(line, i)]

  results = []
  for gcode in candidates:
    if gcode_query(gcode, query):
      results += [gcode]

  return results

def gcode_findone(gcode_doc, term, query={}):
  results = gcode_find(gcode_doc, term, query)
  if not results:
    return None

  return results[0]

def gcode_commentline(gcode_doc, gcode):
  gcode_doc[gcode["lineno"]] = GCODE_COMMENT_CHAR+" "+gcode_tostr(gcode)

def speedify(path):
  with open(path, 'r') as f:
    gcode_doc = f.read()

  gcode_doc = gcode_doc.split("\n")

  # 1. change first temp setting to the final extrude temp
  bed_tempset = gcode_findone(gcode_doc, "M104", {
    "comment": " set extruder temp for bed leveling"
  })
  print_tempset = gcode_findone(gcode_doc, "M104", {
    "comment": " set extruder temp"
  })

  bed_tempset["args"][0] = print_tempset["args"][0]
  gcode_doc[bed_tempset["lineno"]] = gcode_tostr(bed_tempset)

  # 2. comment out the bed level extruder temp wait
  bed_wait = gcode_findone(gcode_doc, "M109", {
    "comment": " wait for bed leveling temp"
  })
  gcode_commentline(gcode_doc, bed_wait)

  # 3. comment out later extruder temp set
  ext_tempset = gcode_findone(gcode_doc, "M104", {
    "comment": " set extruder temp"
  })
  gcode_commentline(gcode_doc, ext_tempset)

  # 4. replace bed mesh level with load existing data
  meshlevel = gcode_findone(gcode_doc, "G29")
  gcode_commentline(gcode_doc, meshlevel)

  gcode_doc[meshlevel["lineno"]] = "M420 S1 ; load bed leveling mesh"

  with open(path, "w") as f:
    for line in gcode_doc:
      f.write(line+"\n")

if __name__ == '__main__':
  speedify(sys.argv[1])