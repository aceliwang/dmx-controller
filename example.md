timecode

// init
import palettes
patch "trimmer pars" from 101 at [100, 500]
patch laser

// palettes

/// groups
pars = select 101 > 101
/// colours
pink = rgb(100, 255, 255)
/// positions
home = position(100, 255) for pars


// cuelist
startcl "main cuelist ty"
@100 pars on sc blue sp out # cue name / cue description
/// this should become @100, macs, on, sc blue, sp out, # cue name
@120 macs si 25 in 2 # cue name
@123 macs on pars 25 in 2
@150 macs sp home si 50 sc green in 5
@200 repeat every 5000 for 200 until @400
    @0 macs sp pos1 pars 
    @50 macs sp pos2
    macs se ticky
    macs sv horizontalAngle rot 50
@250 group
    pars off
@f pars blue ie. follow
@f 

timings: @number, @f (follow)