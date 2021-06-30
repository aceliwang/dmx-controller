timecode

// init
import palettes
patch "trimmer pars" from 101 at [100, 500]
patch laser
patch "led bars"

/// custom palettes

/// groups
cyc = select 101 > 184
cyc_1/3 = select 101 > 128
cyc_2/3 = select 129 > 156
cyc_3/3 = select 157 > 184
cycP = select 101 > 142
cycOP = select 143 > 184
/// TODO: select group and split into n groups
lustrs = select 201 > 218
lustrsP = select 201 > 209
lustrsOP = select 210 > 218
///
tops = select 301  > 312
topsFront = select 301 > 304
topsMid = select 305 > 308
topsBack = select 309 > 312
topsP = select 301 302 305 306 309 310
topsOP = select 303 304 307 308 311 312
///
pars = select 401 > 408
parsP = select 401 > 404
parsOP = select 405 > 408
parsUp = select 401 403 405 407
parsDown = select 402 404 406 408
//
heads = select 501 > 508
//
bars = select 701 > 710
//
laser = select 901

/// colours
pink = rgb(100, 255, 255)
/// positions
home = position(100, 255) for pars

// https://github.com/chrvadala/music-beat-detector

// cuelist
startcl "showcase"
@100 pars on sc blue sp out # cue name / cue description
/// this should become @100, macs, on, sc blue, sp out, # cue name
@120 macs si 25 in 2 # cue name
@123 macs on pars 25 in 2
@150 macs sp home si 50 sc green in 5
@200 repeat every 5000 for 200 until @400
    @0 macs sp pos1 &&  
    @50 macs sp pos2
    macs se ticky
    macs sv horizontalAngle rot 50
@250 # beat
    pars off
    macs on
@f pars sc blue ie. follow
@f 
stopcl "showcase"

timings: @number, @f (follow)