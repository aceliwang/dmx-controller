# Timeline

- [DONE] Get '101 si 100' working
- [DONE] Get programmer to reflect states for '101 si 100'
- [TODO] Get programmer to reflect palette state in programmer for '101 si 100'
- [TODO] Set colour, set position, set effects
- [TODO] If repatch, change all palettes for reference
- [TODO] Programmer
  - Programmer is a dictionary with each fixture and each parameter
  - {'commands': [list of commands], 101: {"intensity": [('command', 100)], "colour": red}}
  - How to handle overlapping commands? LTP
  - How to handle knock out? 
  - Figure out overwrite behaviour. Ordered dicts are annoying.

## Programming

- [TODO] Get mouse hook working to tie into programmer
- [TODO] Remove from programmer
- [TODO] Remove parameters specific to fixtures from programmer
- [TODO] Empty palettes with only names

## Cuelists

- [TODO] Click to select cuelist
- [TODO] Edit cues in cuelist

## General Palettes

- [TODO] Enable empty palettes or default palette?

## Colours
- [TODO] Create all colours
- [TODO] RGB to RGBW conversion
- [TODO] HSL to HS conversion

## ArtNet
- [TODO] ArtNet output
- [TODO] Universe support