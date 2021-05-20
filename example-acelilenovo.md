timecode

// init
import palettes
patch "trimmer pars" 101 at [100, 500]
patch laser

// palettes

/// groups
pars = select 101 103 > 105 "front pars"
/// colours
/// positions
up = position(0, 0) // default
home = position(100, 255) for s 101 > 101 // for selection
down = position(0, 0) for fixture type


// cuelist
start cl "main cuelist"
@100 macs on sc blue sp out
@120 macs si 25
@150 macs sp home si 50 sc green
@200 repeat every 5000 for 200 until @400
    @0 macs sp pos1 pars 
    @50 macs sp pos2
    macs se ticky
    macs sv horizontalAngle 