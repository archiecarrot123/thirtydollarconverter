import midi
import instrument_names
from tkinter import *
from tkinter import ttk
from tkinter import filedialog

default_instrument = "noteblock_harp"
default_pitch = 60


# globals
resolution = 0
notes_mixed = []
instruments = set()
drums = set()
instrument_widgets = {}
drum_widgets = {}
instrument_variables = {}
drum_variables = {}
instrument_mappings = {}
drum_mappings = {}


root = Tk()
root.title("DON'T YOU LECTURE ME WITH YOUR THIRTY DOLLAR CONVERTER")

mainframe = ttk.Frame(root, padding="12 3 12 3")
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
instframe = ttk.Frame(mainframe, padding="12 3 12 3")
instframe.grid(column=0, row=1, sticky=(N, W, E, S))
drumframe = ttk.Frame(mainframe, padding="12 3 12 3")
drumframe.grid(column=1, row=0, rowspan=3, sticky=(N, W, E, S))


class GDCevent:
    def __init__(self, event, value=None):
        self.event = event
        self.value = value
    
    def appendtofile(self, file_, beginning=False):
        suffix = ""
        if self.value:
            suffix = "@" + str(self.value)
        #suffix = "@" + str(self.value)
        if beginning:
            file_.write(self.event + suffix)
        else:
            file_.write("|" + self.event + suffix)

def printdelay(ticks, resolution, bpm):
    if ticks != 0:
        print("delay 1/", round(resolution*bpm/ticks), " minutes", sep="")

def loadmidi(filename):
    global resolution
    pattern = midi.read_midifile(filename)
    print("Format", pattern.format, "MIDI file")
    resolution = pattern.resolution
    print("Resolution:", resolution)
    pattern.make_ticks_abs()
    return pattern

def mix(pattern):
    global drums
    global instruments
    
    instruments = set() # need to reset instruments
    drums = set()
    n = 0
    for track in pattern:
        print("Track", n)
        #print(track)
        mixing_index = 0
        current_instrument = 0
        for event in track:
            if event.statusmsg == 0x90:
                if event.get_velocity() != 0 and event.channel != 9:
                    while mixing_index < len(notes_mixed) and event.tick >= notes_mixed[mixing_index]["tick"]:
                        mixing_index += 1
                    notes_mixed.insert(mixing_index, {'instrument': current_instrument, 'tick': event.tick, 'pitch': event.get_pitch()})
                elif event.get_velocity() != 0 and event.channel == 9:
                    while mixing_index < len(notes_mixed) and event.tick >= notes_mixed[mixing_index]["tick"]:
                        mixing_index += 1
                    notes_mixed.insert(mixing_index, {'instrument': 'precussion', 'tick': event.tick, 'pitch': event.get_pitch()})
                    drums.add(event.get_pitch())
                
            elif event.statusmsg == 0xFF and event.metacommand == 0x51:
                while mixing_index < len(notes_mixed) and event.tick >= notes_mixed[mixing_index]["tick"]:
                    mixing_index += 1
                #print(mixing_index, event.tick, notes_mixed[mixing_index]["tick"], event.tick >= notes_mixed[mixing_index]["tick"])
                notes_mixed.insert(mixing_index, {'instrument': 'tempo', 'tick': event.tick, 'bpm': event.get_bpm()})
                
            elif event.statusmsg == 0xC0:
                current_instrument = event.get_value()
                if current_instrument not in instruments:
                    instruments.add(current_instrument)
                
            else:
                print(event)
        
        n += 1
    
    return notes_mixed

def gdcize(notes):
    gdcevents = []
    delta = 0
    last_tick = 0
    bpm = 120
    freq = 0
    gdcindex = 0
    for note in notes:
        if note['instrument'] == 'dummy':
            continue
        if note['instrument'] == 'tempo':
            bpm = note['bpm']
            continue
        
        delta = note['tick'] - last_tick
        #print(note['tick'], last_tick, delta)
        last_tick = note['tick']
        if delta != 0:
            if freq != round(resolution*bpm/delta) and round(resolution*bpm/delta) != 0:
                freq = round(resolution*bpm/delta)
                gdcevents.insert(gdcindex, GDCevent("!speed", freq))
                gdcindex += 1
        else:
            gdcevents.append(GDCevent("!combine"))
        
        if note['instrument'] == 'precussion':
            gdcindex = len(gdcevents)
            gdcevents.append(GDCevent(drum_mappings[note['pitch']]))
        else:
            gdcindex = len(gdcevents)
            gdcevents.append(GDCevent(instrument_mappings[note['instrument']], note['pitch'] - default_pitch))
    
    return gdcevents

def writeevents(gdcevents, filename):
    f = open(filename, 'w')
    for gdcevent in gdcevents:
        gdcevent.appendtofile(f)

def load():
    global notes_mixed
    
    pattern = loadmidi(filedialog.askopenfilename())
    notes_mixed = mix(pattern)
    #print(notes_mixed)
    
    global instruments
    global instrument_widgets
    global instrument_variables
    global instframe
    
    selector(instruments, instrument_widgets, instrument_variables, instframe, instrument_names.INSTRUMENT_NAMES, instrument_names.GDC_INSTRUMENTS)
    
    global drums
    global drum_widgets
    global drum_variables
    global drumframe
    
    selector(drums, drum_widgets, drum_variables, drumframe, instrument_names.PRECUSSION_NAMES, instrument_names.GDC_INSTRUMENTS, instrument_names.PRECUSSION_DEFAULTS)

def update_mappings():
    global instrument_variables
    global instrument_mappings
    
    for instrument in instrument_variables:
        instrument_mappings[instrument] = instrument_variables[instrument].get()
    print(instrument_mappings)
    
    global drum_variables
    global drum_mappings
    for drum in drum_variables:
        drum_mappings[drum] = drum_variables[drum].get()
    print(drum_mappings)

def selector(values, widgets, variables, parent, names, options, defaults=None):
    # need to clear widgets each time to avoid issues
    for i in widgets:
        widgets[i]['label'].destroy()
        widgets[i]['combobox'].destroy()
    widgets = {}
    
    n = 0
    for value in values:
        if not defaults or not defaults[value]:
            variables[value] = StringVar(value=default_instrument)
        else:
            variables[value] = StringVar(value=defaults[value])
        widgets[value] = {
            'label': ttk.Label(parent, text=names[value]),
            'combobox': ttk.Combobox(parent, textvariable=variables[value])
            }
        widgets[value]['label'].grid(column=0, row=n, sticky=(N, W, E, S))
        widgets[value]['combobox'].grid(column=1, row=n, sticky=(N, W, E, S))
        widgets[value]['combobox']["values"] = options
        n += 1

def run():
    global notes_mixed
    
    update_mappings()
    gdcevents = gdcize(notes_mixed)
    writeevents(gdcevents, filedialog.asksaveasfilename())


openbutton = ttk.Button(mainframe, text="Open", command=load)
openbutton.grid(column=0, columnspan=1, row=0, sticky=(W, E))
runbutton = ttk.Button(mainframe, text="Run", command=run)
runbutton.grid(column=0, columnspan=1, row=2, sticky=(W, E))

root.mainloop()
