// META
function e(css) {
    elements = document.querySelectorAll(css)
    if (elements.length > 1) {
        return elements
    } else {
        return elements[0]
    }
}

// META::GUI

function remove_all_children(node) {
    while (node.firstChild) {
        node.removeChild(node.firstChild)
    }
    return
}

function toggle(node, type) {
    switch (type) {
        case 'visibility':
            node.style.display = (node.style.display == 'none') ? 'block' : 'none'
            break;
        case 'button':
            if (node.classList.contains('button-primary')) {
                node.classList.remove('button-primary')
            } else {
                node.classList.add('button-primary')
            }
        default:
            break;
    }
    return
}

// VARIABLES::STATE

let selected_cues = {}
let selected_fixtures = {}
let selected_cuelist = ''
let timecode_state = false




// CONSOLE::HANDLERS

e('#submit').onclick = handle_submit
e('#input').onkeydown = function (evt) { if (evt.keyCode == 13) { handle_submit() } }

function handle_submit() {
    console.log(input.value)
    eel.read_line(input.value)
    let text = document.createTextNode(input.value)
    logDiv.appendChild(text)
    input.value = ''
    return
}


// BUTTON MANAGEMENT




e('#patching-toggle').onclick = () => toggle(e('#patching'), 'visibility')
e('#timecode-toggle').onclick = () => {
    toggle(e('#timecode-toggle'), 'button')
    timecode_state = !timecode_state
}

// REFLECT STATE
eel.expose(refresh_selected_cuelist)
function refresh_selected_cuelist(cuelist) {
    document.getElementById('active-cuelist').innerText = cuelist
    for (div of e('#cuelist div')) { // TODO: for multiple cuelists visible
        div.classList.remove('selectedCue')
    }
}

eel.expose(refresh_timeline)
function refresh_timeline() {
    remove_all_children(e('#cuelist'))
    remove_all_children(e('#timeline'))
    select_cuelist()

}

eel.expose(refresh_selection)
function refresh_selection(selection) {
    e('#active-selection').innerText = selection
    current
}

eel.expose(refresh_programmer)
function refresh_programmer(program) {
    console.log('[FUNC] refresh_programmer STARTED')
    if (!program) {program = eel.get_programmed()(); console.log('getting program', program);}
    let programmer = e('#programmed')
    function fill_programmer() {
        console.log(program)
        for (fixture in program) {
            div = document.createElement('div')
            let fixture_programs = {}
            if (fixture == 'commands') {
                fixture_programs = program[fixture]
            } else {
                for (parameter in program[fixture]) {
                    console.log(program[fixture][parameter])
                    fixture_programs[parameter] = program[fixture][parameter][program[fixture][parameter].length - 1]
                }
            }
            console.log(fixture_programs);
            div.innerText = fixture + ' ' + JSON.stringify(fixture_programs)
            programmer.appendChild(div)
        }
    }
    remove_all_children(programmer)
    fill_programmer()
    console.log('[FUNC] refresh_programmer ENDED')
    return
}


// PROGRAMMERS

eel.expose(program_position)
// document.getElementById('position-programmer').onmousemove = program_position
function program_position(event) {
    console.log(event)
}

function verify_intensity(event) {
    let value = Number(this.value)
    console.log('hi', value);
    if (value > 100 || value < 0) {
        this.value = ''
        alert(`Intensity is out of bounds. Intensity = ${value}`)
    } else {
        let selection = selected_fixtures // TODO: TO FIX
        eel.set_value('intensity', 'intensity', value)
    }
}

// e('input[name="intensity"]').onblur = set_intensity
console.log(e('input[name="intensity"'));

// eel.expose(find_mouse_position)
MOUSE_PROGRAMMING_STATUS = false
document.getElementById('trigger').onclick = function (evt) {
    if (!MOUSE_PROGRAMMING_STATUS) {
        let channel = 0
        eel.init_listen_to_movement([evt.screenX, evt.screenY], channel)
        MOUSE_PROGRAMMING_STATUS = true
    } else {
        MOUSE_PROGRAMMING_STATUS = false
    }
    console.log(evt.screenX, evt.screenY)
}
find_mouse_position
function find_mouse_position(evt) {
    return [evt.screenX, evt.screenY]
    // let position
    // console.log(position)
    // let get_position = function(evt) {
    //     position = [evt.screenX, evt.screenY]
    //     console.log('position', position)
    //     document.body.removeEventListener('mousemove', get_position)
    // }
    // document.body.addEventListener('mousemove', get_position)
    // // while (true) {
    // //     console.log('hi', position);
    // //     if (position !== undefined) {
    // //         break
    // //     }
    // // }
    // console.log('broken');

    // console.log(position)
    // return position
}

eel.expose(change_intensity)
function change_intensity(args) {
    e('#intensity').innerText = args.toString()
}

// PATCHING
async function fill_patching() {
    patching = await eel.get_patching()()
    console.log(patching);
    for (let i = 1; i < 2; i++) {
        let universeDiv = document.getElementById('universe-' + ('0' + i).slice(-2))
        console.log(universeDiv);
        universeHeader = document.createElement('div')
        universeHeader.innerText = 'Universe'
        // universeDiv.appendChild(universeHeader)
        for (let address = 1; address <= 512; address++) {
            addressBlock = document.createElement('div')
            addressBlock.className = 'patchingAddressBlock'
            addressBlock.innerText = address
            universeDiv.appendChild(addressBlock)
        }
    }
    for (let fixture of Object.values(patching)) {
        console.log('fixture', fixture);
        let universe = '01' // TODO
        let h = document.querySelector('#universe-' + universe + ' > div:nth-child(' + fixture[1] + ')')
        h.classList.add('channelUsedStart')
        for (div of document.querySelectorAll(`#universe-${universe} > div:nth-child(n+${fixture[1] + 1}):nth-child(-n+${fixture[1] + fixture[2] - 1})`)) {
            console.log(div)
            div.classList.add('channelUsed')
        }
    }
}

fill_patching()

// CUELIST::RECORDING

function  record_cue(cuelist) {
    cuelist = cuelist || 
    eel.record_programmer_to_cuelist()
    refresh_timeline()
}

// CUELIST::SELECTION

document.body.addEventListener('keydown', function (evt) {
    if (evt.key == 'Escape') {

    }
})

eel.expose(add_cue_to_selection)
function add_cue_to_selection(cuelist, cue_number) {
    console.log(selected_cues.hasOwnProperty(cuelist), cue_number, selected_cues[cuelist])
    if (selected_cues.hasOwnProperty(cuelist)) {
        if (selected_cues[cuelist].includes(cue_number)) {
            // let hi = cue_number in selected_cues[cuelist]
            console.log(cue_number, selected_cues[cuelist])
            console.log('triggered1')
            // TODO: CLEAN
            return
        } else {
            console.log('riggered');
            selected_cues[cuelist].push(cue_number)
        }
    } else {
        selected_cues[cuelist] = [cue_number]
    }
    e(`#cuelist div:nth-of-type(${cue_number + 2})`).classList.add('selectedCue')
    e(`#timeline div.cueGroup:nth-of-type(${cue_number + 2})`).classList.add('selectedCue')
    e('#selected-cues').innerText = JSON.stringify(selected_cues)
}

eel.expose(remove_cue_from_selection)
function remove_cue_from_selection(cuelist, cue_number) {
    console.log(cue_number)
    if (selected_cues.hasOwnProperty(cuelist)) {
        let index = selected_cues[cuelist].indexOf(cue_number)
        selected_cues[cuelist].splice(index, 1)
        if (selected_cues[cuelist].length == 0) {
            delete selected_cues[cuelist]
        }
        e(`#cuelist div:nth-of-type(${cue_number + 2})`).classList.remove('selectedCue')
        e(`#timeline div.cueGroup:nth-of-type(${cue_number + 2})`).classList.remove('selectedCue')
        e('#selected-cues').innerText = JSON.stringify(selected_cues)
    } else {
        console.log(`[ERROR]: func remove_cue_from_selection: ${cuelist} does not exist.`)
    }
}

// function remove_cue_from_selection(cuelist, cue_number) {
//     if (selected_cues.hasOwnProperty(cuelist)) {
//         if (cue_number in selected_cues[cuelist]) {
//             let index = selected_cues[cuelist].indexOf(cue_number)
//             selected_cues[cuelist].splice(index, 1)
//         }
//     }
// }

// CUELIST
eel.expose(select_cuelist)
async function select_cuelist() {
    let cueLists = await eel.get_cuelists()()
    let patching = await eel.get_patching()()

    let None = ''
    let cue_lists
    console.log(patching)
    // lists = cueLists.cuelists
    lists = cueLists
    let cuelist = e('#cuelist')
    function create_box() {
        div = document.createElement('div')
        
    }
    for (list in lists) {
        // list = mainCueList
        console.log(list)
        // generate cue list blocks
        let cueHeaderGroup = document.createElement('div')
        cueHeaderGroup.className = 'cueGroup'
        for (light in patching) { // generate cueHeaders
            let cueItem = document.createElement('div')
            cueItem.className = 'cueHeader'
            cueItem.innerText = light
            cueHeaderGroup.appendChild(cueItem)
        }
        timeline.appendChild(cueHeaderGroup)
        // structure = ???
        for ([number, cue] of lists[list].entries()) {
            console.log(number, cue);
            // cue = cue object
            let name = cue.name
            let desc = cue.desc
            let timing = cue.timing
            let commands = cue.commands
            let dmx = cue.dmx
            let state = cue.state
            let cueRow = document.createElement('div')
            cueRow.className = 'cueRow'
            cueRow.innerText = `${number}, ${name}, ${desc}, ${timing}, ${JSON.stringify(commands)}, ${dmx}, ${state}`
            cueRow.number = number
            cueRow.list = list
            cueRow.onclick = handle_click_cue
            cuelist.appendChild(cueRow)
            // TODO: resizable divs
            let cueGroup = document.createElement('div')
            cueGroup.className = 'cueGroup'
            let tempItems = {}
            for (light in patching) { // create cue item
                let cueBackground = document.createElement('div')
                cueBackground.className = 'cueBackground'
                let cueItem = document.createElement('div')
                cueItem.className = 'cueItem'
                cueItem.id = `${light}-${number}`
                defaultColor = 'rgba(255,255,255,0)' // should be from templates
                cueItem.style.backgroundColor = defaultColor
                tempItems[light] = cueItem
                cueBackground.appendChild(cueItem)
                cueGroup.appendChild(cueBackground)
            }
            console.log(cueGroup)
            timeline.appendChild(cueGroup)
            for (command in cue.commands) {
                console.log(cue.commands[command])
                for (instructionGroup of cue.commands[command]) {
                    let dmxChannel = instructionGroup[0]
                    let dmxValue = instructionGroup[1]
                    if (humanDMX[dmxChannel]) {
                        let [light, type] = humanDMX[dmxChannel]
                        let [r, g, b, a] = tempItems[light].style.backgroundColor.replace('rgba(', '').replace(')', '').replaceAll(' ', '').split(',')
                        switch (type) {
                            case 'intensity':
                                a = (dmxValue / 256).toFixed(2)
                                break
                            case 'red':
                                r = dmxValue
                                break
                            case 'blue':
                                b = dmxValue
                                break
                            case 'green':
                                g = dmxValue
                                break
                            default:
                                break;
                        }
                        tempItems[light].style.backgroundColor = `rgb(${r},${g},${b},${a})`
                    }
                }
            }
        }
    }
}
// populateGroups()

// CUELIST::HANDLE INPUTS

function handle_click_cue(evt) {
    if (!evt.ctrlKey) {
        for (div of e('#cuelist div, #timeline div')) {
            div.classList.remove('selectedCue')
        }
        selected_cues = {}
    } else {
    }
    add_cue_to_selection(this.list, this.number)
    this.classList.add('selectedCue')
}

// CUELIST::PLAYBACK

function play_cues() {
    function resolve_selected_cues_playback() {
        let temp = {}
        for (list in selected_cues) {
            temp[list] = Math.max(...selected_cues[list])
        }
        return temp
    }
    resolved_cues = resolve_selected_cues_playback()
    if (Object.keys(resolved_cues).length > 0) {
        for (cuelist in resolved_cues) {
            let cue_number = resolved_cues[cuelist]
            if (timecode_state) {
                eel.start_timecode(cuelist, cue_number)
                return
            }
            eel.play_cue(cuelist, cue_number) // TODO: AWAIT BEFORE CONTINUING. HUH?
            // remove_cue_from_selection(cuelist, cue_number)
            // console.log(selected_cues);
            // let new_cue = cue_number == cuelist.length && 
            // add_cue_to_selection(cuelist, cue_number + 1)
            // console.log('test')
        }
    }
}

// KEYBOARD SHORTCUTS

document.body.onkeydown = function (evt) {
    if (!evt.getModifierState("CapsLock")) { return } else {
        console.log('hi');
    }
    switch (evt.key) {
        case ' ': // SPACEBAR
            console.log('KEY DETECTED: SPACE BAR')
            // TODO: make sure this happens when entering stuff into console
            if (document.activeElement != e('#input') && Object.keys(selected_cues).length > 0) {
                evt.preventDefault()
                if (evt.shiftKey) {
                    // TODO: change selection to previous
                } else {
                    play_cues()
                }
            }
            break
        case 'Escape':

            break
        case 'A':
            toggle(e('#patching'))
            break
    }

}

// ON START
async function load_programmer () {
    let program = await eel.get_programmer()()
    refresh_programmer(program)
    return
}
load_programmer()