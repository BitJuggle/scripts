import json
import os
from pathlib import Path
import xml.etree.ElementTree as xmltree

# Simple script to update StashApp JSON metadata by applying values read from JRiver sidecar files.

# JRiver sidecar format: https://wiki.jriver.com/index.php/Sidecar_Files (no real documentation)
#
# Example JRiver sidecar XML file:
# ----------------------------------------------------------------------
# <?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
# <MPL Version="2.0" Title="JRSidecar" PathSeparator="\">
# <Item>
# <Field Name="Filename">P:\\FILE.mp4</Field>
# <Field Name="Rating">3</Field>
# <Field Name="Last Skipped">1572833185</Field>
# <Field Name="Compression">mp4 video (video: h264, audio: aac)</Field>
# <Field Name="Bitrate">12174</Field>
# <Field Name="Number Plays">2</Field>
# <Field Name="Bit Depth">16</Field>
# <Field Name="Genre">genre</Field>
# <Field Name="Aspect Ratio">16:9</Field>
# <Field Name="FPS">29.9699993133544922</Field>
# <Field Name="Last Played">1592825796</Field>
# <Field Name="Channels">2</Field>
# <Field Name="Date First Rated">1546364470</Field>
# <Field Name="Keywords">keyword1;keyword2</Field>
# <Field Name="Bookmark">135931</Field>
# <Field Name="Stack View">0</Field>
# <Field Name="Playable">1</Field>
# <Field Name="Skip Count">1</Field>
# <Field Name="Name">Title</Field>
# <Field Name="Sample Rate">48000</Field>
# <Field Name="Duration">2533.568000000000211</Field>
# </Item>
# </MPL>
# ----------------------------------------------------------------------

JRIVER_FILENAME = 'Filename'
JRIVER_RATING = 'Rating'
JRIVER_GENRE = 'Genre'
JRIVER_KEYWORDS = 'Keywords'
JRIVER_NAME = 'Name'

# StashApp scene format: https://github.com/stashapp/stash/wiki/JSON-Specification#scenejson
SCENE_TITLE = 'title'
SCENE_RATING = 'rating'
SCENE_TAGS = 'tags'

jriver_media_dir = r"D:\Videos"
stash_mappings_path = r"D:\StashApp\Metadata\mappings.json"
stash_scenes_path = r"D:\StashApp\Metadata\scenes"

jriver_metadata_map = dict()
path_checksum_map = dict()

# Find all JRiver sidecar files
sidecar_files = list(Path(jriver_media_dir).rglob("*.[xX][mM][lL]"))

# Read in all JRiver metadata from Sidebar XML files
for file in sidecar_files:
  with open(file, 'r', encoding="utf8") as file:
    mpl = xmltree.fromstring(file.read())
    if mpl.attrib.get('Title') == 'JRSidecar':
      items = list(mpl)
      # Sidecars are implemented as single element MPL Playlists
      if len(items) == 1:
        JRIVER_fields = list(items[0])
        fields = dict()
        for JRIVER_field in JRIVER_fields:
          key = JRIVER_field.attrib['Name']
          value = JRIVER_field.text
          fields[key] = value
        filename = fields.get('Filename')
        jriver_metadata_map[filename] = fields

# Parse StashApp mapping file to find scene JSON path
with open(stash_mappings_path, 'r', encoding="utf8") as mapping_file:
  mappings_str = mapping_file.read()
  mappings_json = json.loads(mappings_str)
  for scene in mappings_json['scenes']:
    path_checksum_map[scene['path']] = scene['checksum']

# Update StashApp metadata files with JRider metadata
for filename, jriver_metadata in jriver_metadata_map.items():
  stashapp_checksum = path_checksum_map.get(filename)
  if stashapp_checksum:
    stash_scene_path = os.path.join(stash_scenes_path, stashapp_checksum + ".json")
    with open(stash_scene_path, 'r+', encoding="utf8") as scene_file:
      scene_json = json.loads(scene_file.read())
      jriver_name = jriver_metadata.get(JRIVER_NAME)
      jriver_rating = jriver_metadata.get(JRIVER_RATING)
      jriver_keywords_str = jriver_metadata.get(JRIVER_KEYWORDS)
      jriver_keywords = jriver_keywords_str and jriver_keywords_str.split(';')
      jriver_genre = jriver_metadata.get(JRIVER_GENRE)
      # Update StashApp metadata
      if jriver_name:
        scene_json[SCENE_TITLE] = jriver_name
      if jriver_rating:
        scene_json[SCENE_RATING] = int(jriver_rating)
      if jriver_keywords:
        scene_json[SCENE_TAGS] = jriver_keywords
      else:
        scene_json[SCENE_TAGS] = []
      # Map genre to tags as no dedicated genre field
      if jriver_genre:
        scene_json[SCENE_TAGS].append(jriver_genre)
      # Write changes
      scene_file.seek(0)
      scene_file.truncate()
      json.dump(scene_json, scene_file, indent=2)
